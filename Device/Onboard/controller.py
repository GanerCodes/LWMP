from util          import *
from interface     import *
from lightwave     import *
from scene_manager import *

_LOOP_NONE   = const(0)
_LOOP_TIGHT  = const(1)
_LOOP_UPDATE = const(2)

Activation = namedtuple("Activation",["Ta","Ts","s","d"])
inf0       = lambda x,inf=inf: 0 if x==inf else x

leds  = b'\0'*3*2048
𝕒_ptr = Ѧ(𝕒_static := bytearray(4*11))
class Controller:
  __repr__ = lambda 𝕊: f"LED_Controller⟨{𝕊.dmode} lstate={𝕊.lstate}⟩"
  def __init__(𝕊,ℭ,𝔐):
    𝕊.ℭ,𝕊.lstate = ℭ,_LOOP_UPDATE
    𝕊.scenes = Scene_Cacher(𝔐)
    𝕊.mode,𝕊.dmode,𝕊.𝔔 = None,None,[]
  
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
    log(f"Setting {s} with {q=} {d=} {Ta=} {Ts=}")
    
    𝔔,s = 𝕊.𝔔,𝕊.scenes[s]
    M = MS()
    
    if d is None:
      d = inf
    if Ts is None:
      if   𝔔: Ta = max(𝔔).Ta + inf0(max(𝔔).d) # 󰤱 this is wrong, should be start of first 𝔔 gap
      else  : Ts = week_start(M*1000) // 1_000 # 󷹇 if ntp not ran then its just some ancient date
    if q:
      assert d<inf, "󰤱"
      if Ta is None:
        if   𝔔     : Ta = max(𝔔).Ta + inf0(max(𝔔).d) # 󰤱 this is wrong, should be start of first 𝔔 gap
        elif 𝕊.mode: Ta = 𝕊.mode.Ta + inf0(𝕊.mode.d)
        else       : Ta = M
      h_add(𝔔,Activation(Ta,Ts,s,d))
    else:
      assert Ta is None, "󰤱"
      assert d==inf, "󰤱"
      𝕊.mode = Activation(Ts,Ts,s,d)
      𝕊.Δ = 𝕊.get_Δ(𝕊.mode)
    𝕊.lstate = _LOOP_UPDATE

  def update_to_que(𝕊):
    𝔔,T = 𝕊.𝔔,MS()
    while 𝔔:
      ν = 𝔔[0]
      if T < ν.Ta: return
      h_pop(𝔔)
      if T >= ν.Ta+ν.d: continue
      𝕊.mode,𝕊.Δ = ν,get_Δ(ν)
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
  def loop(𝕊,leds=leds,𝕒_static=𝕒_static,𝕒_ptr=𝕒_ptr):
    _log_intrv_ms = const(5_000)
    _free_intrv_frame = const(30)
    while 𝕊.lstate:
      try:
        pin,order,reverse,timing = 𝕊.get_wait_hwconf()
        ((S_,S_len,atoms,atoms_len,fades,stk),(l,h)),targΔ = 𝕊.get_wait_mode()
        𝕒_static[:] = pack(len(𝕒_static)//4*'i',
          Ѧ(S_),S_len,Ѧ(atoms),atoms_len,Ѧ(fades),Ѧ(stk),Ѧ(leds),order,reverse,l,h)
        ledv = memoryview(leds)[:3*(h-l)]
        𝕊.lstate = _LOOP_TIGHT
        log(f"Starting with {l}󷸻{h} ({targΔ=})")
        
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
          
          if (n:=n+1)%_free_intrv_frame and dt_ms(m,free_ts)<1000: continue
          δ_log = dt_ms(free_ts:=ms(),log_ts)
          if δ_log >= _log_intrv_ms:
            FPS = (n-log_n)/(δ_log or 10**-5)*1000
            log(f"{tq:06}.{tr:03} ⟨{fmt_date()}⟩ {FPS=:6.2f} {mem_perc()} Que🃌={len(𝕊.𝔔)} {Δ=}\n"
                f"Last Ntp: ⟨{fmt_date(last_ntp[1] or 0)}⟩ peformed at ⟨{fmt_dur(last_ntp[0] or 0)}⟩\n"
                f"Activated=⟨{fmt_date(1000*𝕊.mode.Ta)}⟩ Sync=⟨{fmt_date(1000*𝕊.mode.Ts)}⟩ Duration=⟨{fmt_dur(1000*𝕊.mode.d)}⟩")
            log_n,log_ts = n,free_ts
          if targΔ != 𝕊.Δ:
            targΔ,prevΔ,tsΔ = 𝕊.Δ,Δ,free_ts
            log(f"Moving Δ: {prevΔ}→{targΔ}")
          frees()
          if 𝕊.update_to_que(): break
      except Exception as ε:
        dbg(f"Error in LED loop! Restarting in 3 seconds:",ε)
        frees(3)

__all__ = "Controller",