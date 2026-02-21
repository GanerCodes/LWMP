from uctypes import addressof as Ѧ
leds_ptr = Ѧ(leds     := b'\0'*3*2048   )
lstk_ptr = Ѧ(lstk     := b'\0'*4*3*512  )
𝕒_ptr    = Ѧ(𝕒_static := bytearray(4*11))
ref_hold,scene_check,last_ntp = [],[None],[None,None]
NTP_HOSTS = ("time.cloudflare.com","time.google.com","time.apple.com","time.aws.com")
del Ѧ