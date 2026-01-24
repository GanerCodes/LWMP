from util import *

class Scene_Manager:
  def __init__(𝕊,dir="/scenes"):
    𝕊.dir = 𝐩(dir)
  def __call__(𝕊,name=None):
    if name is not None:
      if (loc:=𝕊.dir/name).is_file():
        return loc
    else:
      return [x.name for x in ls(𝕊.dir)]
  def __contains__(𝕊,x):
    return 𝕊(x) is not None
  def __setitem__(𝕊,name,mode,log=log):
    if not isinstance(mode,str):
      E = (loc:=𝕊.dir/name).is_file()
      𝔍wf(loc,mode)
      log(f'{"Updated" if E else "Wrote"} scene "{name}" at "{loc}"')
  def __delitem__(𝕊,name,log=log):
    if loc := 𝕊():
      rm(loc)
      TRUE(log(f'Removed scene "{name}"'))
    return FALSE(log(f'Scene "{name}" already does not exist'))
  def __getitem__(𝕊,name,log=print):
    if (loc := 𝕊(name)) is None:
      raise FileNotFoundError(f'Could not find scene "{name}"!')
    try:
      return 𝔍lf(loc)
    except Exception as ε:
      dbg(f'Failed to load scene from "{loc}"!')
      raise ε
  def bulk_dump(𝕊,destroy_cripples=True):
    r = {}
    for f in 𝕊():
      try:
        r[f] = 𝕊[f]
      except Exception as ε:
        if destroy_cripples:
          loc = 𝕊(f)
          log(f'Removing broken scene from "{loc}"')
          rm(loc)
        dbg(f'Broken scene found at "{loc}":',ε)
    return r
  def bulk_save(𝕊,X):
    N = 0
    for k,v in X.items():
      try:
        𝕊[k] = v
        N += 1
      except Exception as ε:
        dbg(f'Failed to save scene "{k}":',ε)
    return N

__all__ = "Scene_Manager",