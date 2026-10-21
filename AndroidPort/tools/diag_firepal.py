"""Decode the tileset fire pcx files: are they palettes or images?"""
import os
import struct
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))


def pcx_decode(data):
    if data[0:1] != b"\x0a" or data[1] != 5:
        return None
    xmin, ymin, xmax, ymax = struct.unpack_from("<HHHH", data, 4)
    w, h = xmax - xmin + 1, ymax - ymin + 1
    pal = data[-768:]
    px = bytearray()
    i = 128
    while len(px) < w * h and i < len(data) - 768:
        b = data[i]; i += 1
        if b & 0xC0 == 0xC0:
            cnt = b & 0x3F
            if i >= len(data) - 768:
                break
            px.extend(bytes([data[i]]) * cnt); i += 1
        else:
            px.append(b)
    return bytes(px[:w * h]), pal, w, h


for ts in ("badlands", "platform", "jungle", "desert", "ice", "twilight"):
    for kind in ("ofire", "gfire", "bfire"):
        name = "tileset\\%s\\%s.pcx" % (ts, kind)
        ar = next((a for a in (PT, SD, BD) if a.has(name)), None)
        if ar is None:
            print("%-28s MISS" % name)
            continue
        data, gaps = ar.read_with_gaps(name)
        r = pcx_decode(data)
        if not r:
            print("%-28s decode-fail len=%d" % (name, len(data)))
            continue
        px, pal, w, h = r
        lut = [(pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2]) for i in range(256)]
        # sample a few entries to see whether this is a fire gradient
        sample = [lut[i] for i in range(0, 40, 5)]
        print("%-28s %dx%d  pal[0,5,10..35]=%s" % (name, w, h, sample))
