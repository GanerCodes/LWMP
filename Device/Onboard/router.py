from utils import *

def wifi_via_file(f="credentials",retries=30,log=print):
  if f not in os.listdir():
    return FALSE(log("Could not find wifi config."))
  try:
    router_ssid,router_pass,token = map(str.strip,read_file(f).split('\n')[:3])
  except Exception as ε:
    return FALSE(log(f'Could not parse "{f}": {ε}'))
  log(f'SSID: "{router_ssid}"\nRouter Password: "{router_pass}"\nToken: "{token}"')
  sta_if = network.WLAN(network.STA_IF)
  sta_if.active(True)
  try:
    sta_if.connect(router_ssid,router_pass)
  except Exception as ε:
    return FALSE(log(f'Error connecting using above SSID and password: {ε}'))
  for i in range(r := retries):
    onboard_led(1)
    if sta_if.isconnected():
      onboard_led(0)
      break
    time.sleep(0.1)
    onboard_led(0)
    time.sleep(0.9)
    log('Failed to connect to network [{}/{}] - "{}"'.format(i+1, r, sta_if.status()))
  else:
    sta_if.active(False)
    return FALSE(log("Could not connect to network."))
  return TRUE(log("Connected to Router!"))