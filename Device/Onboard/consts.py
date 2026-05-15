LED_BUF_SIZE = 3*2048
STK_BUF_SIZE = 4*3*512

ref_hold,scene_check,last_ntp = [],[None],[None,None]
NTP_HOSTS = ("time.cloudflare.com","time.google.com","time.apple.com","time.aws.com")