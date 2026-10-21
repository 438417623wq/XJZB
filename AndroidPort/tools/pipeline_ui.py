"""UI asset pipeline: wireframe portraits + official unit names -> Android assets.

Outputs into AndroidPort/app/app/src/main/assets/:
    ui/wire/wire_<unitID>.png     wireframe portrait (neutral palette)
    ui/unitnames.txt              "<unitID> <official name>" per line

Both are indexed by units.dat unit ID. wirefram.grp has 228 frames == the
unit-ID space; verified frame 0=Marine, 5=Tank, 7=SCV, 32=Firebat.
rez/stat_txt.tbl is likewise unit-ID indexed (0='Terran Marine', ...).
"""
import os
import struct

from PIL import Image

import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\app\app\src\main\assets")
WIREDIR = os.path.join(OUT, "ui", "wire")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
# WPE entries are R,G,B,0 (see pipeline_sprites.py); the old read was B,G,R.
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]


def frame_image(f, pal):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    px = im.load()
    src = f["px"]
    for y in range(f["h"]):
        base = y * f["w"]
        for x in range(f["w"]):
            v = src[base + x]
            if v != 255:
                px[x, y] = pal[v] + (255,)
    return im


def extract_wireframes():
    """One portrait per unit id, rendered with the tileset palette.

    NOTE on colour: wirefram.grp draws itself from its own dedicated palette
    ramp, NOT the team-colour slots. Measured across all 228 frames:
      Terran units use indices 192,193 + 208..211 (brown outline, blue-grey fill)
      Zerg   units use indices 216..219 (dark blue-grey)
      pixels in team slots 8..15: 0
    So there is no per-team variant to produce -- an earlier pass wrote _b/_r
    copies that were byte-identical. The portraits are rendered once, with the
    same WPE palette the terrain and sprites use.
    """
    os.makedirs(WIREDIR, exist_ok=True)
    data, gaps = SD.read_with_gaps("unit\\wirefram\\wirefram.grp")
    frames, mw, mh = grpm.decode_grp(data, gaps)
    n = 0
    for i, f in enumerate(frames):
        im = frame_image(f, PAL)
        if not any(p[3] for p in im.getdata()):
            continue
        im.save(os.path.join(WIREDIR, "wire_%d.png" % i))
        n += 1
    print("wireframes: %d unit portraits, cell %dx%d" % (n, mw, mh))


def extract_unitnames():
    """Dump rez/stat_txt.tbl as "<unitID> <name>", one row per unit id.

    Some rows in the table are continuation text (e.g. "(Marine and Firebat
    ability)") with no id of their own; the Android reader skips any line that
    does not start with a digit, so they are harmless here, but we keep the id
    prefix strictly numeric to make that contract explicit.
    """
    data, gaps = PT.read_with_gaps("rez\\stat_txt.tbl")
    n, = struct.unpack_from("<H", data, 0)
    offs = struct.unpack_from("<%dH" % n, data, 2)
    lines = []
    for i in range(n):
        a = offs[i]
        e = data.find(b"\0", a)
        name = data[a:e].decode("latin1").replace("\n", " ").strip()
        if name:
            lines.append("%d %s" % (i, name))
    with open(os.path.join(OUT, "ui", "unitnames.txt"), "w", encoding="utf8") as fp:
        fp.write("\n".join(lines) + "\n")
    print("unitnames: %d entries" % len(lines))


if __name__ == "__main__":
    extract_wireframes()
    extract_unitnames()
