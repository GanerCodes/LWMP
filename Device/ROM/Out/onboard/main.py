import machine,esp,sys,gc
# machine.mem32[0x3FF48044] = 0 # brownout detector
machine.freq(240_000_000)
esp.osdebug(None)
gc.disable()

from updater import *
check_perform_update()
del check_perform_update
del sys.modules["updater"]
gc.collect()

import lw