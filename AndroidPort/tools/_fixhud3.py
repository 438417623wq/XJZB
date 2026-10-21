"""Final pass: repair the literals whose damaged middle spans a missing char.

_hudrev.ps1 undid the cp936 layer file-wide via .NET's GBK. Where cp936 had no
mapping the original damage wrote '?', so a byte is gone and the literal is one
or two characters short of the truth. The pre-damage compiled class still holds
every original string, so match on prefix + suffix with a small length
tolerance and accept only unambiguous candidates.
"""
import re
import struct

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
    src = open(REV, 'rb').read().decode('utf-8', errors='replace')

    pool = set()
    for v in class_strings(CLASS):
        if v and any(ord(c) > 127 for c in v) and not v.startswith('\x01'):
            pool.add(v)

    repaired, unresolved = 0, []

    def repl(m):
        nonlocal repaired
        lit = m.group(0)
        body = lit[1:-1]
        if '\ufffd' not in body:
            return lit

        # everything up to the first damaged spot, and after the last one
        head = body.split('\ufffd')[0].rstrip('?')
        tail = body.split('\ufffd')[-1].lstrip('?')
        cands = [o for o in pool
                 if o.startswith(head) and o.endswith(tail)
                 and len(head) + len(tail) <= len(o) <= len(head) + len(tail) + 4]
        if len(cands) == 1:
            repaired += 1
            return '"' + cands[0] + '"'
        unresolved.append((body, cands))
        return lit

    out = re.sub(r'"[^"\r\n]*"', repl, src)
    open(OUT, 'w', encoding='utf-8', newline='').write(out)

    print('repaired:', repaired, 'unresolved:', len(unresolved))
    for body, cands in unresolved:
        print('   ', body.encode('unicode_escape').decode('ascii'),
              '->', [c.encode('unicode_escape').decode('ascii') for c in cands])
    print('U+FFFD left:', out.count('\ufffd'))
    for n, line in enumerate(out.split('\n'), 1):
        if '\ufffd' in line:
            print('   line', n, line.strip().encode('unicode_escape').decode('ascii'))


if __name__ == '__main__':
    main()
