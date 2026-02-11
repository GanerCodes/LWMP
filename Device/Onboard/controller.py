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
𝕒_ptr = Ѧ(𝕒_static := bytearray(4*10))
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
  
  @micropython.native
  def loop(𝕊,leds=leds,𝕒_static=𝕒_static,𝕒_ptr=𝕒_ptr):
    while 𝕊.lstate:
      try:
        pin,order,reverse,timing = 𝕊.get_wait_hwconf()
        ((S_,S_len,atoms,fades,stk),(l,h)),targΔ = 𝕊.get_wait_mode()
        𝕒_static[:] = pack(len(𝕒_static)//4*'i',Ѧ(S_),S_len,Ѧ(atoms),Ѧ(fades),Ѧ(stk),Ѧ(leds),order,reverse,l,h)
        ledv = memoryview(leds)[:3*(h-l)]
        𝕊.lstate = _LOOP_TIGHT
        log(f"Starting with {l}󷸻{h} ({targΔ=})")
        
        Δ = prevΔ = targΔ
        n = tsΔ = 0
        m_o = start = ms()
        while 𝕊.lstate == _LOOP_TIGHT:
          δ = (m:=ms())-m_o
          if ΔΔ := targΔ-Δ:
            if -10_000 <= ΔΔ < 10000 and m-tsΔ<1000: # https://www.desmos.com/calculator/hexqqffwi9?nobranding=&nokeypad=
              l = min(1,max((m-tsΔ) * 0.001,0))
              Δ = prevΔ+ceil((targΔ-prevΔ)*((exp(2*l)-1)/(exp(2)-1)))
            else:
              Δ = targΔ
            # log(f"{m=}/{tsΔ+1000} {ΔΔ=} {prevΔ}≤{Δ=}≤{targΔ} ({int(100*l):03}%)")
          tq,tr = divmod(m+Δ,1000)
          assign_leds(𝕒_ptr,tq+tr*0.001)
          bitstream(pin,0,timing,ledv)
          if not (n:=n+1)%30:
            # log(tq+tr*0.001)
            m_o,m = m,ms()
            if not n%1200:
              log(f"{tq:06}.{tr:03} ⟨{fmt_date()}⟩ {1200*1000/(m-start):6.2f}FPS {mem_perc()} Que🃌={len(𝕊.𝔔)} {Δ=}")
              log(f"{𝕊.mode.Ta=} {𝕊.mode.Ts=} {𝕊.mode.d=}")
              # log(f"{fmt_date(𝕊.mode.Ts)}")
              start = m
            if targΔ != 𝕊.Δ:
              targΔ,prevΔ,tsΔ = 𝕊.Δ,Δ,m
            frees()
            if 𝕊.update_to_que(): break
      except Exception as ε:
        dbg(f"Error in LED loop! Restarting in 3 seconds:",ε)
        frees(3)

__all__ = "Controller",