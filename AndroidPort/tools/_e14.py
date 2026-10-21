"""Batch E probe 14: zoom the top-left corner of all six race score panels at 6x.
That corner is the only place a race emblem could hide in this chrome."""
import os, sys
from PIL import Image

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"

C = 90
Z = 6
keys = ["ScorePv", "ScoreTv", "ScoreZv", "ScorePd", "ScoreTd", "ScoreZd"]
sheet = Image.new("RGB", (C * Z * 3, C * Z * 2), (0, 0, 0))
for k, key in enumerate(keys):
    im = Image.open(os.path.join(OUT, "_e11_%s.png" % key)).convert("RGB")
    im = im.crop((0, 0, C, C)).resize((C * Z, C * Z), Image.NEAREST)
    sheet.paste(im, ((k % 3) * C * Z, (k // 3) * C * Z))
sheet.save(os.path.join(OUT, "_e14_corners6x.png"))
print("sheet %s  order=%s" % (sheet.size, keys))
