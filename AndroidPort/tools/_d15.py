"""Batch D probe 15: doodads. Scenario.chk says the graphical part of a doodad
lives in MTXM (the tile itself), and DD2 is editor-only. So doodads should
already appear in the rebuilt terrain. Verify by locating every CV5 type-1
(doodad) tile on each map, reporting its group index (pre-remaster doodads sit
at 1024+), its flags/overlay, and cropping a zoom so the artwork is visible.
"""
import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
from PIL import Image

ASSETS = os.path.join(pm.ROOT, r"AndroidPort\app\app\src\main\assets\maps")
SRC = {m: s for s, m, _n in pm.MAPS}

for mid in sorted(os.listdir(ASSETS)):
    if not os.path.isdir(os.path.join(ASSETS, mid)):
        continue
    meta = pm.json.load(open(os.path.join(ASSETS, mid, "meta.json"), encoding="utf8"))
    w, h, tsname = meta["w"], meta["h"], meta["tileset"]
    T = pm.load_tileset(tsname)
    chk, gaps = pm.read_chk(os.path.join(pm.ROOT, SRC[mid]))
    g, sec = pm.parse_chk(chk, gaps)
    mo, _ = sec[b"MTXM"]
    dd = collections.Counter()
    grps = collections.Counter()
    tiles = []
    for i in range(w * h):
        v = g.u16(mo + i * 2)
        grp = (v & 0x7FF0) >> 4
        var = v & 0xF
        if grp < len(T["cv5_type"]) and T["cv5_type"][grp] == 1:
            dd[(i % w, i // w)] = var
            grps[grp] += 1
            tiles.append((i % w, i // w, grp, var))
    print("%-12s %-9s doodad-tiles=%-4d distinct-groups=%-3d group-range=%s" % (
        mid, tsname, len(tiles), len(grps),
        (min(grps), max(grps)) if grps else None))
    if tiles:
        # decode the CV5 doodad record for the first group seen
        grp = sorted(grps)[0]
        rec = [T["cv5_tiles"][grp][k] for k in range(16)]
        print("       grp %d @20 tiles=%s" % (grp, rec))
        print("       first 6 tiles (tx,ty,grp,var) = %s" % (tiles[:6],))

# crop a doodad-heavy patch of hunters and divide for eyeballing
for mid, box in (("hunters", (1400, 1400, 2000, 2000)),
                 ("divide", (300, 100, 900, 700))):
    d = os.path.join(ASSETS, mid)
    meta = pm.json.load(open(os.path.join(d, "meta.json"), encoding="utf8"))
    w, h = meta["w"], meta["h"]
    img = Image.new("RGB", (w * 32, h * 32))
    for f in os.listdir(d):
        if f.startswith("c_") and f.endswith(".png"):
            cx, cy = f[2:-4].split("_")
            img.paste(Image.open(os.path.join(d, f)), (int(cx) * 512, int(cy) * 512))
    img.crop(box).resize(((box[2] - box[0]) * 2, (box[3] - box[1]) * 2),
                         Image.NEAREST).save("_d15_%s.png" % mid)
    print("saved _d15_%s.png %s" % (mid, box))
