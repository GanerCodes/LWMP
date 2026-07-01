import os

ls,rm,mv = os.listdir,os.remove,os.rename
def path_exists(p,_=os.stat):
  try:
    _(p)
    return True
  except OSError:
    return False

def f_esc_a(C):
  assert C
  r = ""
  for c in C:
    if   c=='.' : r += '\\d'
    elif c==':' : r += '\\c'
    elif c=='/' : r += '\\s'
    elif c=='\\': r += '\\\\'
    elif c=='\0': r += '\\z'
    else        : r += c
  return r
def f_esc_z(C):
  assert C
  r,𝔰 = "",0
  for c in C:
    if 𝔰:
      if   c=='d' : r += '.'
      elif c=='c' : r += ':'
      elif c=='s' : r += '/'
      elif c=='\\': r += '\\'
      elif c=='z' : r += '\0'
      else        : assert 0
      𝔰 = 0
    else:
      if c=='\\': 𝔰 = 1
      else      : r += c
  assert not 𝔰
  return r

# a = "joe.\\wee hi\0::smoke//\0;\\"
# print(f"{a!r}")
# a = f_esc_a(a)
# print(f"{a!r}")
# a = f_esc_z(a)
# print(f"{a!r}")