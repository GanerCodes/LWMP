# Seg = namedtuple("Seg", ["σ","Σ","d","m","r0","rΔ"])
# σ,Σ,d,m: ints
# r0,rΔ: floats

# S: [Seg]
# stk: [(int,int,int)]
# leds: [int]

from collections import namedtuple
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
    # def __repr__(𝕊): return f"⟨{𝕊.σ}…{𝕊.σ+𝕊.Σ}={𝕊.d} → {𝕊.ν}⟩"
    def __repr__(𝕊): return f"⟨{'T '*𝕊.m}{𝕊.σ}…{𝕊.σ+𝕊.Σ}@{𝕊.d} {𝕊.rΔ}↺+{𝕊.r0}⟩"

def pre(N,ν=None,σ=0,d=0):
    r,C = Node(None,σ,None,N[0],N[1],d),N[2]
    if type(C) is int:
        r.ν,r.Σ,r.m = ν,C,True
    else:
        r.Σ = 0
        r.ν = h1 = Node()
        for i,n in enumerate(C):
            h2 = ν if i==len(C)-1 else Node(None)
            pre(n,h2,r.Σ,d+1).to(h1)
            r.Σ += h1.Σ
            h1 = h2
    return r
def flat(S): return [S]+(flat(S.ν) if S.ν else [])
def optf(S):
    H,m = [],0
    for x in S:
        m += x.m
        H.append(Seg(x.σ,x.Σ,x.d,int(x.m and m),x.r0,x.rΔ))
    return H

def f(S,t):
    p,d = 0,0
    i = 0
    for i in range(len(S)):
        s = S[i]
        if s.d < d: p += s.d-d
        d = s.d
        stk[p] = (int(s.r0 + s.rΔ*t),s.σ,s.Σ)
        if not s.m:
            p+=1
            continue
        for o in range(s.Σ):
            n = o
            for q in [*range(p+1)][::-1]:
                e = stk[q]
                n = (e[0]+n) % e[2] + e[1]
            leds[n] = s.m-1 # mode_id
            o += 1

# N = (1,1, [(0,0,4), (0,0,3)])
N = (0,1, [(0,-1, [(0,0,3),(0,0,4)]), (0,0,5), (0,0,2)])

scheme = optf(flat(pre(N)))
leds = [0]*scheme[0].Σ
stk = [0]*(max(s.d for s in scheme)+1)

print(*scheme,'',sep='\n')
h = lambda t: print(f"{t:06.3f}",''.join(map(str,leds)))
for t in [t/3 for t in range(15+1)]:
    f(scheme,t)
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
