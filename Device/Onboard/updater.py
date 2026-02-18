from consts   import *
from util     import *
from settings import *
from wifi     import *
from requests import get

def check_perform_update(force=None,fp="UPDATE_FLAG"):
  if isinstance(force,str): write_file("UPDATE_FLAG",force)
  if not path_exists(fp): return NONE(log("[Updater] Update flag not set."))
  old_v,status = ℭ.ver.strip(),0
  try:
    if old_v == (new_v := read_file(fp).strip()):
      return NONE(log("[Updater] Already up to date."))
    
    status = -1
    
    try                  : wifi_from_ℭ(ℭ)
    except Exception as ε: return FALSE(dbg("[Updater] Could not connect to WiFi.",ε))
    
    need = 150*1024
    u,f = fs_info()
    log(f"[Updater] Used FS: {fs_perc()}")
    if f<need:
      log(f"[Updater] Removing scenes due to needing space ({f}<{need})")
      ℭ.DEF_SCENE = "_default"
      for s in ls("/Scenes"):
        if s[8] == '_': continue
        log(f'  Removing "{s}"')
        rm(s)
      u,f = fs_info()
      if f<need: return FALSE(log(f"[Updater] Unable to clear enough space! This is really bad! ({f}<{need})"))
    
    base = f"{ℭ.UPDATE_URL}/{new_v}"
    try:
      r = get(f"{base}/index.json")
      file_list = 𝔍l(r.content.decode("utf-8"))
    except Exception as ε:
      return FALSE(dbg("[Updater] failed to get index.",ε))
    log(f"[Updater] Got file list: {file_list}")
    
    try:
      for f in file_list:
        url = f"{base}/{f}"
        dest = f"{f}.new"
        log(f"[Updater] Pulling {url} to {dest}")
        try:
          content = get(url).content
          with open(dest,'wb') as F: F.write(content)
          del content; free()
        except Exception as ε:
          log(f"[Updater] Failed updating file {url}→{dest}")
          raise ε
    except Exception as ε:
      dbg(f"[Updater] Failed with partial update!",ε)
      for f in file_list:
        try             : rm(f"{f}.new")
        except Exception: pass
      return FALSE(log(f"[Updater] Cleaned partially downloaded update."))
    for f in file_list: rename(f"{f}.new",f)
    status = 1
  except Exception as ε:
    return FALSE(dbg(f"[Updater] Unhandled error",ε))
  finally:
    rm(fp)
    if   status < 0:
      log(f"[Updater] Update failed. Sleeping for 30 seconds to avoid trolling server")
      reset()
    elif status > 0:
      ℭ.VER = new_v
      log(f"[Updater] Update successful ({old_v} → {new_v})")
      reset()

__all__ = "check_perform_update",