import micropython,socket,select,ssl
from collections import namedtuple
from network     import WLAN,STA_IF,AP_IF
from time        import sleep
from util        import *

class CloseConnection(Exception): None

URI = namedtuple('URI',('prot','host','port','path'))
def uriparse(uri,no_p="https",sec=("https","wss")): # wildly not complete but whatever lol
  if "://" in uri : prot,host = uri.split("://",1)
  else            : prot,host = no_p,host
  if '/'   in host: host,path = host.split('/',1)
  else            : host,path = host,""
  if ':'   in host: host,port = host.split(':',1)
  else            : host,port = host,(80,443)[prot in sec]
  path,port = '/'+path,int(port)
  free()
  return URI(prot,host,port,path)

def wlan(m,**𝕂):
  net = WLAN(m)
  net.active(True)
  net.config(pm=0,**𝕂)
  return net

def wifi_connect(router_ssid,router_pass,retries=30):
  log(f'[WiFi] Connecting to wifi: SSID="{router_ssid}" Pass="{router_pass}"')
  net = wlan(STA_IF)
  try:
    net.connect(router_ssid,router_pass)
  except Exception as ε:
    net.active(False)
    dbg(f'[WiFi] Error connecting using above SSID and password',ε)
    return False
  for i in range(r := retries):
    onboard_led(1)
    if net.isconnected():
      onboard_led(0)
      break
    sleep(0.1)
    onboard_led(0)
    sleep(0.9)
    log(f'[WiFi] Failed to connect to network [{i+1}/{r}] - "{net.status()}"')
  else:
    net.active(False)
    log("[WiFi] Could not connect to network.")
    return False
  log("[WiFi] Connected.")
  return lambda: net.active(False)

def AP_basic(get=log,post=log,loop=True,ssid="AP",password=""):
  def recv_until(G,x=b"\r\n\r\n",buf=b""):
    while c := G(512):
      buf += c
      if x in buf: break
      frees(0)
    return buf
  net = wlan(AP_IF,essid=ssid,password=password)
  while not net.active(): frees(0.025)
  log(f'[AP] Created "{ssid}" {net.ifconfig()}')
  s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
  s.bind(("",80))
  s.listen(5)
  def handle():
    conn,addr = s.accept()
    try:
      header,_,body = recv_until(conn.recv).partition(b"\r\n\r\n")
      method,*header = header.decode().split("\r\n")
      method,path,_ = method.split(' ',2)
      log(f'[AP] [{join(addr)}] {method} {path}')
      headers = {}
      for h in header:
        k,v = h.split(':',1)
        del h
        headers[k.lower().strip()] = v.strip()
        del k,v
      del _,header
      # log('[AP] Headers:\n  '+join((f"{k}: {v}" for k,v in headers.items()),'\n  '))
      if blen := int(headers.get("content-length",0))-len(body):
        while blen>0 and (c:=conn.recv(512)):
          body += c
          blen -= len(c)
          frees(0)
      del blen
      
      c,t,B,*𝔸 = post(path,body) if method == "POST" else get(path)
      del body,path,headers
      headers = { "Connection"                 : "close",
                  "Cache-Control"              : "no-store",
                  "Content-Length"             : len(B),
                  "Content-Type"               : t,
                  "Access-Control-Allow-Origin": "*" }
      if isinstance(B,str): B = B.encode()
      else                : headers["Content-Encoding"] = "gzip"
      
      lines = [f"HTTP/1.1 {c} {'OK' if c==200 else 'Bad Request'}"]
      lines.extend([f"{k}:{v}" for k,v in headers.items()])
      del headers
      lines.extend(["",""])
      resp = memoryview(join(lines,"\r\n").encode()+B)
      del lines
      w = 0
      while w<len(resp): w += conn.write(resp[w:])
      conn.close()
      del c,t,B,resp,w
      if 𝔸 and 𝔸[0] == True:
        raise CloseConnection("Closed Intentionally") 
    except Exception as ε:
      if isinstance(ε,CloseConnection): raise ε
      dbg(f'[AP] Error processing request:',ε)
    finally:
      try             : conn.close()
      except Exception: pass
      frees()
  if not loop:
    s.setblocking(False)
    return handle,s,lambda:(s.close(),net.active(False))
  while 1: handle()

