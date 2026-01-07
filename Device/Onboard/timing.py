from ntp import Ntp
import machine

Ntp.set_datetime_callback(machine.RTC().datetime)
Ntp.set_logger_callback(print)
Ntp.set_hosts(('0.pool.ntp.org', '1.pool.ntp.org', '2.pool.ntp.org'))
Ntp.set_ntp_timeout(1)
Ntp.set_epoch(Ntp.EPOCH_1970)

class Time:
  def __init__(𝕊): Ntp.rtc_sync()
  now = staticmethod(lambda: Ntp.time   ())
  ms  = staticmethod(lambda: Ntp.time_ms())

# Ntp.set_dst((Ntp.MONTH_MAR, Ntp.WEEK_LAST, Ntp.WEEKDAY_SUN, 3),
#             (Ntp.MONTH_OCT, Ntp.WEEK_LAST, Ntp.WEEKDAY_SUN, 4),
#             60)
# Ntp.set_timezone(2, 0) # Set timezone to 2 hours and 0 minutes
# Ntp.set_drift_ppm(-4.6) # If you know the RTC drift in advance, set it manually to -4.6ppm

