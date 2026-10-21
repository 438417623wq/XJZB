"""Batch E probe 13: last three emblem candidates.
 (a) zoom the iScore.grp glyph grid 4x -- are any of the 54 glyphs a race emblem?
 (b) crop the top-left 150x150 of all six pMain panels at 3x
 (c) decode glue\\PalMm\\Retail_Ex.pcx + glue\\Battle.net\\Backgrounds\\ProfileExp.pcx
"""
import os, sys
from PIL import Image

sys.path.insert(0, ".")
import sc_archive
import pipeline_score as psc

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

# (a) iscore grid zoom
isc = Image.open(os.path.join(ROOT, r"AndroidPort\app\app\src\main\assets\ui\score\iscore.webp"))
isc.convert("RGB").resize((isc.width * 4, isc.height * 4), Image.NEAREST).save(
    os.path.join(OUT, "_e13_iscore4x.png"))
print("iscore %s -> 4x" % (isc.size,))

# (b) top-left crops
crops = []
for race in ("P", "T", "Z"):
    for suf in ("d", "v"):
        p = os.path.join(OUT, "_e11_Score%s%s.png" % (race, suf))
        im = Image.open(p).crop((0, 0, 150, 150)).resize((300, 300), Image.NEAREST)
        crops.append((race + suf, im))
sheet = Image.new("RGB", (300 * 3, 300 * 2), (0, 0, 0))
for k, (tag, im) in enumerate(crops):
    sheet.paste(im, ((k % 3) * 300, (k // 3) * 300))
sheet.save(os.path.join(OUT, "_e13_corners.png"))
print("corners sheet written")

# (c) the two remaining PCX
for p, out in (("glue\\PalMm\\Retail_Ex.pcx", "_e13_retailex"),
               ("glue\\Battle.net\\Backgrounds\\ProfileExp.pcx", "_e13_profileexp"),
               ("glue\\title\\Title.pcx", "_e13_title")):
    arc = SD if SD.has(p) else (BD if BD.has(p) else None)
    if arc is None:
        print("MISS %s" % p)
        continue
    data, _ = arc.read_with_gaps(p)
    r = psc.pcx_decode(data)
    if r is None:
        print("SKIP %s (not 8bpp)" % p)
        continue
    px, pal, w, h = r
    lut = [(pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2]) for i in range(256)]
    im = Image.new("RGB", (w, h))
    im.putdata([lut[v] for v in px])
    im.save(os.path.join(OUT, out + ".png"))
    print("%-40s %dx%d" % (p, w, h))