def DNS_trap(loop=True):
  s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
  s.bind(("",53))
  def handle(): # this is half AI lol
    dat,addr = s.recvfrom(512)
    log(f'[DNS] [{join(addr)}] Got DNS query')
    if len(dat)<12: return
    i = 12
    while dat[i]: i += dat[i]+1
    s.sendto(dat[:2]+b"\x81\x80"+dat[4:6]+b"\x00\x01\x00\x00\x00\x00"+dat[12:i+5]+
                b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04\xc0\xa8\x04\x01",
             addr)
  if not loop:
    s.setblocking(False)
    return handle,s,s.close
  while 1: handle()

def AP_with_DNS(*𝔸,timeout=None,timeout_f=None,**𝕂):
  (f1,s1,c1),(f2,s2,c2) = AP_basic(*𝔸,loop=False,**𝕂),DNS_trap(loop=False)
  
  poll = select.poll()
  poll.register(s1, select.POLLIN)
  poll.register(s2, select.POLLIN)
  
  l_evt = ms()
  while 1:
    close = False
    try:
      for sock,ev in poll.poll(100):
        free()
        if   sock is s1: f1()
        elif sock is s2: f2()
        else           : continue
        l_evt = ms()
    except CloseConnection: close = True
    except Exception      : dbg("[NET] Unhandled exception",ε)
    finally:
      if close or timeout is not None and dt_ms(l_evt) > 1000*timeout:
        if timeout_f is not None: timeout_f()
        try                  : c1()
        except Exception as ε: dbg("[NET] Failed to close AP" ,ε)
        try                  : c2()
        except Exception as ε: dbg("[NET] Failed to close DNS",ε)
        return

# @micropython.native
def ssl_cond(s,uri,sec=("https","wss")):
  if uri.prot not in sec: return s
  host = uri.host
  del uri,sec
  # micropython.mem_info(0)
  free()
  # import time; log(time.localtime()); del time
  log(f"[SSL] >> Mem: {mem_perc()}")
  ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
  ctx.check_hostname = True
  ctx.verify_mode    = ssl.CERT_REQUIRED
  ctx.load_verify_locations(cafile="CERT.pem")
  try:
    s = ctx.wrap_socket(s, server_hostname=host)
  except Exception as ε:
    dbg(f'Failed to wrap socket! server_hostname="{host}"')
    with open("CERT.pem",'r') as f:
      dbg("cafile:",f.read(),sep='\n')
    dbg(ε)
    free()
    raise ε
    
  log(f"[SSL] << Mem: {mem_perc()}")
  free()
  return s

def http_connect(uri,impl="https"):
  uri = uriparse(uri,impl)
  s = socket.socket()
  s.connect(socket.getaddrinfo(uri.host,uri.port)[0][4])
  s.setblocking(True)
  s = ssl_cond(s,uri)
  return s,uri

# @micropython.native
def http_get(uri):
  s,uri = http_connect(uri)
  s.write(f"GET {uri.path} HTTP/1.1\r\nHost: {uri.host}:{uri.port}\r\n\r\n".encode())
  
  head = s.readline()
  try:
    if head.split(None,2)[1] != b'200':
      raise Exception(f"Response code is not 200!")
  except Exception as ε:
    dbg(f'[HTTP] Could not validate HTTP header: {head!r}',ε)
    free()
    raise ε
  del head
  
  cl = None
  while line := s.readline().decode().strip():
    k,v = line.split(':',1)
    k,v = k.rstrip().lower(), v.lstrip()
    if k == "content-length": cl = int(v)
    del k,v
  del line
  if cl is None: raise Exception("Could not find content-length header!")
  body = bytearray(cl)
  while cl>0: cl -= s.readinto(body)
  s.close()
  del uri,s,cl # this stuff seems excessive
  free()
  return body

# uriparse ssl_cond http_connect http_get wifi_connect AP_basic DNS_trap AP_with_DNS