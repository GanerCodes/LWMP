import json, os
from urllib.parse import quote, quote_plus, unquote_plus, urlsplit
from base64 import urlsafe_b64encode, b64encode
from string import ascii_letters, digits
from sqlitedict import SqliteDict as db
from cryptography.fernet import Fernet
from collections import namedtuple
from unidecode import unidecode 
from hashlib import sha256, md5
from random import choice
from requests import get
from time import time

ParsedPath = namedtuple("ParsedPath", ['path', 'filePath', 'args', 'isFile', 'isDir', 'directory_traversal', 'originalPath', 'decrypted', 'parse'])
def based_path(path : str, basePath : str) -> bool:
    return os.path.commonprefix((os.path.realpath(path), os.path.realpath(basePath))) == os.path.realpath(basePath)
def parse_path(path : str, basePath : str = os.getcwd(), encryption_key : bytes = None, args = None, throw_traversal : bool = True) -> ParsedPath:
    originalPath = path
    path = path.replace('\\', '/')
    parse = urlsplit(path, allow_fragments = False)
    path = list(filter(None, map(lambda x: unquote_plus(x).replace('\\', '/').replace('../', '').replace('/', ''), parse.path.split('/'))))
    args = args or {unquote_plus(o[0]): (unquote_plus(o[1]) if len(o) > 1 else "True") for o in (i.split('=', 1) for i in filter(None, parse.query.split('&')))}
    if encryption_key:
        path = list(map(lambda x: decrypt(x, encryption_key), path))
    filePath = os.path.realpath(f"{basePath}/{'/'.join(path)}").replace('\\', '/')
    directory_traversal = not based_path(filePath, basePath)
    if throw_traversal and directory_traversal:
        raise Exception("Directory traversal attack detected.")
    return ParsedPath(
        path                 = path, 
        filePath             = filePath, 
        args                 = args, 
        isFile               = os.path.isfile(filePath), 
        isDir                = os.path.isdir(filePath), 
        directory_traversal  = directory_traversal,
        originalPath         = originalPath,
        decrypted            = bool(encryption_key),
        parse                = parse
    )
def construct_path(path : str, args : dict = {}, baseURL : str = '/', encryption_key : bytes = None) -> str:
    fmt = (lambda x: quote_plus(encrypt(x, encryption_key))) if encryption_key else quote_plus
    return f"{baseURL}{'/'.join(map(fmt, path))}{('?' + ('&'.join(f'{quote_plus(str(i))}={quote_plus(str(args[i]))}' for i in args))) if args else ''}"
def shortURL(path, password, args = {'comic': "True"}): 
    return get('https://ganer.xyz/createurlshortner', headers = {'encodeURL': construct_path(['archive'] + path.split('/'), encryption_key = transformKey(password), args = args, baseURL = "https://ganer.xyz/encrypted/")}).content.decode('utf-8')

def transformKey(key): return b64encode(key.rjust(32, '0').encode())
def strEncode(msg): return msg if type(msg) == bytes else msg.encode()
def encrypt(msg, key): return Fernet(strEncode(key))._encrypt_from_parts(strEncode(msg), 0, b'#' * 16).decode()
def decrypt(msg, key): return Fernet(strEncode(key)).decrypt_at_time(strEncode(msg), 1, 1).decode()
def encrypt_long(msg, key): return Fernet(strEncode(key)).encrypt(strEncode(msg)).decode()
def decrypt_long(msg, key): return Fernet(strEncode(key)).decrypt(strEncode(msg)).decode()

def makeID(l): return ''.join(choice(ascii_letters + digits) for i in range(l))
def forceASCII(text): return unidecode(text)
def isASCII(text): return text == forceASCII(text)
def makeHash(text, digits = 16):
    r = sha256()
    r.update(text.encode('utf-8'))
    return urlsafe_b64encode(r.digest())[:digits].decode('utf-8')
def setkey(filename, key, val):
    database = db(filename, autocommit = True)
    database[key] = val
    database.close()
def getkey(filename, key):
    database = db(filename, autocommit = True)
    val = database[key]
    database.close()
    return val
def iskey(filename, key):
    database = db(filename, autocommit = True)
    val = key in database
    database.close()
    return val
def keyFromFile(filename):
    with open(filename, 'r') as f:
        return f.read().strip()
def fastFileHash(path, size):
    m = md5()
    with open(path, 'rb') as f:
        b = f.read(size)
        while len(b) > 0:
            m.update(b)
            b = f.read(size)
    return m.hexdigest()
def hashTextSecure(text):
    r = sha256()
    r.update(text.encode('utf-8'))
    return r.hexdigest()
def verifyToken(path, token, key):
    t = json.loads(decrypt_long(token, key))
    assert t[2] > int(time())
    assert getkey(path, t[0]) == t[1]
    return t[0], t[1]
def filenameSafe(text):
    return urlsafe_b64encode(text.encode('utf-8')).decode('utf-8')