import struct, sys

def strings(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'\xca\xfe\xba\xbe', 'not a class file'
    cp_count = struct.unpack('>H', d[8:10])[0]
    i = 10
    out = {}
    idx = 1
    while idx < cp_count:
        tag = d[i]
        if tag == 1:
            ln = struct.unpack('>H', d[i+1:i+3])[0]
            raw = d[i+3:i+3+ln]
            try:
                out[idx] = raw.decode('utf-8')
            except UnicodeDecodeError:
                out[idx] = raw.decode('latin-1')
            i += 3 + ln
        elif tag in (7, 8, 16, 19, 20):
            i += 3
        elif tag == 15:
            i += 4
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            i += 5
        elif tag in (5, 6):
            i += 9
            idx += 1
        else:
            raise ValueError('bad tag %d at %d' % (tag, i))
        idx += 1
    return out

if __name__ == '__main__':
    for p in sys.argv[1:]:
        cp = strings(p)
        cjk = [v for v in cp.values() if any(ord(c) > 127 for c in v)]
        print('==', p, 'consts', len(cp), 'non-ascii', len(cjk))
        for v in cjk:
            print('   ', v.encode('unicode_escape').decode('ascii'))
