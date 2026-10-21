"""Batch B/C rendered comparison sheet (the plan's iron rule: art first).

This does NOT decode the MPQs. It reads the sheets pipeline_sprites.py has
already written into assets/sprites and lays them out with labels, so the
question it answers is "did the pipeline actually produce the walk/attack rows
I asked for, at the right size, with the right team colours" rather than
"which GRP is this building".

  python probe_v211cg.py [units|bld|icons|all]

units: every batch B/C unit sheet, one row of the page per unit, drawn at
       native sheet size with the walk rows and the attack row labelled.
bld:   the new zerg/terran structures.
icons: the new command-card icons, upscaled 4x so they are readable.

Output goes to tools/out/v211_ship/.
"""
import os
import sys

from PIL import Image, ImageDraw

TOOLS = os.path.dirname(os.path.abspath(__file__))
SPR = os.path.join(TOOLS, "..", "app", "app", "src", "main", "assets", "sprites")
OUT = os.path.join(TOOLS, "out", "v211_ship")

# unit key -> (walk rows, attack row or None, death anim key or None)
UNITS = [
    ("ultra",      5, None, "death_ultra"),
    ("queen",     11, None, None),
    ("defiler",    8, None, "death_defiler"),
    ("guardian",   7, None, None),
    ("devourer",   8,    8, None),
    ("lurker",     7,    7, "death_lurker"),
    ("lurker_bur", 13, None, "death_lurker_bur"),
    ("broodling", 12, None, None),
    ("lurk_egg",   1, None, None),
    ("medic",      4,    4, "death_medic"),
    ("valkyrie",   1, None, None),
    ("spider",     1, None, None),
]

BLDS = [
    "creep", "spore", "evolcham", "hydraden", "mutapit", "nest", "nydus",
    "ucereb", "cerebrate", "chrysal", "overmind1", "overmind2", "zbuild",
    "greatspire", "ultracavern", "engbay", "armory", "sciencefac", "spire",
    "sunken",
]

ICONS = [
    "ic_ultra", "ic_broodling", "ic_guardian", "ic_queen", "ic_defiler",
    "ic_devourer", "ic_lurk_egg", "ic_lurker", "ic_nydus", "ic_hydraden",
    "ic_mutapit", "ic_greatspire", "ic_nest", "ic_evolcham", "ic_ultracavern",
    "ic_creep", "ic_spore", "ic_overmind", "ic_chrysal", "ic_cerebrate",
    "ic_medic", "ic_valkyrie", "ic_spider",
]

LABW = 130
PAD = 6


def load(key, team="b"):
    for ext in (".webp", ".png"):
        p = os.path.join(SPR, key + "_" + team + ext)
        if os.path.exists(p):
            return Image.open(p).convert("RGBA")
    p = os.path.join(SPR, key + ".png")
    if os.path.exists(p):
        return Image.open(p).convert("RGBA")
    return None


def sheet_units():
    rows = []
    for key, walk, atk, death in UNITS:
        blue = load(key, "b")
        red = load(key, "r")
        if blue is None:
            print("MISS", key)
            continue
        rows.append((key, walk, atk, blue, red, load(death, "b") if death else None))
    if not rows:
        return
    w = max(r[3].width + (r[4].width if r[4] else 0) for r in rows) + LABW + PAD * 3
    h = sum(max(r[3].height, r[4].height if r[4] else 0) for r in rows) + PAD * len(rows) * 2
    page = Image.new("RGBA", (w, h), (24, 24, 30, 255))
    d = ImageDraw.Draw(page)
    y = 0
    for key, walk, atk, blue, red, death in rows:
        d.text((4, y + 4), "%s\nwalk=%d\natk=%s" % (key, walk, atk), fill=(230, 230, 120))
        x = LABW
        page.paste(blue, (x, y), blue)
        fw = blue.width // 17
        fh = blue.height // max(1, walk + (1 if atk is not None else 0))
        # grid: one thin line per direction column, one bright line per row
        for r in range(walk + (1 if atk is not None else 0) + 1):
            d.line([(x, y + r * fh), (x + blue.width, y + r * fh)],
                   fill=(90, 90, 110) if r != walk else (255, 90, 90))
        for c in range(18):
            d.line([(x + c * fw, y), (x + c * fw, y + blue.height)], fill=(70, 70, 90))
        x += blue.width + PAD
        if red is not None:
            page.paste(red, (x, y), red)
            x += red.width + PAD
        if death is not None:
            page.paste(death, (x, y), death)
            d.text((x, y + 2), "death", fill=(255, 140, 140))
        y += max(blue.height, red.height if red else 0, death.height if death else 0) + PAD * 2
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "ship_units.png")
    page.save(p)
    print("wrote", p, page.size)


def sheet_blds():
    imgs = [(k, load(k, "b"), load(k, "r")) for k in BLDS]
    imgs = [(k, b, r) for k, b, r in imgs if b is not None]
    if not imgs:
        return
    cellw = max(b.width + (r.width if r else 0) for _, b, r in imgs) + PAD * 3
    cellh = max(max(b.height, r.height if r else 0) for _, b, r in imgs) + 22 + PAD
    per = 4
    rows = (len(imgs) + per - 1) // per
    page = Image.new("RGBA", (cellw * per, cellh * rows), (24, 24, 30, 255))
    d = ImageDraw.Draw(page)
    for i, (k, b, r) in enumerate(imgs):
        cx = (i % per) * cellw
        cy = (i // per) * cellh
        d.text((cx + 4, cy + 2), "%s  %dx%d" % (k, b.width, b.height), fill=(230, 230, 120))
        page.paste(b, (cx + PAD, cy + 20), b)
        if r is not None:
            page.paste(r, (cx + PAD + b.width + PAD, cy + 20), r)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "ship_bld.png")
    page.save(p)
    print("wrote", p, page.size)


def sheet_icons():
    S = 4
    cells = []
    for k in ICONS:
        im = load(k)
        if im is None:
            print("icon MISS", k)
            continue
        cells.append((k, im.resize((im.width * S, im.height * S), Image.NEAREST)))
    if not cells:
        return
    cw = max(c.width for _, c in cells) + 8
    ch = max(c.height for _, c in cells) + 20
    per = 6
    rows = (len(cells) + per - 1) // per
    page = Image.new("RGBA", (cw * per, ch * rows), (24, 24, 30, 255))
    d = ImageDraw.Draw(page)
    for i, (k, c) in enumerate(cells):
        cx = (i % per) * cw
        cy = (i // per) * ch
        d.text((cx + 3, cy + 3), k, fill=(230, 230, 120))
        page.paste(c, (cx + 3, cy + 18), c)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "ship_icons.png")
    page.save(p)
    print("wrote", p, page.size)


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("units", "all"):
        sheet_units()
    if what in ("bld", "all"):
        sheet_blds()
    if what in ("icons", "all"):
        sheet_icons()


main()
