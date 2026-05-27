GLOBAL_PTR_IDX = b"\x00\x00\x00\x0B\x00\x0C\x00\x0D\x00\x13\x00\x16\x00\x17\x00\x19\x00\x1A\x00\x1B\x00\x1C\x00\x1D\x00\x1E\x00\x20\x00\x22\x00\x25\x00\x2C\x00\x2D\x00\x30\x00\x35\x00\x36\x00\x37\x00\x38\x00\x39\x00\x3A"

from uctypes   import addressof as Ѧ
from machine   import Pin
from struct    import pack
from lightwave import get_loop_ptr
from util      import *
from consts    import LED_BUF_SIZE,STK_BUF_SIZE
from lw_thread import get_ptrs,run_on_core,xPortGetCoreID
import lw_thread

LSTK   = bytearray(STK_BUF_SIZE)
LEDS_α = bytearray(LED_BUF_SIZE)
LEDS_β = bytearray(LED_BUF_SIZE)
# LEDS  = bytearray(LED_BUF_SIZE)
# I2S_α = bytearray(LED_BUF_SIZE*3)
# I2S_β = bytearray(LED_BUF_SIZE*3)

mpy_core = xPortGetCoreID()
log0("Device", mpy_core, lw_thread.RMT_CLK_SRC_DEFAULT(), lw_thread.RMT_CLK_SRC_REF_TICK())

_STATE_LOOP_NONE     = const(  0)
_STATE_LOOP          = const(  1)
_STATE_SET_DEV       = const(  2)
_STATE_SET_MODE      = const(  3)
_STATE_UPDATE_Δ      = const(  4)
_STATE_ARGS_SET      = const(  5)
_STATE_INIT          = const(  6)
_STATE_CLEAR         = const(  7)
_STATE_DEAD          = const(254)
_STATE_SPIN          = const(255)

def parse_rgb_mode(M):
  if isinstance(M,int):
    M &= 0b111111
    T = (M>>4)&3, (M>>2)&3, M&3 # 󷹇 allowing modes like GGR here bc it's interesting / doesn't crash
  elif isinstance(M,str):
    T = M.index('R'), M.index('G'), M.index('B')
  else:
    raise TypeError()
  if len(T) != 3: raise ValueError("RGB mode not length 3")
  if not all(0<=x<=2 for x in T): raise ValueError("Invalid RGB mode")
  return T[0]<<4 | T[1]<<2 | T[2]

def parse_timing(t): # all in ns
  if   isinstance(t,(tuple,list)): T = map(int,t)
  elif isinstance(t,str)         : T = map(int,t.strip().split())
  else                           : raise TypeError()
  T = list(T)
  if   len(T) == 4: T.push(60000)
  elif len(T) != 5: raise ValueError("Timing is not length 5")
  lch = T.pop(-1)
  if not (all(25<=x<=0xFFFF for x in T) and 0<=lch<=0xFFFFFFFF):
    raise ValueError("Invalid timing")
  return T[0]<<48 | T[1]<<32 | T[2]<<16 | T[3], lch

class LW_Loop:
  def state(𝕊,x):
    𝕊.d_state[0] = x
  def wait(𝕊,x):
    d = 𝕊.d_state
    while d[0] != x: pass
  def set_exit_conf(𝕊,x):
    𝕊.state(x)
    𝕊.wait(_STATE_ARGS_SET)
    if 𝕊.looping: 𝕊.on()
    free()
  def set_exit_val(𝕊,x,v):
    𝕊.d_args[8:12] = pack("<I",Ѧ(v))
    𝕊.set_exit_conf(x)
  
  def set_dev(𝕊,n,t,p,rgb_offs,reverse):
    (t,lch),rgb_offs = parse_timing(t),parse_rgb_mode(rgb_offs)
    if 3*n>LED_BUF_SIZE:
      log("LW-Loop","Trimming device LED count to not overrun buffer")
      n = LED_BUF_SIZE//3
    𝼥 = bytearray(pack("<IQIIIBBBx",n,t,lch,Ѧ(LEDS_α),Ѧ(LEDS_β),p,rgb_offs,reverse))
    if 𝕊.𝼥 == 𝼥: return
    𝕊.𝼥 = 𝼥
    𝕊.set_exit_val(_STATE_SET_DEV,𝕊.𝼥)
  def set_mode(𝕊,S_,atoms,fades,l,h):
    𝕊.d_mode = pack("<IIIIIIII",Ѧ(S_   ),len(S_   )//24,
                                Ѧ(atoms),len(atoms)//16,
                                Ѧ(fades),Ѧ(LSTK),l,h)
    𝕊.set_exit_val(_STATE_SET_MODE,𝕊.d_mode)
    𝕊._active_refs = S_,atoms,fades
  def set_Δ(𝕊,Δ=None):
    if Δ is None: Δ=𝕊.Δ
    Δb = pack("<I",Δ)
    if 𝕊.d_state[4:8] == Δb: return
    𝕊.d_state[4:8] = Δb
    𝕊.set_exit_conf(_STATE_UPDATE_Δ)
    𝕊.Δ = Δ
  def clear(𝕊):
    𝕊.looping = False
    𝕊.d_args[8:12] = pack("<I",LED_BUF_SIZE//3)
    𝕊.state(_STATE_CLEAR)
    𝕊.wait(_STATE_ARGS_SET)
  
  def kill(𝕊):
    if 𝕊.d_state[0] != _STATE_DEAD:
      𝕊.state(_STATE_LOOP_NONE)
      𝕊.wait(_STATE_DEAD)
    𝕊.looping = False
  def off (𝕊):
    𝕊.state(_STATE_SPIN)
    𝕊.looping = False
  def on  (𝕊):
    𝕊.state(_STATE_LOOP)
    𝕊.looping = True
  
  def __init__(𝕊):
    𝕊.looping,𝕊.𝼥,𝕊.Δ = False,None,0
    # "looping" is a dumb name
    
    ptrs,d_globals = get_ptrs(),bytearray()
    for i in range(len(GLOBAL_PTR_IDX)//2):
      i = int.from_bytes(GLOBAL_PTR_IDX[2*i:2*(i+1)])
      d_globals += ptrs[4*i:4*(i+1)]
    𝕊.d_state = bytearray(pack("<BxxxI", _STATE_SPIN ,𝕊.Δ            ))
    𝕊.d_args  = bytearray(pack("<III"  , Ѧ(d_globals),Ѧ(𝕊.d_state), 0))
    
    log("LW-Loop","Starting C loop")
    run_on_core(get_loop_ptr(),Ѧ(𝕊.d_args),1-mpy_core,24)
    𝕊.wait(_STATE_INIT)
    log0("LW-Loop","Loop started")
    del ptrs,d_globals
    free()
  def __repr__(𝕊):
    return f"LW_Loop{{looping={"NY"[𝕊.looping]} Δ={𝕊.Δ}}}"