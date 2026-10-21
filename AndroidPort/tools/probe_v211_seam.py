"""v2.11: numbered full-frame strip + block similarity, for the walk/attack seam.

Two things probe_v211j/g cannot answer, and this script exists only for them:

  (a) NUMBERED FRAME STRIP -- probe_v211j indexes by BLOCK (b0 = frames 0..16),
      which silently assumes the file really is 17-directional. lurk_egg (20
      frames) and spider (12 frames) are not, so for those the block grid
      mislabels the animation. This prints every raw frame index in order, which
      is the only way to read the true sequence of a non-17 file.

  (b) BLOCK SIMILARITY -- for a 17-directional unit, "is this block a real walk
      cycle?" is a numeric question: a walk block repeats a small cycle, so a
      late block is close to an early one at the same direction. An attack or
      death block is the opposite -- it stands apart from every other block.

Usage:
  python probe_v211_seam.py <key> strip [scale]        -> numbered all-frames strip
  python probe_v211_seam.py <key> sim [dir]            -> intra/inter block stats
  python probe_v211_seam.py <key> frames <csv> [scale] -> chosen raw frame indices
Output: tools/out/v211_blocks/<key>_frames.png  (strip mode)
        tools/out/v211_blocks/<key>_sel.png    (frames mode)
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out\v211_blocks")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

PATHS = {
    "ultra":      "unit\\zerg\\ultra.grp",
    "guardian":   "unit\\zerg\\guardian.grp",
    "defiler":    "unit\\zerg\\defiler.grp",
    "queen":      "unit\\zerg\\queen.grp",
    "lurker":     "unit\\zerg\\lurknorm.grp",
    "lurker_bur": "unit\\zerg\\lurkburr.grp",
    "devourer":   "unit\\zerg\\devour.grp",
    "broodling":  "unit\\zerg\\brood.grp",
    "lurk_egg":   "unit\\zerg\\LurkEgg.grp",
    "medic":      "unit\\terran\\medic.grp",
    "valkyrie":   "unit\\terran\\bomber.grp",
    "spider":     "unit\\terran\\Spider.grp",
    "marine":     "unit\\terran\\marine.grp",
    "zealot":     "unit\\protoss\\zealot.grp",
}


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def frame_image(f):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    px = im.load()
    src = f["px"]
    for y in range(f["h"]):
        base = y * f["w"]
        for x in range(f["w"]):
            v = src[base + x]
            if v != 255:
                px[x, y] = PAL[v] + (255,)
    return im


def tight(f):
    im = frame_image(f)
    bb = im.getbbox()
    return im.crop(bb) if bb else None


def diff(a, b):
    """mean abs RGBA difference over the union canvas; None counts as empty."""
    if a is None and b is None:
        return 0.0
    if a is None or b is None:
        return 255.0
    w, h = max(a.width, b.width), max(a.height, b.height)
    ca = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cb = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ca.paste(a, ((w - a.width) // 2, (h - a.height) // 2), a)
    cb.paste(b, ((w - b.width) // 2, (h - b.height) // 2), b)
    pa, pb = ca.load(), cb.load()
    tot = 0
    for y in range(h):
        for x in range(w):
            ra, ga, ba, aa = pa[x, y]
            rb, gb, bb2, ab = pb[x, y]
            if aa == 0 and ab == 0:
                continue
            tot += abs(ra - rb) + abs(ga - gb) + abs(ba - bb2) + abs(aa - ab)
    return tot / (3.0 * w * h)


key = sys.argv[1]
mode = sys.argv[2] if len(sys.argv) > 2 else "strip"

r = load(PATHS[key])
if r is None:
    print("MISS", key)
    sys.exit(1)
frames, mw, mh = r
n = len(frames)
blocks = (n + 16) // 17
print("%s  n=%d blocks=%d cell=%dx%d" % (key, n, blocks, mw, mh))

if mode == "strip":
    SC = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    crops = [tight(f) for f in frames]
    cw = max((c.width for c in crops if c), default=1)
    ch = max((c.height for c in crops if c), default=1)
    cw = (cw + 4) * SC
    ch = (ch + 4) * SC
    COLS = 10
    rows = (n + COLS - 1) // COLS
    lab = 22
    img = Image.new("RGBA", (COLS * cw, rows * (ch + lab)), (22, 26, 34, 255))
    d = ImageDraw.Draw(img)
    for k, c in enumerate(crops):
        gx, gy = k % COLS, k // COLS
        x, y = gx * cw, gy * (ch + lab)
        # label with the raw frame index AND the block it lands in at 17/block
        d.text((x + 2, y + 2), "f%d b%d d%d" % (k, k // 17, k % 17),
               fill=(240, 220, 120, 255))
        if c is not None:
            c = c.resize((c.width * SC, c.height * SC), Image.NEAREST)
            img.paste(c, (x + 2 * SC, y + lab), c)
    img.save(os.path.join(OUT, "%s_frames.png" % key))
    print("-> %s_frames.png (%dx%d)" % (key, img.width, img.height))

elif mode == "frames":
    # raw frame indices, so a non-17 file can be read as a real sequence
    idx = [int(x) for x in sys.argv[3].split(",")]
    SC = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    crops = [(k, tight(frames[k]) if k < n else None) for k in idx]
    cw = max((c.width for _, c in crops if c), default=1)
    ch = max((c.height for _, c in crops if c), default=1)
    cw = (cw + 4) * SC
    ch = (ch + 4) * SC
    COLS = min(len(crops), 10)
    rows = (len(crops) + COLS - 1) // COLS
    lab = 22
    img = Image.new("RGBA", (COLS * cw, rows * (ch + lab)), (22, 26, 34, 255))
    d = ImageDraw.Draw(img)
    for m, (k, c) in enumerate(crops):
        gx, gy = m % COLS, m // COLS
        x, y = gx * cw, gy * (ch + lab)
        d.text((x + 2, y + 2), "f%d" % k, fill=(240, 220, 120, 255))
        if c is not None:
            c = c.resize((c.width * SC, c.height * SC), Image.NEAREST)
            img.paste(c, (x + 2 * SC, y + lab), c)
    img.save(os.path.join(OUT, "%s_sel.png" % key))
    print("-> %s_sel.png (%dx%d)" % (key, img.width, img.height))

elif mode == "sim":
    dd = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    cells = {}
    for b in range(blocks):
        fi = b * 17 + dd
        cells[b] = tight(frames[fi]) if fi < n else None

    print("\n[dir %d] block-to-block mean abs diff (lower = more alike):" % dd)
    print("      " + "".join("%6d" % b for b in range(blocks)))
    for i in range(blocks):
        row = "b%-4d " % i
        for j in range(blocks):
            row += "%6d" % min(999, round(diff(cells[i], cells[j])))
        print(row)

    print("\n[dir %d] each block vs its nearest OTHER block:" % dd)
    for i in range(blocks):
        best = min(((j, diff(cells[i], cells[j]))
                    for j in range(blocks) if j != i and cells[j] is not None),
                   key=lambda t: t[1], default=None)
        if best:
            print("  b%-3d -> b%-3d  d=%5.1f" % (i, best[0], best[1]))

    print("\nINTRA-block spread (how much the 17 directions of a block differ):")
    for b in range(blocks):
        fs = [tight(frames[b * 17 + d2]) for d2 in range(17)
              if b * 17 + d2 < n]
        fs = [f for f in fs if f is not None]
        if len(fs) < 2:
            print("  b%-3d  n=%d  (too few)" % (b, len(fs)))
            continue
        vals = [diff(fs[i], fs[j]) for i in range(len(fs))
                for j in range(i + 1, len(fs))]
        print("  b%-3d  n=%-3d  mean=%5.1f  max=%5.1f"
              % (b, len(fs), sum(vals) / len(vals), max(vals)))
