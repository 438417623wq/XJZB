"""v2.10 pre-flight probe: protoss unit GRP block structure + protoss voice list.

Answers two questions before pipeline_sprites.py is extended:
  1. how many 17-direction blocks does each protoss unit GRP actually hold
     (walk / attack), so UNITS entries get real attack blocks instead of
     duplicated walk blocks;
  2. which protoss voice wavs exist in the repack (expand only pulled corsair
     and dark archon), so batch A units get real voices instead of silence.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

UNITS = [
    ("probe", "unit\\protoss\\probe.grp"),
    ("zealot", "unit\\protoss\\zealot.grp"),
    ("dragoon", "unit\\protoss\\dragoon.grp"),
    ("templar", "unit\\protoss\\templar.grp"),
    ("dtemplar", "unit\\protoss\\dtemplar.grp"),
    ("archon", "unit\\protoss\\archon.grp"),
    ("darchon", "unit\\protoss\\darchn.grp"),
    ("shuttle", "unit\\protoss\\shuttle.grp"),
    ("scout", "unit\\protoss\\scout.grp"),
    ("arbiter", "unit\\protoss\\arbiter.grp"),
    ("carrier", "unit\\protoss\\carrier.grp"),
    ("intercep", "unit\\protoss\\Intercep.grp"),
    ("reaver", "unit\\protoss\\trilob.grp"),
    ("observer", "unit\\protoss\\witness.grp"),
    ("corsair", "unit\\protoss\\corsair.grp"),
]

BUILDINGS = [
    ("nexus", "unit\\protoss\\nexus.grp"),
    ("pylon", "unit\\protoss\\pylon.grp"),
    ("assim", "unit\\protoss\\assim.grp"),
    ("gateway", "unit\\protoss\\gateway.grp"),
    ("forge", "unit\\protoss\\forge.grp"),
    ("photon", "unit\\protoss\\photon.grp"),
    ("gencore", "unit\\protoss\\gencore.grp"),
    ("citadel", "unit\\protoss\\citadel.grp"),
    ("robotic", "unit\\protoss\\robotic.grp"),
    ("archives", "unit\\protoss\\archives.grp"),
    ("stargate", "unit\\protoss\\stargate.grp"),
    ("beacon", "unit\\protoss\\beacon.grp"),
    ("sbattery", "unit\\protoss\\sbattery.grp"),
    ("supportbay", "unit\\protoss\\prism.grp"),
    ("tribunal", "unit\\protoss\\warp.grp"),
    ("observatory", "unit\\protoss\\texture.grp"),
]

EFFECTS = [
    ("psistorm", "unit\\thingy\\psiStorm.grp"),
    ("pshield", "unit\\thingy\\pshield.grp"),
    ("b_pspark", "unit\\bullet\\pspark.grp"),
    ("pcirglow", "unit\\protoss\\pCirGlow.grp"),
]


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps), ar
    return None, None


def main():
    print("=== units: 17-direction block structure ===")
    for name, path in UNITS:
        r, ar = load(path)
        if r is None:
            print("%-10s MISS %s" % (name, path))
            continue
        frames, mw, mh = r
        n = len(frames)
        blocks = n / 17.0
        # frame sizes tell walk (small) from attack (often wider) blocks apart
        sizes = []
        for b in range(int(n // 17) + 1):
            lo, hi = b * 17, min(b * 17 + 17, n)
            if lo >= n:
                break
            w = max(frames[i]["w"] for i in range(lo, hi))
            h = max(frames[i]["h"] for i in range(lo, hi))
            sizes.append("b%d:%dx%d(%d)" % (b, w, h, hi - lo))
        print("%-10s n=%-4d blocks=%-6s cell=%dx%d  %s  [%s]"
              % (name, n, ("%.2f" % blocks), mw, mh, " ".join(sizes),
                 os.path.basename(ar.path)))
    print()
    print("=== buildings ===")
    for name, path in BUILDINGS:
        r, ar = load(path)
        if r is None:
            print("%-12s MISS %s" % (name, path))
            continue
        frames, mw, mh = r
        print("%-12s n=%-3d cell=%dx%d [%s]" % (name, len(frames), mw, mh,
                                                os.path.basename(ar.path)))
    print()
    print("=== effects ===")
    for name, path in EFFECTS:
        r, ar = load(path)
        if r is None:
            print("%-10s MISS %s" % (name, path))
            continue
        frames, mw, mh = r
        print("%-10s n=%-3d cell=%dx%d [%s]" % (name, len(frames), mw, mh,
                                                os.path.basename(ar.path)))
    print()
    print("=== protoss sounds present in the repack ===")
    # sfxdata.tbl gives the canonical voice paths; listfile gives the rest
    for ar, tag in ((SD, "StarDat"), (BD, "BrooDat")):
        try:
            names = ar.listfile()
        except Exception as ex:
            print(tag, "listfile FAIL", ex)
            continue
        hits = sorted({n for n in names
                       if re.search(r"sound[\\/]protoss", n, re.I)
                       and n.lower().endswith(".wav")})
        print("-- %s: %d protoss wavs" % (tag, len(hits)))
        for h in hits:
            print("   ", h)


main()
