"""Check which shift the calibration picks for SCV frames, and render f12 alone."""
import sc_archive
from PIL import Image
import grp as grpm

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\SCV.grp")

for fi in (9, 10, 11, 12, 14, 16):
    base = 6 + fi * 8
    w, h = d[base + 2], d[base + 3]
    off = int.from_bytes(d[base + 4:base + 8], "little")
    lo = [int.from_bytes(d[off + i * 2:off + i * 2 + 2], "little") for i in range(h)]
    scores = {}
    for shift in range(-6, 7):
        scores[shift] = grpm._score_base(d, off, lo, h, w, len(d), shift)
    best = max(scores, key=scores.get)
    print("f%02d (w=%d h=%d off=%d): best shift=%+d score=%d/%d  all=%s"
          % (fi, w, h, off, best, scores[best], h - 1,
             {k: v for k, v in sorted(scores.items()) if v > 0}))
