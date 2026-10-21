"""v2.8 gate: resolve cmdicons indices for the new units by silhouette match.

The v2.7 plan deferred ghost/wraith (and the rest of the Terran roster) behind
one gate: verify the GRP *and* the cmdicons frame first, because v2.2 was burned
by a guessed index. probe_newunits.py answered the GRP half (all 20 decode).
This answers the icon half the same way icon_match.py did for the v2 roster:
match the unit's own GRP frame-0 silhouette against every cmdicons frame and
report the best candidates, then compare the winner with the units.dat id that
rez/stat_txt.tbl names for that unit.

Run from AndroidPort/tools:  python verify_v28_gate.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import sc_archive
import grp as grpm
from PIL import Image, ImageDraw

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

# stat_txt.tbl names straight out of tools/stat_txt.txt / assets/ui/unitnames.txt
NAMES = {
    1: "Terran Ghost", 3: "Terran Goliath", 8: "Terran Wraith",
    9: "Terran Science Vessel", 11: "Terran Dropship",
    12: "Terran Battlecruiser", 32: "Terran Firebat",
    35: "Zerg Larva", 36: "Zerg Egg", 39: "Zerg Ultralisk",
    41: "Zerg Drone", 42: "Zerg Overlord", 43: "Zerg Mutalisk",
    44: "Zerg Guardian", 45: "Zerg Queen", 46: "Zerg Defiler",
    103: "Zerg Lurker", 112: "Terran Academy", 116: "Terran Science Facility",
    123: "Terran Armory", 124: "Terran Missile Turret", 125: "Terran Bunker",
}

# key -> (expected units.dat id, sprite grp). The expected id is what
# stat_txt.tbl says; the match must independently agree with it.
CASES = {
    "ghost":         (1,   "unit\\terran\\ghost.grp"),
    "goliath":       (3,   "unit\\terran\\goliath.grp"),
    "wraith":        (8,   "unit\\terran\\phoenix.grp"),
    "science":       (9,   "unit\\terran\\wessel.grp"),
    "dropship":      (11,  "unit\\terran\\dropship.grp"),
    "battlecruiser": (12,  "unit\\terran\\BattleCr.grp"),
    "firebat":       (32,  "unit\\terran\\firebat.grp"),
    "larva":         (35,  "unit\\zerg\\larva.grp"),
    "egg":           (36,  "unit\\zerg\\egg.grp"),
    "ultra":         (39,  "unit\\zerg\\ultra.grp"),
    "overlord":      (42,  "unit\\zerg\\overlord.grp"),
    "guardian":      (44,  "unit\\zerg\\guardian.grp"),
    "queen":         (45,  "unit\\zerg\\queen.grp"),
    "defiler":       (46,  "unit\\zerg\\defiler.grp"),
    "lurker":        (103, "unit\\zerg\\Lurker.grp"),
    "academy":       (112, "unit\\terran\\Academy.grp"),
    "sciencefac":    (116, "unit\\terran\\Science.grp"),
    "armory":        (123, "unit\\terran\\Armory.grp"),
    # v2 roster, re-checked because two of them are suspected mis-keyed
    "wraith_alt":    (8,   "unit\\terran\\wessel.grp"),
    "science_alt":   (9,   "unit\\terran\\Science.grp"),
}


def load_grp(path):
    for a in (PT, SD, BD):
        if a.has(path):
            data, gaps = a.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


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
    print("cmdicons frames: %d  cell %dx%d" % (len(icons), ciw, cih))
    print()

    bad = []
    rows = []
    for key, (want, path) in CASES.items():
        r = load_grp(path)
        if r is None:
            print("%-14s MISSING %s" % (key, path))
            bad.append(key)
            continue
        frames, mw, mh = r
        tgt = fit(mask_of(frames[0]))
        scores = sorted(((iou(tgt, im), i) for i, im in enumerate(icon_masks)),
                        reverse=True)
        best = scores[0][1]
        ok = best == want
        if not ok:
            bad.append(key)
        print("%-14s want #%-4d %-26s best #%-4d (%.3f)  %s   top3: %s"
              % (key, want, NAMES.get(want, "?"), best, scores[0][0],
                 "ok" if ok else "*** MISMATCH",
                 ", ".join("#%d=%.3f" % (i, s) for s, i in scores[:3])))
        rows.append((key, want, best, ok))

    # labelled sheet of the icons we care about, so the numbers can be eyeballed
    cell = 64
    want_ids = sorted({w for _, (w, _) in CASES.items()})
    sheet = Image.new("RGB", (len(want_ids) * cell, cell + 16), (30, 32, 40))
    d = ImageDraw.Draw(sheet)
    for i, uid in enumerate(want_ids):
        if uid >= len(icons):
            continue
        f = icons[uid]
        im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
        px = im.load()
        for y in range(f["h"]):
            for x in range(f["w"]):
                v = f["px"][y * f["w"] + x]
                if v != 255:
                    px[x, y] = (200, 210, 230, 255)
        sc = min((cell - 10) / im.width, (cell - 10) / im.height, 2.0)
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))),
                       Image.NEAREST)
        bg = Image.new("RGBA", (cell, cell), (30, 32, 40, 255))
        bg.alpha_composite(im, ((cell - im.width) // 2, (cell - im.height) // 2))
        sheet.paste(bg.convert("RGB"), (i * cell, 16))
        d.text((i * cell + 2, 2), "#%d" % uid, fill=(255, 225, 130))
    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, "v28_icon_gate.png")
    sheet.save(dst)
    print("\nsheet -> %s" % dst)
    print("problems: %s" % (bad if bad else "none"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
