import ws_client
from utils     import *
from timing    import Time
from wifi      import wifi_connect,basic_AP
from interface import Displayer,parse_rgb_mode,parse_bit_timing

_FPS_DISPLAY_DELTA = const(20_000)
_TIMER_MODULO      = const(1<<24)

UUID        = gen_load_UUID()
WS_URL      = load_check_datafile("WS_URL"    , "wss://brynic_led_test.ganer.xyz:2096")
LED_PIN     = load_check_datafile("LED_PIN"   , "23"             , int                )
LED_COUNT   = load_check_datafile("LED_COUNT" , "500"            , int                )
REVERSE     = load_check_datafile("REVERSE"   , "False"          , boolstr            )
BIT_TIMING  = load_check_datafile("BIT_TIMING", "400 850 800 450", parse_bit_timing   )
RGB_ORDER   = load_check_datafile("RGB_ORDER" , "RGB"            , parse_rgb_mode     )

try:
  if "CREDENTIALS" not in os.listdir():
    raise Exception("Credentials file not found.")
  try:
    ROUTER_SSID,ROUTER_PASS,TOKEN = map(str.strip,read_file(f).split('\n')[:3])
  except Exception as ε:
    raise Exception(f'Could not parse credentials file: {ε}')
  if not wifi_connect(ROUTER_SSID,ROUTER_PASS):
    raise Exception(f'Could not connect to wifi!')
  Time()
except Exception as ε:
  print("Could not find wifi config, starting AP.")
  basic_AP() # 󰤱 
  machine.reset()

### TESTING STUFF ###

# N = (0,0.05, [(0,-0.05, [(0,0.1,100),(0.5,0,100),(0.5,0,100)]), (0,0,100), (0,0,100)])
N = (0,0.05, [(0,-0.05, [(0,0.1,25),(0.5,0,25),(0.5,0,25)]), (0,0,25), (0,0,25)])
# N = (0,0, [(0,0, [(0,0,50)]), (0,2.5, [(0,0,150)])])

display = Displayer().load_mode(N)

t0,next_t,n = Time.ms(),1,0
while True:
  try:
    t = 0.001*float(Time.ms()-t0)
    print(Time.ms())
    # print(Time.now(),Time.ms(),t)
    
    display(t)
    n+=1
    if t>next_t:
      print(n)
      next_t,n = t+1,0
  except KeyboardInterrupt:
    break

""" # ≈ 52FPS
# K = 5

S_buf,stk_buf,LED_buf = scheme_to_bufs(N)

BITSTREAM_TIMING = (400,850,800,450)
OFFSET_R,OFFSET_G,OFFSET_B = 0,1,2
RGB_OFF = (OFFSET_B<<16) | (OFFSET_G<<8) | OFFSET_R
PINOUT = machine.Pin(23)
PINOUT.init(PINOUT.OUT)

@micropython.viper
def test_assign_leds(S:ptr8,l:int,stk:ptr8,leds:ptr8,t,RGB_OFF:int):
    assign_leds(S,l,stk,leds,t,RGB_OFF)

def display_LEDS(buf):
    machine.bitstream(PINOUT,0,BITSTREAM_TIMING,buf)

t0,next_t,n = time.ticks_ms(),1,0
while True:
    try:
        # LED_buf = bytearray(len(LED_buf))
        t = 0.001*float(time.ticks_ms()-t0)
        test_assign_leds(S_buf,len(S_buf)//24,stk_buf,LED_buf,t,RGB_OFF)
        # h = bytearray(len(LED_buf)//K)
        # for i in range(0,len(h),3):
        #     for o in range(3):
        #         h[i+o] = int(sum(LED_buf[q] for q in range(i+o,i+o+3*K,3))/K)
        display_LEDS(LED_buf)
        
        n+=1
        if t>next_t:
            print(n)
            next_t,n = t+1,0
    except KeyboardInterrupt:
        break
    # print(''.join(map(str,struct.unpack('<'+'BBB'*(len(LED_buf)//3),LED_buf))))
"""