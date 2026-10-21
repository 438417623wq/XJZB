"""Decode a retail StarCraft GRP and report which frames are duplicates of their
neighbours. Used to decide whether the paired direction columns in the ported
webp sheets are faithful to the retail art or an asset-pipeline artifact.
Read-only: reads StarDat.mpq, prints only.
"""
import sys, struct
sys.path.insert(0, 'F:/KF/XJZB/AndroidPort/tools')
from sc_archive import Archive

def decode_frame(d, off, W, H):
    """Classic GRP RLE -> list of rows, each row a list of palette indices (0 = transparent)."""
    rows = []
    p = off
    row = 0
    prev = None
    while row < H:
        if p >= len(d):
            break
        lt = d[p]; p += 1
        if lt == 0:
            if p >= len(d): break
            row += d[p]; p += 1
            prev = None
        elif lt == 2:
            rows.append(list(prev) if prev else [0]*W)
            row += 1
        else:
            cur = [0]*W
            col = 0
            while col < W:
                if p >= len(d): break
                c = d[p]; p += 1
                if c & 0x80:
                    col += c & 0x7F
                else:
                    for _ in range(c+1):
                        if col >= W or p >= len(d): break
                        cur[col] = d[p]; p += 1; col += 1
            rows.append(cur)
            prev = cur
            row += 1
    while len(rows) < H:
        rows.append([0]*W)
    return rows

def check(name, dirs=17):
    with Archive('F:/KF/XJZB/StarDat.mpq') as a:
        d = a.read(name)
    nframes, sw, sh = struct.unpack_from('<HHH', d, 0)
    frames = []
    for i in range(nframes):
        x, y, fw, fh, off = struct.unpack_from('<BBBBI', d, 6 + i*8)
        frames.append(decode_frame(d, off, fw, fh))
    print('== %s frames=%d sheet=%dx%d  fw=%d fh=%d' % (name, nframes, sw, sh,
          struct.unpack_from('<B', d, 6)[0] and struct.unpack_from('<BBBBI', d, 6)[2],
          struct.unpack_from('<BBBBI', d, 6)[3]))
    dup = [i for i in range(nframes-1) if frames[i] == frames[i+1]]
    print('   frames identical to next frame:', dup)
    # assume frame-major ordering: index = anim*dirs + dir
    if nframes % dirs == 0:
        anims = nframes // dirs
        print('   frame-major layout: %d anim frames x %d dirs' % (anims, dirs))
        for an in range(min(anims, 8)):
            base = an*dirs
            pairs = [dd for dd in range(dirs-1) if frames[base+dd] == frames[base+dd+1]]
            print('     anim%-2d dirs identical-to-next: %s' % (an, pairs))
    else:
        print('   nframes %% %d != 0  (%d)' % (dirs, nframes % dirs))

for nm in ['unit\\terran\\marine.grp', 'unit\\terran\\tank.grp', 'unit\\zerg\\zergling.grp',
           'unit\\terran\\scv.grp', 'unit\\protoss\\dragoon.grp']:
    try:
        check(nm)
    except Exception as e:
        print(nm, 'ERR', repr(e))
