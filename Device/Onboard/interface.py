from collections import namedtuple
from util        import *
from consts      import leds,lstk

@micropython.native
def add_mag(x,y): return (abs(x)+abs(y))*(1-2*(x<0))

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
  r,C = Node(None,σ,None,N[1],N[2],d),N[3]
  if type(C) is int:
    r.ν,r.Σ,r.m = ν,C*(1-2*N[0]),True
    if not r.Σ: raise Exception(f"Atom with length 0!")
  else:
    r.Σ = 0
    r.ν = h1 = Node()
    for i,n in enumerate(C):
      h2 = ν if i==len(C)-1 else Node(None)
      pre(n,h2,abs(r.Σ),d+1).to(h1)
      r.Σ = add_mag(r.Σ,h1.Σ)
      h1 = h2
  r.Σ *= (1-2*N[0])
  return r

# def flat(S): return [S]+(flat(S.ν) if S.ν else []) 
# def optf(S):
#   H,m = [],0
#   for x in S:
#     m += x.m
#     H.append(Seg(x.σ,x.Σ,x.d,int(x.m and m),x.r0,x.rΔ))
#   return H

def flab(S):
  p,m,mx = S,0,0
  R = b''
  while p:
    m += p.m
    if p.d>mx: mx = p.d
    # R += pack("iihhff",p.σ,p.Σ,p.d,int(p.m and m),p.r0,p.rΔ)
    R += pack("iiiiff",p.σ,p.Σ,p.d,int(p.m and m),p.r0,p.rΔ)
    
    # we are graverobbing for memory at this point 😭
    tmp = p.ν
    p.ν = None
    del p; free()
    p = tmp
  return R,mx+1

def rgb_i2b(x):
  x = int(x)
  return x>>16 & 0xFF, x>>8 & 0xFF, x & 0xFF
def convert_atom(dat,bright,out):
  t,*dat = dat
  out["atoms"] += pack("BBxx",int(min(255*bright,255)),t)
  if   t==0: # Static
    out["atoms"] += pack("BBBxxxxxxxxx",*rgb_i2b(dat[0]))
  elif t==1: # Rainbow
    out["atoms"] += pack("fBBxxxxxx"   ,float(dat[0]),int  (dat[1]),int  (dat[2]))
  elif t==2: # Fade
    speed,sharp,*dat = dat
    out["atoms"] += pack("HHff"        ,len(dat),len(out["fades"]),float(speed),float(sharp))
    out["fades"] += 3*b"\00" + b''.join(pack("BBB",*rgb_i2b(c)) for c in dat)
  else:
    raise Exception(f'Unknown atom type "{t}"!')
def parse_mode(mode,brightness=1,data=None,reverse=False):
  free()
  if data is None: data = dict(atoms=b'',fades=b'')
  
  r0 = rΔ = 0
  for t,(*v) in mode.get("fx",()):
    if   t==0: reverse     = True # Rev
    elif t==1: rΔ,r0 = float(v[0]),float(v[1])
    elif t==2: brightness *= max(min(float(v[0]),1000),0) # Lum, idk why im allowing 1000 but it might factor through
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
  # N   = optf(flat(pre(N)))
  # S   = b''.join(pack("iiiiff",s.σ,s.Σ,s.d,s.m,s.r0,s.rΔ) for s in N)
  # mx  = max(s.d for s in N)+1
  N,data = parse_mode(N)
  
  tmp  = pre (N); del N; free(); N=tmp
  S,mx = flab(N); del N; free()
  
  if 3*4*mx > len(lstk): raise Exception(f"Stk too large for lstk! {mx=}")
  
  lens = len(S),len(data["atoms"]),len(data["fades"])
  log(f"[Interface] (Mem:{mem_perc()}) Size = {join(lens,'+')} = {sum(lens)}")
  
  return S,len(S)//24,data["atoms"],len(data["atoms"])//16,bytes(data["fades"])
def specify_mode(mode,offsets,ℭ):
  Σ = int.from_bytes(mode[0][4:8],"little")
  l = (offsets or {}).get(ℭ.UUID,0)
  h = min(l+ℭ.LEDC,abs(Σ))
  if l>=h:
    # log("[Interface] Device has no LEDs to display for mode.")
    log0('.',end='')
    return None
  return mode,(l,h)

# encode_mode specify_mode