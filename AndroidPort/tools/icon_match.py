"""Data-driven cmdicons index resolution.

Instead of guessing indices, match each unit's own GRP frame 0 silhouette
against every frame of cmdicons.grp and report the best-scoring candidates.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import sc_archive
import grp as grpm
from PIL import Image

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
BD = sc_archive.Archive(r"F:\KF\XJZB\BrooDat.mpq")
PT = sc_archive.Archive(r"F:\KF\XJZB\patch_rt.mpq")


def find_archive(path):
    for a in (PT, SD, BD):
        if a.has(path):
            return a
    return None


def silhouette_from_frames(frames, size=32):
    """Union of all frames -> binary mask, aspect-preserved into size x size."""
    minx = min(f["x"] for f in frames)
    miny = min(f["y"] for f in frames)
    maxx = max(f["x"] + f["w"] for f in frames)
    maxy = max(f["y"] + f["h"] for f in frames)
    w, h = maxx - minx, maxy - miny
    m = Image.new("L", (w, h), 0)
    px = m.load()
    for f in frames:
        for y in range(f["h"]):
            for x in range(f["w"]):
                if f["px"][y * f["w"] + x] != 255:
                    px[f["x"] - minx + x, f["y"] - miny + y] = 255
    # aspect-preserving fit into size x size
    sc = min(size / w, size / h)
    nw, nh = max(1, int(round(w * sc))), max(1, int(round(h * sc)))
    m = m.resize((nw, nh), Image.BILINEAR)
    out = Image.new("L", (size, size), 0)
    out.paste(m, ((size - nw) // 2, (size - nh) // 2))
    return out


def load_grp(path):
    a = find_archive(path)
    if a is None:
        return None
    data, gaps = a.read_with_gaps(path)
    return grpm.decode_grp(data, gaps)


def mask_of(f):
    m = Image.new("L", (f["w"], f["h"]), 0)
    px = m.load()
    for y in range(f["h"]):
        for x in range(f["w"]):
            if f["px"][y * f["w"] + x] != 255:
                px[x, y] = 255
    return m


def fit(m, size=32):
    w, h = m.size
    sc = min(size / w, size / h)
    nw, nh = max(1, int(round(w * sc))), max(1, int(round(h * sc)))
    m = m.resize((nw, nh), Image.BILINEAR)
    out = Image.new("L", (size, size), 0)
    out.paste(m, ((size - nw) // 2, (size - nh) // 2))
    return out


def iou(a, b):
    pa, pb = a.load(), b.load()
    inter = union = 0
    for y in range(a.height):
        for x in range(a.width):
            va, vb = pa[x, y] > 96, pb[x, y] > 96
            if va or vb:
                union += 1
                if va and vb:
                    inter += 1
    return inter / union if union else 0.0


def main():
    ci_data, ci_gaps = SD.read_with_gaps("unit\\cmdbtns\\cmdicons.grp")
    icons, ciw, cih = grpm.decode_grp(ci_data, ci_gaps)
    icon_masks = [fit(mask_of(f)) for f in icons]
    print("cmdicons frames:", len(icons), "cell", ciw, cih)

    TARGETS = {
        "scv": "unit\\terran\\SCV.grp",
        "marine": "unit\\terran\\marine.grp",
        "firebat": "unit\\terran\\firebat.grp",
        "vulture": "unit\\terran\\Vulture.grp",
        "tank": "unit\\terran\\tank.grp",
        "goliath": "unit\\terran\\goliath.grp",
        "wraith": "unit\\terran\\wessel.grp",
        "dropship": "unit\\terran\\dropship.grp",
        "battlecruiser": "unit\\terran\\BattleCr.grp",
        "ghost": "unit\\terran\\ghost.grp",
        "depot": "unit\\terran\\Depot.grp",
        "barracks": "unit\\terran\\TBarrack.grp",
        "refinery": "unit\\terran\\refinery.grp",
        "factory": "unit\\terran\\factory.grp",
        "turret": "unit\\terran\\missile.grp",
        "bunker": "unit\\terran\\PillBox.grp",
        "starport": "unit\\terran\\starport.grp",
        "academy": "unit\\terran\\Academy.grp",
        "cc": "unit\\terran\\control.grp",
        "science": "unit\\terran\\Science.grp",
        "armory": "unit\\terran\\Armory.grp",
        "engbay": "unit\\terran\\engbay.grp",
        "comsat": "unit\\terran\\comsat.grp",
        "machine": "unit\\terran\\machine.grp",
        "zergling": "unit\\zerg\\zergling.grp",
        "hydra": "unit\\zerg\\hydra.grp",
        "muta": "unit\\zerg\\mutalid.grp",
        "drone": "unit\\zerg\\drone.grp",
        "hatchery": "unit\\zerg\\hatchery.grp",
        "pool": "unit\\zerg\\Snakey.grp",
        "sunken": "unit\\zerg\\fcolony.grp",
        "overlord": "unit\\zerg\\overlord.grp",
    }

    results = {}
    for key, path in TARGETS.items():
        r = load_grp(path)
        if r is None:
            print("%-14s MISSING %s" % (key, path))
            continue
        frames, mw, mh = r
        tgt = silhouette_from_frames(frames[:1])
        scores = [(iou(tgt, im), i) for i, im in enumerate(icon_masks)]
        scores.sort(reverse=True)
        results[key] = scores[:5]
        print("%-14s top5: %s" % (key, ", ".join("#%d=%.3f" % (i, s) for s, i in scores[:5])))

    return results


if __name__ == "__main__":
    main()
