"""Render the muzzle flash under each tileset palette, at proper per-frame size."""
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


def frame_img(f, pal):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    px = im.load()
    for y in range(f["h"]):
        for x in range(f["w"]):
            v = f["px"][y * f["w"] + x]
            if v != 255:
                px[x, y] = pal[v] + (255,)
    return im


def sheet(label, path, pals, nframes=5):
    r = load(path)
    if r is None:
        print(label, "MISS")
        return
    frames, mw, mh = r
    sc = 3
    use = frames[:min(nframes, len(frames))]
    cellw = mw * sc
    W = cellw * len(use) + 8
    H = (mh * sc + 18) * len(pals) + 8
    img = Image.new("RGB", (W, H), (26, 28, 36))
    d = ImageDraw.Draw(img)
    for row, (nm, pal) in enumerate(pals):
        d.text((4, row * (mh * sc + 18) + 2), "%s / %s" % (label, nm), fill=(120, 255, 140))
        for i, f in enumerate(use):
            im = frame_img(f, pal).resize((cellw, mh * sc), Image.NEAREST)
            img.paste(im, (i * cellw + 4, row * (mh * sc + 18) + 16), im)
    img.save(os.path.join(OUT, "fxpal_%s.png" % label))
    print("wrote fxpal_%s.png %s" % (label, img.size))


PALS = [("jungle", wpe_pal("jungle")), ("platform", wpe_pal("platform")),
        ("desert", wpe_pal("desert"))]
for label, path in [("flshS", r"unit\thingy\tmeFlshS.grp"),
                    ("flshL", r"unit\thingy\tmeFlshL.grp"),
                    ("bsmoke", r"unit\thingy\bsmoke.grp"),
                    ("ephFire", r"unit\bullet\ephFire.grp")]:
    sheet(label, path, PALS)
