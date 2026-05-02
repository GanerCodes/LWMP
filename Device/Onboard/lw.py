from machine       import reset
from _thread       import start_new_thread,stack_size
from time          import sleep
from math          import inf
from util          import *
from net           import AP_with_DNS
from settings      import ℭ,wifi_from_ℭ,parse_rgb_mode
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
free()

log(f"[LW] Starting with Settings={ℭ}");
𝔐 = Scene_Manager()
𝔏 = Controller(ℭ,𝔐)
stack_size(6*1024); start_new_thread(𝔏.loop,()) # 󰤱 was 9*1024 before SSL stuff

del stack_size,start_new_thread,i

def handle_API(𝐦,*𝔸):
  log(f'[API] Handling "{𝐦}"')
  if 𝐦=='*':
    rst,𝚁 = _RESET_NO,[]
    for 𝕒 in 𝔸:
      s,e = handle_API(*𝕒)
      𝚁.append(e)
      rst = max(rst,s)
    return rst,𝚁
  if 𝐦=="Change_dev":
    BOOT = set("VER".split())
    ICON = set("R_SSID R_PASS AP_MODE".split())
    WCON = set("UPDATE_URL WS_URL TOKEN".split())
    RLED = set("RECALB_T LEDP LEDC REVERSE BIT_TIMING RGB_ORDER".split())
    
    # 󰤱󰤱󰤱󰤱󰤱󰤱󰤱󰤱󰤱󰤱󰤱󰤱
    Δ = {}
    for k,v in 𝔸[0].items():
      k = k.upper()
      if k not in ℭ or k=="UUID":
        log(f'Ignoring key "{k}"')
        continue
      Δ[k] = v
    K = set(Δ)
    log(f"[API] Changing settings with",Δ)
    
    if "VER" in Δ:
      v = str(Δ["VER"]).strip()
      if v != ℭ.VER: write_file("UPDATE_FLAG",v)
      del Δ["VER"]
    ℭ(Δ)
    if "LOG_LEVEL" in Δ: Logger.set(Δ["LOG_LEVEL"])
    del Δ
    
    if K & RLED: 𝔏.configure()
    if K & BOOT: return _RESET_BOOT,_RESET_BOOT
    if K & ICON: return _RESET_WIFI,_RESET_WIFI
    if K & WCON: return _RESET_WS  ,_RESET_WS
    return              _RESET_NO  ,True
  elif 𝐦=="Set_scene":
    s,q,dur,Ts = 𝔸
    if s not in 𝔐:
      log(f'[API] Scene "{s}" not found!')
      return _RESET_NO,False
    𝔏(s,q,dur,None,Ts)
    if not q and dur in (-1,inf,None): ℭ.DEF_SCENE = s
    return _RESET_NO,True
  elif 𝐦=="Off"          : return _RESET_NO,𝔏.off() or True # 󰤱 make this become default scene
  elif 𝐦=="Del_scene"    : return _RESET_NO,𝔐.__delitem__(𝔸[0])
  elif 𝐦=="Push_scenes"  : return _RESET_NO,𝔐.bulk_save(𝔸[0])
  elif 𝐦=="Pull_scenes"  : return _RESET_NO,𝔐.bulk_dump()
  elif 𝐦=="Set_schedule" : return _RESET_NO,update_scheg(𝔏,𝔸[0])
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
  ꭐ({k:ℭ[k] for k in "VER TOKEN UUID NAME RECALB_T LEDC REVERSE RGB_ORDER".split()})
  free()
  while 1:
    if (w:=ꭐ()) is None:
      log0('-',end='')
      lw_check_periodics()
      continue
    else:
      log0('+',end='')
    i,cmd = w
    cmd = 𝔍l(cmd)
    free()
    try:
      con,resp = handle_API(*cmd)
    except Exception as ε:
      dbg("[API] Error!",ε)
      # con,resp = _RESET_WS,"ERROR"
      con,resp = _RESET_NO,"ERROR" # 󰤱 why was I resetting on bad request?
    if resp is not None: ꭐ(resp,i=i)
    if con > _RESET_NO:
      try                  : ꭐ.close(reason="Intentional")
      except Exception as ε: dbg(f'[WS] Failed to close WS:',ε)
      return con
    frees()

def lw_AP(setup=False):
  log(f"[LW] Starting AP.")
  def get(path):
    return 200,"text/html",read_file("index.html.gz","rb")
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
        raise Exception(f'Websocket loop exited for an unknown reason ({r})!')
    except OSError   as ε:
      dbg(f'[LW-WS] Connection failed! Resetting net:',ε)
      return
    except Exception as ε:
      dbg(f'[LW-WS] Error in loop! Restarting in 5 seconds:',ε)
    frees(5)

try:
  while lw_net() != _RESET_BOOT: pass
except BaseException as ε:
  𝔏.lstate = 0
  dbg("[LW] Top level exception in network loop",ε)
  if isinstance(ε,KeyboardInterrupt):
    raise ε # avoid reset()
reset()