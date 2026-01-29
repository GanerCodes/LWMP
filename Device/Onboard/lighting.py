from util      import *
from timing    import *
from interface import *
from lightwave import *

_LOOP_NONE     = const(0)
_LOOP_TIGHT    = const(1)
_LOOP_NEW_MODE = const(2)
_LOOP_NEW_HW   = const(3)

# import esp32

# @micropython.viper
# def ws2812_pulses(buf:ptr8,buf_size:int,out:ptr8): # 400 850 800 450
#   for i in range(buf_size):
#     I = 16*i
#     for o in range(8):
#       if buf[i] & (1 << (7 - o)):
#         out[I+o  ] = 32
#         out[I+o+1] = 64
#       else:
#         out[I+o  ] = 68
#         out[I+o+1] = 36

# # r = esp32.RMT(pin=machine.Pin(23), resolution_hz=40000000, clock_div=1)
# r = esp32.RMT(0, pin=machine.Pin(23), resolution_hz=80000000)
# def output_leds(leds,pinout,timing):
#   print("yeag")
#   pulses = bytearray(16*len(leds))
#   ws2812_pulses(bytearray(leds),len(leds),pulses)
#   r.write_pulses(tuple(pulses),1)
#   # esp32.RMT.wait_done(timeout=99)
#   del pulses
#   gc.collect()
#   # machine.bitstream(pinout,0,timing,leds)

def output_leds(leds,pinout,timing):
  machine.bitstream(pinout,0,timing,leds)

@micropython.viper
def render_leds(S:ptr8,S_len:int,atoms:ptr8,stk:ptr8,leds:ptr8,RGB_OFF:int,l:int,h:int,t):
  assign_leds(S,S_len,atoms,stk,leds,RGB_OFF,l,h,t)

class LED_Controller:
  __repr__ = lambda 𝕊: f"LED_Controller⟨{𝕊.dmode} lstate={𝕊.lstate}⟩"
  def __init__(𝕊,ℭ):
    𝕊.ℭ,𝕊.lstate = ℭ,_LOOP_NEW_HW
    𝕊.mode = 𝕊.dmode = 𝕊.time_sync = None
  def configure(𝕊,pin=23,order=(0,1,2),timing=(400,850,800,450)):
    if isinstance(timing,str): timing = tuple(map(int,timing.strip().split()))
    print(f"Configuring controller with {pin=} {order=} {timing=}")
    𝕊.dmode = pin,parse_rgb_mode(order),tuple(timing)
    𝕊.lstate = _LOOP_NEW_HW
    return 𝕊
  def __call__(𝕊,N,time_sync=None):
    if time_sync is not None: 𝕊.time_sync = int(time_sync)
    𝕊.mode,𝕊.lstate = N,max(𝕊.lstate,_LOOP_NEW_MODE)
  def update_wait_params_safe(𝕊,lstate):
    if lstate == _LOOP_NEW_HW:
      while 𝕊.dmode is None: # we need the HW params
        gc.collect(); sleep(0.025)
      p,𝕊.order,𝕊.timing = 𝕊.dmode
      𝕊.pinout = machine.Pin(p)
      𝕊.pinout.init(𝕊.pinout.OUT)
      𝕊.lstate = _LOOP_NEW_MODE
    while 𝕊.mode is None: # we need the mode
      gc.collect(); sleep(0.025)
    𝕊.lstate = 1
  def get_Δ(𝕊,ntp=False):
    if 𝕊.time_sync is not None:
      if ntp: Time()
      m,T,S = Tick.ms(),Time.ms(),𝕊.time_sync
      if abs(T-S) < 60**2 * 1000: 
        return T-S-m # ✣ ms+Δ = 0 ⟺ T=S
      else:
        return -m # something is rlly bad if the request is an hour out of date
    else:
      return -Tick.ms()
  @micropython.native
  def loop(𝕊):
    𝕊.lstate = max(𝕊.lstate,_LOOP_NEW_MODE)
    t,M,ΔR,ΔS = 0,120,1,120#45*60
    ms = Tick.ms
    while 𝕊.lstate:
      try:
        while lstate := 𝕊.lstate:
          if lstate > _LOOP_TIGHT:
            gc.collect()
            𝕊.update_wait_params_safe(lstate)
            S,atoms,stk,leds,(l,h) = mode_to_bufs(𝕊.ℭ,𝕊.mode)
            pinout,order,timing = 𝕊.pinout,𝕊.order,𝕊.timing
            Δ = 𝕊.get_Δ()
            tq,tr = divmod(ms()+Δ,1000)
            t_R,t_S,n = tq+ΔR,tq+ΔS,0
            S_len = len(S)//24
            log(f"{len(leds)=} {l=} {h=}; {sum(timing)*len(leds)*8 / 1_000_000_000}ms")
            gc.collect()
          
          tq,tr = divmod(ms()+Δ,1000)
          t     = tq+0.001*float(tr)
          render_leds(S,S_len,atoms,stk,leds,order,l,h,t)
          # assign_leds(S,S_len,atoms,stk,leds,order,l,h,t)
          output_leds(leds,pinout,timing)
          
          n+=1
          if not n%M:
            gc.collect(); sleep(0)
          if tq>=t_R:
            log(f"{t:12.5f}: FPS={n:6.2f} {n=} {tq=} {t_R=} {t_S=} [{' '.join(map(str,Time.now()))}]") # time={' '.join(map(str,Time.now()))}")
            if tq>=t_S:
              Δ = 𝕊.get_Δ(ntp=True)
              tq,tr = divmod(ms()+Δ,1000)
              t_S = tq+ΔS
            t_R,n = tq+ΔR,n%M
      except Exception as ε:
        dbg(f"Error in LED loop! Restarting in 3 seconds:",ε)
        gc.collect(); sleep(3)

__all__ = "LED_Controller",