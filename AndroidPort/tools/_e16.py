"""Batch E probe: find the per-race accent in the three panels whose body is
near-black. _e15 showed ScoreTv=orange and ScoreZd=green outright; the other
four need a lower frequency threshold to reveal their accent hue."""
import os
from collections import Counter
from PIL import Image

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"

for key in ["ScorePv", "ScorePd", "ScoreTv", "ScoreTd", "ScoreZv", "ScoreZd"]:
    im = Image.open(os.path.join(OUT, "_e11_%s.png" % key)).convert("RGB")
    cnt = Counter(im.getdata())
    tot = sum(cnt.values())
    print("%-8s" % key)
    shown = 0
    for c, n in cnt.most_common(60):
        r, g, b = c
        sat = max(c) - min(c)
        if sat < 40:
            continue
        print("    %6d  rgb%-16s sat=%3d  %5.2f%%" % (n, c, sat, 100.0 * n / tot))
        shown += 1
        if shown >= 6:
            break
