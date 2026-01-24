from util      import *
from timing    import *
from interface import *
from lightwave import *

_LOOP_NONE     = const(0)
_LOOP_TIGHT    = const(1)
_LOOP_NEW_MODE = const(2)
_LOOP_NEW_HW   = const(3)

@micropython.viper
def write_leds(S:ptr8,S_len:int,atoms:ptr8,stk:ptr8,leds:ptr8,t,RGB_OFF:int):
  assign_leds(S,S_len,atoms,stk,leds,t,RGB_OFF)

class LED_Controller:
  __repr__ = lambda 𝕊: f"LED_Controller⟨{𝕊.dmode} lstate={𝕊.lstate}⟩"
  def __init__(𝕊,*𝔸,autoconf=False,**𝕂):
    𝕊.lstate = _LOOP_NEW_HW
    𝕊.mode = 𝕊.dmode = 𝕊.time_sync = None
    if autoconf: 𝕊.configure(*𝔸,**𝕂)
  def configure(𝕊,pin=23,order=(0,1,2),timing=(400,850,800,450)):
    print(f"Configuring controller with {pin=} {order=} {timing=}")
    𝕊.dmode = pin,parse_rgb_mode(order),tuple(timing)
    𝕊.lstate = _LOOP_NEW_HW
    return 𝕊
  def __call__(𝕊,N,time_sync=None):
    if time_sync is not None: 𝕊.time_sync = int(time_sync)
    𝕊.mode,𝕊.lstate = N,max(𝕊.lstate,_LOOP_NEW_MODE)
  
  def update_wait_params_safe(𝕊,lstate):
    if lstate == _LOOP_NEW_HW:
      while 𝕊.dmode is None: # we need HW params
        gc.collect(); sleep(0.025)
      p,𝕊.order,𝕊.timing = 𝕊.dmode
      𝕊.pinout = machine.Pin(p)
      𝕊.pinout.init(𝕊.pinout.OUT)
      𝕊.lstate = _LOOP_NEW_MODE
    while 𝕊.mode is None: # we need the mode
      gc.collect(); sleep(0.025)
    𝕊.lstate = 1
  
  @micropython.native
  def loop(𝕊):
    𝕊.lstate = max(𝕊.lstate,_LOOP_NEW_MODE)
    ms = Tick.ms
    # ms = Time.ms
    ms_accurate = Time.ms
    # ms_accurate = lambda: (lambda x: x[-2] x[-1]//1000)(Time.now())
    
    t,M,ΔR = 0,120,0.25
    while lstate := 𝕊.lstate:
      try:
        if lstate > _LOOP_TIGHT:
          𝕊.update_wait_params_safe(lstate)
          if 𝕊.time_sync is not None:
            Time()
            m,T,S = ms(), ms_accurate(), 𝕊.time_sync
            if abs(T-S) > 60**2 * 1000: # something is rlly bad if the request is an hour out of date
              Δ = -m
            else:
              Δ = T-S-m # ✣ ms+Δ = 0 ⟺ T=S
          else:
            Δ = -ms()
          track,n = 0.001*float(ms()+Δ),0
          gc.collect()
          S,atoms,stk,leds = mode_to_bufs(𝕊.mode)
          pinout,order,timing = 𝕊.pinout,𝕊.order,𝕊.timing
          S_len = len(S)//24
          gc.collect()
        
        t = 0.001*float(ms()+Δ)
        write_leds(S,S_len,atoms,stk,leds,t,order)
        machine.bitstream(pinout,0,timing,leds)
        n+=1
        if not n%M or t>track+ΔR:
          gc.collect(); sleep(0)
          print(f"{t:12.5f}: FPS={n/(t-track or 0.001):6.2f} time={' '.join(map(str,Time.now()))}")
          track,n = t,0
          
      except Exception as ε:
        dbg(f"Error in LED loop! Restarting in 3 seconds:",ε)
        gc.collect(); sleep(3)

__all__ = "LED_Controller",