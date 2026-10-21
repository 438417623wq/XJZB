"""Batch E probe 9: PCX header forensics for the Score panels -- is the trailing
768B really a palette, or is my pcx_decode misreading these files?"""
import os, sys
from PIL import Image

sys.path.insert(0, ".")
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

for p in ("glue\\ScoreTv\\pMain.pcx", "glue\\ScoreTv\\pInset.pcx",
          "glue\\ScoreTv\\scorebox.pcx", "glue\\Battle.net\\icons\\icons.pcx",
          "glue\\title\\Title.pcx"):
    arc = SD if SD.has(p) else BD
    d = arc.read(p)
    print("=== %s  %d bytes" % (p, len(d)))
    print("   manuf=%02x ver=%02x enc=%02x bpp=%02x" % (d[0], d[1], d[2], d[3]))
    xmin = d[4] | (d[5] << 8); ymin = d[6] | (d[7] << 8)
    xmax = d[8] | (d[9] << 8); ymax = d[10] | (d[11] << 8)
    print("   box=(%d,%d)-(%d,%d) -> %dx%d" % (xmin, ymin, xmax, ymax,
                                               xmax - xmin + 1, ymax - ymin + 1))
    print("   hdpi=%d vdpi=%d planes=%d bpl=%d" % (
        d[12] | (d[13] << 8), d[14] | (d[15] << 8), d[65], d[66] | (d[67] << 8)))
    print("   bytes[64..79] = %s" % d[64:80].hex(" "))
    print("   trailer 768 first 12: %s" % d[-768:-756].hex(" "))
    print("   last 8 bytes: %s" % d[-8:].hex(" "))
    # count RLE runs to estimate compressed pixel count
    i = 128; n = 0; runs = 0
    while i < len(d) - 769:
        b = d[i]
        if b & 0xC0 == 0xC0:
            n += b & 0x3F; i += 2; runs += 1
        else:
            n += 1; i += 1; runs += 1
    print("   body decoded %d px (want %d), runs=%d, end=%d" % (
        n, (xmax - xmin + 1) * (ymax - ymin + 1), runs, i))
    # is the trailing 768 plausible as a palette? count distinct R,G,B triples
    pal = d[-768:]
    tri = set()
    for k in range(256):
        tri.add((pal[k * 3], pal[k * 3 + 1], pal[k * 3 + 2]))
    print("   trailer distinct triples = %d ; sample %s" % (
        len(tri), [tuple(pal[k * 3:k * 3 + 3]) for k in range(4)]))
