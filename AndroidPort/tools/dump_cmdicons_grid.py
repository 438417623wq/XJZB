"""v2.8 gate, decisive half: is cmdicons frame index == units.dat id?

icon_match.py's silhouette IoU is not trustworthy -- it scores the already
shipped firebat icon at #50 while the pipeline uses #10 and Game.java uses #32,
three different answers for a unit that is known good. So instead of scoring,
render a LABELLED grid of cmdicons frames and read it.

Ground truth for the label comes from rez/stat_txt.tbl (assets/ui/unitnames.txt):
0 Marine, 1 Ghost, 2 Vulture, 3 Goliath, 5 Siege Tank, 7 SCV, 8 Wraith,
9 Science Vessel, 11 Dropship, 12 Battlecruiser, 32 Firebat, 35 Larva,
36 Egg, 39 Ultralisk, 41 Drone, 42 Overlord, 43 Mutalisk, 44 Guardian,
45 Queen, 46 Defiler, 103 Lurker, 106 CC ... 112 Academy, 116 Science Facility,
122 Engineering Bay, 123 Armory, 124 Missile Turret, 125 Bunker.

If frame index == units.dat id, the grid reads: Marine, Ghost, Vulture, ...

Run from AndroidPort/tools:  python dump_cmdicons_grid.py
Writes tools/out/cmdicons_ids.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import sc_archive
import grp as grpm
from PIL import Image, ImageDraw

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))

# ids we care about, in the order the plan needs them. Override from argv to
# check a specific suspicion, e.g. `python dump_cmdicons_grid.py 10 32 115 116`.
IDS = [0, 1, 2, 3, 5, 7, 8, 9, 11, 12, 32, 34, 35, 36, 39, 41, 42, 43, 44,
       45, 46, 47, 62, 103, 106, 109, 111, 112, 113, 116, 122, 123, 124, 125,
       131, 142, 146]
if len(sys.argv) > 1:
    IDS = [int(a) for a in sys.argv[1:]]

LABEL = {
    0: "Marine", 1: "Ghost", 2: "Vulture", 3: "Goliath", 5: "Tank", 7: "SCV",
    8: "Wraith", 9: "ScienceV", 11: "Dropship", 12: "BattleCr", 32: "Firebat",
    34: "Medic", 35: "Larva", 36: "Egg", 39: "Ultralisk", 41: "Drone",
    42: "Overlord", 43: "Mutalisk", 44: "Guardian", 45: "Queen",
    46: "Defiler", 47: "Scourge", 62: "Devourer", 103: "Lurker",
    106: "CmdCtr", 109: "Depot", 111: "Barracks", 112: "Academy",
    113: "Factory", 116: "SciFac", 122: "EngBay", 123: "Armory",
    124: "Turret", 125: "Bunker", 131: "Hatchery", 142: "Pool", 146: "Sunken",
}


def main():
    data, gaps = SD.read_with_gaps("unit\\cmdbtns\\cmdicons.grp")
    frames, mw, mh = grpm.decode_grp(data, gaps)
    print("cmdicons frames=%d cell=%dx%d" % (len(frames), mw, mh))

    scale = 3
    cw, ch = mw * scale, mh * scale
    cols = 8
    rows = (len(IDS) + cols - 1) // cols
    img = Image.new("RGB", (cols * cw, rows * (ch + 16)), (26, 28, 36))
    d = ImageDraw.Draw(img)
    for i, uid in enumerate(IDS):
        if uid >= len(frames):
            continue
        f = frames[uid]
        im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
        px = im.load()
        for y in range(f["h"]):
            for x in range(f["w"]):
                v = f["px"][y * f["w"] + x]
                if v != 255:
                    px[x, y] = (205, 214, 232, 255)
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        ox = (i % cols) * cw + (cw - im.width) // 2
        oy = (i // cols) * (ch + 16) + 16 + (ch - im.height) // 2
        bg = Image.new("RGBA", (cw, ch), (26, 28, 36, 255))
        bg.alpha_composite(im, ((cw - im.width) // 2, (ch - im.height) // 2))
        img.paste(bg.convert("RGB"), ((i % cols) * cw, (i // cols) * (ch + 16) + 16))
        d.text(((i % cols) * cw + 3, (i // cols) * (ch + 16) + 3),
               "#%d %s" % (uid, LABEL.get(uid, "?")), fill=(255, 225, 130))

    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, "cmdicons_ids.png")
    img.save(dst)
    print("saved", dst, img.size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
