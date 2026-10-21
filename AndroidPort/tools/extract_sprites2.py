"""Extract unit sprites preferring StarDat (classic RLE GRPs).

BrooDat stores a different GRP variant, so StarDat is the primary source.
Composites each frame at its (x, y) offset inside the unit bounding box.
"""

import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image  # noqa: E402
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\assets_src"


def parse_frames(d):
    if len(d) < 14:
        return None
    frames, w, h = struct.unpack_from("<HHH", d, 0)
    if not (0 < frames < 4000) or not (0 < w <= 512) or not (0 < h <= 512):
        return None
    if 6 + frames * 8 > len(d):
        return None
    frs = []
    for i in range(frames):
        x, y, fw, fh, off = struct.unpack_from("<BBBBI", d, 6 + i * 8)
        frs.append((x, y, fw + 1, fh + 1, off))
    return (frames, w, h, frs)


def decode_frame(d, fr, pal):
    x, y, w, h, off = fr
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    p = off
    row = 0
    prev = None
    while row < h and p < len(d):
        lt = d[p]
        p += 1
        if lt == 0:
            if p >= len(d):
                break
            row += d[p]
            p += 1
            prev = None
        elif lt == 2:
            if prev:
                for i in range(w):
                    px[i, row] = prev[i]
            row += 1
        else:
            cur = [(0, 0, 0, 0)] * w
            col = 0
            while col < w and p < len(d):
                c = d[p]
                p += 1
                if c & 0x80:
                    col += c & 0x7F
                else:
                    for _ in range(c + 1):
                        if p >= len(d) or col >= w:
                            break
                        cur[col] = pal[d[p]]
                        p += 1
                        col += 1
            for i in range(w):
                px[i, row] = cur[i]
            prev = cur
            row += 1
    return img


def sheet_for(d, gi, pal, max_frames=64, cols=8):
    frames, w, h, frs = gi
    n = min(frames, max_frames)
    rows = (n + cols - 1) // cols
    sh = Image.new("RGBA", (w * cols, h * rows), (0, 0, 0, 0))
    for i in range(n):
        fr = frs[i]
        img = decode_frame(d, fr, pal)
        sh.paste(img, ((i % cols) * w + fr[0], (i // cols) * h + fr[1]), img)
    return sh, n


def load_palette():
    p = os.path.join(OUT, "palettes", "units.pal")
    if not os.path.exists(p):
        return [(i, i, i, 255) for i in range(256)]
    b = open(p, "rb").read()
    return [tuple(b[i * 3:i * 3 + 3]) + (255,) for i in range(256)]


def main():
    pal = load_palette()
    os.makedirs(os.path.join(OUT, "sprites"), exist_ok=True)

    with Archive(os.path.join(ROOT, "BrooDat.mpq")) as a:
        names = [n for n in a.read("(listfile)").decode("latin-1")
                 .replace("\r", "\n").split("\n") if n.strip()]
    grps = [n for n in names if n.lower().endswith(".grp")]

    manifest = []
    with Archive(os.path.join(ROOT, "StarDat.mpq")) as sd:
        for n in grps:
            bi = sd.find(n)
            if bi is None:
                continue
            try:
                d = sd.read_block(bi, n.split("\\")[-1])
            except Exception:
                continue
            gi = parse_frames(d)
            if not gi:
                continue
            try:
                sh, nf = sheet_for(d, gi, pal)
            except Exception:
                continue
            safe = n.replace("\\", "__").replace(".grp", "")
            path = os.path.join(OUT, "sprites", safe + ".png")
            sh.save(path)
            manifest.append({"name": n, "file": "sprites/%s.png" % safe,
                             "frames": gi[0], "w": gi[1], "h": gi[2], "sheet": nf})
    with open(os.path.join(OUT, "sprites.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    print("sprites exported from StarDat: %d" % len(manifest))
    for m in manifest[:20]:
        print("   %-36s frames=%-5d %dx%d" % (m["name"], m["frames"], m["w"], m["h"]))


if __name__ == "__main__":
    main()
