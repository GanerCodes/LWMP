# Based on https://github.com/danni/uwebsockets

import select
from util import *
from net  import http_connect

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

class NoDataException (Exception): pass
class ConnectionClosed(Exception): pass
class WebsocketClient:
  def __init__(𝕊,uri):
    s,uri = http_connect(uri,"wss")
    𝕊.sock,𝕊.open = s,True
    𝕊.raw_buf = bytearray()
    𝕊.frag_buf,𝕊.expect_cont = bytearray(),False
    
    send = lambda h: s.write(h.encode()+b"\r\n")
    send(f"GET {uri.path} HTTP/1.1")
    send(f"Host: {uri.host}:{uri.port}")
    send("Connection: Upgrade")
    send("Upgrade: websocket")
    send("Sec-WebSocket-Key: TFdNUFdlYnNvY2tldEtleQ==") # outside spec but I control full stack >:)
    send("Sec-WebSocket-Version: 13")
    send("")
    del send
    header = s.readline()[:-2]
    if not header.startswith(b'HTTP/1.1 101 '): raise Exception(f'Invalid header: "{header}"')
    while header: header = s.readline()[:-2]
    s.setblocking(False)
    𝕊.poller = select.poll()
    𝕊.poller.register(s,select.POLLIN)
  def write_frame(𝕊,opcode,data=b''):
    l,b1 = len(data), 0x80|opcode
    if   l <  126 : 𝕊.sock.write(pack('!BB' , b1, l  |0x80  ))
    elif l < 1<<16: 𝕊.sock.write(pack('!BBH', b1, 126|0x80, l))
    else          : 𝕊.sock.write(pack('!BBQ', b1, 127|0x80, l))
    𝕊.sock.write(mask_bits := b"\01\23\45\67")
    data = bytes(b^mask_bits[i%4] for i,b in enumerate(data))
    𝕊.sock.write(data)
  def read_frame(𝕊):
    p = 0
    def read(n):
      nonlocal p
      while p+n>len(𝕊.raw_buf):
        try:
          c = 𝕊.sock.read(512)
          if c ==  b'': raise OSError("TCP closed.")
          if c is None: raise NoDataException()
          𝕊.raw_buf.extend(c)
        except OSError as ε:
          if ε.args[0] != 11: raise 𝕊._close(f"Socket error: {ε}")
      r = memoryview(𝕊.raw_buf)[p:p+n]
      p += n
      return r
    b1,b2 = unpack("!BB",read(2))
    fin,mask = bool(b1 & 0x80),bool(b2 & (1<<7))
    op,l = b1&0x0F, b2&0x7F
    if   l==126: l, = unpack("!H",read(2))
    elif l==127: l, = unpack("!Q",read(8))
    # log(f"[WS] Recv frame length: {l}")
    if mask: mask_bits = read(4)
    dat = read(l)
    dat = bytearray(dat)
    𝕊.raw_buf[:p] = b''
    if mask:
      for i,b in enumerate(dat):
        dat[i] = b^mask_bits[i%4]
    return fin,op,dat
  def recv(𝕊):
    if not 𝕊.open: raise ConnectionClosed("Already closed")
    while 𝕊.open:
      fin,op,dat = 𝕊.read_frame()
      if 𝕊.expect_cont:
        if op != _OP_CONT:
          log("[WS] Unfinished message:",𝕊.frag_buf)
          log("[WS] Irrelevent data:",dat)
          𝕊.frag_buf[:],𝕊.expect_cont = b'',False
          raise ValueError(f'Expected CONT frame, got "{op}"')
        𝕊.frag_buf.extend(dat)
        if fin:
          r = 𝕊.frag_buf
          𝕊.frag_buf,𝕊.expect_cont = bytearray(),False
          log(f"[WS] Multifragment total recieve length: {len(r)}")
          return r
      elif op in (_OP_TEXT,_OP_BYTES):
        if fin: return dat
        𝕊.expect_cont = True
        𝕊.frag_buf.extend(dat)
      elif op==_OP_PONG : pass
      elif op==_OP_PING : 𝕊.write_frame(_OP_PONG,dat)
      elif op==_OP_CLOSE: raise 𝕊._close("WS Connection closed.")
      elif op==_OP_CONT : raise ValueError("Unexpected CONT frame")
      else              : raise ValueError(f'[WS] Unknown op "{op}" ({dat=} {fin=})')
  def recv_instant(𝕊):
    if not 𝕊.open          : raise ConnectionClosed("Already closed")
    if not 𝕊.poller.poll(0): raise NoDataException()
    return 𝕊.recv()
  def recv_timeout(𝕊,t=5):
    if not 𝕊.open: raise ConnectionClosed("Already closed")
    if t is None:
      try                   : return 𝕊.recv()
      except NoDataException: return None
        
    s,t = ms(),1000*t
    while 1:
      try                   : return 𝕊.recv()
      except NoDataException: pass
      if dt_ms(s)>=t: return None
      frees()
  
  def close(𝕊,code=_CLOSE_OK,reason=''):
    if not 𝕊.open: return
    𝕊.write_frame(_OP_CLOSE, pack('!H',code)+reason.encode())
    𝕊._close()
  def _close(𝕊,E=None):
    𝕊.open = False
    𝕊.sock.close()
    if E is not None: raise ConnectionClosed(E)

class WS_Client:
  def __init__(𝕊,uri,t=None):
    𝕊.ws = WebsocketClient(uri)
    𝕊.recv_timeout = t
  def read(𝕊):
    r = 𝕊.ws.recv_timeout(𝕊.recv_timeout)
    if r is not None: return bytes(r[:6]),memoryview(r)[6:]
  def write(𝕊,i,b):
    if isinstance(i,int): i = int.to_bytes(i,6,"big")
    𝕊.ws.write_frame(_OP_BYTES,i+b)
  def close(𝕊,*𝔸,**𝕂):
    return 𝕊.ws.close(*𝔸,**𝕂)
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
      𝑿 = {} if 𝑿 is None else 𝑿
      𝑿 = 𝔍d(𝑿|𝕂 if 𝕂 else 𝑿)
    𝕊.write(i,𝑿.encode("utf-8") if isinstance(𝑿,str) else 𝑿)

#  WS_Client