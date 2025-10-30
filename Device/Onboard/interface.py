from collections import namedtuple
from lightwave import *
import struct,time,machine

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
        H.append(Seg(x.σ,x.Σ,x.d,int(x.m and m),x.r0,x.rΔ*x.Σ))
    return H

def scheme_to_bufs(N):
    scheme = optf(flat(pre(N)))
    S_buf = bytearray()
    for s in scheme: S_buf += struct.pack("iiiiff",s.σ,s.Σ,s.d,s.m,s.r0,s.rΔ)
    stk_buf = (max(s.d for s in scheme)+1)*struct.pack("iii",0,0,0)
    LED_buf =                  scheme[0].Σ*struct.pack("BBB",0)
    return S_buf,stk_buf,LED_buf

K = 5

N = (0,0.05, [(0,-0.05, [(0,0,100),(0,0,100),(0.5,0,100)]), (0,0,100), (0,0,100)])
# N = (0,0, [(0,0, [(0,0,50)]), (0,2.5, [(0,0,150)])])
S_buf,stk_buf,LED_buf = scheme_to_bufs(N)

_BITSTREAM_TIMING  = const((400,850,800,450))
OFFSET_R,OFFSET_G,OFFSET_B = 0,1,2
RGB_OFF = (OFFSET_B << 16) | (OFFSET_G << 8) | OFFSET_R
PINOUT = machine.Pin(23)
PINOUT.init(PINOUT.OUT)

@micropython.viper
def test_assign_leds(S:ptr8,l:int,stk:ptr8,leds:ptr8,t,RGB_OFF:int):
    assign_leds(S,l,stk,leds,t,RGB_OFF)
def display_LEDS(buf):
    machine.bitstream(PINOUT,0,_BITSTREAM_TIMING,buf)

t0,next_t,n = time.ticks_ms(),1,0
while True:
    try:
        # LED_buf = bytearray(len(LED_buf))
        t = 0.001*float(time.ticks_ms()-t0)
        test_assign_leds(S_buf,len(S_buf)//24,stk_buf,LED_buf,t,RGB_OFF)
        # h = bytearray(len(LED_buf)//K)
        # for i in range(0,len(h),3):
        #     for o in range(3):
        #         h[i+o] = int(sum(LED_buf[q] for q in range(i+o,i+o+3*K,3))/K)
        display_LEDS(LED_buf)
        
        n+=1
        if t>next_t:
            print(n)
            next_t,n = t+1,0
    except KeyboardInterrupt:
        break
    # print(''.join(map(str,struct.unpack('<'+'BBB'*(len(LED_buf)//3),LED_buf))))