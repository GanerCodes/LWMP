# <chatgpt>
import colorsys
def clr(c, n, m):
    hue = (n / m) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    r, g, b = int(r*255), int(g*255), int(b*255)
    return f"\033[38;2;{r};{g};{b}m{c}\033[0m"
# </chatgpt>

# σ,Σ,d,m: ints
# r0,rΔ: floats

# S: [Seg]
# stk: [(int,int,int)]
# leds: [int]

from time import time
from collections import namedtuple
import sys
from random import randrange as F, randint as I
sys.setrecursionlimit(1_000_000)

# <>
ⴳ,ⴴ = True,False
r = lambda: bool(I(0,2))
s = lambda: F(-5,5)
# c = lambda: I(1,50)
c = lambda: 1
P = lambda: (r(),s(),s())
def mk(d): return (*P(),[mk(I(0,d)) for x in range(I(1,d+1))] if d else c())
# </>

Seg = namedtuple("Seg", ["σ","Σ","d","m","r0","rΔ"])
StackEntry = namedtuple("StackEntry", ["r","σ","Σ"])

class Node:
  def __init__(𝕊,ν=None,σ=None,Σ=None,r0=None,rΔ=None,d=None,m=False):
    𝕊.ν,𝕊.σ,𝕊.Σ = ν,σ,Σ
    𝕊.r0,𝕊.rΔ = r0,rΔ
    𝕊.d,𝕊.m = d,m
  def to(𝕊,x):
    x.ν,x.σ,x.Σ = 𝕊.ν,𝕊.σ,𝕊.Σ
    x.r0,x.rΔ = 𝕊.r0,𝕊.rΔ
    x.d,x.m = 𝕊.d,𝕊.m
  # def __repr__(𝕊): return f"⟨{𝕊.σ}…{𝕊.σ+𝕊.Σ}={𝕊.d} → {𝕊.ν}⟩"
  def __repr__(𝕊): return f"⟨{'T '*𝕊.m}{𝕊.σ}…{𝕊.σ+𝕊.Σ}@{𝕊.d} {𝕊.rΔ}↺+{𝕊.r0}⟩"

add = lambda x,y: (abs(x)+abs(y))*(1-2*(x<0))

def pre(N,ν=None,σ=0,d=0):
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

def f(S,t,atoms_len):
  p,d = 0,0
  for i in range(len(S)):
      s = S[i]
      if s.d < d: p += s.d-d
      d = s.d
      stk[p] = StackEntry(int(s.r0 + s.rΔ*t),s.σ,s.Σ)
      if not s.m:
          p+=1
          continue
      AΣS = abs(s.Σ)
      for o in range(AΣS):
          n = o
          for q in [*range(p+1)][::-1]:
              e = stk[q]
              AΣE = abs(e.Σ)
              n = (n+e.r) % AΣE
              # if Σ<0: n = AΣE-1-n
              if e.Σ<0: n = AΣE-1-n # = abs(Σ)-1-n
              n += e.σ
              if n<0: exit("NOOOO")
          leds[int(n)] = clr('█',s.m-1,atoms_len+1) # clr(s.m-1,o,AΣS)
          # 󷹇 mode_id ≜ s.m-1

# N = (*P(),[
#   (*P(),[(*P(),[(*P(),c()),(*P(),c())]),(*P(),[(*P(),c()),(*P(),c())]),(*P(),[(*P(),c()),(*P(),c())])]),
#   (*P(),[(*P(),[(*P(),c()),(*P(),c())]),(*P(),[(*P(),c()),(*P(),c())]),(*P(),[(*P(),c()),(*P(),c())])]),
#   (*P(),[(*P(),[(*P(),c()),(*P(),c())]),(*P(),[(*P(),c()),(*P(),c())]),(*P(),[(*P(),c()),(*P(),c())])])
# ])
# N = (ⴴ,1,1, [(ⴴ,0,0,4), (ⴴ,0,0,3)])
# N = (ⴴ,1,1, [(ⴳ,0,0,4), (ⴴ,0,0,3)])
# N = (ⴳ,0,1, [(ⴳ,0,1,[(ⴴ,0,0,[(ⴳ,0,1,[(ⴴ,0,0,5),(ⴴ,0,0,3)]), (ⴴ,0,0,10)]),(ⴴ,0,0,3)]), (ⴴ,0,0,10)])
# N = (ⴳ,s(),s(), [
#       (ⴳ,s(),s(),[(ⴴ,s(),s(),[(ⴳ,s(),s(),[(ⴴ,s(),s(),5*4),(ⴴ,s(),s(),3*4)]), (ⴴ,s(),s(),10*4)]),(ⴴ,s(),s(),3*4)]),
#       (ⴳ,s(),s(),[(ⴴ,s(),s(),[(ⴳ,s(),s(),[(ⴴ,s(),s(),5*4),(ⴴ,s(),s(),3*4)]), (ⴴ,s(),s(),10*4)]),(ⴴ,s(),s(),3*4)])
#     ])
# N = (ⴴ,0,1, [(ⴳ,0,-1, [(ⴳ,0,2,3),(ⴴ,0,-2,4)]), (ⴴ,0,1,5), (ⴳ,0,-2.2,2)])
# N = (r(),0,1, [(r(),0,s(), [(r(),0,s(),3),(r(),0,s(),4)]), (r(),0,s(),5), (r(),0,s(),2)])
# N = (ⴴ,0,1,[(ⴴ,0,0,3),(ⴴ,0,0,7)])
# N = (ⴳ,0,1,[(ⴴ,0,0,3),(ⴴ,0,0,7)])
# N = mk(8)

N = (ⴴ,0,5,[(ⴴ,0,-5,[(ⴴ,0,0,5),
                     (ⴴ,0,0,5)]),
            (ⴴ,0,-5,[(ⴴ,0,0,5),
                     (ⴴ,0,0,5)])])

print(flat(pre(N)))

scheme = optf(flat(pre(N)))
leds = [0]*abs(scheme[0].Σ)
stk = [0]*(max(s.d for s in scheme)+1)

atoms_len = max(s.m for s in scheme)-1

print(N,'\n')
print(*scheme,'',sep='\n')
h = lambda t: print(f"{t:06.3f}",''.join(map(str,leds)))

import sys
if len(sys.argv)>1:
  t0 = time()
  while ⴳ:
    t = time()-t0
    f(scheme,3*t,atoms_len)
    h(t)
else:
  D = 3
  for t in [t/D for t in range(2*D*len(leds)+1)]:
      f(scheme,t,atoms_len)
      h(t)

# scheme = \
# ((  (6,0,0),
#     ((  (4,0,0),
#         ((  (2,0,0),
#             (3,0,0)
#          ),0,2)
#      ),2,1.5),
#     ((  (2,0,0),
#         (1,0,0)
#      ),0,0)
#  ),-2.1,1.05)