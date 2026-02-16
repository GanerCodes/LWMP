from util     import *
from settings import *
from wifi     import *
from requests import get

def check_perform_update():
  if not (fp := 𝐩("UPDATE_FLAG")).is_file():
    log("[Updater] Update flag not set.")
    return
  old_v,status = ℭ.ver,0
  try:
    if (new_v := read_file(fp).strip()) == ℭ.ver:
      log("[Updater] Already up to date.")
      return
    
    try:
      wifi_from_ℭ(ℭ)
    except Exception as ε:
      rm(fp)
      dbg("[Updater] Could not connect to WiFi.",ε)
      return False
    
    base = f"{ℭ.UPDATE_URL}/{new_v}"
    try:
      r = get(f"{base}/index.json")
      file_list = 𝔍l(r.content.decode("utf-8"))
    except Exception as ε:
      dbg("[Updater] failed to get index.",ε)
      return False
    log(f"[Updater] Got file list: {file_list}")
    status = 1
    for f in file_list:
      url = f"{base}/{f}"
      f = 𝐩(f)
      log(f"[Updater] Pulling {url} to {f}")
      try:
        content = get(url).content
        if f.is_file(): rm(f)
        with open(str(f),'wb') as F: F.write(content)
        free()
      except Exception as ε:
        dbg(f"[Updater] Failed with partial update! Failed updating file {f} from {url}",ε)
        return False
    status = 2
  except Exception as ε:
    dbg(f"[Updater] Unhandled error",ε)
    return False
  finally:
    if status in (0,2):
      rm(fp)
    if status < 2:
      log(f"[Updater] Update failed. Sleeping for 30 seconds to avoid trolling server")
      sleep(30)
    else:
      ℭ.VER = new_v
      log(f"[Updater] Update successful ({old_v} → {new_v})")
      reset()

__all__ = "check_perform_update",