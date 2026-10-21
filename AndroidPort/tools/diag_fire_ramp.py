"""Find the fire ramp in the unit palette and test index offsets for effects.

StarCraft draws muzzle flashes / explosions as fire. If the effect GRP indices
are offset relative to the palette's fire ramp, a constant shift should turn
them orange. This searches for that shift instead of guessing.
"""
import os
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def pal(ts):
    for ar in (SD, BD):
        p = "tileset\\%s.wpe" % ts
        if ar.has(p):
            w, _ = ar.read_with_gaps(p)
            if len(w) < 1024:
                w += bytes(1024 - len(w))
            return [(w[i * 4 + 2], w[i * 4 + 1], w[i * 4]) for i in range(256)]
    return None


P = pal("jungle")
print("=== fire-coloured indices in jungle.wpe (warm, bright) ===")
fire = []
for i in range(256):
    r, g, b = P[i]
    if r > 120 and r >= g > b and r - b > 40:
        fire.append((i, (r, g, b)))
for i, c in fire:
    print("  idx %3d %s" % (i, c))

print("\n=== grey/white ramp indices (bright, low saturation) ===")
for i in range(256):
    r, g, b = P[i]
    mx, mn = max(r, g, b), min(r, g, b)
    if mx > 180 and mx - mn < 25:
        print("  idx %3d %s" % (i, (r, g, b)))

# structure of one flash frame
r = load(r"unit\thingy\tmeFlshS.grp")
frames, mw, mh = r
peak = max(frames, key=lambda f: sum(1 for v in f["px"] if v != 255))
print("\n=== peak flash frame %dx%d index grid ===" % (peak["w"], peak["h"]))
for y in range(peak["h"]):
    row = []
    for x in range(peak["w"]):
        v = peak["px"][y * peak["w"] + x]
        row.append(".." if v == 255 else "%02x" % v)
    print("   " + " ".join(row))
