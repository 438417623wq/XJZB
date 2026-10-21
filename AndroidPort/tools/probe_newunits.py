"""v2.8 probe: which Terran/Zerg unit GRPs actually decode from this repack?

The v2.7 plan deferred ghost/wraith behind one gate: verify the GRPs and the
cmdicons frames first (the v2.2 lesson -- never guess an index). This script
answers the GRP half of that gate with data, and renders a contact sheet so the
answer can be eyeballed rather than assumed.

Paths come from tools/images_tbl.txt (the arr/images.tbl dump), NOT from
guessing: the MPQ keys are "unit\\" + the table row, e.g. row "terran\\ghost.grp"
-> key "unit\\terran\\ghost.grp".

Run from AndroidPort/tools:  python probe_newunits.py
Writes tools/out/newunits_probe.png
"""
import os
import sys

from PIL import Image

import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

# rows copied verbatim out of tools/images_tbl.txt
TERRAN = ["ghost.grp", "goliath.grp", "BattleCr.grp", "dropship.grp",
          "phoenix.grp", "wessel.grp", "Spider.grp", "ughost.grp"]
ZERG = ["queen.grp", "defiler.grp", "ultra.grp", "guardian.grp",
        "larva.grp", "egg.grp", "spire.grp", "Extract.grp",
        "Lurker.grp", "cocoon.grp"]
EXTRA = ["protoss\\scout.grp", "protoss\\shuttle.grp"]


def load(path):
    for tag, ar in (("PT", PT), ("SD", SD), ("BD", BD)):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return tag, grpm.decode_grp(data, gaps)
    return None, None


def main():
    wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
    pal = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]
    # index 8..15 are the team slots; colour them so a decoded sheet is obvious
    for i in range(8):
        k = i / 7.0
        pal[8 + i] = (int(16 + 112 * k), int(28 + 148 * k), int(96 + 159 * k))

    rows = []
    for group, names in (("terran", TERRAN), ("zerg", ZERG), ("extra", EXTRA)):
        for n in names:
            path = n if "\\" in n else "%s\\%s" % (group, n)
            key = "unit\\" + path
            tag, got = load(key)
            if not got:
                print("  --   %-30s MISS" % key)
                continue
            frames, mw, mh = got
            blocks = len(frames) // 17
            print("  OK   %-30s %s frames=%-4d %dx%d (%d dir-blocks, rem %d)"
                  % (key, tag, len(frames), mw, mh, blocks, len(frames) % 17))
            rows.append((key, frames, mw, mh))

    if not rows:
        print("nothing decoded")
        return 1

    # contact sheet: frame 0 of each decoded GRP, scaled to a common cell
    cell = 96
    cols = 6
    rc = (len(rows) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell, rc * (cell + 14)), (24, 24, 32, 255))
    for i, (key, frames, mw, mh) in enumerate(rows):
        f = frames[0]
        im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
        px = im.load()
        for y in range(f["h"]):
            for x in range(f["w"]):
                v = f["px"][y * f["w"] + x]
                if v != 255:
                    px[x, y] = pal[v] + (255,)
        sc = min(cell / max(1, f["w"]), cell / max(1, f["h"]))
        im = im.resize((max(1, int(f["w"] * sc)), max(1, int(f["h"] * sc))),
                       Image.NEAREST)
        ox = (i % cols) * cell + (cell - im.width) // 2
        oy = (i // cols) * (cell + 14) + 12
        sheet.alpha_composite(im, (ox, oy))
    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, "newunits_probe.png")
    sheet.save(dst)
    print("\n%d decoded -> %s" % (len(rows), dst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
