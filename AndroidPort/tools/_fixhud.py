"""Recover HudPreview.java Chinese string literals after the cp936 corruption.

The corruption was: UTF-8 bytes -> decoded as cp936 -> re-encoded as UTF-8.
That transform is reversible per string EXCEPT where cp936 had no mapping and
wrote '?' (0x3F), which destroys a byte. The compiled class predates the
damage and still holds all 60 original strings, so it is the authority: we
reverse-transform what we can and look the rest up in the class constants.
"""
import re
import struct
import sys

JAVA = r'F:\KF\XJZB\AndroidPort\tools\HudPreview.java'
CLASS = r'F:\KF\XJZB\AndroidPort\tools\bin\HudPreview.class'


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


def reverse(s):
    """cp936-encode then utf-8-decode; returns None when a '?' ate a byte."""
    if '?' in s:
        return None
    try:
        return s.encode('cp936').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return None


def main():
    originals = [v for v in class_strings(CLASS)
                 if v and any(ord(c) > 127 for c in v)]
    # the class also carries '\u0001…' style fragments; keep only real labels
    originals = [v for v in originals if not v.startswith('\x01')]
    pool = set(originals)

    src = open(JAVA, encoding='utf-8').read()
    bom = src.startswith('\ufeff')
    if bom:
        src = src[1:]

    fixed, unresolved = 0, []

    def repl(m):
        nonlocal fixed
        lit = m.group(0)
        body = lit[1:-1]
        if not any(ord(c) > 127 for c in body):
            return lit
        got = reverse(body)
        if got is not None and got in pool:
            fixed += 1
            return '"' + got + '"'
        # '?' destroyed a byte: match by the surviving structure
        cands = [o for o in pool
                 if len(o) == len(body) and all(
                     a == b or a == '?'
                     for a, b in zip(body, o))]
        if len(cands) == 1:
            fixed += 1
            return '"' + cands[0] + '"'
        unresolved.append(body)
        return lit

    out = re.sub(r'"[^"\n]*"', repl, src)

    open(JAVA, 'w', encoding='utf-8', newline='').write(out)
    print('fixed', fixed, 'unresolved', len(unresolved))
    for u in unresolved:
        print('   UNRESOLVED', u.encode('unicode_escape').decode('ascii'))
    left = [c for c in out if ord(c) > 127 and not (0x4e00 <= ord(c) <= 0x9fff)]
    print('non-CJK leftovers:', sorted({c.encode('unicode_escape').decode('ascii') for c in left}))


if __name__ == '__main__':
    main()
