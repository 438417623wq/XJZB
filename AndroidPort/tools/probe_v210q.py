"""v2.10: find the Protoss Observatory GRP.

images.tbl has no entry that decodes to a building for units.dat id 159, and
pipeline_expand.py's BUILDINGS table maps "observatory" to protoss\\texture.grp
-- which renders as a blue plasma swirl (the stasis/recall texture), not a
building. Brute-force the plausible names, then render whatever hits.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image

import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "v210_bld")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

STEMS = ["observ", "obsrv", "obser", "obs", "ob", "pobserv", "pObs", "observe",
         "observatory", "pobs", "obscol", "eye", "pEye", "pobsrv", "obsl",
         "obsrvtry", "pObserv", "pObservatory", "po"]
DIRS = ["unit\\protoss\\", "unit\\thingy\\", "unit\\neutral\\"]
EXTS = [".grp"]

hits = []
for d in DIRS:
    for s in STEMS:
        for e in EXTS:
            p = d + s + e
            for tag, ar in (("PT", PT), ("SD", SD), ("BD", BD)):
                if ar.has(p):
                    hits.append((p, tag))
                    break

print("hits:", hits or "none")


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def frame_image(f):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    px = im.load()
    src = f["px"]
    for y in range(f["h"]):
        base = y * f["w"]
        for x in range(f["w"]):
            v = src[base + x]
            if v != 255:
                px[x, y] = PAL[v] + (255,)
    return im


for p, tag in hits:
    r = load(p)
    if r is None or not r[0]:
        print(p, tag, "empty")
        continue
    frames, mw, mh = r
    im = frame_image(frames[0])
    sc = min(240 / max(1, mw), 240 / max(1, mh), 3.0)
    if sc != 1.0:
        im = im.resize((max(1, int(mw * sc)), max(1, int(mh * sc))), Image.NEAREST)
    name = os.path.basename(p).replace(".grp", "")
    im.save(os.path.join(OUT, "obs_%s_%s.png" % (tag, name)))
    print("%-34s %s %dx%d frames=%d" % (p, tag, mw, mh, len(frames)))
