"""Finish the HudPreview.java recovery.

_hudrev.ps1 already produced $TEMP/hud_rev.bin: the whole file with the
cp936 layer undone via .NET's GBK. Bytes that cp936 could not map were written
as '?' during the original damage, so those spots no longer form valid UTF-8.
This script decodes leniently, then repairs each damaged literal by matching it
against the pre-damage string constants still present in the compiled class.
"""
import re
import struct
import sys

REV = r'C:\Users\XiaoXin\AppData\Local\Temp\hud_rev.bin'
CLASS = r'F:\KF\XJZB\AndroidPort\tools\bin\HudPreview.class'
OUT = r'F:\KF\XJZB\AndroidPort\tools\HudPreview.java'


def class_strings(path):
    d = open(path, 'rb').read()
    cp_count = struct.unpack('>H', d[8:10])[0]
    i, idx, out = 10, 1, []
    while idx < cp_count:
        tag = d[i]
        if tag == 1:
            ln = struct.unpack('>H', d[i + 1:i + 3])[0]
            raw = d[i + 3:i + 3 + ln]
            try:
                out.append(raw.decode('utf-8'))
            except UnicodeDecodeError:
                out.append(None)
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


def main():
    raw = open(REV, 'rb').read()
    src = raw.decode('utf-8', errors='replace')

    pool = set()
    for v in class_strings(CLASS):
        if v and any(ord(c) > 127 for c in v) and not v.startswith('\x01'):
            pool.add(v)

    fixed, unresolved = 0, []

    def repl(m):
        nonlocal fixed
        lit = m.group(0)
        body = lit[1:-1]
        if '\ufffd' not in body:
            if any(ord(c) > 127 for c in body):
                fixed += 1
            return lit
        # one or more bytes were destroyed: match by length + surviving chars
        cands = [o for o in pool
                 if len(o) == len(body) and all(
                     a == '\ufffd' or a == b for a, b in zip(body, o))]
        if len(cands) == 1:
            fixed += 1
            return '"' + cands[0] + '"'
        unresolved.append(body)
        return lit

    out = re.sub(r'"[^"\r\n]*"', repl, src)

    open(OUT, 'w', encoding='utf-8', newline='').write(out)
    print('literals repaired:', fixed)
    print('unresolved:', len(unresolved))
    for u in unresolved:
        print('   ', u.encode('unicode_escape').decode('ascii'))
    print('replacement chars left in file:', out.count('\ufffd'))


if __name__ == '__main__':
    main()
