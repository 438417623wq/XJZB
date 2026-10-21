"""Do the Brood War unit icons exist in BrooDat's cmdicons.grp?

The batch B/C icon sheet came back with #34 (Medic), #58 (Valkyrie), #62
(Devourer) and #95..#98 all BLANK in StarDat's unit\cmdbtns\cmdicons.grp --
which is expected, because StarDat is the CLASSIC (pre-Brood-War) archive.
The BW icons should have been added to the same file in BrooDat.

  python probe_v211ch.py            # compare the two files, dump both grids
  python probe_v211ch.py 34 58 62   # override the frames to render

Writes tools/out/v211_ship/icons_sd.png and icons_bd.png.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import sc_archive
import grp as grpm
from PIL import Image, ImageDraw

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "v211_ship")
PATH = "unit\\cmdbtns\\cmdicons.grp"

# units.dat id -> label, from rez/stat_txt.tbl (patch_rt, 1547 entries).
LABEL = {
    0: "Marine", 1: "Ghost", 2: "Vulture", 3: "Goliath", 5: "Tank", 7: "SCV",
    8: "Wraith", 9: "ScienceV", 11: "Dropship", 12: "BattleCr", 13: "SpiderM",
    14: "Nuke", 32: "Firebat", 34: "Medic", 35: "Larva", 36: "Egg",
    37: "Zergling", 38: "Hydralisk", 39: "Ultralisk", 40: "Broodling",
    41: "Drone", 42: "Overlord", 43: "Mutalisk", 44: "Guardian", 45: "Queen",
    46: "Defiler", 47: "Scourge", 58: "Valkyrie", 59: "Cocoon",
    60: "Corsair", 61: "DTemplar", 62: "Devourer", 63: "DArchon",
    64: "Probe", 65: "Zealot", 66: "Dragoon", 67: "HTemplar", 68: "Archon",
    69: "Shuttle", 70: "Scout", 71: "Arbiter", 72: "Carrier", 73: "Intercep",
    83: "Reaver", 84: "Observer", 97: "LurkEgg", 103: "Lurker",
    106: "CmdCtr", 107: "Comsat", 108: "NukeSilo", 109: "Depot",
    110: "Refinery", 111: "Barracks", 112: "Academy", 113: "Factory",
    114: "Starport", 116: "SciFac", 122: "EngBay", 123: "Armory",
    124: "Turret", 125: "Bunker", 131: "Hatchery", 134: "Nydus",
    135: "HydraDen", 136: "DefMound", 137: "GtSpire", 138: "QNest",
    139: "EvoCham", 140: "UltCavern", 141: "Spire", 142: "Pool",
    143: "CreepCol", 144: "SporeCol", 146: "Sunken", 147: "Overmind",
    149: "Extractor", 150: "Chrysalis", 151: "Cerebrate",
}


def render(frames, mw, mh, ids, dst, title):
    scale = 3
    cw, ch = mw * scale, mh * scale
    cols = 8
    rows = (len(ids) + cols - 1) // cols
    img = Image.new("RGB", (cols * cw, rows * (ch + 16)), (26, 28, 36))
    d = ImageDraw.Draw(img)
    blank = 0
    for i, uid in enumerate(ids):
        if uid >= len(frames):
            continue
        f = frames[uid]
        im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
        px = im.load()
        opaque = 0
        for y in range(f["h"]):
            for x in range(f["w"]):
                v = f["px"][y * f["w"] + x]
                if v != 255:
                    px[x, y] = (205, 214, 232, 255)
                    opaque += 1
        if opaque == 0:
            blank += 1
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        bg = Image.new("RGBA", (cw, ch), (26, 28, 36, 255))
        bg.alpha_composite(im, ((cw - im.width) // 2, (ch - im.height) // 2))
        img.paste(bg.convert("RGB"), ((i % cols) * cw, (i // cols) * (ch + 16) + 16))
        d.text(((i % cols) * cw + 3, (i // cols) * (ch + 16) + 3),
               "#%d %s%s" % (uid, LABEL.get(uid, "?"), " BLANK" if opaque == 0 else ""),
               fill=(255, 140, 140) if opaque == 0 else (255, 225, 130))
    os.makedirs(OUT, exist_ok=True)
    img.save(dst)
    print("%s -> %s %s  (blank %d/%d)" % (title, dst, img.size, blank, len(ids)))


def want_ids():
    """Every frame index ICONS_WANT in pipeline_sprites.py asks for.

    Parsed with a regex rather than imported, because importing the pipeline
    would run its main() and rewrite the whole sprite set.
    """
    import re
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "pipeline_sprites.py"), encoding="utf8").read()
    body = src.split("ICONS_WANT = {", 1)[1].split("\n}", 1)[0]
    pairs = re.findall(r'"(ic_\w+)":\s*(\d+)', body)
    return [(int(v), k) for k, v in pairs]


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--want":
        want = want_ids()
        print("ICONS_WANT has %d entries" % len(want))
        byid = {}
        for uid, key in want:
            byid.setdefault(uid, []).append(key)
        ids = sorted(byid)
        # PT first: it is the Brood-War-patched copy and the one load_grp picks.
        ar = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))
        data, gaps = ar.read_with_gaps(PATH)
        frames, mw, mh = grpm.decode_grp(data, gaps)
        ar.close()
        print("PT cmdicons: %d frames" % len(frames))
        # A placeholder frame is the literal word "BLANK" drawn as art, so it
        # cannot be detected by "is it empty" -- measure the opaque coverage
        # instead and flag the outliers for eyeballing.
        for uid in ids:
            if uid >= len(frames):
                print("  #%-4d OUT OF RANGE  %s" % (uid, ",".join(byid[uid])))
                continue
            f = frames[uid]
            op = sum(1 for v in f["px"] if v != 255)
            frac = op / float(f["w"] * f["h"])
            print("  #%-4d cov=%.3f  %s" % (uid, frac, ",".join(byid[uid])))
        render(frames, mw, mh, ids, os.path.join(OUT, "icons_want.png"), "ICONS_WANT")
        return
    ids = [int(a) for a in sys.argv[1:]] or [
        34, 58, 62, 97, 40, 39, 44, 45, 46, 103, 13, 14,
        134, 135, 136, 137, 138, 139, 140, 141, 143, 144, 147, 150, 151,
    ]
    for tag, name in (("SD", "StarDat.mpq"), ("BD", "BrooDat.mpq"),
                      ("PT", "patch_rt.mpq")):
        ar = sc_archive.Archive(os.path.join(ROOT, name))
        if not ar.has(PATH):
            print("%s: no %s" % (tag, PATH))
            ar.close()
            continue
        data, gaps = ar.read_with_gaps(PATH)
        frames, mw, mh = grpm.decode_grp(data, gaps)
        print("%s: %d frames %dx%d" % (tag, len(frames), mw, mh))
        render(frames, mw, mh, ids, os.path.join(OUT, "icons_%s.png" % tag.lower()),
               "%s cmdicons" % tag)
        ar.close()


main()
