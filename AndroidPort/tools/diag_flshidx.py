"""What do the flash's dominant palette indices map to in each tileset palette?"""
import os
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

IDX = [3, 4, 7, 9, 10, 12, 13, 14, 15, 17, 19, 24, 32]

for ts in ("badlands", "platform", "jungle", "desert", "ice", "twilight"):
    wpe = None
    for ar in (SD, BD):
        p = "tileset\\%s.wpe" % ts
        if ar.has(p):
            wpe, _ = ar.read_with_gaps(p)
            break
    if wpe is None:
        print(ts, "MISS")
        continue
    pal = [(wpe[i * 4 + 2], wpe[i * 4 + 1], wpe[i * 4]) for i in range(256)]
    print("%-9s " % ts + "  ".join("%d=%s" % (i, pal[i]) for i in IDX))
