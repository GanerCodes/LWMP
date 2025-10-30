import websockets, mimetypes, asyncio, aiohttp, time, json, os, requests, urllib.parse
from collections import namedtuple
from collections.abc import Mapping
from sqlitedict import SqliteDict
from aiohttp import web
from sys import argv

WEBSOCKET_PORT = 2096
WEBSITE_PORT = 40
SITE_DIR = "website_compiled"

ENABLE_VERBOSE_LOGGING = len(argv) > 1 and argv[1] == "verbose"

mimetypes.add_type(".ttf", "font/ttf")

startTimeNS = time.time_ns()
clientList = {}
database = SqliteDict("deviceInfo.db", autocommit=True) # https://ganer.xyz/s/tlmRDw

getTimeJSON = json.dumps({'action': 'getTime'})
CORS_HEADERS = {
    # 'Access-Control-Allow-Origin' : '*',
    # 'Access-Control-Allow-Methods': 'GET,PUT,POST,DELETE',
    # 'Access-Control-Allow-Headers': '*'
}

def get_nested_key(obj, *keys, default=False):
    for i in keys:
        if isinstance(obj, Mapping) and i in obj:
            obj = obj[i]
        else:
            return default
    return obj

def print_nested_dict(d, t=""):
    for k,v in d.items():
        if isinstance(v, Mapping):
            print(f"{t}{k}:")
            print_nested_dict(v, f"{t}  ")
        else:
            print(f"{t}{k}:{v}")

print_nested_dict(database)

async def removeDevice(TOKEN, UUID):
    if entry := get_nested_key(clientList, TOKEN, UUID):
        sock = entry["SOCKET"]
        del entry
        await sock.close()

