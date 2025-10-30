import os
def boolstr(s):
    return s.strip().lower() in ('true', '1')
def read_file(filename, strip=True):
    with open(filename, 'r') as f:
        contents = f.read()
        return contents if strip else contents.strip()
def write_file(filename, content):
    with open(filename, 'w') as f:
        f.write(str(content))
def load_check_datafile(f, default, parse=str):
    if f in os.listdir():
        try:
            return parse(read_file(f).strip())
        except Exception as err:
            print('Failed to read config file [will re-write default] "{}"'.format(f), err)
    write_file(f, default)
    return default