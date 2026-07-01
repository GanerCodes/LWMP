# HEADER: "I'm not 􇦌" ↓   ↓↓↓↓ API/format version
#                     1xxx0000
#             Reserved ↑↑↑
# HEADER COMMAND

from bin_tools import *

_API_FMT_VER         = const(0x00)
_API_B               = const(0x00)
_API_B_FMT           = const(0x01)
_API_B_UNKNOWN_CMD   = const(0x02)
_API_B_NO_SCENE      = const(0x03)
_API_G               = const(0x80)
_API_G_SCENE_NOEXIST = const(0x81)

_CMD_CHANGE_DEV    = const(1)
_CMD_SET_SCENE     = const(2)
_CMD_OFF           = const(3)
_CMD_DEL_SCENE     = const(4)
_CMD_PUSH_SCENES   = const(5)
_CMD_PULL_SCENES   = const(6)
_CMD_SET_SCHEDULE  = const(7)
_CMD_PULL_SCHEDULE = const(8)
_CMD_SYNC          = const(9)

def api(𝔇,𝔈=None):
  head = 𝔇.𝐼()
  if not head&0b10000000:
    𝔇.i = 0
    return api_old(*𝔍l(𝔇.B))
  
  if 𝔈 is None: 𝔈 = Encoder()
  ret = lambda c=_API_G,e="",*𝔸: 𝔈.Σ("B"+e,_API_G,*𝔸)
  
  if head&0x0F != _API_FMT_VER:
    return _RESET_NO,ret(_API_B_FMT)
  cmd = 𝔇.𝐼(1)
  if cmd&0x80: # last 5 bits
    rst = _RESET_NO
    for _ in range(cmd&0x1F):
      s,v = api(𝔇,𝔈)
      𝔄(isinstance(v,Encoder))
      rst = max(rst,s)
    return rst,𝔈
  if cmd==_CMD_CHANGE_DEV   :
    pass # 󰤱
  if cmd==_CMD_SET_SCENE    : # Ts dur(leftmost bit is q) name
    Ts,dur = 𝔇.𝐼(4),𝔇.𝐼(4)
    q = dur&0x80000000
    dur &= ~0x80000000
    s = 𝔇.𝑆(2)
    if s not in 𝔐:
      log("API",f'Scene "{s}" not found!')
      return _RESET_NO,ret(_API_B_NO_SCENE)
    𝔏(s,q,dur,None,Ts)
    if not q and dur in (-1,inf): ℭ.DEF_SCENE = s
    return _RESET_NO,ret()
  if cmd==_CMD_OFF          :
    𝔏.off()
    return _RESET_NO,ret()
  if cmd==_CMD_DEL_SCENE    :
    s = 𝔇.𝑆(2)
    return _RESET_NO,ret(_API_G if 𝔐.__delitem__(s) else _API_G_SCENE_NOEXIST)
  if cmd==_CMD_PUSH_SCENES  :
    pass # 󰤱
  if cmd==_CMD_PULL_SCENES  :
    pass # 󰤱
  if cmd==_CMD_SET_SCHEDULE :
    pass # 󰤱
  if cmd==_CMD_PULL_SCHEDULE:
    pass # 󰤱
  if cmd==_CMD_SYNC         :
    try:
      T,ΔΔ = 𝔏.check_ntp(True)
      return _RESET_NO,ret(_API_G,"LL",T,ΔΔ)
    except Exception as ε:
      dbg("API","NTP Sync failed!",ε)
      return _RESET_NO,ret(_API_B)
  return _RESET_NO,ret(_API_B_UNKNOWN)