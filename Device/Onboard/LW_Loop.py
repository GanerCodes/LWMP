from uctypes   import addressof as Ѧ
from machine   import Pin
from struct    import pack
from lightwave import get_loop_ptr
from lw_thread import RMT_CLK_SRC_DEFAULT,xPortGetCoreID,get_ptrs,run_on_core
from util      import *
from consts    import LED_BUF_SIZE,STK_BUF_SIZE

log0("Device",
     f"RMT_CLK_SRC_DEFAULT={RMT_CLK_SRC_DEFAULT()}"
     f"\nxPortGetCoreID()={xPortGetCoreID     ()}")

_STATE_LOOP_NONE   = const(0)
_STATE_LOOP        = const(1)
_STATE_SET_DEV     = const(2)
_STATE_SET_MODE    = const(3)
_STATE_UPDATE_Δ    = const(4)
_STATE_ARGS_SET    = const(5)
_STATE_INIT        = const(6)
_STATE_CLEAR       = const(7)
_STATE_DEAD        = const(254)
_STATE_SPIN        = const(255)

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

def parse_timing(t): # in ns
  if isinstance(t,(tuple,list)):
    T = tuple(map(int,t))
  elif isinstance(t,int):
    t &= 2**64-1
    T = t>>48 & 0xFFFF, t>>32 & 0xFFFF, t>>16 & 0xFFFF, t>>0 & 0xFFFF
  elif isinstance(t,str):
    T = tuple(map(int,t.strip().split()))
  else:
    raise TypeError()
  if len(T) != 4: raise ValueError("Timing is not length 4")
  if not all(25<=x<=65535 for x in T): raise ValueError("Invalid timing")
  return T[0]<<48 | T[1]<<32 | T[2]<<16 | T[3]

LEDSα = bytearray(LED_BUF_SIZE)
LEDSβ = bytearray(LED_BUF_SIZE)
LSTK  = bytearray(STK_BUF_SIZE)
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
    t,rgb_offs = parse_timing(t),parse_rgb_mode(rgb_offs)
    𝼥 = bytearray(pack("<IQIIBBBx",n,t,Ѧ(LEDSα),Ѧ(LEDSβ),p,rgb_offs,reverse))
    if 𝕊.𝼥 == 𝼥: return
    𝕊.𝼥 = 𝼥
    (pin := Pin(p)).init(pin.OUT)
    𝕊.set_exit_val(_STATE_SET_DEV,𝕊.𝼥)
  def set_mode(𝕊,S_,atoms,fades,l,h):
    𝕊.d_mode = pack("<IIIIIIII",Ѧ(S_   ),len(S_   )//24,
                                Ѧ(atoms),len(atoms)//16,
                                Ѧ(fades),Ѧ(LSTK),l,h)
    𝕊.set_exit_val(_STATE_SET_MODE,𝕊.d_mode)
    𝕊._active_refs = S_,atoms,fades
  def set_Δ(𝕊,Δ=None):
    if Δ is None: Δ=𝕊.Δ
    Δb = pack("I",Δ)
    if 𝕊.d_state[4:8] == Δb: return
    𝕊.d_state[4:8] = Δb
    𝕊.set_exit_conf(_STATE_UPDATE_Δ)
    𝕊.Δ = Δ
  
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
  
  def clear(𝕊):
    𝕊.looping = False
    𝕊.d_args[8:12] = pack("<I",LED_BUF_SIZE//3)
    𝕊.state(_STATE_CLEAR)
    𝕊.wait(_STATE_ARGS_SET)
  
  def __init__(𝕊):
    𝕊.looping,𝕊.𝼥,𝕊.Δ = False,None,0
    # "looping" is a dumb name
    
    ptrs = get_ptrs()
    𝔸 = "P sleep portInterrupts_N portInterrupts_Y taskCritical_Y taskCritical_N f_malloc f_free micros xPortGetCoreID rmt_disable rmt_enable rmt_encoder_reset rmt_new_bytes_encoder rmt_new_tx_channel rmt_transmit rmt_tx_wait_all_done rmt_del_channel rmt_del_encoder".split()
    d_globals = bytearray(pack('<'+len(𝔸)*"I", *(ptrs[p] for p in 𝔸)       ))
    𝕊.d_state = bytearray(pack("<BxxxI"      , _STATE_SPIN ,𝕊.Δ            ))
    𝕊.d_args  = bytearray(pack("<III"        , Ѧ(d_globals),Ѧ(𝕊.d_state), 0))
    
    log("LW-Loop","Starting C loop")
    run_on_core(get_loop_ptr(),Ѧ(𝕊.d_args),1)
    𝕊.wait(_STATE_INIT)
    del ptrs,𝔸,d_globals
    free()
  def __repr__(𝕊):
    return f"LW_Loop{{looping={"NY"[𝕊.looping]} Δ={𝕊.Δ}}}"