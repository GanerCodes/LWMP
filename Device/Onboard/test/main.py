# TIMED_MODES: DURATION (int) MODE (bytearray) LED_COUNT (int) SHADERS (list)

import interface
exit()

import machine,random,network,_thread,time,json,sys,gc
import usocket as socket
from ulab import numpy as np

import ws_client
from storage_utils import *
from lightwave import *

_WEBSOCKET_SERVER  = const("wss://brynic_led_test.ganer.xyz:2096")
_DEFAULT_LED_COUNT = const(500)
_DEFAULT_LED_PIN   = const(23)
_BITSTREAM_TIMING  = const((400,850,800,450)) # const((800,1700,1600,900))
_FPS_DISPLAY_DELTA = const(20_000)
_TIMER_MODULO      = const(1<<24)

START_TIME_MS = time.time_ns() // 1_000_000
def uptime_ms():
    return time.time_ns() // 1_000_000 - START_TIME_MS

def parse_RGB_mode(mode):
    mode = mode.upper()
    return int(mode.index('R')), int(mode.index('G')), int(mode.index('B'))

def update_elements():
    global static_rgb,color_fade,divide_brightness,rotate_LEDs
    write_file("elements.py", read_file("elements.py.template", False) \
                               .replace("OFFSET_R", "0x{}".format(OFFSET_R)) \
                               .replace("OFFSET_G", "0x{}".format(OFFSET_G)) \
                               .replace("OFFSET_B", "0x{}".format(OFFSET_B)))
    sys.modules.pop("elements",None)
    from elements import static_rgb,color_fade,divide_brightness,rotate_LEDs

LED_PIN   = load_check_datafile("LED_PIN", _DEFAULT_LED_PIN, int)
LED_COUNT = load_check_datafile("LED_COUNT", _DEFAULT_LED_COUNT, int)
REVERSE   = load_check_datafile("REVERSE", False, boolstr)
RGB_ORDER = load_check_datafile("RGB_ORDER", "RGB")
OFFSET_R, OFFSET_G, OFFSET_B = parse_RGB_mode(RGB_ORDER)
PREVIOUS_LED_COUNT = LED_COUNT
update_elements()

if 'UUID' not in os.listdir():
    UUID = hex(int(''.join(str(random.random())[2:] for i in range(3))))[2:10]
    write_file("UUID", UUID)
    print("Created UUID " + UUID)
else:
    UUID = read_file("UUID")
    print("Loaded UUID: " + UUID)

PINOUT = machine.Pin(LED_PIN)
PINOUT.init(PINOUT.OUT)
ONBOARD_LED_PINPOUT = machine.Pin(2)
ONBOARD_LED_PINPOUT.init(ONBOARD_LED_PINPOUT.OUT)

LOOP = True
MODES,SHADERS = [],[]
RECTIME,TIMEDELTA = 0,0

print("""\
WEBSOCKET_SERVER: {}
LED_PIN: {}, LED_COUNT: {}
RGB_ORDER: {}, REVERSE: {}\
""".format(_WEBSOCKET_SERVER,LED_PIN,LED_COUNT,RGB_ORDER,REVERSE))

def onboard_led(state):
    ONBOARD_LED_PINPOUT.value(int(bool(state)))

def parse_mode_data(data, LED_COUNT):
    if 'LED_COUNT' in data:
        LED_COUNT = int(data['LED_COUNT'])
        write_file("LED_COUNT", LED_COUNT)
    for i,v in enumerate(data['modes']):
        bar = None
        if v['type'] == 'color':
            bar = bytearray([0x00, int(v['color'][0]), int(v['color'][1]), int(v['color'][2])])
        elif v['type'] == 'fade':
            tmp = []
            for x in v['colors']:
                for y in x:
                    tmp.append(int(y))
            sharpness = int(v['sharpness'] if 'sharpness' in v else 2)
            speed     = int(v['speed'    ] if 'speed'     in v else 4)
            bar = bytearray([0x01, speed, sharpness] + tmp + [0x00, 0x00, 0x00])
        elif v['type'] == 'rainbow':
            bar = bytearray([0x02, 255 - int(v['speed']), int(v['segCount']), int(v['direction'])])
            bar[1] = max(bar[1], 0x01)
        data['modes'][i] = [bar, np.array([], dtype=np.uint16)] if bar else None

    inverse = np.array([], dtype=np.uint16)

    if 'segments' in data['mask']:
        for i in data['mask']['segments']:
            for o in data['mask']['segments'][i]:
                r = np.arange(o[0], o[1], dtype=np.uint16)
                data['modes'][int(i)][1] = np.concatenate((data['modes'][int(i)][1], r))
                inverse = np.concatenate((inverse, r))

    default = np.array([int(i) for i in range(LED_COUNT) if int(i) not in inverse], dtype=np.uint16)

    data['modes'][data['mask']['default']][1] = np.concatenate((data['modes'][data['mask']['default']][1], default))

    for i in data['modes']:
        i[1] = np.array([o for o in i[1] if o<LED_COUNT], dtype=np.uint16)
    
    if 'shaders' in data:
        shaders = data['shaders']
        for shader in shaders:
            if shader[0] == 'brightnessDiv':
                shader[1] = 11 - int(shader[1]) # Brightness comes in as as scale from 1 to 10
            elif shader[0] == 'rotate':
                shader[1] = int(shader[1]) * 1000
                shader[2] = int(shader[2])
    else:
        shaders = []
    
    return [list(filter(None, data['modes'])), LED_COUNT, shaders]
    return [[x for x in data['modes'] if x], LED_COUNT, shaders]

