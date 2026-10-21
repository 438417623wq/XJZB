# -*- coding: utf-8 -*-
"""Render candidate Terran air GRPs side by side to identify the Wraith.

Name-based guessing already failed once (probe_newunits.py assumed phoenix.grp
was a Protoss unit). This renders the actual pixels so the call is made on art,
not filenames.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive, grp as grpm
from PIL import Image

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)

# palette: same source and byte order as pipeline_sprites.py:43 -- WPE entries
# are R,G,B,0 (not B,G,R), and index 255 is the transparent filler.
wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]


def palette_from(arc, name):
    return PAL


CANDIDATES = [
    (r"unit\terran\phoenix.grp", "phoenix.grp (candidate Wraith)"),
    (r"unit\terran\wessel.grp", "wessel.grp (Science Vessel)"),
    (r"unit\terran\ghost.grp", "ghost.grp (Ghost)"),
    (r"unit\terran\battlecr.grp", "battlecr.grp (BattleCruiser)"),
    (r"unit\terran\dropship.grp", "dropship.grp (Dropship)"),
    (r"unit\terran\medic.grp", "medic.grp (Medic)"),
    (r"unit\terran\bomber.grp", "bomber.grp (?)"),
]

CELL = 140
rows = []
for name, label in CANDIDATES:
    if not SD.has(name):
        print("MISS", name)
        continue
    data, gaps = SD.read_with_gaps(name)
    pal = palette_from(SD, name)
    frames, w, h = grpm.decode_grp(data, gaps)
    print("%-42s frames=%-4d %dx%d" % (name, len(frames), w, h))
    # pick a spread of frames: 0 (usually idle facing 0) and a mid frame
    picks = [0]
    if len(frames) > 17:
        picks.append(17)
    if len(frames) > 40:
        picks.append(40)
    rows.append((label, frames, w, h, picks, pal))

cols = max(len(r[4]) for r in rows)
sheet = Image.new("RGB", (CELL * cols, CELL * len(rows)), (18, 20, 26))
for ri, (label, frames, w, h, picks, pal) in enumerate(rows):
    for ci, fi in enumerate(picks):
        if fi >= len(frames):
            continue
        fr = frames[fi]
        fw, fh = fr["w"], fr["h"]
        idx = fr["px"]
        img = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        px = img.load()
        for y in range(fh):
            for x in range(fw):
                v = idx[y * fw + x]
                if v == 255:
                    continue
                px[x, y] = pal[v] + (255,)
        img = img.resize((CELL - 8, max(1, int((CELL - 8) * fh / max(1, fw)))), Image.NEAREST)
        sheet.paste(img, (ci * CELL + 4, ri * CELL + 4), img)

sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
p = os.path.join(OUT, "wraith_ident.png")
sheet.save(p)
print("wrote", p)
