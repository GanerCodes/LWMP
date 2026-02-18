import micropython,machine,esp,sys,gc
gc.disable()

# machine.mem32[0x3FF48044] = 0 # brownout detector
machine.freq(240_000_000)
machine.RTC().init((2026,1,1,0,0,0,0,0))
esp.osdebug(None)

import lightwave,consts,util,wifi,ws_client,settings,scene_manager,interface

import updater
updater.check_perform_update()
del updater,sys.modules["updater"],sys.modules["requests"]
gc.collect()
# micropython.mem_info(1)

for x in list(globals().keys()):
  del globals()[x]
del x

import lw