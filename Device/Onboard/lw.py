from wifi          import AP_with_DNS
from settings      import ℭ,wifi_from_ℭ
from ws_client     import WS_Client
from controller    import Controller,controller_check_ntp
from scene_manager import get_scheg,check_scheg,update_scheg,Scene_Manager
from util          import *

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

# @micropython.native
# def bruh():
#   while 1:
#     frees(0.05)
# thread(bruh)

update_LED_HW = lambda: 𝔏.configure(ℭ.LEDP,ℭ.RGB_ORDER,ℭ.REVERSE,ℭ.BIT_TIMING)
update_LED_HW()

def lw_WAN():
  try:
    wifi_from_ℭ(ℭ)
    controller_check_ntp(𝔏,True)
    𝔏()
    check_scheg(𝔏)
    free()
  except Exception as ε:
    dbg(f'[LW] Could not connect to WiFi:',ε)
    log(f"[LW] Starting AP.")
    𝔏("_ap")
    def get(path):
      return 200,"text/html",read_file("index.html")
    def post(path,body):
      try:
        ℭ(𝔍l(body))
        reset()
      except Exception as ε:
        dbg(f"[LW] Error getting credentials from AP:",ε)
        return 400,"application/json",𝔍d({"msg":"Cannot parse credentials!"})
    AP_with_DNS(get,post,timeout=60**2,timeout_f=reset)
    reset()

def handle_API(𝐦,d=None):
  log(f'[API] Handling "{𝐦}"')
  if 𝐦=="Change_dev":
    WCON = set("WS_URL DELETE".split())
    ICON = set("R_SSID R_PASS".split())
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
      r = 𝔍d(controller_check_ntp(𝔏,True))
    except Exception as ε:
      log("[API] NTP Sync failed!",ε)
      r = False
    return _RESET_NO,str(r)
  return _RESET_NO,False

def lw_check_periodics():
  controller_check_ntp(𝔏)
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

update_LED_HW()
try:
  while 1:
    lw_WAN()
    while 1:
      try:
        r = lw_websocket_loop()
        if   r == _RESET_BOOT:
          log("[WS] Resetting machine")
          reset()
        elif r == _RESET_WIFI:
          log("[WS] Resetting WiFi")
          free(); break
        else:
          raise Exception("Websocket loop exited for an unknown reason!")
      except OSError   as ε: dbg(f'[WS] Connection failed! Restarting in 5 seconds:',ε)
      except Exception as ε: dbg(f'[WS] Error in loop! Restarting in 5 seconds:',ε)
      frees(5)
except:
  𝔏.loop = 0
  raise