try:
    if "datafile" not in os.listdir():
        raise Exception("No datafile found!")
    dat = read_file("datafile")
    JSON = json.loads(dat)
    TIMED_MODES = [[-1] + parse_mode_data(JSON, LED_COUNT)[:3]]
    print("Loaded mode:", JSON)
except Exception as e:
    print("Could not load mode from file:", e)
    # TIMED_MODES = [[-1, [
    #     [bytearray([0x00, 0x00, 0x00, 0x00]), np.array([i for i in range(LED_COUNT) if i%6     ], dtype=np.uint16)],
    #     [bytearray([0x00, 0x00, 0x00, 0xFF]), np.array([i for i in range(LED_COUNT) if i%6 == 0], dtype=np.uint16)]
    # ], LED_COUNT, [['rotate', 265_000, 1]]]]
    TIMED_MODES = [[-1, [
        [bytearray([2,255-230,5,0]), np.array([i for i in range(LED_COUNT)], dtype=np.uint16)]
    ], LED_COUNT, []]]

@micropython.viper
def light_interface(buf:ptr8, l:int, TIMER:int): # Best optimization is had here (I think)
    # I *assume* tuple unpacking isn't optimized but idk honestly this code sucks
    for idx in MODES:
        j = ptr8 (idx[0])
        j0 = j[0] # idk if this helps
        k = ptr16(idx[1])
        itt = int(len(idx[1])) # is this like what led segment or something? (there's no way that we're re-writing the first part for each segment... right?)
        if j0 == 0: # Static
            for offset in range(itt):
                static_rgb(j[1], j[2], j[3], buf, 3*k[offset])
        elif j0 == 1: # Fade
            length = int(len(idx[0]))
            for offset in range(itt):
                static_rgb(j[length-3], j[length-2], j[length-1], buf, 3*k[offset])
        elif j0 == 2: # Rainbow
            j2_255 = j[2] * 0xFF
            base_hue = (0xFF * TIMER) // (j[1] * 100)
            
            if not j[3]: 
                for offset in range(itt):
                    pass
                    # hsv_to_rgb((base_hue + (k[offset] * j2_255) // l) % 0xFF,
                            #    0xE5, 0xFF, buf, 3*k[offset],
                            #    (OFFSET_B << 16) | (OFFSET_G << 8) | OFFSET_R)
            else: # Reversed
                for offset in range(itt):
                    pass
                    # hsv_to_rgb((base_hue + (k[offset] * j2_255) // l) % 0xFF,
                            #    0xE5, 0xFF, buf, 3*k[itt-1-offset],
                            #    (OFFSET_B << 16) | (OFFSET_G << 8) | OFFSET_R)

