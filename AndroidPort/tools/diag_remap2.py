"""Test the hypothesis that tileset ofire.pcx is a remap table for effects.

Each row is 256 bytes. Apply row R as  pixel -> ofire[R][pixel]  then look the
result up in the terrain palette, and see whether the flash turns fire-coloured.
"""
import os
from PIL import Image, ImageDraw
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def wpe_pal(ts):
    for ar in (SD, BD):
        p = "tileset\\%s.wpe" % ts
        if ar.has(p):
            w, _ = ar.read_with_gaps(p)
            if len(w) < 1024:
                w += bytes(1024 - len(w))
            return [(w[i * 4 + 2], w[i * 4 + 1], w[i * 4]) for i in range(256)]
    return None


def ofire_rows(ts):
    p = "tileset\\%s\\ofire.pcx" % ts
    for ar in (SD, BD, PT):
        if ar.has(p):
            d, _ = ar.read_with_gaps(p)
            # 128-byte header, then RLE payload, then 768-byte junk palette
            payload = d[128:-768]
            px = bytearray()
            i = 0
            while len(px) < 256 * 63 and i < len(payload):
                b = payload[i]; i += 1
                if b & 0xC0 == 0xC0:
                    cnt = b & 0x3F
                    if i >= len(payload):
                        break
                    px.extend(bytes([payload[i]]) * cnt); i += 1
                else:
                    px.append(b)
            return [bytes(px[r * 256:(r + 1) * 256]) for r in range(63)]
    return None


ts = "platform"
PAL = wpe_pal(ts)
ROWS = ofire_rows(ts)
print("ofire rows:", len(ROWS) if ROWS else None)
if ROWS:
    print("row0 unique vals:", len(set(ROWS[0])), "row0[32]=", ROWS[0][32], "row0[3]=", ROWS[0][3])
    print("row5[32]=", ROWS[5][32], "row10[32]=", ROWS[10][32], "row30[32]=", ROWS[30][32])
    print("row0[0:16]=", list(ROWS[0][:16]))
    print("row0[240:256]=", list(ROWS[0][240:256]))

r = load(r"unit\thingy\tmeFlshS.grp")
frames, mw, mh = r
sc = 3
use = frames[:5]

variants = [("terrain-palette", None)]
if ROWS:
    for ridx in (0, 10, 30):
        variants.append(("ofire row%d" % ridx, ROWS[ridx]))

W = mw * sc * len(use) + 8
H = (mh * sc + 18) * len(variants) + 8
img = Image.new("RGB", (W, H), (26, 28, 36))
d = ImageDraw.Draw(img)
for row, (nm, remap) in enumerate(variants):
    d.text((4, row * (mh * sc + 18) + 2), "%s (%s)" % (nm, ts), fill=(120, 255, 140))
    for i, f in enumerate(use):
        im = Image.new("RGBA", (mw, mh), (0, 0, 0, 0))
        px = im.load()
        for y in range(mh):
            for x in range(mw):
                o = y * mw + x
                if o >= len(f["px"]):
                    continue
                v = f["px"][o]
                if v != 255:
                    vv = remap[v] if remap else v
                    px[x, y] = PAL[vv] + (255,)
        im = im.resize((mw * sc, mh * sc), Image.NEAREST)
        img.paste(im, (i * mw * sc + 4, row * (mh * sc + 18) + 16), im)
img.save(os.path.join(OUT, "flsh_remap_test.png"))
print("wrote flsh_remap_test.png", img.size)
