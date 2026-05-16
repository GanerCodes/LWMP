from collections   import namedtuple
from uctypes       import addressof as Ѧ
from machine       import bitstream,mem8
from heapq         import heappush as h_add,heappop as h_pop
from math          import inf,exp,ceil
from time          import sleep
from util          import *
from consts        import ref_hold,last_ntp
from interface     import get_mode_bounds
from scene_manager import Scene_Cacher
from LW_Loop       import LW_Loop

_NTP_REFRESH_TIME_μs = const(15*60*1_000_000)

_MS_PER_6H = const(   6*60*60*1000)
_S_PER_D   = const(  24*60*60     )
_MS_PER_D  = const(  24*60*60*1000)
_S_PER_W   = const(7*24*60*60     )
_MS_PER_W  = const(7*24*60*60*1000)

Activation = namedtuple("Activation",["Ta","Ts","s","d"])

def clamp(x,a,b): return a if x<=a else b if x>=b else x
def inf0(x,inf=inf): return 0 if x==inf else x
def day_start_ms(): return day_start(1000*MS())//1000

class Controller: # 󰤱
  def __init__(𝕊,ℭ,𝔐):
    𝕊.𝔏 = LW_Loop()
    𝕊.ℭ,𝕊.scenes = ℭ,Scene_Cacher(𝔐)
    𝕊.mode,𝕊.recalb_t,𝕊.recalb_t_day = None,0,0
    𝕊.𝔖,𝕊.𝔔 = [],[]
    𝕊.configure()
  def __repr__(𝕊):
    return f"{{recalb_t={𝕊.recalb_t} recalb_t_day={𝕊.recalb_t_day} 𝔖🃌={len(𝕊.𝔖)} 𝔔🃌={len(𝕊.𝔔)} loop={𝕊.𝔏}}}"
  def __call__(𝕊,s=None,q=False,d=inf,Ta=None,Ts=None):
    log("Controller",f'Calling with ({s!r}, {q}, {d}, {Ta}, {Ts})')
    if s is None:
      𝕊.mode = None
      return
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
      𝕊.set(Activation(Ts,Ts,s,d),M,m)
    free()

  def check_ntp(𝕊,force=False):
    t = μs()
    if not force and last_ntp[0] is not None and t <= last_ntp[0] + _NTP_REFRESH_TIME_μs: return
    log("Controller",f"Starting NTP sync")
    try:
      T,ΔΔ = ntp()
    except Exception as ε:
      dbg("Controller",f"NTP sync failed!",ε)
      return False
    ΔΔ //= 1000
    if ΔΔ:
      prevΔ = 𝕊.𝔏.Δ
      𝕊.𝔏.Δ += ΔΔ
      log("Controller",f"Updating Δ from NTP drift {prevΔ}+{ΔΔ}={𝕊.𝔏.Δ}")
      𝕊.𝔏.set_Δ()
    return T,ΔΔ
  def check_update_mode(𝕊,M,m):
    for i,𝚇 in enumerate((𝕊.𝔖,𝕊.𝔔)):
      while 𝚇:
        ν = 𝚇[0]
        if M<ν.Ta: break
        h_pop(𝚇)
        if M>=ν.Ta+ν.d: continue
        log("Controller",f"Setting from {"𝔖𝔔"[i]} at {fmt_date(1000*M)}: {fmt_date(1000*(ν.Ta or 0))} {ν.d/1000}s")
        𝕊.set(ν,M,m)
        return 2
    if 𝕊.mode is None or M>=𝕊.mode.Ta+𝕊.mode.d:
      if ν := 𝕊.load_def_scene():
        𝕊.set(ν,M,m)
        return 2
    # 󷹇 at this point the current mode is potentially really old
    day = M//_MS_PER_D
    if day <= 𝕊.recalb_t_day: return 0
    s_day = M//1000 - day_start(1000*M)//1_000_000
    if s_day < 𝕊.recalb_t: return 0
    pΔ = 𝕊.𝔏.Δ
    while m+𝕊.𝔏.Δ > _MS_PER_6H: 𝕊.𝔏.Δ -= _MS_PER_6H # 𝕊.𝔏.Δ = -m would prob be fine but eeeh
    𝕊.update_recalb_day(M)
    log("Controller",f"{fmt_date(1000*M)} Recalibrated Δ {pΔ}→{𝕊.𝔏.Δ} to avoid rounding issues.")
    return int(pΔ!=𝕊.𝔏.Δ)
  def feed(𝕊,_count=[ms()]):
    𝕊.check_ntp()
    M,m = MS(),ms()
    𝕊.check_update_mode(M,m)
    if m>_count[0]:
      log("Controller",𝕊,"Mem:",mem_perc())
      _count[0] += 5000

  def configure(𝕊):
    ℭ = 𝕊.ℭ
    𝕊.𝔏.set_dev(ℭ.LEDC,ℭ.BIT_TIMING,ℭ.LEDP,ℭ.RGB_ORDER,ℭ.REVERSE)

  def set(𝕊,ν,M,m):
    𝕊.mode,𝕊.𝔏.Δ = ν,M-ν.Ts-m
    𝕊.update_recalb_day(M)

    # (s,s_len,atoms,atoms_len,fades),offsets = 𝕊.mode.s
    (S_,atoms,fades),offsets = 𝕊.mode.s
    if not(r := get_mode_bounds(S_,offsets,𝕊.ℭ)): return
    l,h = r
    𝕊.𝔏.set_Δ()
    log("Controller",f'Setting mode: range<{l} {h}>')
    # 𝕊.𝔏.set_mode(Ѧ(S_),s_len,Ѧ(atoms),Ѧ(fades),l,h)
    𝕊.𝔏.set_mode(S_,atoms,fades,l,h)
    𝕊.𝔏.on()
    free()

  def load_def_scene(𝕊):
    if 𝕊.ℭ.DEF_SCENE not in 𝕊.scenes.man:
      log("Controller","No default scene found.")
      return False
    s = 𝕊.ℭ.DEF_SCENE
    D = day_start_ms()
    log("Controller",f'Loading default scene "{s}"')
    return Activation(D,D,𝕊.scenes[s],inf)

  def update_scheg(𝕊,schedule,reset=False,tried={-1}): # -1 is a dumb hack bc namespace stuff
    # https://www.desmos.com/calculator/0w2tpi3lci
    # also theoretically this has offset bugs with extremely specific conditions (submitting schedule like within seconds of it activating)
    𝔊 = sorted((int(k),v) for k,v in schedule.items())

    if reset:
      tried.clear()
      𝕊.𝔖[:] = [] # 󰤱􊽨

    now = μS()
    d,W = get_date(now),week_start(now)//1_000_000
    now //= 1_000_000

    local_scene_cache = {}
    T = now-W
    for i,(Δ,(s,q,d)) in enumerate(𝔊):
      if (Δ-T)%_S_PER_W > _S_PER_D: continue
      A = 1000*(W + Δ + (Δ<T)*_S_PER_W)
      if A in tried: continue
      tried.add(A)
      if q:
        log("Controller",f'󰤱 allow scheduling qued modes! 󰤱')
        continue
      if s not in 𝕊.scenes.man:
        log("Controller",f'Unable to find scene "{s}"!')
        continue

      if s not in local_scene_cache:
        local_scene_cache[s] = 𝕊.scenes[s]
      scene = local_scene_cache[s]

      d = min(_MS_PER_W if d in (None,-1,0) else d,
              ((1000*(𝔊[(i+1)%len(𝔊)][0] - Δ)) - 1)%_MS_PER_W + 1)

      log("Controller",f'Scheduling: "{s}" @ {fmt_date(1000*A)} ({W=}) for {fmt_dur(1000*d)}')
      h_add(𝕊.𝔖,Activation(A,A,scene,d))
    return True

  def update_recalb_day(𝕊,M):
    day = M//_MS_PER_D
    s_day = M//1000 - day_start(1000*M)//1_000_000
    𝕊.recalb_t_day = day - (s_day < 𝕊.recalb_t-60) # prevents ᵉᵍ mode at 12am w/ 1159pm recalb_t taking ≈48hr

  def off(𝕊):
    𝕊.𝔏.clear()

# Controller