# @micropython.native
def LED_thread():
    global LOOP,LED_COUNT,PREVIOUS_LED_COUNT,TIMEDELTA,TIMED_MODES,SHADERS,MODES

    count = 3*LED_COUNT
    buf = bytearray(count)
    buf_new = bytearray(count)
    buf_final = bytearray(count)

    NEXT_FPS_TIME = uptime_ms() + _FPS_DISPLAY_DELTA
    COUNTER = 0
    
    while LOOP:
        ct_tmp = uptime_ms()
        TIMER = (ct_tmp + TIMEDELTA) % _TIMER_MODULO
        COUNTER += 1
        if ct_tmp >= NEXT_FPS_TIME:
            a = gc.mem_free()
            b = gc.mem_alloc()
            print("FPS: {}\tMEM: {}/{}\tRUNTIME: {}".format(
                COUNTER / (_FPS_DISPLAY_DELTA / 1_000),
                str(b), str(a+b), str(ct_tmp)))
            COUNTER = 0
            NEXT_FPS_TIME = ct_tmp + _FPS_DISPLAY_DELTA

        while len(TIMED_MODES) > 1 and ct_tmp > TIMED_MODES[0][0]:
            TIMED_MODES.pop(0)
        MODES     = TIMED_MODES[0][1]
        LED_COUNT = TIMED_MODES[0][2]
        SHADERS   = TIMED_MODES[0][3]

        if LED_COUNT != PREVIOUS_LED_COUNT:
            del buf
            count = 3*LED_COUNT
            buf = bytearray(count)
            buf_new = bytearray(count)
            buf_final = bytearray(count)
            PREVIOUS_LED_COUNT = LED_COUNT

        for b in MODES:
            b = b[0]
            if b[0] == 1: # Fade
                length = len(b) - 1 # minus 1 for easy color set code
                count = (length - 5) // 3 # length -5 for id, speed, sharpness, buffer; all minus 1 because line above

                v = b[1] * float(ct_tmp) / 5000
                dec = (v - int(v)) ** (b[2] / 2.0) # Decimal ^ (sharpness / 2.0)
                c1 = int(v) % count
                c2 = 3 + 3 * ((c1 + 1) % count)
                c1 = 3 + 3 * c1

                b[length-2] = int(b[c1  ] + dec * (b[c2  ] - b[c1  ]))
                b[length-1] = int(b[c1+1] + dec * (b[c2+1] - b[c1+1]))
                b[length  ] = int(b[c1+2] + dec * (b[c2+2] - b[c1+2]))
        
        light_interface(buf, LED_COUNT, TIMER)
        
        tradeBuf = False
        for shader in SHADERS:
            if shader[0] == 'brightnessDiv': # brightness div
                divide_brightness(buf, shader[1], LED_COUNT)
            if shader[0] == 'rotate': # duration, shift number
                tradeBuf = True
                rot = LED_COUNT * (TIMER / shader[1])
                if shader[2] == 1:
                    rotate_LEDs(buf, buf_new, 3 * shader[2] * (int(rot) % LED_COUNT), LED_COUNT, True, int(255 * rot) % 255)
                else:
                    rotate_LEDs(buf, buf_new, 3 * shader[2] * (int(rot) % LED_COUNT), LED_COUNT, False)
        finalBufRef = buf_new if tradeBuf else buf
        
        if REVERSE: # shouldnt this be moved to a viper function?
            for i in range(LED_COUNT):
                index = 3*i
                buf_final[index  ] = finalBufRef[-index-3]
                buf_final[index+1] = finalBufRef[-index-2]
                buf_final[index+2] = finalBufRef[-index-1]
            finalBufRef = buf_final
        
        # write LED output
        machine.bitstream(PINOUT, 0, _BITSTREAM_TIMING, finalBufRef)

_thread.start_new_thread(LED_thread, ())

try:
    onboard_led(1)
    assert (credentials := 'credentials') in os.listdir(), "Could not find wifi config."
    
    router_ssid, router_pass, token = map(str.strip, read_file(credentials).split('\n')[:3])
    print('SSID: "{}"\nRouter Password: "{}"\nToken: "{}"'.format(router_ssid, router_pass, token))
    
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(router_ssid, router_pass)
    for i in range(r := 30):
        if sta_if.isconnected():
            break
        time.sleep(1)
        print('Failed to connect to network [{}/{}] - "{}"'.format(i+1, r, sta_if.status()))
    else:
        sta_if.active(False)
        raise Exception("Could not connect to network.")
    onboard_led(0)
    print("Connected to Router!")
