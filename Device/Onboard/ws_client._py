# https://github.com/danni/uwebsockets

from util import *

OP_CONT  = const(0x0)
OP_TEXT  = const(0x1)
OP_BYTES = const(0x2)
OP_CLOSE = const(0x8)
OP_PING  = const(0x9)
OP_PONG  = const(0xa)
CLOSE_OK                 = const(1000)
CLOSE_GOING_AWAY         = const(1001)
CLOSE_PROTOCOL_ERROR     = const(1002)
CLOSE_DATA_NOT_SUPPORTED = const(1003)
CLOSE_BAD_DATA           = const(1007)
CLOSE_POLICY_VIOLATION   = const(1008)
CLOSE_TOO_BIG            = const(1009)
CLOSE_MISSING_EXTN       = const(1010)
CLOSE_BAD_CONDITION      = const(1011)

URI = namedtuple('URI',('proto','host','port','path'))
URL_RE = re.compile(r'(wss|ws)://([A-Za-z0-9-\._]+)(?:\:([0-9]+))?(/.+)?')

def urlparse(uri):
  M = URL_RE.match(uri)
  P = M.group(1)
  return URI(P, M.group(2),
             int(M.group(3) or ((80,433)[P=='wss'])),
             M.group(4))

class NoDataException (Exception): pass
class ConnectionClosed(Exception): pass
class WebsocketClient:
  def __init__(𝕊,uri):
    𝕊.open = True
    uri = urlparse(uri)
    𝕊.sock = socket.socket()
    𝕊.sock.settimeout(30)
    𝕊.sock.connect(socket.getaddrinfo(uri.host,uri.port)[0][4])
    if uri.proto=='wss': 
      # mfw this doesn't even work when GC: total: 112000, used: 39520, free: 72480, max new split: 30720 ; No. of 1-blocks: 402, 2-blocks: 120, max blk sz: 157, max free sz: 3343 # "free()"; micropython.mem_info()
      # 𝕊.sock = ssl.wrap_socket(𝕊.sock,server_hostname=uri.host,server_side=False,cert_reqs=0)
      pass

    send_header = lambda h: 𝕊.sock.write(h.encode("utf-8")+b"\r\n")
    send_header(f"GET {uri.path or '/'} HTTP/1.1")
    send_header(f"Host: {uri.host}:{uri.port}")
    send_header(f"Connection: Upgrade")
    send_header(f"Upgrade: websocket")
    send_header(f"Sec-WebSocket-Key: {b2a_base64(bytes(getrandbits(8) for _ in range(16)))[:-1].decode("utf-8")}")
    send_header(f"Sec-WebSocket-Version: 13")
    send_header(f"")
    header = 𝕊.sock.readline()[:-2]
    if not header.startswith(b'HTTP/1.1 101 '):
      raise Exception(f'Got invalid header: "{header}"')
    while header: header = 𝕊.sock.readline()[:-2] # We don't need these headers
  def settimeout(𝕊,to):
    𝕊.sock.settimeout(to)
  def read_frame(𝕊,max_size=None):
    two_bytes = 𝕊.sock.read(2)
    if not two_bytes: raise NoDataException()
    b1,b2 = unpack('!BB', two_bytes)
    opcode,length = b1 & 0x0f, b2 & 0x7f
    if   length==126: length, = unpack('!H', 𝕊.sock.read(2))
    elif length==127: length, = unpack('!Q', 𝕊.sock.read(8))
    fin,mask = bool(b1 & 0x80), bool(b2 & (1<<7))
    if mask: mask_bits = 𝕊.sock.read(4)
    try:
      data = 𝕊.sock.read(length)
    except MemoryError:
      𝕊.close(code=CLOSE_TOO_BIG)
      return True,OP_CLOSE,None
    if mask: data = bytes(b^mask_bits[i%4] for i,b in enumerate(data))
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
      except NoDataException:
        return b''
      except ValueError:
        raise 𝕊._close("WS Connection closed unexpectedly")
      if not fin: raise NotImplementedError()
      if   opcode==OP_TEXT : return data # .decode('utf-8')
      elif opcode==OP_BYTES: return data
      elif opcode==OP_CLOSE: raise 𝕊._close("WS Connection closed.")
      elif opcode==OP_PING :
        𝕊.write_frame(OP_PONG,data)
        continue
      elif opcode==OP_PONG: continue
      elif opcode==OP_CONT: raise NotImplementedError(opcode)
      else                :
        log(f'UNKNOWN WS RECV! {opcode=} {data=}')
        raise ValueError(opcode)
  def close(𝕊,code=CLOSE_OK,reason=''):
    if not 𝕊.open: return
    𝕊.write_frame(OP_CLOSE, pack('!H',code)+reason.encode('utf-8'))
    𝕊._close()
  def _close(𝕊,E=None):
    𝕊.open = False
    𝕊.sock.close()
    if E is not None:
      raise ConnectionClosed(E)

class WS_Client:
  def __init__(𝕊,uri): 𝕊.ws = WebsocketClient(uri)
  close = lambda 𝕊: 𝕊.ws.close()
  
  def read(𝕊):
    r = 𝕊.ws.recv()
    return r[:6],r[6:]
  def write(𝕊,i,b):
    if isinstance(i,int):
      i = int.to_bytes(i,6,"big")
    𝕊.ws.write_frame(OP_BYTES,i+b)
  
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