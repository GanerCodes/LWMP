import struct
from math import inf
from json import loads as 𝔍l,dumps as 𝔍d

log = lambda a,*𝔸:print(a,*𝔸)or a

pack   = lambda x,*𝔸: struct.pack    ('<'+x,*𝔸)
unpack = lambda x,*𝔸: struct.unpack  ('<'+x,*𝔸)
packsz = lambda x   : struct.calcsize('<'+x   )

_𝔄 = object()
def 𝔄(c=False,r=_𝔄):
  assert c
  return c if r is _𝔄 else r
𝔄𝑖 = lambda x    : 𝔄(isinstance(x,int  )                         , x)
𝔄𝑢 = lambda x    : 𝔄(isinstance(x,int  ) and 0<=x<2**8           , x)
𝔄ℎ = lambda x    : 𝔄(isinstance(x,int  ) and 0<=x<2**16          , x)
𝔄𝑓 = lambda x    : 𝔄(((x:=float(x))or 1) and x==x and abs(x)!=inf, x)
𝔄𝑙 = lambda x,l=0: 𝔄(isinstance(x,list ) and len(x)>=l           , x)
𝔄𝑑 = lambda x    : 𝔄(isinstance(x,dict )                         , x)
𝔄𝑦 = lambda x    : 𝔄(isinstance(x,bytes)                         , x)
𝔄𝑠 = lambda x    : 𝔄(isinstance(x,str  )                         , x)

class Encoder:
  def __init__(𝕊): 𝕊.B = bytearray()
  def __repr__(𝕊): return f"𝔈[{len(𝕊.B)}]"
  def __call__(𝕊,b):
    𝕊.B += b.B if isinstance(b,Encoder) else b
    return 𝕊
  def Σ(𝕊,f,*𝔸 ): return 𝕊(pack(f,*𝔸))
  def 𝐼(𝕊,x,n=1): return 𝕊(x.to_bytes(n))
  def 𝐹(𝕊,x    ): return 𝕊.Σ("f",𝔄𝑓(x))
  def 𝑆(𝕊,s,l=4):
    𝕊.𝐼(len(s := s.encode("utf-8")),l)
    return 𝕊(s)
  def 𝑀(𝕊,d,𝙺,𝚅,n=2):
    𝕊.𝐼(len(d),n)
    for k,v in d.items(): 𝙺(k);𝚅(v)
    return 𝕊

class Decoder:
  def __init__(𝕊,B,i=0):
    if isinstance(B,Encoder): B = B.B
    𝔄(isinstance(B,(bytes,bytearray)) and isinstance(i,int))
    𝕊.B,𝕊.i = B,i
  def __repr__(𝕊): return f"𝔇[{𝕊.i} / {len(𝕊.B)}]"
  def __call__(𝕊,n=1):
    𝕊.i += n
    𝔄(𝕊.i <= len(𝕊.B))
    return 𝕊.B[𝕊.i-n:𝕊.i]
  def Σ(𝕊,f      ): return unpack(f,𝕊(packsz(f)))
  def 𝐼(𝕊,    n=1): return int.from_bytes(𝕊(n))
  def 𝐹(𝕊        ): return 𝔄𝑓(𝕊.Σ("f")[0])
  def 𝑆(𝕊,    l=4): return 𝕊(𝕊.𝐼(l)).decode("utf-8")
  def 𝑀(𝕊,𝙺,𝚅,n=2): return { 𝙺():𝚅() for _ in range(𝕊.𝐼(n)) }