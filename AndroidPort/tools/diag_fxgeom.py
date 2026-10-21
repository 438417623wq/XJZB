"""One clean diagnostic: effect GRP frame geometry + which palette makes them fire-coloured.

Prints frame dims (to catch the stride bug), then evaluates candidate palettes
by scoring how "fire-like" (red/orange/yellow, high luminance) the result is.
"""
import os
import struct
from PIL import Image, ImageDraw
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def wpe_pal(ts):
    for ar in (SD, BD):
        p = "tileset\\%s.wpe" % ts
        if ar.has(p):
            w, _ = ar.read_with_gaps(p)
            if len(w) < 1024:
                w += bytes(1024 - len(w))
            return [(w[i * 4 + 2], w[i * 4 + 1], w[i * 4]) for i in range(256)]
    return None


print("=== frame geometry ===")
for label, path in [("flshS", r"unit\thingy\tmeFlshS.grp"),
                    ("bangS", r"unit\thingy\tBangS.grp"),
                    ("bsmoke", r"unit\thingy\bsmoke.grp"),
                    ("ephFire", r"unit\bullet\ephFire.grp"),
                    ("marine", r"unit\terran\marine.grp")]:
    r = load(path)
    if r is None:
        print(label, "MISS"); continue
    frames, mw, mh = r
    dims = sorted({(f["w"], f["h"]) for f in frames})
    short = [(f["w"], f["h"], len(f["px"])) for f in frames if len(f["px"]) != f["w"] * f["h"]]
    print("%-8s frames=%-4d nominal=%dx%d distinctdims=%s short=%s" %
          (label, len(frames), mw, mh, dims[:6], short[:3]))

print("\n=== candidate palettes: what does index 32 / index 3 become? ===")
for ts in ("platform", "jungle", "badlands", "desert"):
    pal = wpe_pal(ts)
    if pal:
        print("%-9s idx3=%-16s idx32=%-16s idx246=%-16s idx247=%s" %
              (ts, pal[3], pal[32], pal[246], pal[247]))

# is there a dedicated units/effects palette in the archive?
print("\n=== searching archives for other .wpe / palette-ish files ===")
for nm, ar in (("StarDat", SD), ("BrooDat", BD)):
    for cand in (r"tileset\jungle.wpe", r"unit\units.wpe", r"arr\palette.wpe",
                 r"tileset\platform.wpe"):
        print("  %s %-24s %s" % (nm, cand, ar.has(cand)))
