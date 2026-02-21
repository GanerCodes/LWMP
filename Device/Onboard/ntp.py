from machine import RTC
from random  import randrange,choice

from util    import *
from time    import ticks_diff
from consts  import NTP_HOSTS,last_ntp
from lw_ntp  import ntp_raw,micros as μs

S_PER_D   = const(60*60*24             )
S_PER_W   = const(60*60*24*7           )
ΜS_PER_D  = const(60*60*24  *1000      )
MS_PER_W  = const(60*60*24*7*1000      )
_μS_PER_D = const(60*60*24  *1000000   )
_μS_70Y   = const(2_208_988_800_000_000)

@micropython.native
def sample(X,n):
  I = list(range(len(X)))
  r = [X[I.pop(randrange(len(I)))] for _ in range(min(n,len(X)))]
  del X,n,I,_
  free()
  return r

@micropython.native
def ms(*,μs=μs): return μs()//1000
@micropython.native
def dt_ms(x,y=None,*,ms=ms): return ms()-x if y is None else x-y
# def dt_ms(x,y=None,td=ticks_diff,ms=ms): return td(*(ms(),x) if y is None else (x,y))

@micropython.native
def μS(*,S=last_ntp,μs=μs):
  if S[0] is None: return μs()
  o,T = S
  return μs()-o+T
@micropython.native
def MS(*,μS=μS): return μS()//1000
@micropython.native
def week_start(μ=None):
  if μ is None: μ = μS()
  μ //= _μS_PER_D
  return (μ-((μ+4)%7)) * _μS_PER_D
@micropython.native
def is_leap(x): return x%4==0 and (x%100 or not x%400)
@micropython.native
def get_date(μ=None,*,dm=divmod):
  if μ is None: μ = μS()
  s,μ = dm(μ,1_000_000)
  m,s = dm(s,60)
  h,m = dm(m,60)
  d,h = dm(h,24)
  wd  = (d+4)%7
  y,mo = 1970,0
  while 1:
    N = 366 if is_leap(y) else 365
    if d < N: break
    d -= N
    y += 1
  month_days = (31,28+bool(is_leap(y)),31,30,31,30,31,31,30,31,30,31)
  while d >= month_days[mo]:
    d -= month_days[mo]
    mo += 1
  return y,mo,d,wd,h,m,s,μ
@micropython.native
def fmt_date(d=None):
  if d is None          : d = get_date( )
  elif isinstance(d,int): d = get_date(d)
  return f"{d[0]:04}/{d[1]+1:02}/{d[2]+1:02} [Sun+{d[3]}] {d[4]:02}:{d[5]:02}:{d[6]:02}.{d[7]:06}"
@micropython.native
def fmt_dur(μ):
  if μ == inf: return "∞"
  s,μ = divmod(μ,1_000_000)
  m,s = divmod(s,60)
  h,m = divmod(m,60)
  d,h = divmod(h,24)
  R  =   f"{s:02}.{μ:06}"
  if not (m or h or d): return R
  R  =   f"{m:02}:{R}"
  if not (     h or d): return R
  R  =   f"{h:02}:{R}"
  if not (          d): return R
  return f"{d   }:{R}"
@micropython.native
def ntp_single(host=None,timeout=10):
  if host is None: host=choice(NTP_HOSTS)
  
  T0,T3,DAT = ntp_raw(host,timeout or -1)
  if T0 == -1: raise Exception(f"[NTP] ⟨{host}⟩: ntp_raw failed")

  T1_s,T1_μ,T2_s,T2_μ = unpack('!IIII',DAT[32:48])
  if  DAT[0]     & 0b00000111 != 4: raise Exception(f"[NTP] ⟨{host}⟩: Invalid packet due to bad mode")
  if (DAT[0]>>6) & 0b00000011  > 2: raise Exception(f"[NTP] ⟨{host}⟩: Invalid packet due to bad leap")
  if not (1 <= DAT[1] <= 15)      : raise Exception(f"[NTP] ⟨{host}⟩: Invalid packet due to bad stratum")
  if not (T2_s and T1_s)          : raise Exception(f"[NTP] ⟨{host}⟩: Invalid packet")
  T1 = 1_000_000*T1_s + (1_000_000*T1_μ >> 32)
  T2 = 1_000_000*T2_s + (1_000_000*T2_μ >> 32)
  θ = ((T1-T0)+(T2-T3))//2 - _μS_70Y
  δ =  (T3-T0)-(T2-T1)
  return T3, T3+θ, δ # subtract δ//2 from ret[0]?
@micropython.native
def ntp(hosts=2,dup=3,cull_rtt=2,cull_mid=3,timeout=5): # 3 4 3 3
  if isinstance(hosts,int): hosts = sample(NTP_HOSTS,hosts)
  print(f"[NTP] Average: using {dup*len(hosts)} trials")
  X,Δ = { h:[] for h in hosts },[]
  for h in hosts:
    for d in range(dup):
      try:
        X[h].append(ntp_single(h,timeout))
      except Exception as ε:
        X[h].append(ε)
  
  print(f"[NTP] Times:")
  for h,V in X.items():
    for i,v in enumerate(V):
      if not (e := isinstance(v,BaseException)):
        t,RTT = v[1]-v[0],v[2]
      s = f"Failed to sync: {v}" if e else f"{fmt_date(get_date(t+μs()))} (RTT={RTT/1_000_000})"
      print(f"  ⟨{h}⟩ Trial #{i}: {s}")
      if e: continue
      Δ.append((RTT,t))
  
  if not Δ: raise Exception(f"NTP[{', '.join(hosts)}] Could not connect to any servers!")
  
  def show_Δ(v):
    X,Y = [x[0] for x in Δ],[x[1] for x in Δ]
    print(f"[NTP] [n={len(Δ)}] Statistics - {v}")
    print(f"  Mid range: {(max(Y)-min(Y)) / 1_000_000}")
    print(f"  RTT range: {(max(X)-min(X)) / 1_000_000}")
  
  show_Δ("Initial")
  if cull_rtt := max(0, min(cull_rtt, len(Δ)   -1)):
    Δ.sort(key=lambda x: x[0])
    Δ = Δ[:-cull_rtt]
    show_Δ("RTT Cull")
  if cull_mid := max(0, min(cull_mid, len(Δ)//2-1)):
    Δ.sort(key=lambda x: x[1])
    Δ = Δ[cull_mid:-cull_mid]
    show_Δ("Avg Cull")
  
  off = sum(t for _,t in Δ)//len(Δ)
  r = (t := μs()) + off
  ΔΔ = off-(last_ntp[1]-last_ntp[0]) if (last_ntp[0] is not None) else 0
  last_ntp[:] = [t,r]
  print(f"[NTP] Got time: {r}⟨{fmt_date(get_date(r))}⟩ @ {t}⟨{fmt_dur(t)}⟩")
  # d = get_date(r); RTC().init((d[0],d[1],d[2],d[4],d[5],d[6],d[7],0))
  return r,ΔΔ

__all__ = "S_PER_D","S_PER_W","MS_PER_W","ΜS_PER_D","fmt_date","fmt_dur","week_start", \
          "get_date","μs","ms","dt_ms","μS","MS","last_ntp","ntp"

# if __name__ == "__main__":
#   T = get_date(t := ntp())
#   W = get_date(w := week_start(t))
#   print(f"{t} ⇒ {fmt_date(T)}")
#   print(f"{w} ⇒ {fmt_date(W)}")
#   while 1:
#     print(fmt_date())
#     sleep(1)