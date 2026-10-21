"""v2.10 probe 2: (a) render block boundaries of each protoss unit GRP so the
walk/attack block split can be eyeballed instead of guessed; (b) list every
protoss voice the repack actually carries."""
import os
import struct
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out")
os.makedirs(OUT, exist_ok=True)
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))
wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
BASE_PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

UNITS = [
    ("probe", "unit\\protoss\\probe.grp"),
    ("zealot", "unit\\protoss\\zealot.grp"),
    ("dragoon", "unit\\protoss\\dragoon.grp"),
    ("templar", "unit\\protoss\\templar.grp"),
    ("dtemplar", "unit\\protoss\\dtemplar.grp"),
    ("archon", "unit\\protoss\\archon.grp"),
    ("darchon", "unit\\protoss\\darchn.grp"),
    ("scout", "unit\\protoss\\scout.grp"),
    ("arbiter", "unit\\protoss\\arbiter.grp"),
    ("carrier", "unit\\protoss\\carrier.grp"),
    ("intercep", "unit\\protoss\\Intercep.grp"),
    ("reaver", "unit\\protoss\\trilob.grp"),
    ("corsair", "unit\\protoss\\corsair.grp"),
]


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
                px[x, y] = BASE_PAL[v] + (255,)
    return im


def block_grid(name, path):
    r = load(path)
    if r is None:
        print("MISS", name)
        return
    frames, mw, mh = r
    n = len(frames)
    nb = (n + 16) // 17
    dirs = [0, 4, 8, 12, 16]
    cw, ch = mw + 4, mh + 14
    img = Image.new("RGBA", (len(dirs) * cw + 60, nb * ch + 20), (22, 26, 34, 255))
    d = ImageDraw.Draw(img)
    for b in range(nb):
        d.text((2, 10 + b * ch + mh // 2), "b%d" % b, fill=(230, 200, 120, 255))
        for k, dd in enumerate(dirs):
            fi = b * 17 + dd
            if fi >= n:
                continue
            f = frames[fi]
            im = frame_image(f)
            img.paste(im, (60 + k * cw + 2, 10 + b * ch + 12), im)
            d.text((60 + k * cw + 2, b * ch + 2), "d%d" % dd, fill=(150, 170, 190, 255))
    p = os.path.join(OUT, "v210_blocks_%s.png" % name)
    img.save(p)
    print("%-10s n=%-4d blocks=%-3d -> %s (%dx%d)"
          % (name, n, nb, os.path.basename(p), img.width, img.height))


print("=== block boundary grids ===")
for name, path in UNITS:
    block_grid(name, path)

print()
print("=== protoss voices ===")


def parse_tbl(data):
    n, = struct.unpack_from("<H", data, 0)
    offs = struct.unpack_from("<%dH" % n, data, 2)
    out = []
    for i in range(n):
        end = data.find(b"\0", offs[i])
        out.append(data[offs[i]:end].decode("latin1"))
    return out


seen = []
for ar, tag in ((SD, "StarDat"), (BD, "BrooDat")):
    try:
        entries = parse_tbl(ar.read("arr\\sfxdata.tbl"))
    except Exception as ex:
        print(tag, "sfxdata FAIL", ex)
        continue
    hits = [e for e in entries if "protoss" in e.lower()]
    print("-- %s sfxdata.tbl: %d protoss entries" % (tag, len(hits)))
    for h in sorted(set(hits)):
        print("   ", h)
        seen.append(h)

# and every wav the listfiles mention
lf = os.path.join(ROOT, r"AndroidPort\tools\listfile_BrooDat.txt")
if os.path.exists(lf):
    with open(lf, encoding="latin1") as fp:
        names = [l.strip() for l in fp]
    hits = sorted({n for n in names
                   if "protoss" in n.lower() and n.lower().endswith(".wav")})
    print("-- BrooDat listfile: %d protoss wavs" % len(hits))
    for h in hits:
        print("   ", h)
