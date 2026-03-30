from collections   import namedtuple
from uctypes       import addressof as Ѧ
from machine       import bitstream,Pin,mem8
from heapq         import heappush as h_add,heappop as h_pop
from math          import inf,exp,ceil
from util          import *
from consts        import ref_hold,lstk_ptr,leds,leds_ptr,last_ntp,𝕒_static,𝕒_ptr
from settings      import parse_rgb_mode
from interface     import specify_mode
from lightwave     import assign_leds
from scene_manager import Scene_Cacher

_LOOP_NONE   = const(0)
_LOOP_TIGHT  = const(1)
_LOOP_UPDATE = const(2)
_LOG_INTRV_MS     = const(30_000)
_FREE_INTRV_MS    = const(250)
_FREE_INTRV_FRAME = const(30)
_NTP_REFRESH_TIME_μs = const(15*60*1_000_000)

_MS_PER_6H = const(   6*60*60*1000)
_S_PER_D   = const(  24*60*60     )
_MS_PER_D  = const(  24*60*60*1000)
_S_PER_W   = const(7*24*60*60     )
_MS_PER_W  = const(7*24*60*60*1000)

Activation = namedtuple("Activation",["Ta","Ts","s","d"])

@micropython.native
def clamp(x,a,b): return a if x<=a else b if x>=b else x
@micropython.native
def inf0(x,inf=inf): return 0 if x==inf else x
@micropython.native
def set_𝕒(hw,mode,arg_fmt=len(𝕒_static)//4*'i'):
  (pin,order,reverse,timing),(((S,S_len,atoms,atoms_len,fades),(l,h)),targΔ) = hw,mode
  𝕒_static[:] = pack(arg_fmt,Ѧ(S),S_len,Ѧ(atoms),atoms_len,Ѧ(fades),lstk_ptr,leds_ptr,order,reverse,l,h)
  ledv = memoryview(leds)[:3*(h-l)]
  ref_hold[:] = S,atoms,fades
  log(f"[Controller] Specialized mode with {l}󷸻{h} ({targΔ=})")
  return pin,timing,ledv,targΔ

class Controller:
  __repr__ = lambda 𝕊: f"Controller⟨{𝕊.dmode} recalb_t={𝕊.recalb_t} lstate={𝕊.lstate}⟩"
  def __init__(𝕊,ℭ,𝔐):
    𝕊.ℭ,𝕊.scenes = ℭ,Scene_Cacher(𝔐)
    𝕊.𝔖,𝕊.𝔔 = [],[]
    𝕊.mode = 𝕊.dmode = None
    𝕊.recalb_t,𝕊.recalb_t_day = 0,0
    𝕊.Δ,𝕊.lstate = 0,_LOOP_UPDATE
    𝕊.configure()
  @micropython.native
  def off(𝕊):
    𝕊({"1":[2048,0,0],"fx":[[2,0.25]]})
    frees(0.05)
    for i in range(3*2048): mem8[leds_ptr+i] = 0
    if 𝕊.dmode: bitstream(𝕊.dmode[0],0,𝕊.dmode[3],leds)
  def configure(𝕊):
    ℭ = 𝕊.ℭ
    timing = ℭ.BIT_TIMING
    if isinstance(timing,str): timing = tuple(map(int,timing.strip().split()))
    (pin := Pin(ℭ.LEDP)).init(pin.OUT)
    𝕊.dmode = pin,parse_rgb_mode(ℭ.RGB_ORDER),bool(ℭ.REVERSE),tuple(timing)
    𝕊.recalb_t = ℭ.RECALB_T
    𝕊.lstate = _LOOP_UPDATE
    log(f"[Controller] Configured to {𝕊}")
    free()
    return 𝕊
  def __call__(𝕊,s=None,q=False,d=inf,Ta=None,Ts=None):
    log(f'[Controller] Calling with ({s!r}, {q}, {d}, {Ta}, {Ts})')
    if s is not None:
      𝔖_,𝔔,s = 𝕊.𝔖,𝕊.𝔔,𝕊.scenes[s]
      if d in (None,-1): d = inf
      M,m = MS(),ms()
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
        if Ts is None: Ts = day_start(M*1000)//1_000 # 󷹇 if ntp not ran then its just some ancient date
        ν = Activation(Ts,Ts,s,d)
        𝕊.set(ν,M,m)
    else:
      𝕊.mode = None
      𝕊.load_def_scene() # this is for cache ∵ our thread has small stack. 󰤱 fix this behavior in general
    free()
    𝕊.lstate = _LOOP_UPDATE
  
  def load_def_scene(𝕊):
    if 𝕊.ℭ.DEF_SCENE not in 𝕊.scenes.man:
      log("[Controller] No default scene found.")
      return False
    s = 𝕊.ℭ.DEF_SCENE
    D = day_start(1000*MS())//1000
    log(f'[Controller] Loading default scene "{s}"')
    return Activation(D,D,𝕊.scenes[s],inf)
  
  def check_ntp(𝕊,force=False):
    t = μs()
    if not force and last_ntp[0] is not None and t <= last_ntp[0] + _NTP_REFRESH_TIME_μs: return
    log(f"[Controller] Starting NTP sync")
    T,ΔΔ = ntp()
    ΔΔ //= 1000
    if ΔΔ:
      prevΔ = 𝕊.Δ
      𝕊.Δ += ΔΔ
      log(f"[Controller] Updating Δ from NTP drift {prevΔ}→{𝕊.Δ}")
    return T,ΔΔ
  
  def update_scheg(𝕊,schedule,reset=False,cache=set()):
    # https://www.desmos.com/calculator/0w2tpi3lci
    # also theoretically this has offset bugs with extremely specific conditions (submitting schedule like within seconds of it activating)
    𝔛 = 𝕊.𝔖
    𝔊 = sorted((int(k),v) for k,v in schedule.items())
    
    if reset:
      cache.clear()
      𝔛[:] = [] # 󰤱􊽨
      frees()
    
    now = μS()
    d,W = get_date(now),week_start(now)//1_000_000
    now //= 1_000_000
    # log(f"Now={fmt_date(1_000_000*now)} Week={fmt_date(1_000_000*W)}")
    
    T = now-W
    for i,(Δ,(s,q,d)) in enumerate(𝔊):
      assert not q, "󰤱"
      if (Δ-T)%_S_PER_W > _S_PER_D: continue
      A = 1000*(W + Δ + (Δ<T)*_S_PER_W)
      if A in cache: continue
      cache.add(A)
      d = min(_MS_PER_W if d in (None,-1,0) else d,
              ((1000*(𝔊[(i+1)%len(𝔊)][0] - Δ)) - 1)%_MS_PER_W + 1)
      log(f'[Controller] Scheduled: "{s}" @ ⟨{fmt_date(1000*A)}⟩ (W=⟨{fmt_date(1000*W)}⟩) for ⟨{fmt_dur(1000*d)}⟩')
      h_add(𝔛,Activation(A,A,𝕊.scenes[s],d))
    return True
  
  # @micropython.native
  def update_recalb_day(𝕊,M):
    day = M//_MS_PER_D
    s_day = M//1000 - day_start(1000*M)//1_000_000
    𝕊.recalb_t_day = day - (s_day < 𝕊.recalb_t-60) # prevents ᵉᵍ mode at 12am w/ 1159pm recalb_t taking ≈48hr
  
  # @micropython.native
  def set(𝕊,ν,M,m):
    𝕊.mode,𝕊.Δ = ν,M-ν.Ts-m
    # log(f"[Controller] get_Δ: M={M} - Ts={ν.Ts} - m={m} = Δ={𝕊.Δ}")
    𝕊.update_recalb_day(M)
    free()
  
  # @micropython.native
  def update_to_que(𝕊):
    M,m = MS(),ms()
    
    for i,𝚇 in enumerate((𝕊.𝔖,𝕊.𝔔)):
      while 𝚇:
        ν = 𝚇[0]
        if M<ν.Ta: break
        h_pop(𝚇)
        if M>=ν.Ta+ν.d: continue
        𝕊.set(ν,M,m)
        log(f"[Controller] Setting from {"𝔖𝔔"[i]} at ⟨{fmt_date(1000*M)}⟩: ({fmt_date(1000*(ν.Ta or 0))} {ν.d/1000}s)")
        return 2
    if 𝕊.mode is None or M>=𝕊.mode.Ta+𝕊.mode.d:
      if ν := 𝕊.load_def_scene():
        𝕊.set(ν,M,m)
        return 2
    
    day = M//_MS_PER_D
    if day <= 𝕊.recalb_t_day: return 0
    s_day = M//1000 - day_start(1000*M)//1_000_000
    if s_day < 𝕊.recalb_t: return 0
    pΔ = 𝕊.Δ
    while m+𝕊.Δ > _MS_PER_6H: 𝕊.Δ -= _MS_PER_6H # 𝕊.Δ = -m would prob be fine but eeeh
    𝕊.update_recalb_day(M)
    log(f"[Controller] ⟨{fmt_date(1000*M)}⟩ Recalibrated Δ {pΔ}→{𝕊.Δ} to avoid rounding issues.")
    return 1 if pΔ!=𝕊.Δ else 0
  
  def get_wait_mode(𝕊):
    while 𝕊.lstate:
      𝕊.update_to_que()
      if 𝕊.mode is None:
        frees(0.1)
        continue
      if r := specify_mode(*𝕊.mode.s,𝕊.ℭ):
        return r,𝕊.Δ
  
  @micropython.native
  def loop(𝕊,leds=leds,set_𝕒=set_𝕒,𝕒_ptr=𝕒_ptr):
    while 𝕊.lstate:
      try:
        𝕊.lstate = _LOOP_TIGHT
        pin,timing,ledv,targΔ = set_𝕒(𝕊.dmode,𝕊.get_wait_mode())
        
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
          
          if u:=𝕊.update_to_que():
            if u==2: break
            if u==1: Δ = targΔ = prevΔ = 𝕊.Δ
          if (n:=n+1)%_FREE_INTRV_FRAME and dt_ms(m,free_ts)<_FREE_INTRV_MS: continue
          if (δ_log := dt_ms(free_ts:=ms(),log_ts)) >= _LOG_INTRV_MS:
            M = MS()
            cur_s = M//1000 - day_start(1000*M)//10**6
            FPS = (n-log_n)/(δ_log or 10**-5)*1000
            log(f"[Controller] {tq:06}.{tr:03} {FPS=:6.2f} {fs_perc()} {mem_perc()} 𝔖🃌={len(𝕊.𝔖)} 𝔔🃌={len(𝕊.𝔔)} {Δ=}\n"
                f"  {fmt_date()} (Ntp=⟨{fmt_date(last_ntp[1] or 0)}⟩ @ ⟨{fmt_dur(last_ntp[0] or 0)}⟩)\n"
                f"  Sec=⟨{fmt_dur(10**6*cur_s)}⟩ recalb_t=⟨{fmt_dur(10**6*𝕊.recalb_t)}⟩ recalb_t_day=⟨{fmt_date(1000*𝕊.recalb_t_day)}⟩\n"
                f"  Ta=⟨{fmt_date(1000*𝕊.mode.Ta)}⟩ Ts=⟨{fmt_date(1000*𝕊.mode.Ts)}⟩ d=⟨{fmt_dur(1000*𝕊.mode.d)}⟩")
            log_n,log_ts = n,free_ts
          if targΔ != 𝕊.Δ:
            targΔ,prevΔ,tsΔ = 𝕊.Δ,Δ,free_ts
            log(f"[Controller] Moving Δ: {prevΔ}→{targΔ}")
          frees()
      except Exception as ε:
        dbg(f"[Controller] Error in LED loop! Restarting in 3 seconds:",ε)
        frees(3)
  
# Controller