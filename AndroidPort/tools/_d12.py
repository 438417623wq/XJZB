"""Batch D probe 12: is divide's disconnection real (cliffs) or a ramp-decode
bug? Crop the terrain+region overlay around two region boundaries at high zoom,
and histogram the VF4 flag words actually used by the map.
"""
import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
from PIL import Image
from gapio import GapReader

d = os.path.join(pm.ROOT, r"AndroidPort\app\app\src\main\assets\maps\divide")
meta = pm.json.load(open(os.path.join(d, "meta.json"), encoding="utf8"))
w, h = meta["w"], meta["h"]

chk, gaps = pm.read_chk(os.path.join(pm.ROOT, r"maps\(2)The Small Divide.scm"))
g, sec = pm.parse_chk(chk, gaps)
mo, _ = sec[b"MTXM"]
vals = [g.u16(mo + i * 2) for i in range(w * h)]
T = pm.load_tileset("jungle")
flaghist = collections.Counter()
typehist = collections.Counter()
grpused = collections.Counter()
for v in vals:
    grp = (v & 0x7FF0) >> 4
    var = v & 0xF
    grpused[grp] += 1
    if grp < len(T["cv5_type"]):
        typehist[T["cv5_type"][grp]] += 1
    vx4m = T["cv5_tiles"][grp][var] if grp < len(T["cv5_tiles"]) else 0
    if vx4m < len(T["vf4_flags"]):
        for fl in T["vf4_flags"][vx4m]:
            flaghist[fl] += 1
print("divide CV5 terrain-type histogram:", dict(typehist.most_common(12)))
print("divide VF4 flag-word histogram (top 20):")
for fl, c in flaghist.most_common(20):
    print("    0x%04X  x%-6d walkable=%d mid=%d high=%d blocksview=%d ramp=%d" % (
        fl, c, fl & 1, (fl >> 1) & 1, (fl >> 2) & 1, (fl >> 3) & 1, (fl >> 4) & 1))
ramp_only = sum(c for fl, c in flaghist.items() if (fl & 0x10) and not (fl & 1))
print("ramp-flagged but NOT walkable minitiles: %d" % ramp_only)

ov = Image.open("_d11_divide_overlay.png")
for name, box in (("a", (100, 550, 700, 1150)), ("b", (900, 100, 1500, 700))):
    ov.crop(box).resize(((box[2] - box[0]) * 2, (box[3] - box[1]) * 2),
                        Image.NEAREST).save("_d12_zoom_%s.png" % name)
    print("saved _d12_zoom_%s.png %s" % (name, box))
