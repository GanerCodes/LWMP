import machine,time
from ntp import Ntp
from random import choice

_rtc = machine.RTC()
Ntp.set_datetime_callback(_rtc.datetime)
# Ntp.set_hosts(("0.pool.ntp.org", "1.pool.ntp.org", "2.pool.ntp.org"))

NTP_HOSTS = (choice("0.gentoo.pool.ntp.org 0.pool.ntp.org time.cloudflare.com time.google.com time.nist.gov".split()),
             choice("1.gentoo.pool.ntp.org 1.pool.ntp.org north-america.pool.ntp.org ntp0.ntp-servers.net time-a-g.nist.gov".split()),
             choice("time.android.com time.apple.com time.aws.com time.facebook.com time.windows.com".split()))
print(f'Randomly choosen NTP servers:\n\t{"\n\t".join(NTP_HOSTS)}')

Ntp.set_hosts(NTP_HOSTS)
Ntp.set_ntp_timeout(3)
Ntp.set_epoch(Ntp.EPOCH_1970)
# Ntp.set_dst((Ntp.MONTH_MAR, Ntp.WEEK_LAST, Ntp.WEEKDAY_SUN, 3), (Ntp.MONTH_OCT, Ntp.WEEK_LAST, Ntp.WEEKDAY_SUN, 4), 60)
# Ntp.set_timezone(2, 0) # Set timezone to 2 hours and 0 minutes
# Ntp.set_drift_ppm(-4.6) # If you know the RTC drift in advance, set it manually to -4.6ppm

class Time:
  def __call__(𝕊):
    Ntp.rtc_sync()
    # 0    1  2  3  4  5  6  7  8
    # year mo da hr mn se wd dy micros
    # 2026 01 28 21 41 32 02 28 392025
    d,ms = Time.now(),Time.ms()
    print(f'Synced time, got {' '.join(map(str,d))}')
    s = 60*(60*(24*(d[6]) + d[3]) + d[4]) + d[5]
    print(f"UTC MS: {ms}")
    print(f"UTC SECONDS: {ms//1000}")
    print(f"UTC WEEK START: {ms//1000 - s}")
  now = staticmethod(lambda: Ntp.time   ())
  ms  = staticmethod(lambda: Ntp.time_ms())
Time = Time()

class Tick:
  ms = staticmethod(lambda: time.ticks_ms())
  dt = staticmethod(lambda x,y=None: time.ticks_diff(*(Tick.ms(),x) if y is None else (x,y)))
Tick = Tick()

__all__ = "Ntp","Time","Tick"