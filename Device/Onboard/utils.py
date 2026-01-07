import machine,_thread,network,struct,random,time,json,sys,gc,os
import usocket as socket
from time import sleep
from ulab import numpy as np
from collections import namedtuple

LED_ONBOARD = machine.Pin(2)
LED_ONBOARD.init(LED_ONBOARD.OUT)
onboard_led = lambda s=1: LED_ONBOARD.value(int(bool(s)))

TRUE,FALSE = lambda *𝔸,**𝕂:True, lambda *𝔸,**𝕂:False
boolstr = lambda s: s.strip().lower() in ('true', '1')
def read_file(fn,strip=True):
  with open(fn,'r') as f:
    contents = f.read()
    return contents if strip else contents.strip()
def write_file(fn,content):
  with open(fn,'w') as f:
    f.write(str(content))
def load_check_datafile(f,default,parse=str,log=print):
  if f in os.listdir():
    try:
      return parse(read_file(f).strip())
    except Exception as ε:
      log(f'Error parsing config file: {ε}')
  log(f'Writing "{default}" to file "{f}"')
  write_file(f,default)
  return parse(default)

def gen_load_UUID(log=print):
  if 'UUID' not in os.listdir():
      UUID = hex(int(''.join(str(random.random())[2:] for i in range(3))))[2:10]
      write_file("UUID", UUID)
      log("Created UUID " + UUID)
  else:
      UUID = read_file("UUID")
      log("Loaded UUID: " + UUID)