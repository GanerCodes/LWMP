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
class Websocket:
  is_client = False
  def __init__(𝕊,sock):
    𝕊.sock,𝕊.open = sock,True
  def __call__(𝕊,buf=None,**𝕂):
    if buf is None and not 𝕂:
      return 𝕊.recv()
    assert 𝕊.open
    if isinstance(buf,str):
      opcode = OP_TEXT
      buf = buf.encode('utf-8')
      assert not 𝕂
    else:
      opcode = OP_BYTES
      if buf is None: buf = {}
      if isinstance(buf,dict):
        buf = 𝔍d(buf|𝕂 if 𝕂 else buf).encode("utf-8")
      else:
        assert not 𝕂
    𝕊.write_frame(opcode,buf)
  def __enter__(𝕊):
    return 𝕊
  def __exit__(𝕊,exc_type,exc,tb):
    𝕊.close()
  def settimeout(𝕊,timeout):
    𝕊.sock.settimeout(timeout)
  def read_frame(𝕊,max_size=None):
    two_bytes = 𝕊.sock.read(2)
    if not two_bytes: raise NoDataException
    b1,b2 = struct.unpack('!BB', two_bytes)
    opcode,length = b1 & 0x0f, b2 & 0x7f
    if   length==126: length, = struct.unpack('!H', 𝕊.sock.read(2))
    elif length==127: length, = struct.unpack('!Q', 𝕊.sock.read(8))
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
    fin,l,mask = True,len(data),𝕊.is_client
    b1 = (0x80 if fin  else 0)|opcode
    b2 =  0x80 if mask else 0
    if   l <  126 : 𝕊.sock.write(struct.pack('!BB' , b1, b2|l     ))
    elif l < 1<<16: 𝕊.sock.write(struct.pack('!BBH', b1, b2|126, l))
    elif l < 1<<64: 𝕊.sock.write(struct.pack('!BBQ', b1, b2|127, l))
    else          : raise ValueError()
    if mask:
      mask_bits = struct.pack('!I', random.getrandbits(32))
      𝕊.sock.write(mask_bits)
      data = bytes(b^mask_bits[i%4] for i,b in enumerate(data))
    𝕊.sock.write(data)
  def recv(𝕊):
    assert 𝕊.open
    while 𝕊.open:
      try:
        fin,opcode,data = 𝕊.read_frame()
      except NoDataException:
        return ''
      except ValueError:
        𝕊._close()
        raise ConnectionClosed()
      if not fin:
        raise NotImplementedError()
      if   opcode==OP_TEXT : return data.decode('utf-8')
      elif opcode==OP_BYTES: return data
      elif opcode==OP_CLOSE: return 𝕊._close()
      elif opcode==OP_PING :
        𝕊.write_frame(OP_PONG,data)
        continue
      elif opcode== OP_PONG: continue
      elif opcode== OP_CONT: raise NotImplementedError(opcode)
      raise ValueError(opcode)
  def close(𝕊,code=CLOSE_OK,reason=''):
    if not 𝕊.open: return
    𝕊.write_frame(OP_CLOSE, struct.pack('!H',code)+reason.encode('utf-8'))
    𝕊._close()
  def _close(𝕊):
    𝕊.open = False
    𝕊.sock.close()
class WebsocketClient(Websocket):
  is_client = True

def connect(uri):
  uri = urlparse(uri)
  𝚂 = socket.socket()
  𝚂.settimeout(5)
  𝚂.connect(socket.getaddrinfo(uri.host,uri.port)[0][4])
  if uri.proto=='wss': 
    # mfw this doesn't even work when GC: total: 112000, used: 39520, free: 72480, max new split: 30720 ; No. of 1-blocks: 402, 2-blocks: 120, max blk sz: 157, max free sz: 3343 # "gc.collect()"; micropython.mem_info()
    # 𝚂 = ssl.wrap_socket(𝚂,server_hostname=uri.host,server_side=False,cert_reqs=0)
    pass

  send_header = lambda h: 𝚂.write(h.encode("utf-8")+b"\r\n")
  send_header(f"GET {uri.path or '/'} HTTP/1.1")
  send_header(f"Host: {uri.host}:{uri.port}")
  send_header(f"Connection: Upgrade")
  send_header(f"Upgrade: websocket")
  send_header(f"Sec-WebSocket-Key: {binascii.b2a_base64(bytes(random.getrandbits(8) for _ in range(16)))[:-1].decode("utf-8")}")
  send_header(f"Sec-WebSocket-Version: 13")
  # send_header(f"Origin: http://{uri.host}:{uri.port}")
  send_header(f"Origin: http{'s'*(uri.proto=='wss')}://{uri.host}:{uri.port}")
  send_header(f"")

  header = 𝚂.readline()[:-2]
  assert header.startswith(b'HTTP/1.1 101 '), header
  
  # We don't (currently) need these headers
  # FIXME: should we check the return key?
  while header: header = 𝚂.readline()[:-2]
  
  return WebsocketClient(𝚂)