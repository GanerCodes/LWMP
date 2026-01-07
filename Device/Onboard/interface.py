from utils import *
from lightwave import *

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

@micropython.viper
def test_assign_leds(S:ptr8,l:int,stk:ptr8,leds:ptr8,t,RGB_OFF:int):
  assign_leds(S,l,stk,leds,t,RGB_OFF)

def parse_bit_timing(s):
  return tuple(int(x) for x in (s.split(' ') if isinstance(s,str) else s))
def parse_rgb_mode(mode):
  if isinstance(mode,int):
    return mode
  if isinstance(mode,str):
    mode = mode.upper()
    mode = int(mode.index('R')), int(mode.index('G')), int(mode.index('B'))
  return (mode[0]<<16)|(mode[1]<<8)|mode[2]

class Displayer:
  def __init__(𝕊,pin=23,order=(0,1,2),timing=(400,850,800,450)):
    𝕊.pinout = machine.Pin(pin)
    𝕊.pinout.init(𝕊.pinout.OUT)
    𝕊.timing = timing
    𝕊.order = parse_rgb_mode(order)
  def load_mode(𝕊,N):
    𝕊.S_buf,𝕊.stk_buf,𝕊.LED_buf = scheme_to_bufs(N)
    return 𝕊
  def __call__(𝕊,t):
    test_assign_leds(𝕊.S_buf,len(𝕊.S_buf)//24,𝕊.stk_buf,𝕊.LED_buf,t,𝕊.order)
    machine.bitstream(𝕊.pinout,0,𝕊.timing,𝕊.LED_buf)