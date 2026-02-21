from util          import *
from net           import AP_with_DNS
from settings      import ℭ,wifi_from_ℭ
from ws_client     import WS_Client
from controller    import Controller
from scene_manager import get_scheg,check_scheg,update_scheg,Scene_Manager

_RESET_NO   = const(0)
_RESET_WS   = const(1)
_RESET_WIFI = const(2)
_RESET_BOOT = const(3)

for i in range(10): # blinky at boots
  onboard_led(~i%2)
  sleep(0.05)
del i

log(f"[LW] Starting with Settings={ℭ}");
𝔐 = Scene_Manager()
𝔏 = Controller(ℭ,𝔐)
thread(𝔏.loop)

update_LED_HW = lambda: 𝔏.configure(ℭ.LEDP,ℭ.RGB_ORDER,ℭ.REVERSE,ℭ.BIT_TIMING)
update_LED_HW()

def handle_API(𝐦,d=None):
  log(f'[API] Handling "{𝐦}"')
  if 𝐦=="Change_dev":
    WCON = set("WS_URL DELETE".split())
    ICON = set("R_SSID R_PASS AP_MODE".split())
    RLED = set("LEDP LEDC REVERSE BIT_TIMING RGB_ORDER".split())
    
    D = { k.upper():v for k,v in d.items() }
    K = set(D)
    
    if "VER" in D and D["VER"] != ℭ.VER:
      write_file("UPDATE_FLAG",str(D["VER"]).strip())
      return _RESET_BOOT,_RESET_BOOT
    
    if "RGB_ORDER" in D     : D["RGB_ORDER"] = parse_rgb_mode(d['RGB_ORDER'])
    if K & {"DELETE","UUID"}: D["NAME"] = D["UUID"] = gen_id()
    
    ℭ({ k:v for k,v in D.items() if k in ℭ })
    
    if K & RLED: update_LED_HW()
    if K & ICON: return _RESET_WIFI,_RESET_WIFI
    if K & WCON: return _RESET_WS  ,_RESET_WS
  elif 𝐦=="Set_scene":
    s,q,dur,Ts = d
    if s not in 𝔐:
      log(f'[API] Scene "{s}" not found!')
      return _RESET_NO,False
    𝔏(s,q,dur,None,Ts)
    if not q and dur in (-1,inf,None): ℭ.DEF_SCENE = s
    return _RESET_NO,True
  elif 𝐦=="Del_scene"    : return _RESET_NO,𝔐.__delitem__(d)
  elif 𝐦=="Push_scenes"  : return _RESET_NO,𝔐.bulk_save(d)
  elif 𝐦=="Pull_scenes"  : return _RESET_NO,𝔐.bulk_dump()
  elif 𝐦=="Set_schedule" : return _RESET_NO,update_scheg(𝔏,d)
  elif 𝐦=="Pull_schedule": return _RESET_NO,get_scheg()
  elif 𝐦=="Sync":
    try:
      r = 𝔍d(𝔏.check_ntp(True))
    except Exception as ε:
      log("[API] NTP Sync failed!",ε)
      r = False
    return _RESET_NO,str(r)
  return _RESET_NO,False

def lw_check_periodics():
  𝔏.check_ntp()
  check_scheg(𝔏)
  frees(0.05)

def lw_websocket_loop():
  lw_check_periodics()
  ꭐ = WS_Client(ℭ.WS_URL)
  log("[WS] Connected.")
  ꭐ({k:ℭ[k] for k in "token UUID LEDC REVERSE RGB_ORDER VER".split()})
  free()
  while 1:
    if (w:=ꭐ()) is None:
      lw_check_periodics()
      continue
    i,cmd = w
    cmd = 𝔍l(cmd)
    free()
    try:
      con,resp = handle_API(*cmd['_'])
    except Exception as ε:
      dbg("[API] Error!",ε)
      con,resp = _RESET_WS,"ERROR"
    if resp is not None: ꭐ(resp,i=i)
    if con > _RESET_NO:
      try                  : ꭐ.close()
      except Exception as ε: dbg(f'Failed to close WS:',ε)
      if con > _RESET_WS   : return con
      break
    frees()

def lw_AP(setup=False):
  log(f"[LW] Starting AP.")
  def get(path):
    return 200,"text/html",read_file("index.html.gzip","rb")
  def post(path,body):
    try:
      body = 𝔍l(body) if body else ""
      if path=="/getConfig":
        return 200,"application/json",𝔍d({
          "modes" : join(𝔐()),
          "R_SSID": ℭ.R_SSID,"R_PASS": ℭ.R_PASS,
          "TOKEN" : ℭ.TOKEN ,"setup" : False })
      if   path=="/config":
        ℭ(body)
        if "TOKEN" in body: return 200,"text/plain","Exiting AP",True
      elif path=="/mode":
        𝔏(m := body["mode"])
        ℭ.DEF_SCENE = m
    except Exception as ε:
      dbg(f"[LW] Error in AP:",ε)
      return 400,"text/plain","Error!"
    return 200,"text/plain","Success!"
    
  dottrim = lambda x,l=10,d="...": x[:l-len(d)]+d if len(x)>l else x
  AP_with_DNS(get,post,timeout=60**2 if setup else None,
              ssid=f"LightWave Controller {dottrim(ℭ.uuid,10)}")

def lw_net():
  if ℭ.AP_MODE:
    𝔏()
    lw_AP()
    return
  
  try:
    close_wifi = wifi_from_ℭ(ℭ)
  except Exception as ε:
    dbg(f'[LW] Could not connect to WiFi:',ε)
    𝔏("_ap")
    lw_AP(True)
    return
  
  try:
    𝔏.check_ntp(True)
    𝔏()
    check_scheg(𝔏)
  except Exception as ε:
    dbg("[LW] Unhandled Exception!",ε)
  
  while 1:
    free()
    try:
      r = lw_websocket_loop()
      if r == _RESET_BOOT:
        log("[LW-WS] Resetting machine")
        return r
      if r == _RESET_WIFI:
        log("[LW-WS] Resetting WiFi")
        close_wifi()
        break
      if r == _RESET_WS:
        log("[LW-WS] Resetting WS")
        continue
      else:
        raise Exception("Websocket loop exited for an unknown reason!")
    except OSError   as ε:
      dbg(f'[LW-WS] Connection failed! Resetting net:',ε)
      return
    except Exception as ε:
      dbg(f'[LW-WS] Error in loop! Restarting in 5 seconds:',ε)
    frees(5)

update_LED_HW()
try:
  while lw_net() != _RESET_BOOT: pass
except BaseException as ε:
  𝔏.lstate = 0
  dbg("[LW] Top level exception in network loop",ε)
  if isinstance(ε,KeyboardInterrupt):
    raise ε
reset()