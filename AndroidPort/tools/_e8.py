"""Batch E probe 8: dump glue\\Score{P,T,Z}{d,v}\\pMain.pcx (real names) and look
for race emblems. Also renders a 6-up sheet."""
import os, sys
from PIL import Image

sys.path.insert(0, ".")
import sc_archive
import pipeline_sounds as ps

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

FILES = []
for race in ("P", "T", "Z"):
    for suf in ("d", "v"):
        for base in ("pMain.pcx", "pInset.pcx", "scorebox.pcx", "untab.pcx", "tminimap.pcx"):
            FILES.append("glue\\Score%s%s\\%s" % (race, suf, base))

imgs = []
for p in FILES:
    arc = SD if SD.has(p) else (BD if BD.has(p) else None)
    if arc is None:
        print("MISS %s" % p)
        continue
    data = arc.read(p)
    px, pal, w, h = ps.pcx_decode(data)
    im = Image.new("RGB", (w, h))
    im.putdata(px)
    tag = p.replace("glue\\", "").replace("\\", "_").replace(".pcx", "")
    im.save(os.path.join(OUT, "_e8_%s.png" % tag))
    print("%-32s %3dx%-4d %6dB" % (p, w, h, len(data)))
    imgs.append((tag, im))

# 6-up sheet of the pMain only, scaled 2x
pm = [t for t in imgs if t[0].endswith("pMain")]
if pm:
    W = max(i.width for _, i in pm)
    H = max(i.height for _, i in pm)
    sheet = Image.new("RGB", (W * 3, H * 2), (20, 20, 24))
    for k, (tag, im) in enumerate(pm):
        sheet.paste(im, ((k % 3) * W, (k // 3) * H))
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
    sheet.save(os.path.join(OUT, "_e8_pmain_sheet.png"))
    print("sheet %s" % (sheet.size,))
