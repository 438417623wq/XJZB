"""Verify console wireframes match the units they represent.

Renders, for each playable unit: the tinted console wireframe beside the
in-game sprite frame 0, so a mismatch (wrong units.dat id) is obvious.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import sc_archive
import grp as grpm
from PIL import Image, ImageDraw

ROOT = r"F:\KF\XJZB"
ASSETS = os.path.join(ROOT, r"AndroidPort\app\app\src\main\assets")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4 + 2], wpe[i * 4 + 1], wpe[i * 4]) for i in range(256)]

# (label, unitId, sprite grp, first-frame index)
CASES = [
    ("SCV", 7, "unit\\terran\\SCV.grp", 0),
    ("Marine", 0, "unit\\terran\\marine.grp", 0),
    ("Firebat", 32, "unit\\terran\\firebat.grp", 0),
    ("Vulture", 2, "unit\\terran\\Vulture.grp", 0),
    ("Tank", 5, "unit\\terran\\tank.grp", 0),
    ("Zergling", 37, "unit\\zerg\\zergling.grp", 0),
    ("Hydralisk", 38, "unit\\zerg\\hydra.grp", 0),
    ("Mutalisk", 43, "unit\\zerg\\mutalid.grp", 0),
    ("Drone", 41, "unit\\zerg\\drone.grp", 0),
    ("Overlord", 42, "unit\\zerg\\overlord.grp", 0),
    ("CmdCenter", 106, "unit\\terran\\control.grp", 0),
    ("Depot", 109, "unit\\terran\\Depot.grp", 0),
    ("Barracks", 111, "unit\\terran\\TBarrack.grp", 0),
    ("Factory", 113, "unit\\terran\\factory.grp", 0),
    ("Turret", 124, "unit\\terran\\missile.grp", 0),
    ("Bunker", 125, "unit\\terran\\PillBox.grp", 0),
    ("Hatchery", 131, "unit\\zerg\\hatchery.grp", 0),
    ("Sunken", 146, "unit\\zerg\\fcolony.grp", 0),
]

CELL = 96
img = Image.new("RGB", (len(CASES) * CELL, 2 * CELL + 20), (46, 50, 62))
d = ImageDraw.Draw(img)
bad = []
for i, (label, uid, path, fi) in enumerate(CASES):
    # console wireframe, as the HUD draws it (no team variant: wirefram.grp
    # paints from its own ramp and never uses the team-colour slots)
    wp = os.path.join(ASSETS, "ui", "wire", "wire_%d.png" % uid)
    if os.path.exists(wp):
        w = Image.open(wp).convert("RGBA")
        w = w.resize((CELL - 16, CELL - 16), Image.NEAREST)
        bg = Image.new("RGBA", (CELL, CELL), (46, 50, 62, 255))
        bg.alpha_composite(w, (8, 8))
        img.paste(bg.convert("RGB"), (i * CELL, 16))
    else:
        d.text((i * CELL + 4, 30), "NO WIRE", fill=(255, 90, 90))
        bad.append((label, uid, "missing wireframe"))

    # in-game sprite frame 0
    data, gaps = SD.read_with_gaps(path)
    frames, mw, mh = grpm.decode_grp(data, gaps)
    f = frames[fi]
    s = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    for y in range(f["h"]):
        for x in range(f["w"]):
            v = f["px"][y * f["w"] + x]
            if v != 255:
                s.putpixel((x, y), PAL[v] + (255,))
    sc = min((CELL - 12) / s.width, (CELL - 12) / s.height, 3.0)
    s = s.resize((max(1, int(s.width * sc)), max(1, int(s.height * sc))), Image.NEAREST)
    bg2 = Image.new("RGBA", (CELL, CELL), (46, 50, 62, 255))
    bg2.alpha_composite(s, ((CELL - s.width) // 2, (CELL - s.height) // 2))
    img.paste(bg2.convert("RGB"), (i * CELL, CELL + 16))

    d.text((i * CELL + 3, 2), "%s id=%d" % (label, uid), fill=(255, 225, 130))
    # sanity: wireframe file must be non-trivial
    wf = os.path.join(ASSETS, "ui", "wire", "wire_%d.png" % uid)
    if os.path.exists(wf) and os.path.getsize(wf) < 200:
        bad.append((label, uid, "suspiciously small wireframe"))

img.save(os.path.join(ROOT, r"AndroidPort\tools\out\ui_wire_vs_sprite.png"))
print("saved ui_wire_vs_sprite.png", img.size)
print("problems:", bad if bad else "none")
