import socket,select
from network import WLAN,STA_IF,AP_IF
from util    import *

def wifi_connect(router_ssid,router_pass,retries=30):
  log(f'[WiFi] Connecting to wifi: SSID="{router_ssid}" Pass="{router_pass}"')
  wlan = WLAN(STA_IF)
  wlan.active(True)
  wlan.config(pm=0)
  try:
    wlan.connect(router_ssid,router_pass)
  except Exception as ε:
    wlan.active(False)
    return FALSE(dbg(f'[WiFi] Error connecting using above SSID and password',ε))
  for i in range(r := retries):
    onboard_led(1)
    if wlan.isconnected():
      onboard_led(0)
      break
    sleep(0.1)
    onboard_led(0)
    sleep(0.9)
    log(f'[WiFi] Failed to connect to network [{i+1}/{r}] - "{wlan.status()}"')
  else:
    wlan.active(False)
    return FALSE(log("[WiFi] Could not connect to network."))
  return TRUE(log("[WiFi] Connected."))

def AP_basic(get=print,post=print,loop=True): # 󰤱
  def recv_until(G,x=b"\r\n\r\n",buf=b""):
    while c := G(4096):
      buf += c
      if x in buf: break
    return buf
  ap = WLAN(AP_IF)
  ap.active(True)
  ap.config(essid="LightWave Controller",password="")
  while not ap.active(): sleep(0.01)
  log(f'Created AP: {ap.ifconfig()}')
  s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
  s.bind(("",80))
  s.listen(5)
  def handle():
    conn,addr = s.accept()
    log(f'[AP] Got connection from {addr}')
    try:
      header,_,body = recv_until(conn.recv).partition(b"\r\n\r\n")
      req_l,*headers = header.decode().split("\r\n")
      method,path,_ = req_l.split(' ',2)
      headers = dict((x.lower().split(':',1) for x in headers))
      if blen := int(headers.get("content-length",0)):
        while blen>0 and (c:=conn.recv(4096)):
          body += c
          blen -= len(c)
      # log(f"{method=}\n{path=}\n{headers=}\n{body=}")
      c,t,B = post(path,body) if method == "POST" else get(path)
      if isinstance(B,str): B = B.encode("utf-8")
      conn.sendall(f"""\
HTTP/1.1 200 OK\r
Connection: close\r
Cache-Control: no-store\r
Content-Length: {len(B)}\r
Content-Type: {t}\r
Access-Control-Allow-Origin: *\r\n\r\n""".encode("utf-8")+B)
      conn.close()
    except Exception as ε:
      dbg(f'[AP] Error processing request:',ε)
    finally:
      try             : conn.close()
      except Exception: pass
      free()
  if not loop:
    s.setblocking(False)
    return handle,s
  while 1: handle()

def DNS_trap(log=print,loop=True): # this is half AI lol
  s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
  s.bind(("",53))
  def handle():
    dat,addr = s.recvfrom(512)
    print(f'Got DNS message from {addr}')
    if len(dat)<12: return
    i = 12
    while dat[i]: i += dat[i]+1
    s.sendto(dat[:2]+b"\x81\x80"+dat[4:6]+b"\x00\x01\x00\x00\x00\x00"+dat[12:i+5]+
                b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04\xc0\xa8\x04\x01",
             addr)
  if not loop:
    s.setblocking(False)
    return handle,s
  while 1: handle()

def AP_with_DNS(*𝔸,timeout=None,timeout_f=log,**𝕂):
  (f1,s1),(f2,s2) = AP_basic(*𝔸,loop=False,**𝕂),DNS_trap(loop=False)
  
  poll = select.poll()
  poll.register(s1, select.POLLIN)
  poll.register(s2, select.POLLIN)
  
  l_evt = ms()
  while 1:
    for sock,ev in poll.poll(100):
      if   sock is s1: f1()
      elif sock is s2: f2()
      else           : continue
      l_evt = ms()
    if timeout is not None and dt_ms(l_evt) > 1000*timeout:
      timeout_f()

__all__ = "wifi_connect","AP_basic","DNS_trap","AP_with_DNS"