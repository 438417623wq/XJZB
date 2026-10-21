import os
from PIL import Image
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
OUT = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\ui"


def pcx_decode(data):
    if data[0:1] != b"\x0a" or data[1] != 5:
        return None
    x0 = data[4] | (data[5] << 8)
    y0 = data[6] | (data[7] << 8)
    x1 = data[8] | (data[9] << 8)
    y1 = data[10] | (data[11] << 8)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    print("pcx bounds:", w, "x", h, "data len:", len(data))
    pal = data[-768:]
    px = bytearray(w * h)
    i = 128
    end = len(data) - 768
    pos = 0
    while pos < w * h and i < end:
        b = data[i]
        i += 1
        if b & 0xC0 == 0xC0:
            cnt = b & 0x3F
            v = data[i] if i < end else 0
            i += 1
            for _ in range(cnt):
                if pos < w * h:
                    px[pos] = v
                    pos += 1
        else:
            px[pos] = b
            pos += 1
    print("decoded pixels:", pos, "of", w * h)
    return bytes(px), pal, w, h


name = "glue" + chr(92) + "title" + chr(92) + "Title.pcx"
data, gaps = SD.read_with_gaps(name)
r = pcx_decode(data)
if r:
    px, pal, w, h = r
    img = Image.new("RGB", (w, h))
    fp = img.load()
    for y in range(min(h, len(pal) // 3 // w)):
        base = y * w
        for x in range(w):
            j = (base + x) * 3
            fp[x, y] = (pal[j + 2], pal[j + 1], pal[j])
    img.save(os.path.join(OUT, "title.png"))
    print("title.png", w, "x", h)
