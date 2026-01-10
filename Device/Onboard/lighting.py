from util      import *
from timing    import *
from interface import *
from lightwave import *

@micropython.viper
def test_assign_leds(S:ptr8,l:int,stk:ptr8,leds:ptr8,t,RGB_OFF:int):
  assign_leds(S,l,stk,leds,t,RGB_OFF)

class LED_Controller:
  def __init__(𝕊,pin=23,order=(0,1,2),timing=(400,850,800,450)):
    𝕊.pinout = machine.Pin(pin)
    𝕊.pinout.init(𝕊.pinout.OUT)
    𝕊.timing = tuple(timing)
    𝕊.order = parse_rgb_mode(order)
    𝕊.mode,𝕊.loop = None,0
  def __call__(𝕊,N):
    𝕊.mode,𝕊.loop = 2,N
  @micropython.viper
  def loop(𝕊):
    𝕊.loop = 1
    ms = Tick.ms
    while loop := 𝕊.loop:
      if loop == 2:
        if 𝕊.mode is None:
          sleep(0.025)
          continue
        t0,next_t,n = Tick.ms(),1,0
        S_buf,stk_buf,LED_buf = mode_to_bufs(𝕊.mode)
        pinout,order,timing = 𝕊.pinout,𝕊.order,𝕊.timing
        l = len(S_buf)//24
        𝕊.loop = 1
        gc.collect()
      
      t = 0.001*float(ms()-t0)
      test_assign_leds(S_buf,l,stk_buf,LED_buf,t,order)
      machine.bitstream(pinout,0,timing,LED_buf)
      n+=1
      if t>next_t:
        print(f"{t:12.5f}: FPS: {n}")
        next_t,n = t+1,0
  __repr__ = lambda 𝕊: f"Controller⟨dargs={𝕊.dargs}⟩"

__all__ = "LED_Controller",