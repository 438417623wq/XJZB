"""v2.11: the LO files.

The repack's arr\\images.tbl lists, for each image, a .grp row AND a companion
row with a LO extension (.lof/.log/.lou/.lod/.los). In StarCraft those LO files
are the authoritative per-image animation layout: they say how the GRP's frames
are grouped into animations, and how many directions each one has. That is
exactly the walk/attack boundary batch B needs, so this probe:

  1. lists every distinct extension in the table, with counts
  2. reads a handful of LO files and dumps their header + first bytes
  3. cross-checks a few against their GRP frame counts

Usage: python probe_v211bh.py [n]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

RAW, _ = BD.read_with_gaps("arr\\images.tbl")
cnt = struct.unpack_from("<H", RAW, 0)[0]
offs = list(struct.unpack_from("<%dH" % cnt, RAW, 2))
rows = []
for i in range(cnt):
    o = offs[i]
    e = RAW.index(b"\x00", o)
    rows.append(RAW[o:e].decode("latin-1"))
print("images.tbl: %d rows" % len(rows))

ext = {}
for r in rows:
    e = os.path.splitext(r)[1].lower()
    ext[e] = ext.get(e, 0) + 1
print("extensions:", sorted(ext.items(), key=lambda kv: -kv[1])[:16])

los = [r for r in rows if os.path.splitext(r)[1].lower() in
       (".lof", ".log", ".lou", ".lod", ".los")]
print("LO rows: %d" % len(los))
for r in los[:20]:
    print("   ", r)


def load(name):
    for ar in (PT, SD, BD):
        try:
            if ar.has(name):
                d, g = ar.read_with_gaps(name)
                return d, g
        except Exception:
            pass
    return None, None


n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
print("\n--- LO file dumps ---")
for r in los[:n]:
    for pre in ("unit\\", ""):
        d, g = load(pre + r)
        if d is not None:
            break
    if d is None:
        print("%-34s MISS" % r)
        continue
    hdr = struct.unpack_from("<HH", d, 0) if len(d) >= 4 else None
    print("%-34s %6d bytes gaps=%d  u16x2=%s  head=%s"
          % (r, len(d), len(g), hdr, d[:32].hex(" ")))
    # the GRP next to it
    base = os.path.splitext(r)[0]
    for cand in (base + ".grp", base + ".GRP"):
        gd, _ = load("unit\\" + cand)
        if gd is None:
            gd, _ = load(cand)
        if gd is not None:
            fr, mw, mh = grpm.decode_grp(gd, ())
            print("     %-30s grp frames=%d cell=%dx%d" % (cand, len(fr), mw, mh))
            break
