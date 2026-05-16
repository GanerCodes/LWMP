from machine  import reset
from time     import sleep
from util     import *
from net      import http_get
from settings import ℭ,wifi_from_ℭ

def check_perform_update(force=None,fp="UPDATE_FLAG"):
  if isinstance(force,str): write_file("UPDATE_FLAG",force)
  if not path_exists(fp):
    log("Updater","Update flag not set.")
    return
  old_v,status = ℭ.ver.strip(),0
  try:
    if old_v == (new_v := read_file(fp).strip()) and not force:
      log("Updater","Already up to date.")
      return
    
    status = -1
    
    try:
      wifi_from_ℭ(ℭ)
    except Exception as ε:
      dbg("Updater","Could not connect to WiFi.",ε)
      return False
    try:
      ntp()
    except Exception as ε:
      dbg("Updater","NTP failed! SSL might have issues.",ε)
      return False
    
    need = 150*1024
    u,f = fs_info()
    log("Updater",f"FS={fs_perc()} MEM={mem_perc()}")
    if f<need:
      log("Updater",f"Removing scenes due to needing space ({f}<{need})")
      ℭ.DEF_SCENE = "_default_"
      for s in ls("/Scenes"):
        if s[0] == '_': continue
        s = f"/Scenes/{s}"
        log("Updater",f'  Removing "{s}"')
        rm(s)
      u,f = fs_info()
      if f<need:
        log("Updater",f"Unable to clear enough space! This is really bad! ({f}<{need})")
        return False
    
    base = f"{ℭ.UPDATE_URL}/{new_v}"
    try:
      r = http_get(f"{base}/index.json")
      file_list = 𝔍l(r.decode())
    except Exception as ε:
      dbg("Updater","failed to get index.",ε)
      return False
    log("Updater","Got file list:",file_list)
    
    try:
      for f in file_list:
        url = f"{base}/{f}"
        dest = f"{f}.new"
        log("Updater",f"Pulling {url} to {dest}")
        try:
          content = http_get(url)
          with open(dest,'wb') as F: F.write(content)
          del content; free()
        except Exception as ε:
          log("Updater",f"Failed updating file {url}→{dest}")
          raise ε
    except Exception as ε:
      dbg("Updater","Failed with partial update!",ε)
      for f in file_list:
        try             : rm(f"{f}.new")
        except Exception: pass
      log("Updater","Cleaned partially downloaded update.")
      return False
    for f in file_list: mv(f"{f}.new",f)
    status = 1
  except Exception as ε:
    dbg("Updater","Unhandled error",ε)
    return False
  finally:
    rm(fp)
    if   status < 0:
      log("Updater","Update failed. Sleeping for 30 seconds to avoid trolling server")
      sleep(30)
      reset()
    elif status > 0:
      ℭ.VER = new_v
      log("Updater",f"Update successful ({old_v} → {new_v})")
      reset()

# check_perform_update