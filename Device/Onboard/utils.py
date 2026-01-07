import machine,_thread,network,struct,random,time,json,sys,gc,os
import usocket as socket
from ulab import numpy as np
from collections import namedtuple

LED_ONBOARD = machine.Pin(2)
LED_ONBOARD.init(LED_ONBOARD.OUT)
onboard_led = lambda s=1: ONBOARD_LED_PINPOUT.value(int(bool(state)))

TRUE,FALSE = lambda *𝔸,**𝕂:True, lambda *𝔸,**𝕂:False
boolstr = lambda s: s.strip().lower() in ('true', '1')
def read_file(filename, strip=True):
  with open(filename, 'r') as f:
    contents = f.read()
    return contents if strip else contents.strip()
def write_file(filename, content):
  with open(filename, 'w') as f:
    f.write(str(content))
def load_check_datafile(f,default,parse=str,parse_def=True):
  if f in os.listdir():
    try:
      return parse(read_file(f).strip())
    except Exception as err:
      print('Failed to read config file [will re-write default] "{}"'.format(f), err)
  r = parse(default) if parse_def else default
  write_file(f,r)
  return r

START_TIME_MS = time.time_ns() // 1_000_000
uptime_ms = lambda: time.time_ns() // 1_000_000 - START_TIME_MS
def gen_load_UUID(log=print):
  if 'UUID' not in os.listdir():
      UUID = hex(int(''.join(str(random.random())[2:] for i in range(3))))[2:10]
      write_file("UUID", UUID)
      log("Created UUID " + UUID)
  else:
      UUID = read_file("UUID")
      log("Loaded UUID: " + UUID)