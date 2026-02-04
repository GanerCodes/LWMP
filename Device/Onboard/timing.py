from util import *
import ntp
Ntp = ntp.Ntp

Ntp.set_datetime_callback(RTC().datetime)
NTP_HOSTS = (choice("0.gentoo.pool.ntp.org 0.pool.ntp.org time.cloudflare.com time.google.com time.nist.gov".split()),
             choice("1.gentoo.pool.ntp.org 1.pool.ntp.org north-america.pool.ntp.org ntp0.ntp-servers.net time-a-g.nist.gov".split()),
             choice("time.android.com time.apple.com time.aws.com time.facebook.com time.windows.com".split()))
print(f'Randomly choosen NTP servers:\n\t{"\n\t".join(NTP_HOSTS)}')
Ntp.set_hosts(NTP_HOSTS)
Ntp.set_ntp_timeout(3)
Ntp.set_epoch(ntp.EPOCH_1970)
# Ntp.set_drift_ppm(-4.6) # If you know the RTC drift in advance, set it manually to -4.6ppm

time  = Ntp.time
MS    = Ntp.time_ms
def Time():
  Ntp.rtc_sync()
  # year mo da hr mn se wd dy micros
  d,m = time(),ms()
  s = 60*(60*(24*(d[6]) + d[3]) + d[4]) + d[5]
  log(f"Synced time, got {join(d)}",
      f"UTC MS: {m}",
      f"UTC SECONDS: {m//1000}",
      f"UTC WEEK START: {m//1000 - s}", sep='\n')