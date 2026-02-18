# https://github.com/danni/uwebsockets

import micropython

import socket,select,errno,sys,ssl,re
from binascii import b2a_base64
from consts   import *
from util     import *

_OP_CONT  = const(0x0)
_OP_TEXT  = const(0x1)
_OP_BYTES = const(0x2)
_OP_CLOSE = const(0x8)
_OP_PING  = const(0x9)
_OP_PONG  = const(0xa)
_CLOSE_OK                 = const(1000)
_CLOSE_GOING_AWAY         = const(1001)
_CLOSE_PROTOCOL_ERROR     = const(1002)
_CLOSE_DATA_NOT_SUPPORTED = const(1003)
_CLOSE_BAD_DATA           = const(1007)
_CLOSE_POLICY_VIOLATION   = const(1008)
_CLOSE_TOO_BIG            = const(1009)
_CLOSE_MISSING_EXTN       = const(1010)
_CLOSE_BAD_CONDITION      = const(1011)

URI = namedtuple('URI',('proto','host','port','path'))
def urlparse(uri,URL_RE=re.compile(r'(wss|ws)://([A-Za-z0-9-\._]+)(?:\:([0-9]+))?(/.+)?')):
  P = (M := URL_RE.match(uri)).group(1)
  return URI(P, M.group(2), int(M.group(3) or ((80,433)[P=='wss'])), M.group(4))

