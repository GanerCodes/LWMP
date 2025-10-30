def preprocess(L):
    if isinstance(L[0],int):
        return L+(L[0],)
    t,r = 0,[]
    for i,v in enumerate(L[0]):
        Δ = preprocess(v)
        r.append(Δ)
        t += Δ[3]
    return (tuple(r),)+L[1:]+(t,)

def f(leds,modes,S,t:float,H,m:int) -> int:
    if type(S[0]) is int:
        for i in range(S[0]):
            n = i
            for c,σ,l in reversed(H):
                n = (c+n) % l + σ
            leds[n] = modes[m] # i ↦ n
    else:
        σ = 0
        for E in S[0]:
            H.append((int(E[2]*t+E[1]),σ,E[3]))
            m = f(leds,modes,E,t,H,m+1)
            σ += E[3]
    H.pop()
    return m
def g(leds,modes,S,t:float,H=[]):
    H.append((int(S[2]*t+S[1]),0,S[3]))
    f(leds,modes,S,t,H,0)

# example usage

clrs = [None,0xffff00,None,0xfc00dc,None,0x00fcf4,0xff2222,None,0xff8800,0x00ff00]
scheme = \
((  (6,0,0),
    ((  (4,0,0),
        ((  (2,0,0),
            (3,0,0)
         ),0,2)
     ),2,1.5),
    ((  (2,0,0),
        (1,0,0)
     ),0,0)
 ),-2.1,1.05)

from rgbprint import Color
from time import time,sleep
sc = lambda x,c: f"{Color(c)}{x}{Color.reset}"

scheme = preprocess(scheme)
leds = [(0,0,0)]*scheme[3]

t0 = time()
while True:
    g(leds,clrs,scheme,t:=time()-t0)
    print('\n'*10,''.join(sc('⬤',c) for c in leds),sep='')
    sleep(1/144)