"""Batch E probe: what accent colour does each race's score panel actually use?

The plan's Battle.net race emblems do not exist in this repack (see _e14), so
the race row has to be re-styled from something real. The score panels are the
only per-race chrome that survives, so pull their dominant non-background
colours and use those as the row accent.
"""
import os
from collections import Counter
from PIL import Image

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"

for key in ["ScoreTv", "ScoreZv", "ScorePv", "ScorePd", "ScoreTd", "ScoreZd"]:
    im = Image.open(os.path.join(OUT, "_e11_%s.png" % key)).convert("RGB")
    px = list(im.getdata())
    cnt = Counter(px)
    tot = len(px)
    # background = whatever owns the panel body; drop the darkest half so the
    # accent survives, then rank by luminance-weighted frequency
    ranked = []
    for c, n in cnt.most_common(400):
        r, g, b = c
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        sat = max(c) - min(c)
        if lum < 24 and sat < 24:
            continue
        ranked.append((n, c, lum, sat))
        if len(ranked) >= 5:
            break
    print("%-8s total=%d" % (key, tot))
    for n, c, lum, sat in ranked:
        print("    %6d  rgb%-16s lum=%5.1f sat=%3d  %5.2f%%"
              % (n, c, lum, sat, 100.0 * n / tot))
