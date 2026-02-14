from util import *

Seg = namedtuple("Seg", ["σ","Σ","d","m","r0","rΔ"])
class Node:
  def __init__(𝕊,ν=None,σ=None,Σ=None,r0=None,rΔ=None,d=None,m=False):
    𝕊.ν,𝕊.σ,𝕊.Σ = ν,σ,Σ
    𝕊.r0,𝕊.rΔ = r0,rΔ
    𝕊.d,𝕊.m = d,m
  def to(𝕊,x):
    x.ν,x.σ,x.Σ = 𝕊.ν,𝕊.σ,𝕊.Σ
    x.r0,x.rΔ = 𝕊.r0,𝕊.rΔ
    x.d,x.m = 𝕊.d,𝕊.m
  def __repr__(𝕊): return f"⟨{'T '*𝕊.m}{𝕊.σ}…{𝕊.σ+𝕊.Σ}@{𝕊.d} {𝕊.rΔ}↺+{𝕊.r0}⟩"
def pre(N,ν=None,σ=0,d=0):
  add = lambda x,y: (abs(x)+abs(y))*(1-2*(x<0))
  r,C = Node(None,σ,None,N[1],N[2],d),N[3]
  if type(C) is int:
    r.ν,r.Σ,r.m = ν,C*(1-2*N[0]),True
  else:
    r.Σ = 0
    r.ν = h1 = Node()
    for i,n in enumerate(C):
      h2 = ν if i==len(C)-1 else Node(None)
      pre(n,h2,abs(r.Σ),d+1).to(h1)
      r.Σ = add(r.Σ,h1.Σ)
      h1 = h2
  r.Σ *= (1-2*N[0])
  return r
def flat(S): return [S]+(flat(S.ν) if S.ν else [])
def optf(S):
  H,m = [],0
  for x in S:
      m += x.m
      H.append(Seg(x.σ,x.Σ,x.d,int(x.m and m),x.r0,x.rΔ))
  return H

rgb_i2b = lambda x:(x>>16 & 0xFF, x>>8 & 0xFF, x & 0xFF)
def convert_atom(dat,bright,out):
  t,*dat = dat
  out["atoms"] += pack("BBxx",int(min(255*bright,255)),t)
  if   t==0: # Static
    out["atoms"] += pack("BBBxxxxxxxxx",*rgb_i2b(dat[0]))
  elif t==1: # Rainbow
    out["atoms"] += pack("fBBxxxxxx"   ,*dat) # seg,sat,val
  elif t==2: # Fade
    speed,sharp,*dat = dat
    out["atoms"] += pack("HHff"        ,len(dat),len(out["fades"]),speed,sharp)
    out["fades"] += 3*b"\00" + b''.join(pack("BBB",*rgb_i2b(c)))
  else:
    raise Exception(f'Unknown atom type "{t}"!')
def parse_mode(mode,brightness=1,data=None,reverse=False):
  if data is None: data = dict(atoms=b'',fades=b'')
  
  r0 = rΔ = 0
  for t,(*v) in mode.get("fx",[]):
    if   t==0: reverse     = True # Rev
    elif t==1: rΔ,r0       = v    # Rot
    elif t==2: brightness *= v[0] # Lum
    else     : raise Exception(f'Unknown effect type "{t}"!')
  if '*' in mode:
    s = tuple(parse_mode(m,brightness,data)[0] for m in mode["*"])
  elif "1" in mode:
    s,*v = mode["1"]
    convert_atom(v,brightness,data)
  else:
    raise Exception(f'Invalid mode "{mode}"!')
  return (reverse,r0,rΔ,s),data

def encode_mode(N):
  N,data = parse_mode(N)
  N = optf(flat(pre(N)))
  S     = b''.join(pack("iiiiff",s.σ,s.Σ,s.d,s.m,s.r0,s.rΔ) for s in N)
  stk   = (max(s.d for s in N)+1)*pack("iii",0,0,0)
  free()
  return S,len(S)//24,data["atoms"],len(data["atoms"])//16,bytes(data["fades"]),stk
def specify_mode(mode,offsets,ℭ):
  Σ = int.from_bytes(mode[0][4:8],"little")
  l = (offsets or {}).get(ℭ.UUID,0)
  h = min(l+ℭ.LEDC,abs(Σ))
  return mode,(l,h)

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

__all__ = "encode_mode","specify_mode","parse_rgb_mode"