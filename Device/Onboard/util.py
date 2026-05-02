import machine,time,sys,os
from struct import pack,unpack
from json   import loads as 𝔍l,dumps as 𝔍d
from gc     import mem_alloc,mem_free,collect as free

def frees(t=0,f=free,s=time.sleep): f();s(t)

def path_exists(p,_=os.stat):
  try:
    _(p)
    return True
  except OSError:
    return False

ls,rm,mv = os.listdir,os.remove,os.rename
(LED_ONBOARD := machine.Pin(2)).init(LED_ONBOARD.OUT)
onboard_led = lambda s=1,_=LED_ONBOARD:_.value(s)
𝔍lf         = lambda f      : 𝔍l(read_file(f))
𝔍wf         = lambda f,x    : write_file(f,𝔍d(x))
join        = lambda x,s=' ': s.join(map(str,x))

class Logger:
  l = 0
  def set(l):
    l = min(max(0,int(l)),255)
    print(f"[Logger] Setting loglevel to {l}")
    Logger.l = l
  def get(f,l):
    return lambda *𝔸,**𝕂: f(*𝔸,**𝕂) if l>=Logger.l else 0

def show_dbg(*𝔸,_=print,pe=sys.print_exception,**𝕂):
  v = _(*𝔸,**𝕂)
  for ε in 𝔸:
    if not isinstance(ε,BaseException): continue
    _(f'Printing exception ε={ε}\n>>>>>>>')
    pe(ε)
    _("<<<<<<<")
  return v
log0 = Logger.get(print   ,0)
log  = Logger.get(print   ,1)
dbg  = Logger.get(show_dbg,2)

def mem_info(a=mem_alloc,u=mem_free):
  return a(),u()
def fs_info(_=os.statvfs):
  S = _("/")
  T,F = S[1]*S[2],S[0]*S[3]
  return T-F,F
def fs_perc():
  u,f = fs_info()
  return f"{int(u/(u+f)*100):02}%"
def mem_perc():
  u,f = mem_info()
  return f"{int(u/(u+f)*100):02}%"

def read_file(fn,m="r"):
  with open(str(fn),m) as f:
    return f.read()
def write_file(fn,content,m="w"):
  with open(str(fn),m) as f:
    f.write(c := str(content))
    return c

del machine,time,sys,os,LED_ONBOARD,mem_alloc,mem_free

from ntp import *