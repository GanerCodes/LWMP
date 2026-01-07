from utils import *
import ntptime

def wifi_connect(router_ssid,router_password,retries=30,log=print):
  log(f'Connecting to wifi:\nSSID: {router_ssid}"\nPass: {router_pass}')
  sta_if = network.WLAN(network.STA_IF)
  sta_if.active(True)
  try:
    sta_if.connect(router_ssid,router_pass)
  except Exception as ε:
    sta_if.active(False)
    return FALSE(log(f'Error connecting using above SSID and password: {ε}'))
  for i in range(r := retries):
    onboard_led(1)
    if sta_if.isconnected():
      onboard_led(0)
      break
    sleep(0.1)
    onboard_led(0)
    sleep(0.9)
    log('Failed to connect to network [{}/{}] - "{}"'.format(i+1, r, sta_if.status()))
  else:
    sta_if.active(False)
    return FALSE(log("Could not connect to network."))
  return TRUE(log("Connected to Router!"))
# wifi_connect = (lambda f:lambda*𝔸,**𝕂:(lambda r:r if r else (sta_if.active(False),r)[1])(f(*𝔸,**𝕂)))(wifi_connect)

def basic_AP(get=print,post=print,log=print): # 󰤱
  def recv_until(G,x=b"\r\n\r\n"):
    buf = b""
    while x not in buf:
      if not (c := G(4096)): break
      buf += c
    return buf
  ap = network.WLAN(network.AP_IF)
  ap.active(True)
  ap.config(essid="LightWave Controller", password="")
  while not ap.active(): sleep(0.01)
  log(f'Created AP: {ap.ifconfig()}')
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(("", 80))
  s.listen(5)
  while True:
    conn,addr = s.accept()
    log(f'Got connection from {addr}')
    try:
      header,_,body = recv_until(conn.recv).partition(b"\r\n\r\n")
      req_l,*headers = header.decode().split("\r\n")
      method,path,_ = req_l.split(' ',2)
      headers = dict(map(str.lower,x.split(':',1)) for x in headers)
      if blen := headers.get("content-length",0):
        while blen>0:
          if not (c:=conn.recv(4096)): break
          body += c
          blen -= len(c)
      c,t,B = post(path,body) if method == "POST" else get(path)
      if isinstance(v,str): v = v.encode("utf-8")
      
      conn.sendall("\r\n".join(
        [ f"HTTP/1.0 200 OK",
          f"Connection: close",
          f"Content-Length: {len(v)}",
          f"Content-Type: {t}",
          "", B ]).encode("utf-8"))
      conn.close()
    except Exception as ε:
      log(f'Error processing request: {ε}')