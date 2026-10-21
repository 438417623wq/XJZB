"""Batch E probe 11: render the six race score panels with the CORRECT palette
(_e8 rendered raw indices as grey -- that is why they looked like red wireframe)
and diff them to see whether the race identity shows up anywhere."""
import os, sys
from PIL import Image, ImageChops

sys.path.insert(0, ".")
import sc_archive
import pipeline_score as psc

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

panels = {}
for race in ("P", "T", "Z"):
    for suf in ("d", "v"):
        key = "Score%s%s" % (race, suf)
        p = "glue\\%s\\pMain.pcx" % key
        arc = SD if SD.has(p) else BD
        data, _ = arc.read_with_gaps(p)
        px, pal, w, h = psc.pcx_decode(data)
        lut = [(pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2]) for i in range(256)]
        im = Image.new("RGB", (w, h))
        im.putdata([lut[v] for v in px])
        im.save(os.path.join(OUT, "_e11_%s.png" % key))
        panels[key] = im
        print("%-8s %dx%d" % (key, w, h))

sheet = Image.new("RGB", (640 * 3, 480 * 2), (0, 0, 0))
for k, key in enumerate(("ScorePv", "ScoreTv", "ScoreZv", "ScorePd", "ScoreTd", "ScoreZd")):
    sheet.paste(panels[key], ((k % 3) * 640, (k // 3) * 480))
sheet.save(os.path.join(OUT, "_e11_sheet.png"))

# where do the panels differ? bounding box of the pixel diff per pair
print()
base = panels["ScoreTv"]
for key in ("ScorePv", "ScoreZv"):
    d = ImageChops.difference(base, panels[key])
    print("%s vs ScoreTv  bbox=%s  nonzero=%d" % (
        key, d.getbbox(), sum(1 for v in d.convert("L").getdata() if v)))
# victory vs defeat within one race
for race in ("P", "T", "Z"):
    a = panels["Score%sv" % race]
    b = panels["Score%sd" % race]
    d = ImageChops.difference(a, b)
    print("Score%sv vs Score%sd  bbox=%s  nonzero=%d" % (
        race, race, d.getbbox(), sum(1 for v in d.convert("L").getdata() if v)))