except Exception as e: # This entire section is dumb but it works
    onboard_led(1)
    print(e)

    is_ap_configuring = True # for timer reset in lightThread
    
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid="Brynic LED Controller", password="")
    while ap.active() == False: pass

    print('Created AP:', ap.ifconfig())

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)

    headers = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n"
    pageHTML = read_file('index.html')

    while True:
        conn, addr = s.accept()
        print("Got a connection from", addr)
        time.sleep(0.05)
        while True:
            try:
                c = str(conn.recv(1024))
                print("GOT C:", c)
                try:
                    if " ^Z_ " in c:
                        try:
                            c = json.loads(c.split(' ^Z_ ')[1].strip())
                            write_file(credentials, c['SSID']+'\n'+c['PASS']+'\n'+c['TOKE'])
                        except Exception as e:
                            print("Error decoding request JSON:", e)
                            continue
                        print("Got new credentials, resetting.")
                        onboard_led(0)
                        machine.reset()
                    else:
                        print("Delimiter not found in request.")
                except Exception as e:
                    print("Error processing request (2):", e)
                    raise e
                print("Sending page.")
                conn.sendall(headers + pageHTML)
                conn.close()
                print("Sent page.")
            except Exception as e2:
                print("Connection failed? Sleeping for 5 seconds.", e2)
                conn.close()
                time.sleep(5)
                break

try:
    while True: #Reconnect loop
        print("Starting websocket.")
        json_err_count = 0
        try:
            w = ws_client.connect(_WEBSOCKET_SERVER)
            deviceInfo = {'action': 'init', 'UUID': UUID, 'TOKEN': token, 'LED_COUNT': LED_COUNT}
            w.send(json.dumps(deviceInfo))
            print("Send device info:", deviceInfo)
        except Exception as e:
            print("Could not connect:", e)
            time.sleep(5)
            continue

        while True: #Websocket read loop
            gc.collect()
            try:
                data = w.recv()
                
                try:
                    JSON = json.loads(data)
                except Exception as e:
                    print('Error parsing "{}" as JSON: "{}"'.format(str(data), str(e)))
                    if json_err_count > 3:
                        raise Exception("Too many JSON errors, reconnecting.")
                    json_err_count += 1
                    time.sleep(1.25)
                    continue
                
                print("Got JSON:", JSON)
                if JSON['action'] == 'mode':
                    try:
                        tmp = parse_mode_data(JSON, LED_COUNT)
                        if ('duration' not in JSON) or ('duration' in JSON and int(JSON['duration']) < 0):
                            TIMED_MODES[-1] = [-1, tmp[0],tmp[1],tmp[2]]
                            write_file("datafile", data)
                        else:
                            insIndex = (len(TIMED_MODES) - 1) if ('isQued' in JSON and JSON['isQued'] and str(JSON['isQued']).lower() != "false") else 0
                            TIMED_MODES.insert(insIndex, [int(JSON['duration']) * 100 + uptime_ms(), tmp[0],tmp[1],tmp[2]])
                        print("Modes:", TIMED_MODES) #Print compiled mode
                    except Exception as e:
                        print("Error parsing mode:", e)
                elif JSON['action'] == 'RGB_ORDER':
                    write_file("RGB_ORDER", JSON['RGB_ORDER'])
                    OFFSET_R, OFFSET_G, OFFSET_B = parse_RGB_mode(JSON['RGB_ORDER'])
                    print("RGB offsets ->", OFFSET_R, OFFSET_G, OFFSET_B)
                elif JSON['action'] == 'LED_PIN':
                    write_file("RGB_ORDER", JSON['LED_PIN'])
                    LED_PIN = int(JSON['LED_PIN'])
                    PINOUT = machine.Pin(LED_PIN)
                    PINOUT.init(PINOUT.OUT)
                    print("LED_PIN ->", LED_PIN)
                elif JSON['action'] == 'REVERSE':
                    write_file("REVERSE", JSON['REVERSE'])
                    REVERSE = boolstr(JSON['REVERSE']) 
                    print("Reverse ->", REVERSE)
                elif JSON['action'] == 'getTime':
                    RECTIME = time.time_ns() // 1_000_000
                    w.send(json.dumps({'action': 'getTime'}))
                elif JSON['action'] == 'timeDelta':
                    TIMEDELTA = JSON['time'] - RECTIME
                elif JSON['action'] == 'reset':
                    print("Resetting, modes are:", TIMED_MODES)
                    machine.reset()
                    LOOP = False
                elif JSON['action'] == 'forget_creds':
                    try:
                        os.remove('credentials')
                        print("Reset credentials.")
                    except Exception as e:
                        print("Error deleting credentials:", e)
                    machine.reset()
                    LOOP = False
                
                del JSON,data
            except Exception as e:
                print("Websocket error:", e)
                try:
                    del w,data
                except Exception:
                    pass
                gc.collect()
                time.sleep(5)
                break
            time.sleep(0.2)      
except:
    LOOP = False