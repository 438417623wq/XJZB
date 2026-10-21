"""Decode StarCraft GRP sprites to PNG using the unit palette.

GRP frame data is RLE:
  line type 0 -> skip N transparent lines
  line type 1 -> a row of pixels: repeat (0x80|count) transparent, else
                 `count` literal palette indices (count is 0-based)
  line type 2 -> repeat the previous line
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image  # noqa: E402
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\extracted"


def parse_pal(data):
    """A .pal file is 256 RGB triples; StarCraft uses the first 0-255."""
    colors = []
    n = min(256, len(data) // 3)
    for i in range(n):
        r, g, b = data[i * 3:i * 3 + 3]
        colors.append((r, g, b, 255))
    while len(colors) < 256:
        colors.append((0, 0, 0, 0))
    return colors


def decode_frame(data, frame, palette):
    """Decode one GRP frame into an RGBA image."""
    x, y, w, h, off = frame
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    p = off
    row = 0
    prev = None
    while row < h:
        if p >= len(data):
            break
        line_type = data[p]
        p += 1
        if line_type == 0:              # skip transparent lines
            if p >= len(data):
                break
            row += data[p]
            p += 1
            prev = None
        elif line_type == 2:            # repeat previous line
            if prev is not None:
                for i in range(w):
                    px[i, row] = prev[i]
            row += 1
        else:                           # literal row
            cur = [(0, 0, 0, 0)] * w
            col = 0
            while col < w:
                if p >= len(data):
                    break
                code = data[p]
                p += 1
                if code & 0x80:         # transparent run
                    col += code & 0x7F
                else:                   # literal run of code+1 pixels
                    for _ in range(code + 1):
                        if p >= len(data) or col >= w:
                            break
                        cur[col] = palette[data[p]]
                        p += 1
                        col += 1
            for i in range(w):
                px[i, row] = cur[i]
            prev = cur
            row += 1
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    with Archive(os.path.join(ROOT, "BrooDat.mpq")) as a:
        # find a unit palette
        names = [n for n in a.read("(listfile)").decode("latin-1")
                 .replace("\r", "\n").split("\n") if n.strip()]
        pals = [n for n in names if n.lower().endswith(".pal")]
        print("palettes: %s" % pals[:10])

        pal_data = None
        for want in ("unit\\palette\\units.pal", "palette\\units.pal",
                     "unit\\palette\\zerg.pal"):
            if a.has(want):
                pal_data = a.read(want)
                print("using palette %s (%d bytes)" % (want, len(pal_data)))
                break
        if pal_data is None:
            # try any palette
            for n in pals:
                try:
                    d = a.read(n)
                    if len(d) >= 768:
                        pal_data = d
                        print("using palette %s" % n)
                        break
                except Exception:
                    pass
        if pal_data is None:
            print("NO PALETTE FOUND; using grayscale")
            pal = [(i, i, i, 255) for i in range(256)]
        else:
            pal = parse_pal(pal_data)

        # decode a medic (small, recognisable)
        data = a.read("unit\\terran\\medic.grp")
        frames, w, h = struct.unpack_from("<HHH", data, 0)
        print("medic: %d frames %dx%d" % (frames, w, h))

        # build a contact sheet of the first 16 frames
        cols, rows = 8, 2
        sheet = Image.new("RGBA", (w * cols, h * rows), (40, 40, 60, 255))
        n = 0
        for i in range(min(16, frames)):
            x, y, fw, fh, off = struct.unpack_from("<BBBB I".replace(" ", ""), data, 6 + i * 8)
            img = decode_frame(data, (x, y, fw + 1, fh + 1, off), pal)
            nonblank = sum(1 for p in img.getdata() if p[3])
            if nonblank:
                n += 1
            sheet.paste(img, ((i % cols) * w, (i // cols) * h), img)
        out = os.path.join(OUT, "medic_sheet.png")
        sheet.save(out)
        print("wrote %s  (%d/16 frames non-empty)" % (out, n))


if __name__ == "__main__":
    main()
