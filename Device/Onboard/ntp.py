import socket
from time   import ticks_diff,sleep,time_ns,ticks_ms as ms
from random import choice,randrange
from struct import unpack

from lw_ntp import ntp_raw

NTP_HOSTS = """time.cloudflare.com time.google.com time.apple.com time.aws.com""".split()

def sample(X,n):
  I = list(range(len(X)))
  return [X[I.pop(randrange(len(I)))] for _ in range(min(n,len(X)))]

last_ntp = [None]*2
time_us = lambda *,time_ns=time_ns: time_ns()//1000
def time_μ(*,last_ntp=last_ntp,time_us=time_us):
  if last_ntp[0] is None: return time_us()
  o,T = last_ntp
  return time_us()-o+T
MS = lambda *,time_μ=time_μ: time_μ()//1000

is_leap = lambda x: not x%4 and (x%100 or not x%400)
def get_date(μ=None):
  if μ is None: μ = time_μ()
  s,μ = divmod(μ,1_000_000)
  m,s = divmod(s,60)
  h,m = divmod(m,60)
  d,h = divmod(h,24)
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
def fmt_date(d=None):
  if d is None: d = get_date()
  return f"{d[0]:04}/{d[1]+1:02}/{d[2]+1:02} [Sun+{d[3]}] {d[4]:02}:{d[5]:02}:{d[6]:02}.{d[7]:06}"
def week_start(μ=None):
  if μ is None: μ = time_μ()
  DAY_μ = 86_400_000_000
  d = μ // DAY_μ
  wd = (d+4)%7
  return (d-wd) * DAY_μ

@micropython.native
def ntp_single(host=None,timeout=10):
  if host is None: host=choice(NTP_HOSTS)
  
  T0,T3,DAT = ntp_raw(host,timeout or -1)
  if T0 == -1: raise Exception(f"NTP [{host}]: ntp_raw failed")

  T1_s,T1_μ,T2_s,T2_μ = unpack('!IIII', DAT[32:48])
  if  DAT[0]     & 0b00000111 != 4: raise Exception(f"NTP [{host}]: Invalid packet due to bad mode")
  if (DAT[0]>>6) & 0b00000011  > 2: raise Exception(f"NTP [{host}]: Invalid packet due to bad leap")
  if not (1 <= DAT[1] <= 15)      : raise Exception(f"NTP [{host}]: Invalid packet due to bad stratum")
  if not (T2_s and T1_s)          : raise Exception(f"NTP [{host}]: Invalid packet")
  T1 = 1_000_000*T1_s + (1_000_000*T1_μ >> 32)
  T2 = 1_000_000*T2_s + (1_000_000*T2_μ >> 32)
  θ = ((T1-T0)+(T2-T3))//2 - 2_208_988_800_000_000
  δ = (T3-T0) - (T2-T1)
  return T3, T3+θ, δ
  # δ = (RTT := T3-T0) - (T2-T1)
  # return T3, T2 - (2_208_988_800_000_000 + δ//2), RTT

@micropython.native
def ntp(hosts=2,dup=3,cull_rtt=2,cull_mid=3,timeout=5): # 3 4 3 3
  if isinstance(hosts,int): hosts = sample(NTP_HOSTS,hosts)
  print(f"NTP Average: using {dup*len(hosts)} trials")
  X,Δ = { h:[] for h in hosts },[]
  for h in hosts:
    for d in range(dup):
      try:
        X[h].append(ntp_single(h,timeout))
      except Exception as ε:
        X[h].append(ε)
  
  print(f"NTP Times:")
  for h,V in X.items():
    for i,v in enumerate(V):
      if not (e := isinstance(v,BaseException)):
        t,RTT = v[1]-v[0],v[2]
      s = f"Failed to sync: {v}" if e else f"{fmt_date(get_date(t+time_us()))} (RTT={RTT/1_000_000})"
      print(f"\tNTP[{h}] Trial #{i}: {s}")
      if e: continue
      Δ.append((RTT,t))
  
  if not Δ: raise Exception(f"NTP[{', '.join(hosts)}] Could not connect to any servers!")
  
  def show_Δ(v):
    X,Y = [x[0] for x in Δ],[x[1] for x in Δ]
    print(f"NTP [n={len(Δ)}] Statistics - {v}")
    print(f"\tMid range: {(max(Y)-min(Y)) / 1_000_000}")
    print(f"\tRTT range: {(max(X)-min(X)) / 1_000_000}")
  
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
  r = (t := time_us()) + off
  ΔΔ = 0
  if last_ntp[0] is not None:
    ΔΔ = off - (last_ntp[1]-last_ntp[0])
  last_ntp[:] = [t,r]
  print(f"NTP Time: {fmt_date(get_date(r))}")
  return r,ΔΔ

s_per_w = (s_per_d := 60*60*24)*7
dt_ms = lambda x,y=None: ticks_diff(*(ms(),x) if y is None else (x,y))

__all__ = "s_per_d","s_per_w","get_date","week_start","fmt_date", \
          "sleep","ms","dt_ms","MS","time_μ",                     \
          "last_ntp","ntp_single","ntp"

if __name__ == "__main__":
  T = get_date(t := ntp())
  W = get_date(w := week_start(t))
  print(f"{t} ⇒ {fmt_date(T)}")
  print(f"{w} ⇒ {fmt_date(W)}")
  while 1:
    print(fmt_date())
    sleep(1)