from util          import *
from interface     import *
from lightwave     import *
from scene_manager import *

_LOOP_NONE   = const(0)
_LOOP_TIGHT  = const(1)
_LOOP_UPDATE = const(2)

Activation = namedtuple("Activation",["Ta","Ts","s","d"])

leds_ptr = Ѧ(leds     := b'\0'*3*2048   )
𝕒_ptr    = Ѧ(𝕒_static := bytearray(4*11))
ref_hold = []
@micropython.native
def set_𝕒(hw,mode,arg_fmt=len(𝕒_static)//4*'i'):
  (pin,order,reverse,timing),(((S,S_len,atoms,atoms_len,fades,stk),(l,h)),targΔ) = hw,mode
  𝕒_static[:] = pack(arg_fmt,Ѧ(S),S_len,Ѧ(atoms),atoms_len,Ѧ(fades),Ѧ(stk),leds_ptr,order,reverse,l,h)
  ledv = memoryview(leds)[:3*(h-l)]
  ref_hold[:] = S,atoms,fades,stk
  log(f"Configured mode with {l}󷸻{h} ({targΔ=})")
  return pin,timing,ledv,targΔ
@micropython.native
def inf0(x,inf=inf): return 0 if x==inf else x

class Controller:
  __repr__ = lambda 𝕊: f"LED_Controller⟨{𝕊.dmode} lstate={𝕊.lstate}⟩"
  def __init__(𝕊,ℭ,𝔐):
    𝕊.ℭ,𝕊.lstate = ℭ,_LOOP_UPDATE
    𝕊.scenes = Scene_Cacher(𝔐)
    𝕊.mode = 𝕊.dmode = None
    𝕊.𝔖,𝕊.𝔔 = [],[]
  
  def configure(𝕊,pin=23,order=(0,1,2),reverse=False,timing=(400,850,800,450)):
    if isinstance(timing,str): timing = tuple(map(int,timing.strip().split()))
    log(f"Configuring controller with {pin=} {order=} {reverse=} {timing=}")
    (pin := Pin(pin)).init(pin.OUT)
    𝕊.dmode = pin,parse_rgb_mode(order),bool(reverse),tuple(timing)
    𝕊.lstate = _LOOP_UPDATE
    return 𝕊

  def get_Δ(𝕊,ν):
    M,m = MS(),ms()
    log(f"get_Δ({ν.Ts=}) ⟨{m} {M}⟩")
    return M-ν.Ts-m
  
  def __call__(𝕊,s,q=False,d=inf,Ta=None,Ts=None):
    log(f'controller("{s}",{q},{d},{Ta},{Ts})')
    𝔖_,𝔔,s = 𝕊.𝔖,𝕊.𝔔,𝕊.scenes[s]
    if d in (None,-1): d = inf
    M = MS()
    if q:
      assert Ts is not None, "󰤱"
      assert Ta is None, "󰤱"
      assert d<inf, "󰤱"
      if   𝔔     : Ta = max(𝔔).Ta + max(𝔔).d
      elif 𝕊.mode: Ta = (lambda x:x if x>M else Ts)(𝕊.mode.Ta + inf0(𝕊.mode.d))
      else       : Ta = Ts
      h_add(𝔔,Activation(Ta,Ta,s,d))
    else:
      assert Ta is None, "󰤱"
      assert d==inf, "󰤱"
      if Ts is None: Ts = week_start(M*1000) // 1_000 # 󷹇 if ntp not ran then its just some ancient date
      ν = Activation(Ts,Ts,s,d)
      𝕊.mode,𝕊.Δ = ν,𝕊.get_Δ(ν)
    𝕊.lstate = _LOOP_UPDATE
  
  def update_schedule(𝕊,schedule,reset=False,cache=set()):
    # https://www.desmos.com/calculator/0w2tpi3lci
    # also theoretically this has offset bugs with extremely specific conditions (submitting schedule like within seconds of it activating)
    𝔛 = 𝕊.𝔖
    
    if reset:
      cache.clear()
      𝔛[:] = [] # 󰤱
    
    now = time_μ()
    d = get_date(now)
    W = week_start(now)//1_000_000
    now //= 1_000_000
    
    T = now-W
    for Δ,(name,que,dur) in schedule.items():
      Δ = int(Δ)
      if (Δ-T)%s_per_w > s_per_d: continue
      A = W + Δ + (Δ<T)*s_per_w
      if A in cache: continue
      cache.add(A)
      A*=1000
      print(f"{name} is scheduled to activate at {A} ({W=})")
      h_add(𝔛,Activation(A,A,𝕊.scenes[name],3)) # 󰤱 duration
    return True
  
  def update_to_que(𝕊):
    M = MS()
    for i,𝚇 in enumerate((𝕊.𝔖,𝕊.𝔔)):
      while 𝚇:
        ν = 𝚇[0]
        if M<ν.Ta: break
        h_pop(𝚇)
        if M>=ν.Ta+ν.d: continue
        𝕊.mode,𝕊.ν = ν,𝕊.get_Δ(ν)
        log(f"Setting from {"𝔖𝔔"[i]} at ⟨{fmt_date(1000*M)}⟩: ({fmt_date(1000*(ν.Ta or 0))} {ν.d/1000}s)")
        return True
  
  def get_wait_hwconf(𝕊):
    while 𝕊.lstate and 𝕊.dmode is None:
      frees(0.1)
    return 𝕊.dmode
  def get_wait_mode(𝕊):
    𝕊.update_to_que()
    while 𝕊.lstate and 𝕊.mode is None:
      frees(0.1)
      𝕊.update_to_que()
    return specify_mode(*𝕊.mode.s,𝕊.ℭ),𝕊.Δ
  
  # @micropython.native
  def loop(𝕊,leds=leds,set_𝕒=set_𝕒,𝕒_ptr=𝕒_ptr):
    _log_intrv_ms = const(5_000)
    _free_intrv_frame = const(30)
    while 𝕊.lstate:
      try:
        𝕊.lstate = _LOOP_TIGHT
        pin,timing,ledv,targΔ = set_𝕒(𝕊.get_wait_hwconf(),𝕊.get_wait_mode())
        
        Δ = prevΔ = targΔ
        log_n = n = tsΔ = 0
        log_ts = free_ts = ms()
        
        while 𝕊.lstate == _LOOP_TIGHT:
          m = ms()
          if ΔΔ := targΔ-Δ: # experp Δ from prevΔ to targΔ over m-tsΔ ms (assuming nondrastic change)
            if -10_000<=ΔΔ<10000 and (δ_Δ:=dt_ms(m,tsΔ))<1000: # https://www.desmos.com/calculator/hexqqffwi9?nobranding=&nokeypad=
              l = clamp(δ_Δ*0.001,0,1)
              Δ = prevΔ+ceil((targΔ-prevΔ)*((exp(2*l)-1)/(exp(2)-1)))
            else:
              Δ = targΔ
          t = m+Δ # 󰤱 this wraps
          tq,tr = divmod(t,1000)
          assign_leds(𝕒_ptr,tq+tr*0.001)
          bitstream(pin,0,timing,ledv)
          
          if 𝕊.update_to_que(): break
          if (n:=n+1)%_free_intrv_frame and dt_ms(m,free_ts)<1000: continue
          if (δ_log := dt_ms(free_ts:=ms(),log_ts)) >= _log_intrv_ms:
            FPS = (n-log_n)/(δ_log or 10**-5)*1000
            log(f"{tq:06}.{tr:03} {FPS=:6.2f} {mem_perc()} Que🃌={len(𝕊.𝔔)} {Δ=}\n"
                f"{fmt_date()} (Ntp=⟨{fmt_date(last_ntp[1] or 0)}⟩ @ ⟨{fmt_dur(last_ntp[0] or 0)}⟩)\n"
                f"Ta=⟨{fmt_date(1000*𝕊.mode.Ta)}⟩ Ts=⟨{fmt_date(1000*𝕊.mode.Ts)}⟩ d=⟨{fmt_dur(1000*𝕊.mode.d)}⟩")
            log_n,log_ts = n,free_ts
          if targΔ != 𝕊.Δ:
            targΔ,prevΔ,tsΔ = 𝕊.Δ,Δ,free_ts
            log(f"Moving Δ: {prevΔ}→{targΔ}")
          frees()
      except Exception as ε:
        dbg(f"Error in LED loop! Restarting in 3 seconds:",ε)
        frees(3)

__all__ = "Controller",