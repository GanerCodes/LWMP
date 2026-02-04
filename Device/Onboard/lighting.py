from util          import *
from timing        import *
from interface     import *
from lightwave     import *
from scene_manager import *

_LOOP_NONE     = const(0)
_LOOP_TIGHT    = const(1)
_LOOP_NEW_MODE = const(2)
_LOOP_NEW_HW   = const(3)

Activation = namedtuple("Activation",["s","d","Ta","Ts"])

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
# # r = esp32.RMT(pin=Pin(23), resolution_hz=40000000, clock_div=1)
# r = esp32.RMT(0, pin=Pin(23), resolution_hz=80000000)
# def output_leds(leds,pinout,timing):
#   print("yeag")
#   pulses = bytearray(16*len(leds))
#   ws2812_pulses(bytearray(leds),len(leds),pulses)
#   r.write_pulses(tuple(pulses),1)
#   # esp32.RMT.wait_done(timeout=99)
#   del pulses
#   free()
#   # bitstream(pinout,0,timing,leds)


@micropython.viper
def render_leds(S:ptr8,S_len:int,atoms:ptr8,stk:ptr8,leds:ptr8,RGB_OFF:int,REVERSE:int,l:int,h:int,t):
  assign_leds(S,S_len,atoms,stk,leds,RGB_OFF,REVERSE,l,h,t)
@micropython.native
def output_leds(leds,pinout,timing):
  bitstream(pinout,0,timing,leds)

class LED_Controller:
  __repr__ = lambda 𝕊: f"LED_Controller⟨{𝕊.dmode} lstate={𝕊.lstate}⟩"
  def __init__(𝕊,ℭ,𝔐):
    𝕊.ℭ,𝕊.lstate = ℭ,_LOOP_NEW_HW
    𝕊.scenes = Scene_Cacher(𝔐)
    𝕊.dmode,𝕊.𝔔 = None,[]
  
  def configure(𝕊,pin=23,order=(0,1,2),reverse=False,timing=(400,850,800,450)):
    if isinstance(timing,str): timing = tuple(map(int,timing.strip().split()))
    print(f"Configuring controller with {pin=} {order=} {reverse=} {timing=}")
    𝕊.dmode = pin,parse_rgb_mode(order),bool(reverse),tuple(timing)
    𝕊.lstate = _LOOP_NEW_HW
    return 𝕊
  
  # ¿q     : ¿Ta󷸆: Ta = 𝔔 ⭜⁰ after(𝔔⤉)
  # ¡      : ¿Ta󷸆: Ta = 0
  #          𝔔 = 𝔔󰈳󷺻Ta≤⟞ᵀᵃ<Ta+dᐸ
  def __call__(𝕊,s,q=False,d=inf,Ta=None,Ts=None):
    𝔔 = 𝕊.𝔔
    s = 𝕊.scenes[s]
    if d  is None      : d  = inf
    if Ta is None      : Ta = max(𝔔).Ta+max(𝔔).d if q and 𝔔 else 0
    if Ts is None and 𝔔: Ts = 𝔔[-1].Ts
    if not q:
      X = [ν for ν in 𝔔 if not (Ta <= ν.Ta < Ta+d)] # slow lol
      h_from(X)
      𝔔[:] = X
      # 󰤱 set as default background scene if dur == ∞ (? require that Ta is None)?
    h_add(𝔔,Activation(s,d,Ta,Ts))
    frees()
    𝕊.lstate = max(𝕊.lstate,_LOOP_NEW_MODE)
  
  # @micropython.native
  def loop(𝕊,ms=ms,MS=MS):
    𝕊.lstate = max(𝕊.lstate,_LOOP_NEW_MODE)
    
    𝔔,ℭ = 𝕊.𝔔,𝕊.ℭ
    t,mode = 0,None
    N,ΔR,ΔS = 30,1,60 #45*60
    pin=order=reverse=timing=None
    
    @micropython.native
    def get_wait_hwconf():
      while 𝕊.lstate and 𝕊.dmode is None: frees(0.1)
      p,order,reverse,timing = 𝕊.dmode
      pin = Pin(p)
      pin.init(pin.OUT)
      return pin,order,reverse,timing
    
    @micropython.native
    def get_mode():
      m = MS()
      while 𝔔:
        ν = 𝔔[0]
        if m < ν.Ta: return False
        h_pop(𝔔)
        if m >= ν.Ta+ν.d: continue
        return ν
    
    @micropython.native
    def get_Δ(ntp=False):
      S = mode and mode.Ts
      if ntp: Time()
      if S is None: return -ms()
      m,T = ms(),MS()
      if abs(T-S) >= 60**2 * 1000: return -m # request ≥ an hour out of date
      return T-S-m # ✣ ms+Δ = 0 ⟺ T=S
    
    @micropython.native
    def get_times(Δ):
      tq,tr = divmod(ms()+Δ,1000)
      return tq,tr,tq+tr*0.001
    
    leds = b'\0'*3*2048 # hard limit b/c i can't be bothered
    while 𝕊.lstate:
      try:
        while lstate := 𝕊.lstate:
          if lstate >= _LOOP_NEW_HW:
            pin,order,reverse,timing = get_wait_hwconf()
            frees()
          m = get_mode()
          if m:
            mode = m
            del m
            free()
            (S,S_len,atoms,stk),(l,h) = specify_mode(*mode.s,ℭ)
            ledv = memoryview(leds)[:3*(h-l)]
            tq,tr,t = get_times(Δ := get_Δ())
            t_R,t_S,n = tq+ΔR,tq+ΔS,0
            𝕊.lstate = _LOOP_TIGHT
            free()
          elif not mode:
            frees(0.1)
            continue
          
          tq,tr,t = get_times(Δ)
          render_leds(S,S_len,atoms,stk,leds,order,reverse,l,h,t)
          output_leds(ledv,pin,timing)
          
          n+=1
          if not n%N: frees()
          if tq>=t_R:
            frees()
            now,T = time(),MS()
            log(f"{tq:04}.{tr:04}: FPS={n:6.2f} {n=} mem={mem_perc()} {t_R},{t_S}] [{join(now)}",
                f"{T:013} - {mode.Ts or 0:013} = {T-(mode.Ts or 0):08}", sep='\n')
            if 𝔔: log("𝔔:",join(f"[{ν.d} {ν.Ta} {ν.Ts}]" for i,ν in enumerate(𝔔)))
            if tq>=t_S:
              tq,tr,t = get_times(Δ := get_Δ(ntp=True))
              t_S = tq+ΔS
            t_R,n = tq+ΔR,n%N
      except Exception as ε:
        dbg(f"Error in LED loop! Restarting in 3 seconds:",ε)
        frees(3)

__all__ = "LED_Controller",