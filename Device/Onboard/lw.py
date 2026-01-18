import ws_client
from util          import *
from wifi          import *
from timing        import *
from lighting      import *
from interface     import *
from scene_manager import *

_RESET_NO   = const(0)
_RESET_WS   = const(1)
_RESET_WIFI = const(2)

preset_ap     = (0,0, [(0,0, [(0,0,50)]), (0,0.25, [(0,0,150)])])
preset_normal = (0,0.05, [(0,-0.05, [(0,0.1,100),(0.5,0,100),(0.5,0,100)]), (0,0,100), (0,0,100)])

for i in range(10): # blinky at boots
  onboard_led(~i%2)
  sleep(0.05)

controller = LED_Controller(autoconf=False)
thread(controller.loop)

𝔐 = Scene_Manager()
ℭ = Settings(WS_URL     =("ws://brynic_led_test.ganer.xyz:2095",        ),
             UUID       =(gen_id                               ,        ),
             TOKEN      =(                                              ),
             NAME       =(                                              ),
             R_SSID     =(                                              ),
             R_PASS     =(                                              ),
             LEDP       =(23                                   , int    ),
             LEDC       =(505                                  , int    ),
             REVERSE    =(False                                , boolstr),
             BIT_TIMING =([400,850,800,450]                    ,        ),
             RGB_ORDER  =(parse_rgb_mode("GRB")                ,        ) )
if not ℭ.name: ℭ.name = ℭ.UUID
print(ℭ)

update_LED_HW = lambda: controller.configure(pin=ℭ.LEDP, order=ℭ.RGB_ORDER, timing=ℭ.BIT_TIMING)
update_LED_HW()

def lw_WAN():
  try:
    if not all(ℭ("token","r_ssid","r_pass")):
      raise Exception("Credentials not found.")
    controller(preset_normal)
    if not wifi_connect(*ℭ("r_ssid","r_pass")):
      raise Exception(f'Could not connect to wifi!')
    Time(); gc.collect()
  except Exception as ε:
    print(f'Could not connect to wifi: {ε}\nStarting AP.')
    controller(preset_ap)
    def get(path):
      return 200,"text/html",read_file("index.html")
    def post(path,body):
      try:
        ℭ(𝔍l(body))
        machine.reset()
      except Exception as ε:
        print(f"Error getting credentials from AP: {ε}")
        return 400,"application/json",𝔍d({"msg":"Cannot parse credentials!"})
    AP_with_DNS(get,post,timeout=60**2,timeout_f=machine.reset)
    machine.reset()

def handle_API(𝐦,d=None):
  print(f"handle_API({𝐦},{d})")
  if 𝐦=="Change_dev":
    WCON = set("WS_URL DELETE".split())
    ICON = set("R_SSID R_PASS".split())
    RLED = set("LEDP LEDC REVERSE BIT_TIMING RGB_ORDER".split())
    
    ℭ({ k.upper():v for k,v in d.items() if k in ℭ }) # allows setting uuid, bad?
    if "delete" in d:
      # 󰤱􊽨 regenerate uuid?
      ℭ.name = ℭ.uuid
    
    K = set(k.upper() for k in d)
    if K & RLED: update_LED_HW()(preset_normal)
    if K & ICON: return _RESET_WIFI,None
    if K & WCON: return _RESET_WS  ,None
  elif 𝐦=="Set_scene":
    log(f"󰤱 Set_scene ({d})") # 󰤱
  elif 𝐦=="Del_scene":
    return _RESET_NO,𝔐.__delitem__(d["scene"])
  elif 𝐦=="Push_scenes":
    return _RESET_NO,𝔐.bulk_save(d["scenes"])
  elif 𝐦=="Pull_scenes":
    return _RESET_NO,𝔐.bulk_dump()
  elif 𝐦=="Set_schedule":
    log(f"󰤱 Set_schedule ({d})") # 󰤱
  return _RESET_NO,None

def lw_websocket_loop():
  𝘞 = ws_client.connect(ℭ.WS_URL)
  𝘞({k:ℭ[k] for k in "token UUID LEDC REVERSE RGB_ORDER".split()})
  while 1:
    cmd = 𝔍l(𝘞())
    print(f"WS Command: {cmd}")
    con,resp = handle_API(*𝔪(cmd))
    if resp is not None: 𝘞(resp) # 󰤱 new WS stuff
    if con:
      try                  : 𝘞.close()
      except Exception as ε: print(f"Failed to close WS: {ε}")
      if con == _RESET_WIFI: return con
      break
    gc.collect(); sleep(0.1)

update_LED_HW()
try:
  while 1:
    lw_WAN()
    while 1:
      try:
        if lw_websocket_loop() == _RESET_WIFI:
          print("Resetting WiFi")
          gc.collect(); break
      except OSError as ε:
        print(f"WebSocket connection failed! Restarting in 5 seconds: {ε}")
      except Exception as ε:
        print(f"Error in WebSocket loop! Restarting in 5 seconds: {ε}")
      sleep(5)
except:
  controller.loop = 0