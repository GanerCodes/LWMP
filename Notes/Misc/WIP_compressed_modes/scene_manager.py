from fs import *
from bin_tools import Encoder,Decoder
from bin_scenes import scene2bin,bin2scene

SCENE_DIR = "/Scenes"
class Scene_Manager:
  def __call__(𝕊,x,force=False):
    x = f"{SCENE_DIR}/{f_esc_a(x)}"
    if force: return x
    return path_exists(x) and x
  __init__     = lambda 𝕊  : None
  __contains__ = lambda 𝕊,x: bool(𝕊(x))
  __iter__     = lambda 𝕊  : iter(f_esc_z(x) for x in ls(SCENE_DIR))
  def __delitem__(𝕊,s):
    (p:=𝕊(s)) and rm(p)
    return bool(p)
  def __setitem__(𝕊,k,v):
    fp = 𝕊(k,True)
    with open(fp,"wb") as f:
      if   isinstance(v,dict)             : f.write(𝔍d(v))
      elif isinstance(v,(bytes,bytearray)): f.write(   v )
      else                                : 𝔄()
  def __getitem__(𝕊,k):
    pass # 󰤱 (also how distinquish 􇦌 and bin?)
  def bulk_dump(𝕊):
    pass # 󰤱
  def bulk_save(𝕊,d):
    pass # 󰤱

𝔐 = Scene_Manager()