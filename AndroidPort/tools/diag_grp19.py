"""Classify all marine frames: which row-base + run-adj renders each frame cleanly.

Criterion per frame: decode ALL rows at (base, run_adj); count rows where the
ops stop at width WITHOUT overshooting (x never exceeds w mid-row) and the
consumed bytes stay within the row's table region.
"""
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")
fc = int.from_bytes(d[0:2], "little")


def score_frame(base, shift, run_adj):
    xoff, yoff, w, h = d[base], d[base + 1], d[base + 2], d[base + 3]
    off = int.from_bytes(d[base + 4:base + 8], "little")
    lo = [int.from_bytes(d[off + i * 2:off + i * 2 + 2], "little") for i in range(h)]
    good = 0
    for i in range(h):
        p = off + lo[i] + shift
        end = off + (lo[i + 1] if i + 1 < h else lo[0] + (d[base + 3] * 0) + 9999)
        x = 0
        ok = True
        while x < w:
            if p >= len(d) or p >= end + 40:
                ok = False
                break
            b = d[p]
            p += 1
            if b & 0x80:
                x += b & 0x7F
            elif b & 0x40:
                cnt = (b & 0x3F) + run_adj
                p += 1
                x += cnt
            else:
                x += b
                p += b
            if x > w:
                ok = False
                break
        if ok and x == w:
            good += 1
    return good, h


results = []
for fi in range(fc):
    base = 6 + fi * 8
    scores = {}
    for tag, shift, ra in (("A", 0, 0), ("B", -2, 1), ("C", 0, 1), ("D", -2, 0)):
        g, h = score_frame(base, shift, ra)
        scores[tag] = g / max(1, h)
    best = max(scores, key=scores.get)
    results.append((fi, best, scores))

from collections import Counter
print("best-variant counts:", Counter(r[1] for r in results))
for fi, best, scores in results[:40]:
    print("f%03d -> %s  %s" % (fi, best, {k: round(v, 2) for k, v in scores.items()}))
