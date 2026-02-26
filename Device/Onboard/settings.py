from util import *
from net  import wifi_connect

class Settings:
  def __init__(𝕊,**𝕂):
    super().__setattr__("X",{})
    for k,v in 𝕂.items():
      k = k.upper()
      v,f = v if len(v)==2 else (v[0],str) if len(v) else (None,str)
      
      default = False
      if path_exists(k):
        try:
          v = f(𝔍lf(k))
          default = True
        except Exception as ε:
          dbg(f'[Settings] Error parsing file "{k}":',ε)
      else:
        pass # dbg(f'[Settings] File "{k}" not found.')
      if not default:
        v = v() if callable(v) else v
        pass # dbg(f'[Settings] Using default value for "{k}"')
      𝕊.X[k] = [v,f]
      free()
  def __contains__(𝕊,k):
    return k.upper() in 𝕊.X
  def __getattr__(𝕊,k  ):
    return 𝕊.X[k.upper()][0]
  def __setattr__(𝕊,k,v):
    k = k.upper()
    v = 𝕊.X[k][0] = 𝕊.X[k][1](v)
    free()
    𝔍wf(k,v)
    return v
  def __call__(𝕊,*𝔸):
    if not 𝔸: raise Exception()
    if not isinstance(𝔸[0],dict): return tuple(𝕊.__getattr__(k) for k in 𝔸)
    if not len(𝔸)==1: raise Exception()
    for k,v in 𝔸[0].items(): 𝕊[k] = v
    return 𝕊
  __getitem__ = __getattr__
  __setitem__ = __setattr__
  __repr__ = lambda 𝕊: "⟨%s⟩"%(", ".join(f"{k}={v[0]}" for k,v in 𝕊.X.items()),)

boolstr = lambda s: s.strip().lower() in ('true','y','1') if isinstance(s,str) else bool(s)
def parse_rgb_mode(mode):
  if isinstance(mode,int):
    return mode
  if isinstance(mode,str):
    if mode.isdigit():
      return int(mode)
    else:
      mode = mode.upper()
      mode = int(mode.index('R')), int(mode.index('G')), int(mode.index('B'))
  return (mode[0]<<16)|(mode[1]<<8)|mode[2]

ℭ = Settings(WS_URL     =("wss://brynic_led_test.ganer.xyz:2096"    ,       ),
             UPDATE_URL =("https://brynic_led_test.ganer.xyz/update",       ),
             UUID       =(gen_id                                    ,       ),
             AP_MODE    =(False                                     ,boolstr),
             TOKEN      =(                                                  ),
             NAME       =(                                                  ),
             R_SSID     =(                                                  ),
             R_PASS     =(                                                  ),
             LEDP       =(23                                        ,int    ),
             LEDC       =(300                                       ,int    ),
             REVERSE    =(False                                     ,boolstr),
             BIT_TIMING =("400 850 800 450"                         ,       ),
             RGB_ORDER  =("RGB"                                     ,       ),
             DEF_SCENE  =("_default"                                ,       ),
             VER        =("1"                                       ,       ),
             RECALB_T   =(0                                         ,int    ))
if not ℭ.name: ℭ.name = ℭ.UUID
ℭ.RGB_ORDER = parse_rgb_mode(ℭ.RGB_ORDER)

def wifi_from_ℭ(ℭ):
  if not     all(  ℭ("token","r_ssid","r_pass")) : raise Exception(f"WiFi credentials not found.")
  if not (R:=wifi_connect(*ℭ("r_ssid","r_pass"))): raise Exception(f'Could not connect to WiFi!')
  return R

# parse_rgb_mode ℭ wifi_from_ℭ