class NoDataException (Exception): pass
class ConnectionClosed(Exception): pass
class WebsocketClient:
  def __init__(𝕊,uri):
    𝕊.open = True
    uri = urlparse(uri)
    𝕊.sock = socket.socket()
    𝕊.sock.connect(socket.getaddrinfo(uri.host,uri.port)[0][4])
    𝕊.sock.setblocking(True)
    if uri.proto=='wss':
      # from time import localtime
      # from machine import RTC
      # log(f"the {localtime()=} {RTC().datetime()=} {μs()=}")
      # del localtime,RTC
      # micropython.mem_info(1)
      # cln=':'; log(f'[WS] >> SSL ({join(mem_info(),cln)}) {mem_perc()}'); del cln; free()
      free()
      ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
      ctx.check_hostname = True
      ctx.verify_mode    = ssl.CERT_REQUIRED
      ctx.load_verify_locations(cafile="CERT")
      𝕊.sock = ctx.wrap_socket(𝕊.sock, server_hostname=uri.host)
      free()
      # cln=':'; log(f'[WS] << SSL ({join(mem_info(),cln)}) {mem_perc()}'); del cln; free()
      # micropython.mem_info(1)
    
    𝕊.buf = bytearray()

    def send_header(h):
      dat = h.encode("utf-8")+b"\r\n"
      while dat: dat = dat[𝕊.sock.write(dat):]
    send_header(f"GET {uri.path or '/'} HTTP/1.1")
    send_header(f"Host: {uri.host}:{uri.port}")
    send_header(f"Connection: Upgrade")
    send_header(f"Upgrade: websocket")
    send_header(f"Sec-WebSocket-Key: {b2a_base64(bytes(getrandbits(8) for _ in range(16)))[:-1].decode("utf-8")}")
    send_header(f"Sec-WebSocket-Version: 13")
    send_header(f"")
    header = 𝕊.sock.readline()[:-2]
    if not header.startswith(b'HTTP/1.1 101 '): raise Exception(f'Invalid header: "{header}"')
    while header: header = 𝕊.sock.readline()[:-2] # We don't need these headers
    𝕊.sock.setblocking(False)
    𝕊.poller = select.poll()
    𝕊.poller.register(𝕊.sock,select.POLLIN)
  def read_frame(𝕊,max_size=None):
    buf = 𝕊.buf
    try:
      while True:
        c = 𝕊.sock.read(512)
        if c is None: break
        if c == b"" : raise OSError("TCP Connection closed.")
        buf.extend(c)
        free()
      # log(f"WS Message: {c.hex()}")
    except OSError as ε:
      if ε.args[0] != errno.EAGAIN:
        raise 𝕊._close(f"Socket error: {ε}")
    
    p = 0
    def read_n(n,l=len(buf)):
      nonlocal p
      if p+n>l: raise NoDataException()
      r = buf[p:p+n]
      p += n
      return r
    b1,b2 = unpack("!BB",read_n(2))
    opcode,length = b1&0x0f, b2&0x7f
    if   length==126: length, = unpack("!H",read_n(2))
    elif length==127: length, = unpack("!Q",read_n(8))
    fin,mask = bool(b1 & 0x80), bool(b2 & (1<<7))
    if mask: mask_bits = read_n(4)
    data = read_n(length)
    if mask: data = bytes(b^mask_bits[i%4] for i,b in enumerate(data))
    buf[:p] = b""
    return fin,opcode,data
  def write_frame(𝕊,opcode,data=b''):
    l,b1 = len(data), 0x80|opcode
    if   l <  126 : 𝕊.sock.write(pack('!BB' , b1, 0x80|l     ))
    elif l < 1<<16: 𝕊.sock.write(pack('!BBH', b1, 0x80|126, l))
    elif l < 1<<64: 𝕊.sock.write(pack('!BBQ', b1, 0x80|127, l))
    else          : raise ValueError()
    mask_bits = pack('!I', getrandbits(32))
    𝕊.sock.write(mask_bits)
    data = bytes(b^mask_bits[i%4] for i,b in enumerate(data))
    𝕊.sock.write(data)
  def recv(𝕊):
    if not 𝕊.open: raise ConnectionClosed("Already closed")
    while 𝕊.open:
      try:
        fin,opcode,data = 𝕊.read_frame()
      except ValueError:
        raise 𝕊._close("WS Connection closed unexpectedly")
      if not fin: raise NotImplementedError()
      if   opcode==_OP_TEXT : return data # .decode('utf-8')
      elif opcode==_OP_BYTES: return data
      elif opcode==_OP_CLOSE: raise 𝕊._close("WS Connection closed.")
      elif opcode==_OP_PING :
        𝕊.write_frame(_OP_PONG,data)
        continue
      elif opcode==_OP_PONG: continue
      elif opcode==_OP_CONT: raise NotImplementedError(opcode)
      else                :
        log(f'UNKNOWN WS RECV! {opcode=} {data=}')
        raise ValueError(opcode)
  
  def recv_instant(𝕊):
    if not 𝕊.open: raise ConnectionClosed("Already closed")
    if not 𝕊.poller.poll(0): raise NoDataException()
    return 𝕊.recv()
  def recv_timeout(𝕊,t=5):
    if not 𝕊.open: raise ConnectionClosed("Already closed")
    if t is None: 
      try:
        return 𝕊.recv()
      except NoDataException:
        return None
        
    s,t = ms(),1000*t
    while 1:
      try:
        return 𝕊.recv()
      except NoDataException:
        if dt_ms(s)>=t: return None
        frees()
  
  def close(𝕊,code=_CLOSE_OK,reason=''):
    if not 𝕊.open: return
    𝕊.write_frame(_OP_CLOSE, pack('!H',code)+reason.encode('utf-8'))
    𝕊._close()
  def _close(𝕊,E=None):
    𝕊.open = False
    𝕊.sock.close()
    if E is not None: raise ConnectionClosed(E)

class WS_Client:
  def __init__(𝕊,uri,t=None):
    𝕊.ws,𝕊.recv_timeout = WebsocketClient(uri),t
  def read(𝕊):
    r = 𝕊.ws.recv_timeout(𝕊.recv_timeout)
    if r is not None: return r[:6],r[6:]
  def write(𝕊,i,b):
    if isinstance(i,int): i = int.to_bytes(i,6,"big")
    𝕊.ws.write_frame(_OP_BYTES,i+b)
  def close(𝕊):
    return 𝕊.ws.close()
  def __call__(𝕊,𝑿=None,i=0,**𝕂):
    if not 𝕊.ws.open:
      raise ConnectionClosed()
    if 𝑿 is None and not 𝕂:
      return 𝕊.read()
    if type(𝑿) in (str,bytes,float,int,bool):
      if 𝕂:
        raise ValueError(f"Cannot create dict from {type(𝑿)} and kwargs")
      if type(𝑿) not in (str,bytes):
        𝑿 = 𝔍d(𝑿)
    else:
      𝑿 = 𝔍d(({} if 𝑿 is None else 𝑿)|𝕂)
    𝕊.write(i,𝑿.encode("utf-8") if isinstance(𝑿,str) else X)

__all__ = "WS_Client",