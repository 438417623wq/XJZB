"""Combined check: (a) which tileset files exist, (b) each map's ERA byte,
(c) high-zoom render of canonical-colour assets under both channel orders.

Canonical StarCraft colours used as ground truth:
  mineral field = BLUE/cyan crystals
  explosion     = ORANGE fire
  Terran marine = blue-grey armour, tan face
"""
import os
from PIL import Image, ImageDraw
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

print("=== (a) tileset wpe files present ===")
for ar, nm in ((SD, "StarDat"), (BD, "BrooDat")):
    for ts in ("badlands", "platform", "install", "ashworld", "jungle",
               "desert", "ice", "twilight"):
        p = "tileset\\%s.wpe" % ts
        if ar.has(p):
            print("  %s %s" % (nm, p))

print("\n=== (b) ERA byte per map ===")
import pipeline_maps as pm

for src, mid, name in pm.MAPS:
    try:
        r = pm.read_chk(os.path.join(pm.ROOT, src))
        if not r:
            print("  %-12s read-fail" % mid); continue
        chk, gaps = r
        g, sec = pm.parse_chk(chk, gaps)
        if b"ERA " not in sec:
            print("  %-12s no ERA" % mid); continue
        off, _ = sec[b"ERA "]
        era = g.byte(off)
        print("  %-12s ERA=%d -> pipeline reads '%s' (std name for %d is %s)"
              % (mid, era, pm.TILESETS.get(era, "?"), era,
                 {0: "badlands", 1: "platform", 2: "install", 3: "ashworld",
                  4: "jungle", 5: "desert", 6: "ice", 7: "twilight"}.get(era, "?")))
    except Exception as e:
        print("  %-12s err %s" % (mid, e))

# --- (c) high zoom palette comparison
wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
if len(wpe) < 1024:
    wpe += bytes(1024 - len(wpe))
BGR = [(wpe[i * 4 + 2], wpe[i * 4 + 1], wpe[i * 4]) for i in range(256)]
RGB = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def fimg(f, pal):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    p = im.load()
    for y in range(f["h"]):
        for x in range(f["w"]):
            o = y * f["w"] + x
            if o < len(f["px"]) and f["px"][o] != 255:
                p[x, y] = pal[f["px"][o]] + (255,)
    return im


mineral = load(r"unit\neutral\min01.grp")
marine = load(r"unit\terran\marine.grp")
bang = load(r"unit\thingy\tBangL.grp")
flsh = load(r"unit\thingy\tmeFlshS.grp")

ITEMS = [
    ("mineral (must be BLUE)", mineral[0][0]),
    ("marine f0", marine[0][0]),
    ("marine f17", marine[0][17]),
    ("bangL mid (must be ORANGE)", bang[0][len(bang[0]) // 2]),
    ("flshS peak (must be ORANGE)",
     max(flsh[0], key=lambda f: sum(1 for v in f["px"] if v != 255))),
]

sc = 5
rows = [("BGR (shipped)", BGR), ("RGB (raw order)", RGB)]
W = sum(f["w"] * sc + 10 for _, f in ITEMS) + 12
H = sum(max(f["h"] for _, f in ITEMS) * sc + 44 for _ in rows) + 8
canvas = Image.new("RGB", (max(W, 1100), H), (26, 28, 36))
d = ImageDraw.Draw(canvas)
y = 4
for nm, pal in rows:
    d.text((4, y), nm, fill=(120, 255, 140)); y += 16
    x = 4
    for label, f in ITEMS:
        im = fimg(f, pal)
        big = im.resize((im.width * sc, im.height * sc), Image.NEAREST)
        canvas.paste(big, (x, y), big)
        d.text((x, y + big.height + 2), label, fill=(200, 210, 230))
        x += big.width + 10
    y += max(f["h"] for _, f in ITEMS) * sc + 44
canvas.save(os.path.join(OUT, "palette_final.png"))
print("\nwrote palette_final.png", canvas.size)
