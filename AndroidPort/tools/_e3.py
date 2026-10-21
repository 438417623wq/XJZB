"""Batch E probe 3: do the SMK portraits and Battle.net icons actually exist?

The listfile names 100+ portrait .smk files; verify whether this repack carries
them, and check the SMK header so we know if a first-frame still is feasible.
Also decode glue/Battle.net/icons/icons.pcx (the race emblems).
"""
import os, struct, sys
sys.path.insert(0, ".")
import sc_archive

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
os.makedirs(OUT, exist_ok=True)

PORTS = [
    "portrait\\tmedic\\TMEfid00.smk", "portrait\\ZLurker\\ZLuFid00.smk",
    "portrait\\ZDevour\\ZDvFid00.smk", "portrait\\tBomber\\TBmFid00.smk",
    "portrait\\PCORSAIR\\PCsFid00.smk", "portrait\\pDarchon\\PDaFid00.smk",
    "portrait\\tSam\\Tsmfid00.smk", "portrait\\PRaz\\PRzFid00.smk",
]
print("=== portrait SMK presence")
n_hit = 0
for p in PORTS:
    got = []
    for tag, ar in (("SD", SD), ("BD", BD)):
        if ar.has(p):
            got.append((tag, ar.info(p)["size"]))
    if got:
        n_hit += 1
    print("  %-38s %s" % (p, got or "MISS"))
print("  hits %d/%d" % (n_hit, len(PORTS)))

if n_hit:
    p = PORTS[0]
    for ar in (SD, BD):
        if ar.has(p):
            d, g = ar.read_with_gaps(p)
            print("=== %s head %d bytes: %s" % (p, min(64, len(d)),
                                                d[:64].hex(" ")))
            if d[:4] == b"SMK2" or d[:4] == b"SMK4":
                (w, h, nf, fr, flags) = struct.unpack_from("<IIII", d, 4)[:4], 0, 0, 0
                print("  signature %s" % d[:4])
                print("  w=%d h=%d frames=%d" % struct.unpack_from("<iii", d, 4))
            break

print("=== Battle.net race emblems (icons.pcx)")
p = "glue\\Battle.net\\icons\\icons.pcx"
for ar in (SD, BD):
    if ar.has(p):
        d, g = ar.read_with_gaps(p)
        xmin, ymin, xmax, ymax = struct.unpack_from("<HHHH", d, 4)
        print("  size=%d bpp=%d xmin=%d ymin=%d xmax=%d ymax=%d -> %dx%d"
              % (len(d), d[3], xmin, ymin, xmax, ymax,
                 xmax - xmin + 1, ymax - ymin + 1))
        print("  has 768-byte tail palette: %s" % (d[-769] == 0x0C))
        break

print("=== is there a glue palette?")
for p in ("glue\\palettes\\glue.pal", "glue\\palette\\glue.pal",
          "glue\\battle.net\\icons\\icons.pal", "glue\\palettes\\bnet.pal",
          "glue\\Palettes\\glue.pal"):
    got = [t for t, ar in (("SD", SD), ("BD", BD)) if ar.has(p)]
    print("  %-44s %s" % (p, got or "MISS"))
