# https://github.com/ekondayan/micropython-ntp

import socket
import struct
import time

_EPOCH_DELTA_1900_1970 = const(2208988800)  # Seconds between 1900 and 1970
_EPOCH_DELTA_1900_2000 = const(3155673600)  # Seconds between 1900 and 2000
_EPOCH_DELTA_1970_2000 = const(946684800)  # Seconds between 1970 and 2000 = _EPOCH_DELTA_1900_2000 - _EPOCH_DELTA_1900_1970

EPOCH_1900 = const(0)
EPOCH_1970 = const(1)
EPOCH_2000 = const(2)

_MONTH_JAN = const(1)
_MONTH_FEB = const(2)
_MONTH_MAR = const(3)
_MONTH_APR = const(4)
_MONTH_MAY = const(5)
_MONTH_JUN = const(6)
_MONTH_JUL = const(7)
_MONTH_AUG = const(8)
_MONTH_SEP = const(9)
_MONTH_OCT = const(10)
_MONTH_NOV = const(11)
_MONTH_DEC = const(12)

_WEEK_FIRST = const(1)
_WEEK_SECOND = const(2)
_WEEK_THIRD = const(3)
_WEEK_FOURTH = const(4)
_WEEK_FIFTH = const(5)
_WEEK_LAST = const(6)

_SUBSECOND_PRECISION_SEC = const(1000_000)
_SUBSECOND_PRECISION_MS = const(1000)
_SUBSECOND_PRECISION_US = const(1)

