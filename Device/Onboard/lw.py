import ws_client
from util      import *
from wifi      import *
from timing    import *
from interface import *
from lighting  import *

for i in range(10):
  onboard_led(~i%2)
  sleep(0.05)

ℭ = Settings(WS_URL     =("wss://brynic_led_test.ganer.xyz:2096",                 ),
             UUID       =(gen_id                                ,                 ),
             TOKEN      =(                                                        ),
             R_SSID     =(                                                        ),
             R_PASS     =(                                                        ),
             LEDP       =(23                                    , int             ),
             LEDC       =(500                                   , int             ),
             REVERSE    =(False                                 , boolstr         ),
             BIT_TIMING =([400,850,800,450]                     ,                 ),
             RGB_ORDER  =(parse_rgb_mode("GRB")                 ,                 ) )

print(ℭ)

controller = LED_Controller(pin=ℭ.LEDP, order=ℭ.RGB_ORDER, timing=ℭ.BIT_TIMING)
thread(controller.loop)

preset_ap     = (0,0, [(0,0, [(0,0,50)]), (0,0.25, [(0,0,150)])])
preset_normal = (0,0.05, [(0,-0.05, [(0,0.1,100),(0.5,0,100),(0.5,0,100)]), (0,0,100), (0,0,100)])

# controller(preset_normal)
# controller.loop()

try:
  if not all(ℭ("token","r_ssid","r_pass")):
    raise Exception("Credentials not found.")
  if not wifi_connect(*ℭ("r_ssid","r_pass")):
    raise Exception(f'Could not connect to wifi!')
  Time()
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

controller(preset_normal)
# ws_client.connect(ℭ.WS_URL)

while 1:
  print(f"{Thread.get_ident()=}")
  sleep(1)