from util          import *
from wifi          import *
from timing        import *
from lighting      import *
from ws_client     import *
from interface     import *
from scene_manager import *

_RESET_NO   = const(0)
_RESET_WS   = const(1)
_RESET_WIFI = const(2)

ⴳ,ⴴ = True,False
preset_normal = { "mode": { "effects": [["Rotate", [-1,0]]],
                            "_"      : ["atom", [50, ["Rainbow",[5.0 ,0xFF,0xFF]]]]} }
preset_ap     = { "mode": { "effects": [["Rotate", [-1,0]]],
                            "_"      : ["atom", [50, ["Static" ,[0x00,0xFF,0x00]]]]} }

for i in range(10): # blinky at boots
  onboard_led(~i%2)
  sleep(0.05)

𝔐 = Scene_Manager()
ℭ = Settings(WS_URL     =("ws://brynic_led_test.ganer.xyz:2095",        ),
             UUID       =(gen_id                               ,        ),
             TOKEN      =(                                              ),
             NAME       =(                                              ),
             R_SSID     =(                                              ),
             R_PASS     =(                                              ),
             LEDP       =(23                                   , int    ),
             LEDC       =(300                                  , int    ),
             REVERSE    =(False                                , boolstr),
             BIT_TIMING =("400 850 800 450"                    ,        ),
             RGB_ORDER  =("RGB"                                ,        ) )
if not ℭ.name: ℭ.name = ℭ.UUID
ℭ.RGB_ORDER = parse_rgb_mode(ℭ.RGB_ORDER)
log(ℭ)

controller = LED_Controller(ℭ,𝔐)
thread(controller.loop)

update_LED_HW = lambda: controller.configure(ℭ.LEDP,ℭ.RGB_ORDER,ℭ.REVERSE,ℭ.BIT_TIMING)
update_LED_HW()

def lw_WAN():
  try:
    if not all(ℭ("token","r_ssid","r_pass")):
      raise Exception("Credentials not found.")
    controller(preset_normal)
    if not wifi_connect(*ℭ("r_ssid","r_pass")):
      raise Exception(f'Could not connect to WiFi!')
    Time(); free()
  except Exception as ε:
    dbg(f'Could not connect to WiFi:',ε)
    log("Starting AP.")
    controller(preset_ap)
    def get(path):
      return 200,"text/html",read_file("index.html")
    def post(path,body):
      try:
        ℭ(𝔍l(body))
        reset()
      except Exception as ε:
        dbg(f"Error getting credentials from AP:",ε)
        return 400,"application/json",𝔍d({"msg":"Cannot parse credentials!"})
    AP_with_DNS(get,post,timeout=60**2,timeout_f=reset)
    reset()

def handle_API(𝐦,d=None):
  log(f'Handling API "{𝐦}"')
  if 𝐦=="Change_dev":
    WCON = set("WS_URL DELETE".split())
    ICON = set("R_SSID R_PASS".split())
    RLED = set("LEDP LEDC REVERSE BIT_TIMING RGB_ORDER".split())
    
    D = { k.upper():v for k,v in d.items() }
    K = set(D)
    
    if "RGB_ORDER" in D:
      D["RGB_ORDER"] = parse_rgb_mode(d['RGB_ORDER'])
    if K & {"DELETE","UUID"}:
      D["NAME"] = D["UUID"] = gen_id()
    
    ℭ({ k:v for k,v in D.items() if k in ℭ })
    
    if K & RLED: update_LED_HW()
    if K & ICON: return _RESET_WIFI,_RESET_WIFI
    if K & WCON: return _RESET_WS  ,_RESET_WS
  elif 𝐦=="Set_scene":
    name,que,dur,t = d
    if dur == -1: dur = None
    if name not in 𝔐: return _RESET_NO,False
    log(f"Setting scene {name} on {controller} with {t=}")
    controller(name,que,dur,None,t)
    return _RESET_NO,True
  elif 𝐦=="Del_scene":
    return _RESET_NO,𝔐.__delitem__(d)
  elif 𝐦=="Push_scenes":
    return _RESET_NO,𝔐.bulk_save(d)
  elif 𝐦=="Pull_scenes":
    return _RESET_NO,𝔐.bulk_dump()
  elif 𝐦=="Set_schedule":
    log(f"󰤱 Set_schedule ({d})") # 󰤱
  elif 𝐦=="Pull_schedule":
    log(f"󰤱 Pull_schedule") # 󰤱
  return _RESET_NO,False

def lw_websocket_loop():
  ꭐ = WS_Client(ℭ.WS_URL)
  log("Connected to WS!")
  ꭐ({k:ℭ[k] for k in "token UUID LEDC REVERSE RGB_ORDER".split()})
  free()
  while 1:
    i,cmd = ꭐ()
    cmd = 𝔍l(cmd)
    # log(f"Got WS Command {i.hex()}: {cmd}")
    con,resp = handle_API(*𝔪(cmd))
    if resp is not None: ꭐ(resp,i=i)
    if con:
      try                  : ꭐ.close()
      except Exception as ε: dbg(f'Failed to close WS:',ε)
      if con == _RESET_WIFI: return con
      break
    frees(0.01)

update_LED_HW()
try:
  while 1:
    lw_WAN()
    while 1:
      try:
        if lw_websocket_loop() == _RESET_WIFI:
          log("Resetting WiFi")
          free(); break
      except OSError   as ε: dbg(f'WebSocket connection failed! Restarting in 5 seconds:',ε)
      except Exception as ε: dbg(f'Error in WebSocket loop! Restarting in 5 seconds:',ε)
      frees(5)
except:
  controller.loop = 0
  raise