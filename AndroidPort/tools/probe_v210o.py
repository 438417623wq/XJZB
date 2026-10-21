"""v2.10: locate the death block in the protoss unit GRPs numerically.

Calibration: zealot's block 13 is known (visually) to be the 7-frame blue
shatter death. The shatter frames are the only ones that are mostly bright
cyan/white, so a "bright cyan pixel fraction" per block separates death from
walk/attack without another eyeball pass.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def stats(f):
    """(fraction of bright cyan pixels, mean luminance, pixel count)"""
    cyan = lum = n = 0
    px = f["px"]
    for v in px:
        if v == 255:
            continue
        r, g, b = PAL[v]
        n += 1
        lum += (r + g + b) / 3
        if b > 200 and g > 190 and r > 130:
            cyan += 1
    if n == 0:
        return 0.0, 0.0, 0
    return cyan / n, lum / n, n


WANT = [
    ("zealot", "unit\\protoss\\zealot.grp"),
    ("dragoon", "unit\\protoss\\dragoon.grp"),
    ("templar", "unit\\protoss\\templar.grp"),
    ("dtemplar", "unit\\protoss\\dtemplar.grp"),
    ("reaver", "unit\\protoss\\trilob.grp"),
    ("scout", "unit\\protoss\\scout.grp"),
    ("corsair", "unit\\protoss\\corsair.grp"),
]

for key, path in WANT:
    r = load(path)
    if r is None:
        print("MISS", key)
        continue
    frames, mw, mh = r
    n = len(frames)
    blocks = (n + 16) // 17
    print("%s n=%d blocks=%d" % (key, n, blocks))
    for b in range(blocks):
        lo, hi = b * 17, min((b + 1) * 17, n)
        best = max(((stats(frames[i])[0], i) for i in range(lo, hi)))
        csum = sum(stats(frames[i])[0] for i in range(lo, hi)) / (hi - lo)
        lsum = sum(stats(frames[i])[1] for i in range(lo, hi)) / (hi - lo)
        psum = sum(stats(frames[i])[2] for i in range(lo, hi)) / (hi - lo)
        print("  b%-2d len=%-2d cyanAvg=%.3f cyanMax=%.3f lum=%5.1f px=%4d"
              % (b, hi - lo, csum, best[0], lsum, psum))
