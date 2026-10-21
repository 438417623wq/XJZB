"""Objective palette-order test using the six tilesets.

StarCraft tilesets have canonical appearances:
  badlands  brown/tan dirt       platform  grey space
  jungle    dark green           desert    tan sand
  ice       white/pale blue      twilight  dark purple/blue

For each tileset, average the palette (weighted toward the entries terrain
actually uses) under both channel orders and classify the hue. The order that
reproduces the canonical set for all six is the correct one.
"""
import os
import colorsys
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

CANON = {
    "badlands": "brown/tan", "platform": "grey", "jungle": "dark green",
    "desert": "tan", "ice": "pale blue/white", "twilight": "dark purple",
}


def wpe(ts):
    for ar in (SD, BD):
        p = "tileset\\%s.wpe" % ts
        if ar.has(p):
            w, _ = ar.read_with_gaps(p)
            if len(w) < 1024:
                w += bytes(1024 - len(w))
            return w
    return None


def classify(pal):
    """Average hue/sat/val over mid-brightness entries."""
    hs, ss, vs = [], [], []
    for (r, g, b) in pal:
        v = max(r, g, b) / 255.0
        if v < 0.25:            # skip near-black
            continue
        h, s, vv = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        hs.append(h * 360)
        ss.append(s)
        vs.append(vv)
    if not hs:
        return (0, 0, 0)
    # circular mean of hue
    import math
    sx = sum(math.cos(math.radians(h)) for h in hs)
    sy = sum(math.sin(math.radians(h)) for h in hs)
    hue = math.degrees(math.atan2(sy, sx)) % 360
    return (hue, sum(ss) / len(ss), sum(vs) / len(vs))


def name_hue(h, s, v):
    if s < 0.18:
        return "grey"
    if h < 20 or h >= 340:
        return "red"
    if h < 45:
        return "brown/orange"
    if h < 70:
        return "yellow/tan"
    if h < 160:
        return "green"
    if h < 200:
        return "cyan"
    if h < 260:
        return "blue"
    return "purple"


print("%-10s %-16s | %-34s | %-34s" % ("tileset", "canonical", "BGR", "RGB"))
print("-" * 104)
for ts in ("badlands", "platform", "jungle", "desert", "ice", "twilight"):
    w = wpe(ts)
    if w is None:
        print("%-10s MISS" % ts); continue
    bgr = [(w[i * 4 + 2], w[i * 4 + 1], w[i * 4]) for i in range(256)]
    rgb = [(w[i * 4], w[i * 4 + 1], w[i * 4 + 2]) for i in range(256)]
    out = []
    for nm, pal in (("BGR", bgr), ("RGB", rgb)):
        h, s, v = classify(pal)
        out.append("%-12s h=%3.0f s=%.2f v=%.2f" % (name_hue(h, s, v), h, s, v))
    print("%-10s %-16s | %-34s | %-34s" % (ts, CANON[ts], out[0], out[1]))
