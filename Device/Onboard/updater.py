from util     import *
from net      import http_get
from settings import ℭ,wifi_from_ℭ

def check_perform_update(force=None,fp="UPDATE_FLAG"):
  if isinstance(force,str): write_file("UPDATE_FLAG",force)
  if not path_exists(fp): return NONE(log("[Updater] Update flag not set."))
  old_v,status = ℭ.ver.strip(),0
  try:
    if old_v == (new_v := read_file(fp).strip()) and not force:
      return NONE(log("[Updater] Already up to date."))
    
    status = -1
    
    try                  : wifi_from_ℭ(ℭ)
    except Exception as ε: return FALSE(dbg("[Updater] Could not connect to WiFi.",ε))
    try                  : ntp()
    except Exception as ε: dbg("[Updater] NTP failed! SSL might have issues.",ε)
    
    need = 150*1024
    u,f = fs_info()
    log(f"[Updater] FS={fs_perc()} MEM={mem_perc()}")
    if f<need:
      log(f"[Updater] Removing scenes due to needing space ({f}<{need})")
      ℭ.DEF_SCENE = "_default"
      for s in ls("/Scenes"):
        if s[0] == '_': continue
        s = f"/Scenes/{s}"
        log(f'  Removing "{s}"')
        rm(s)
      u,f = fs_info()
      if f<need: return FALSE(log(f"[Updater] Unable to clear enough space! This is really bad! ({f}<{need})"))
    
    base = f"{ℭ.UPDATE_URL}/{new_v}"
    try:
      r = http_get(f"{base}/index.json")
      file_list = 𝔍l(r.decode())
    except Exception as ε:
      return FALSE(dbg("[Updater] failed to get index.",ε))
    log(f"[Updater] Got file list: {file_list}")
    
    try:
      for f in file_list:
        url = f"{base}/{f}"
        dest = f"{f}.new"
        log(f"[Updater] Pulling {url} to {dest}")
        try:
          content = http_get(url)
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
    for f in file_list: mv(f"{f}.new",f)
    status = 1
  except Exception as ε:
    return FALSE(dbg(f"[Updater] Unhandled error",ε))
  finally:
    rm(fp)
    if   status < 0:
      log(f"[Updater] Update failed. Sleeping for 30 seconds to avoid trolling server")
      sleep(30)
      reset()
    elif status > 0:
      ℭ.VER = new_v
      log(f"[Updater] Update successful ({old_v} → {new_v})")
      reset()

# check_perform_update