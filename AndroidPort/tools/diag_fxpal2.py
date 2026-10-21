"""Compare effect frames rendered with the base palette vs the blue team ramp."""
import os
from PIL import Image, ImageDraw
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
BASE = [(wpe[i * 4 + 2], wpe[i * 4 + 1], wpe[i * 4]) for i in range(256)]

print("BASE palette 0..40:")
for i in range(0, 41, 8):
    print("  %2d..%2d" % (i, i + 7), [BASE[j] for j in range(i, i + 8)])

RAMP = [(int(16 + (128 - 16) * k / 7), int(28 + (176 - 28) * k / 7),
         int(96 + (255 - 96) * k / 7)) for k in range(8)]
TEAM = list(BASE)
for i in range(8):
    TEAM[8 + i] = RAMP[i]


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def frame_img(f, pal):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    px = im.load()
    for y in range(f["h"]):
        for x in range(f["w"]):
            v = f["px"][y * f["w"] + x]
            if v != 255:
                px[x, y] = pal[v] + (255,)
    return im


def strip(label, path):
    r = load(path)
    if r is None:
        return None
    frames, mw, mh = r
    use = frames[:min(8, len(frames))]
    scale = 2
    cell = mw * scale
    img = Image.new("RGB", (cell * len(use) + 8, mh * scale * 2 + 40), (26, 28, 36))
    d = ImageDraw.Draw(img)
    d.text((4, 2), label + "  BASE (no team recolor)", fill=(120, 255, 140))
    d.text((4, mh * scale + 20), label + "  TEAM blue", fill=(120, 200, 255))
    for i, f in enumerate(use):
        for row, pal in ((0, BASE), (1, TEAM)):
            im = frame_img(f, pal).resize((mw * scale, mh * scale), Image.NEAREST)
            img.paste(im, (i * cell + 4, row * mh * scale + 18 + row * 2), im)
    return img


for label, path in [("tmeFlshS", r"unit\thingy\tmeFlshS.grp"),
                    ("bsmoke", r"unit\thingy\bsmoke.grp"),
                    ("ephFire", r"unit\bullet\ephFire.grp")]:
    img = strip(label, path)
    if img:
        img.save(os.path.join(OUT, "fxpal_%s.png" % label))
        print("wrote fxpal_%s.png" % label)