async def WS_server(s):
    global clientList
    path = s.request.path
    print(path)
    try:
        INFO = json.loads(await s.recv())
    except Exception as e:
        print("Error getting info!", e)
        return
    UUID, TOKEN, LED_COUNT = INFO['UUID'], INFO['TOKEN'], INFO['LED_COUNT']
    NAME = get_nested_key(database, TOKEN, UUID, 'name', default=None)
    
    dataEntry = {'LED_COUNT': LED_COUNT, 'name': NAME}
    entry = {'SOCKET': s} | dataEntry

    try:
        if TOKEN in clientList:
            clientList[TOKEN][UUID] = entry
        else:
            clientList[TOKEN] = {UUID: entry}

        newEntry = {UUID: dataEntry}
        if TOKEN in database:
            newEntry = database[TOKEN] | newEntry
        database[TOKEN] = newEntry #Force it to update internal dict
        database.commit()
        
        print(f'{TOKEN} - {UUID} ({NAME}): LED Count = "{LED_COUNT}"')
        await asyncio.sleep(0.5)
        
        async def recLoop(s, path):
            try:
                while True:
                    dat = json.loads(await s.recv())
                    print(f"{TOKEN} - {UUID} ({NAME}): {dat}")
                    if dat['action'] == 'getTime':
                        await s.send(json.dumps({
                            'action': 'timeDelta',
                            'time': ((time.time_ns() - startTimeNS) // 1_000_000) % 86400000
                        }))
            except Exception as e:
                print(f'{TOKEN} - {UUID} ({NAME}): Error!', e)
                await removeDevice(TOKEN, UUID)

        receiveLoop = asyncio.create_task(recLoop(s, path))

        await asyncio.sleep(0.5)
        await s.send(getTimeJSON)
        await receiveLoop
    except Exception:
        pass

    await removeDevice(TOKEN, UUID)

async def website(req):
    if req.method == 'POST':
        data = await req.json()
        
        if 'token' in data and 'uuid' in data and 'mode' in data:
            token, uuid, mode = data['token'], data['uuid'], data['mode']
            if ENABLE_VERBOSE_LOGGING:
                print(f"Got data: {token} | {uuid} | {mode}")
            
            for token in token.split('⌈λ⌉', 10):
                if token in clientList:
                    if uuid == 'all' or '|' in uuid:
                        if uuid == 'all':
                            tr = clientList[token]
                        else:
                            tr = (i for i in uuid.split('|') if i in clientList[token])
                        for deviceUUID in tr:
                            mode['LED_COUNT'] = clientList[token][deviceUUID]['LED_COUNT']
                            try:
                                await clientList[token][deviceUUID]['SOCKET'].send(json.dumps(mode))
                            except:
                                await removeDevice(token, deviceUUID)
                    elif uuid in clientList[token]:
                        mode = json.dumps(oldMode := mode)
                        try:
                            await clientList[token][uuid]['SOCKET'].send(mode)
                        except Exception as err:
                            await removeDevice(token, uuid)
                        if "LED_COUNT" in oldMode:
                            clientList[token][uuid]['LED_COUNT'] = oldMode["LED_COUNT"]
                            database[token][uuid]["LED_COUNT"] = oldMode["LED_COUNT"]
                            database[token] = database[token]
                            database.commit()
                        #Maybe update LED count for database and client list here
                
            return web.Response(headers = CORS_HEADERS)
        return web.Response(status = 400, headers = CORS_HEADERS)
    elif req.method == 'GET':
        if 'action' in req.headers and 'token' in req.headers and req.headers['token'] in database:
            token = req.headers['token']
            if req.headers['action'] == 'getDevices':
                if token in database:
                    deviceList = []
                    for device in database[token]:
                        databaseEntry = database[token][device]
                        
                        symbol = '🟢' if (token in clientList and device in clientList[token]) else '🔴'
                        name = databaseEntry['name'] if databaseEntry['name'] else device
                        
                        deviceList.append({
                            'name': f"{symbol} {name} - {databaseEntry['LED_COUNT']}",
                            'UUID': device,
                            'LED_COUNT': databaseEntry['LED_COUNT'] })

                    return web.Response(
                        headers = {'content-type': 'application/json'} | CORS_HEADERS,
                        body    = json.dumps(deviceList))
                else:
                    return web.Response(
                        headers = {'content-type': 'application/json'} | CORS_HEADERS,
                        body    = json.dumps([]))
            elif req.headers['action'] == 'renameDevice' and 'uuid' in req.headers and 'newName' in req.headers:
                uuid = req.headers['uuid']
                if uuid in database[token]:
                    dat = database[token]
                    oldName = database[token][uuid]['name']
                    dat[uuid]['name'] = req.headers['newName']
                    database[token] = dat
                    database.commit()
                    if token in clientList and uuid in clientList[token]:
                        clientList[token][uuid]['name'] = req.headers['newName']
                    print(f'{token} - Renamed Device "{req.headers["uuid"]}" ("{database[token][uuid]["name"]}") ("{oldName}" --> "{req.headers["newName"]}")')
                    return web.Response(headers = CORS_HEADERS)
            elif req.headers['action'] == 'removeDevice' and 'uuid' in req.headers:
                uuid = req.headers['uuid']
                if uuid in database[token]:
                    dat = database[token]
                    oldName = database[token][uuid]['name']
                    del dat[uuid]
                    
                    database[token] = dat
                    database.commit()
                    print(f'{token} - Removed Device "{req.headers["uuid"]}" ("{oldName}")')
                    
                    await removeDevice(token, uuid)
                    return web.Response(headers = CORS_HEADERS)
        else:
            pathName = '/index.html' if req.path in ['/', ''] else req.path
            if pathName.startswith('/call/'):
                q = '{"'+urllib.parse.unquote(req.path).lstrip('/call/').split('`{"')[1].split('`')[0][:2048]
                print("Sending request from URL:", q)
                async with aiohttp.ClientSession() as session:
                    await session.post("https://brynic.ganer.xyz", data = q) # wHAT
                return web.Response(headers = CORS_HEADERS, body="200")
            else:
                try:
                    with open(SITE_DIR + pathName, 'rb') as f:
                        body = f.read()
                    return web.Response(headers = {'content-type': mimetypes.types_map[os.path.splitext(pathName)[1]]} | CORS_HEADERS, body=body)
                except Exception as e:
                    return web.Response(headers = CORS_HEADERS, body="404")

async def main():
    WEBSOCKET_SERVER = websockets.serve(WS_server, "0.0.0.0", WEBSOCKET_PORT)

    server = web.Server(website)
    runner = web.ServerRunner(server)
    await runner.setup()
    WEBSITE_SERVER = web.TCPSite(runner, "0.0.0.0", WEBSITE_PORT)
    await WEBSITE_SERVER.start()

    async def resyncTime():
        while True:
            await asyncio.sleep(60 * 60) #Reset time drift every hour
            for i in clientList:
                for o in clientList[i]:
                    try:
                        await clientList[i][o]['SOCKET'].send(getTimeJSON)
                    except Exception:
                        pass
    asyncio.create_task(resyncTime())

    await WEBSOCKET_SERVER

asyncio.get_event_loop().run_until_complete(main())
asyncio.get_event_loop().run_forever()