class Ntp:
    _log_callback = print  # Callback for message output
    _datetime_callback = None  # Callback for reading/writing the RTC
    _datetime_callback_precision = _SUBSECOND_PRECISION_US  # Callback precision
    _hosts: list = []  # Array of hostnames or IPs
    _timezone: int = 0  # Timezone offset in seconds
    _rtc_last_sync: int = 0  # Last RTC synchronization timestamp. Uses device's epoch
    _drift_last_compensate: int = 0  # Last RTC drift compensation timestamp. Uses device's epoch
    _drift_last_calculate: int = 0  # Last RTC drift calculation timestamp. Uses device's epoch
    _ppm_drift: float = 0.0  # RTC drift
    _ntp_timeout_s: int = 1  # Network timeout when communicating with NTP servers
    _epoch = EPOCH_2000  # User selected epoch
    _device_epoch = None  # The device's epoch

    _dst_start: (tuple, None) = None  # (month, week, day of week, hour)
    _dst_end: (tuple, None) = None  # (month, week, day of week, hour)
    _dst_bias: int = 0  # Time bias in seconds

    _dst_cache_switch_hours_start = None  # Cache the switch hour calculation
    _dst_cache_switch_hours_end = None  # Cache the switch hour calculation
    _dst_cache_switch_hours_timestamp = None  # Cache the year, the last switch time calculation was made

    # ========================================
    # Preallocate ram to prevent fragmentation
    # ========================================
    __weekdays = (5, 6, 0, 1, 2, 3, 4)
    __days = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    __ntp_msg = bytearray(48)
    # Lookup Table for fast access. Row = from_epoch Column = to_epoch
    __epoch_delta_lut = ((0, -_EPOCH_DELTA_1900_1970, -_EPOCH_DELTA_1900_2000),
                         (_EPOCH_DELTA_1900_1970, 0, -_EPOCH_DELTA_1970_2000),
                         (_EPOCH_DELTA_1900_2000, _EPOCH_DELTA_1970_2000, 0))

    @classmethod
    def set_datetime_callback(cls, callback, precision = _SUBSECOND_PRECISION_US):
        cls._datetime_callback_precision = precision

        def precision_adjusted_callback(*args):
            if len(args) == 0:
                # Getter mode
                dt = callback()
                if isinstance(dt, (tuple, list)) and len(dt) == 8:
                    return dt[:7] + (dt[7] * precision,)
                raise ValueError()
            elif len(args) == 1 and isinstance(args[0], (tuple, list)) and len(args[0]) == 8:
                # Setter mode
                dt = args[0]
                return callback(dt[:7] + (dt[7] // precision,))

            raise ValueError()

        cls._datetime_callback = precision_adjusted_callback

    @classmethod
    def set_logger_callback(cls, callback = print):
        cls._log_callback = callback

    @classmethod
    def set_epoch(cls, epoch: int = None):
        if epoch is None:
            cls._epoch = cls.device_epoch()
        elif isinstance(epoch, int) and EPOCH_1900 <= epoch <= EPOCH_2000:
            cls._epoch = epoch

    @classmethod
    def set_dst(cls, start: tuple = None, end: tuple = None, bias: int = 0):
        if start is None or end is None or bias == 0:
            cls._dst_start = None
            cls._dst_end = None
            cls._dst_bias = 0
        else:
            cls.set_dst_start(start[0], start[1], start[2], start[3])
            cls.set_dst_end(end[0], end[1], end[2], end[3])
            cls.set_dst_bias(bias)

    @classmethod
    def set_dst_start(cls, month: int, week: int, weekday: int, hour: int):
        cls._dst_start = (month, week, weekday, hour)

    @classmethod
    def get_dst_start(cls):
        return cls._dst_start

    @classmethod
    def set_dst_end(cls, month: int, week: int, weekday: int, hour: int):
        cls._dst_end = (month, week, weekday, hour)

    @classmethod
    def get_dst_end(cls):
        return cls._dst_end

    @classmethod
    def set_dst_bias(cls, bias: int):
        if bias == 0:
            cls._dst_start = None
            cls._dst_end = None

        # Convert to seconds
        cls._dst_bias = bias * 60

    @classmethod
    def get_dst_bias(cls):
        return cls._dst_bias // 60

    @classmethod
    def dst(cls, dt = None):
        # Return 0 if DST is disabled
        if cls._dst_start is None or cls._dst_end is None or cls._dst_bias == 0:
            return 0

        # If a datetime tuple is passed, the DST will be calculated according to it otherwise read the current datetime
        if dt is None:
            # dt = (year, month, day, weekday, hour, minute, second, subsecond)
            # index  0      1     2      3       4      5       6        7
            dt = cls._datetime()
        elif not isinstance(dt, tuple) or len(dt) != 8:
            raise ValueError()

        # Calculates and caches the hours since the beginning of the month when the DST starts/ends
        if dt[0] != cls._dst_cache_switch_hours_timestamp or \
                cls._dst_cache_switch_hours_start is None or \
                cls._dst_cache_switch_hours_end is None:
            cls._dst_cache_switch_hours_timestamp = dt[0]
            cls._dst_cache_switch_hours_start = cls.weekday_in_month(dt[0], cls._dst_start[0], cls._dst_start[1], cls._dst_start[2]) * 24 + cls._dst_start[3]
            cls._dst_cache_switch_hours_end = cls.weekday_in_month(dt[0], cls._dst_end[0], cls._dst_end[1], cls._dst_end[2]) * 24 + cls._dst_end[3]

        # Condition 1: The current month is strictly within the DST period
        # Condition 2: Current month is the month the DST period starts. Calculates the current hours since the beginning of the month
        #              and compares it with the cached value of the hours when DST starts
        # Condition 3: Current month is the month the DST period ends. Calculates the current hours since the beginning of the month
        #              and compares it with the cached value of the hours when DST ends
        # If one of the three conditions is True, the DST is in effect
        if cls._dst_start[0] < dt[1] < cls._dst_end[0] or \
                (dt[1] == cls._dst_start[0] and (dt[2] * 24 + dt[4]) >= cls._dst_cache_switch_hours_start) or \
                (dt[1] == cls._dst_end[0] and (dt[2] * 24 + dt[4]) < cls._dst_cache_switch_hours_end):
            return cls._dst_bias

        # The current month is outside the DST period
        return 0

    @classmethod
    def set_ntp_timeout(cls, timeout_s: int = 1):
        if not isinstance(timeout_s, int):
            raise ValueError()

        cls._ntp_timeout_s = timeout_s

    @classmethod
    def get_ntp_timeout(cls):
        return cls._ntp_timeout_s

    @classmethod
    def get_hosts(cls):
        return tuple(cls._hosts)

    @classmethod
    def set_hosts(cls, value: tuple):
        cls._hosts.clear()

        for host in value:
            cls._hosts.append(host)

    @classmethod
    def get_timezone(cls):
        return cls._timezone // 3600, (cls._timezone % 3600) // 60

    @classmethod
    def set_timezone(cls, hour: int, minute: int = 0):
        if not isinstance(hour, int) or not isinstance(minute, int):
            raise ValueError()

        if (
                (minute not in (0, 30, 45)) or
                (minute == 0 and not (-12 <= hour <= 14)) or
                (minute == 30 and hour not in (-9, -3, 3, 4, 5, 6, 9, 10)) or
                (minute == 45 and hour not in (5, 8, 12))
        ):
            raise ValueError()

        cls._timezone = hour * 3600 + minute * 60

    @classmethod
    def time(cls, utc: bool = False):
        # gmtime() uses the device's epoch
        us = cls.time_us(cls.device_epoch(), utc = utc)
        # (year, month, day, hour, minute, second, weekday, yearday) + (us,)
        return time.gmtime(us // 1000_000) + (us % 1000_000,)

    @classmethod
    def time_s(cls, epoch: int = None, utc: bool = False):
        return cls.time_us(epoch = epoch, utc = utc) // 1000_000

    @classmethod
    def time_ms(cls, epoch: int = None, utc: bool = False):
        return cls.time_us(epoch = epoch, utc = utc) // 1000

    @classmethod
    def time_us(cls, epoch: int = None, utc: bool = False):
        # dt = (year, month, day, weekday, hour, minute, second, subsecond)
        dt = cls._datetime()

        epoch_delta = cls.epoch_delta(cls.device_epoch(), epoch)

        # Daylight Saving Time (DST) is not used for UTC as it is a time standard for all time zones.
        timezone_and_dst = 0 if utc else (cls._timezone + cls.dst(dt))
        # mktime() uses the device's epoch
        return (time.mktime((dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], 0, 0, 0)) + epoch_delta + timezone_and_dst) * 1000_000 + dt[7]

    @classmethod
    def ntp_time(cls, epoch: int = None):
        # Clear the NTP request packet
        cls.__ntp_msg[0] = 0x1B
        for i in range(1, len(cls.__ntp_msg)):
            cls.__ntp_msg[i] = 0

        for host in cls._hosts:
            s = None
            try:
                host_addr = socket.getaddrinfo(host, 123)[0][-1]
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(cls._ntp_timeout_s)
                transmin_ts_us = time.ticks_us()  # Record send time (T1)
                s.sendto(cls.__ntp_msg, host_addr)
                s.readinto(cls.__ntp_msg)
                receive_ts_us = time.ticks_us()  # Record receive time (T2)
            except Exception as e:
                cls._log('(NTP) Network error: Host({}) Error({})'.format(host, str(e)))
                continue
            finally:
                if s is not None:
                    s.close()

            # Mode: The mode field of the NTP packet is an 8-bit field that specifies the mode of the packet.
            # A value of 4 indicates a server response, so if the mode value is not 4, the packet is invalid.
            if (cls.__ntp_msg[0] & 0b00000111) != 4:
                cls._log('(NTP) Invalid packet due to bad "mode" field value: Host({})'.format(host))
                continue

            # Leap Indicator: The leap indicator field of the NTP packet is a 2-bit field that indicates the status of the server's clock.
            # A value of 0 or 1 indicates a normal or unsynchronized clock, so if the leap indicator field is set to any other value, the packet is invalid.
            if ((cls.__ntp_msg[0] >> 6) & 0b00000011) > 2:
                cls._log('(NTP) Invalid packet due to bad "leap" field value: Host({})'.format(host))
                continue

            # Stratum: The stratum field of the NTP packet is an 8-bit field that indicates the stratum level of the server.
            # A value outside the range 1 to 15 indicates an invalid packet.
            if not (1 <= (cls.__ntp_msg[1]) <= 15):
                cls._log('(NTP) Invalid packet due to bad "stratum" field value: Host({})'.format(host))
                continue

            # Extract T3 and T4 from the NTP packet
            # Receive Timestamp (T3): The Receive Timestamp field of the NTP packet is a 64-bit field that contains the server's time when the packet was received.
            srv_receive_ts_sec, srv_receive_ts_frac = struct.unpack('!II', cls.__ntp_msg[32:40])  # T3
            # Transmit Timestamp (T4): The Transmit Timestamp field of the NTP packet is a 64-bit field that contains the server's time when the packet was sent.
            srv_transmit_ts_sec, srv_transmit_ts_frac = struct.unpack('!II', cls.__ntp_msg[40:48])  # T4

            # If any of these fields is zero, it may indicate that the packet is invalid.
            if srv_transmit_ts_sec == 0 or srv_receive_ts_sec == 0:
                cls._log('(NTP) Invalid packet: Host({})'.format(host))
                continue

            # Convert T3 to microseconds
            srv_receive_ts_us = srv_receive_ts_sec * 1_000_000 + (srv_receive_ts_frac * 1_000_000 >> 32)
            # Convert T4 to microseconds
            srv_transmit_ts_us = srv_transmit_ts_sec * 1_000_000 + (srv_transmit_ts_frac * 1_000_000 >> 32)
            # Calculate network delay in microseconds
            network_delay_us = (receive_ts_us - transmin_ts_us) - (srv_transmit_ts_us - srv_receive_ts_us)
            # Adjust server time (T4) by half of the network delay
            adjusted_server_time_us = srv_transmit_ts_us - (network_delay_us // 2)
            # Adjust server time (T4) by the epoch difference
            adjusted_server_time_us += cls.epoch_delta(from_epoch = EPOCH_1900, to_epoch = epoch) * 1_000_000

            # Return the adjusted server time and the reception time in us
            return adjusted_server_time_us, receive_ts_us

        raise RuntimeError('Can not connect to any of the NTP servers')

    @classmethod
    def rtc_sync(cls, new_time = None):
        if new_time is None:
            new_time = cls.ntp_time(cls.device_epoch())
        elif not isinstance(new_time, tuple) or not len(new_time) == 2:
            raise ValueError()

        # Take into account the time from the moment it was taken up to this point
        ntp_us = new_time[0] + (time.ticks_us() - new_time[1])
        lt = time.gmtime(ntp_us // 1000_000)
        # lt = (year, month, day, hour, minute, second, weekday, yearday)
        # index  0      1     2    3      4       5       6         7

        cls._datetime((lt[0], lt[1], lt[2], lt[6], lt[3], lt[4], lt[5], ntp_us % 1000_000))
        # Store the precision-adjusted value to match what RTC actually stores
        cls._rtc_last_sync = (ntp_us // cls._datetime_callback_precision) * cls._datetime_callback_precision

    @classmethod
    def rtc_last_sync(cls, epoch: int = None, utc: bool = False):
        timezone_and_dst = 0 if utc else (cls._timezone + cls.dst())
        epoch_delta = cls.epoch_delta(cls.device_epoch(), epoch)
        return 0 if cls._rtc_last_sync == 0 else cls._rtc_last_sync + (epoch_delta + timezone_and_dst) * 1000_000

    @classmethod
    def drift_calculate(cls, new_time = None):
        if cls._rtc_last_sync == 0 and cls._drift_last_compensate == 0:
            return 0.0, 0

        if new_time is None:
            new_time = cls.ntp_time(cls.device_epoch())

        rtc_us = cls.time_us(epoch = cls.device_epoch(), utc = True)
        ntp_us = new_time[0] + (time.ticks_us() - new_time[1])
        
        rtc_sync_delta = ntp_us - max(cls._rtc_last_sync, cls._drift_last_compensate)
        rtc_ntp_delta = rtc_us - ntp_us
        cls._ppm_drift = (rtc_ntp_delta / rtc_sync_delta) * 1000_000
        cls._drift_last_calculate = ntp_us

        return cls._ppm_drift, rtc_ntp_delta

    @classmethod
    def drift_last_compensate(cls, epoch: int = None, utc: bool = False):
        timezone_and_dst = 0 if utc else (cls._timezone + cls.dst())
        epoch_delta = cls.epoch_delta(cls.device_epoch(), epoch)
        return 0 if cls._drift_last_compensate == 0 else cls._drift_last_compensate + (epoch_delta + timezone_and_dst) * 1000_000

    @classmethod
    def drift_last_calculate(cls, epoch: int = None, utc: bool = False):
        timezone_and_dst = 0 if utc else (cls._timezone + cls.dst())
        epoch_delta = cls.epoch_delta(cls.device_epoch(), epoch)
        return 0 if cls._drift_last_calculate == 0 else cls._drift_last_calculate + (epoch_delta + timezone_and_dst) * 1000_000

    @classmethod
    def drift_ppm(cls):
        return cls._ppm_drift

    @classmethod
    def set_drift_ppm(cls, ppm: float):
        cls._ppm_drift = float(ppm)

    @classmethod
    def drift_us(cls, ppm_drift: float = None):
        if cls._rtc_last_sync == 0 and cls._drift_last_compensate == 0:
            return 0

        if ppm_drift is None:
            ppm_drift = cls._ppm_drift

        delta_time_rtc = cls.time_us(epoch = cls.device_epoch(), utc = True) - max(cls._rtc_last_sync, cls._drift_last_compensate)
        delta_time_real = int((1000_000 * delta_time_rtc) // (1000_000 + ppm_drift))

        return delta_time_rtc - delta_time_real

    @classmethod
    def drift_compensate(cls, compensate_us: int):
        rtc_us = cls.time_us(epoch = cls.device_epoch(), utc = True) + compensate_us
        lt = time.gmtime(rtc_us // 1000_000)
        # lt = (year, month, day, hour, minute, second, weekday, yearday)
        # index  0      1     2    3      4       5       6         7

        cls._datetime((lt[0], lt[1], lt[2], lt[6], lt[3], lt[4], lt[5], rtc_us % 1000_000))
        cls._drift_last_compensate = rtc_us

    @classmethod
    def weekday(cls, year: int, month: int, day: int):
        if not isinstance(year, int) or not 1 <= year:
            raise ValueError()
        elif not isinstance(month, int) or not cls._MONTH_JAN <= month <= cls._MONTH_DEC:
            raise ValueError()

        days = cls.days_in_month(year, month)
        if day > days:
            raise ValueError()

        if month <= 2:
            month += 12
            year -= 1

        y = year % 100
        c = year // 100
        w = int(day + int((13 * (month + 1)) / 5) + y + int(y / 4) + int(c / 4) + 5 * c) % 7

        return cls.__weekdays[w]

    @classmethod
    def days_in_month(cls, year, month):
        if month == cls._MONTH_FEB:
            if (year % 400 == 0) or ((year % 4 == 0) and (year % 100 != 0)):
                return cls.__days[1] + 1
        return cls.__days[month - 1]

    @classmethod
    def weeks_in_month(cls, year, month):
        first_sunday = 7 - cls.weekday(year, month, 1)
        weeks_list = list()
        weeks_list.append((1, first_sunday))
        days_in_month = cls.days_in_month(year, month)
        for i in range(0, 5):
            if days_in_month <= first_sunday + (i + 1) * 7:
                weeks_list.append((weeks_list[i][1] + 1, days_in_month))
                break
            else:
                weeks_list.append((weeks_list[i][1] + 1, first_sunday + (i + 1) * 7))

        return weeks_list

    @classmethod
    def weekday_in_month(cls, year: int, month: int, ordinal_weekday: int, weekday: int):
        first_weekday = cls.weekday(year, month, 1)  # weekday of first day of month
        first_day = 1 + (weekday - first_weekday) % 7  # monthday of first requested weekday
        weekdays = [i for i in range(first_day, cls.days_in_month(year, month) + 1, 7)]
        return weekdays[-1] if ordinal_weekday > len(weekdays) else weekdays[ordinal_weekday - 1]

    @classmethod
    def day_from_week_and_weekday(cls, year, month, week, weekday):
        weeks = cls.weeks_in_month(year, month)
        # Last day of the last week is the total days in month. This is faster instead of calling days_in_month(year, month)
        days_in_month = weeks[-1][1]

        week_tuple = weeks[-1] if week > len(weeks) else weeks[week - 1]
        day = week_tuple[0] + weekday

        # If the day is outside the boundaries of the month, select the week before the last
        # This behaviour guarantees to return the last weekday of the month
        if day > days_in_month:
            return weeks[-2][0] + weekday

        # The desired weekday overflow the last day of the week
        if day > week_tuple[1]:
            raise Exception('The weekday does not exists in the selected week')

        # The first week is an edge case thus it must be handled in a special way
        if week == cls._WEEK_FIRST:
            # If first week does not contain the week day return the weekday from the second week
            if weeks[0][0] + (6 - weekday) > weeks[0][1]:
                return weeks[1][0] + weekday

            return weekday - (6 - weeks[0][1])

        return day

    @classmethod
    def epoch_delta(cls, from_epoch: int, to_epoch: int):
        if from_epoch is None: from_epoch = cls._epoch
        if to_epoch is None: to_epoch = cls._epoch
        return cls.__epoch_delta_lut[from_epoch][to_epoch]

    @classmethod
    def device_epoch(cls):
        cls._device_epoch = EPOCH_1970
        return cls._device_epoch

    @classmethod
    def _log(cls, message: str):
        if callable(cls._log_callback):
            cls._log_callback(message)

    @classmethod
    def _datetime(cls, *dt):
        try:
            return cls._datetime_callback(*dt)
        except Exception as e:
            cls._log('(RTC) Error. {}'.format(e))
            raise e