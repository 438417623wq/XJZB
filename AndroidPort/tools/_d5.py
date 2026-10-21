"""Batch D probe 5: raw bytes of the zero-tile platform CV5 groups, plus a
census of every group in each tileset whose u16[16] tile array is all zero.
Also tests the wiki VX4 bit layout (bit0 = flip, bits 15..1 = VR4 id) against
the pipeline's (bit15 = flip, bits 14..0 = id).
"""
import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
from gapio import GapReader


def rd(ts, ext):
    for ar in (pm.SD, pm.BD):
        p = "tileset\\%s.%s" % (ts, ext)
        if ar.has(p):
            return ar.read_with_gaps(p)
    return None, None


for ts in ("platform", "jungle", "badlands", "ashworld", "install"):
    d, gaps = rd(ts, "cv5")
    full = len(d) + sum(s for _, s in (gaps or []))
    cv = GapReader(d, gaps or [])
    n = full // 52
    zero = [m for m in range(n) if all(cv.u16(m * 52 + 20 + k * 2) == 0 for k in range(16))]
    zt = collections.Counter(cv.u16(m * 52) for m in zero)
    print("%-9s groups=%d zero-tile=%d types=%s" % (ts, n, len(zero), dict(zt)))
    if ts == "platform":
        for m in (0, 1, 2, 3, 4):
            b = m * 52
            print("   grp %d raw=%s" % (m, [cv.u16(b + k * 2) for k in range(26)]))
        # any gap overlapping group 2/3?
        for gp, gs in (gaps or []):
            if gp < 260:
                print("   gap at %d size %d overlaps low groups" % (gp, gs))

# VX4 bit layout check on platform
d, gaps = rd("platform", "vx4")
vx = GapReader(d, gaps or [])
print("vx4 platform n=%d" % ((len(d) + sum(s for _, s in (gaps or []))) // 32))
for m in (0, 1, 2, 3, 100):
    raw = [vx.u16(m * 32 + k * 2) for k in range(16)]
    print("  vx4[%d] raw=%s" % (m, raw))
    print("     pipeline vri=%s flip=%s" % ([e & 0x7FFF for e in raw], [(e >> 15) & 1 for e in raw]))
    print("     wiki     vri=%s flip=%s" % ([e >> 1 for e in raw], [e & 1 for e in raw]))
