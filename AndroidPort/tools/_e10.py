"""Batch E probe 10: let Pillow decode the score PCX files (ground truth vs my
own pcx_decode) and dump the palette that actually applies."""
import os, sys, tempfile
from PIL import Image

sys.path.insert(0, ".")
import sc_archive

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

for p in ("glue\\ScoreTv\\pMain.pcx", "glue\\ScoreZv\\pMain.pcx",
          "glue\\ScorePv\\pMain.pcx", "glue\\ScoreTv\\pInset.pcx"):
    arc = SD if SD.has(p) else BD
    d = arc.read(p)
    tmp = os.path.join(tempfile.gettempdir(), "e10.pcx")
    with open(tmp, "wb") as f:
        f.write(d)
    im = Image.open(tmp)
    im.load()
    tag = p.replace("glue\\", "").replace("\\", "_").replace(".pcx", "")
    out = os.path.join(OUT, "_e10_%s.png" % tag)
    im.convert("RGB").save(out)
    print("%-28s %s mode=%s  -> %s" % (p, im.size, im.mode, os.path.basename(out)))
    pal = im.getpalette()
    print("     pal[0:12] = %s" % (pal[:12],))
    print("     pal[3:15] = %s" % (pal[3:15],))
