import os
import struct

import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")

for ts in ["badlands", "platform", "install", "ashworld", "jungle",
           "desert", "ice", "twilight"]:
    for nm in ["tileset\\%s\\dddata.bin" % ts, "tileset\\%s\\dddata.bin" % ts.capitalize()]:
        if SD.has(nm):
            d, gaps = SD.read_with_gaps(nm)
            print("%-10s %s size=%d gaps=%s" % (ts, nm, len(d), gaps))
            print("   head:", d[:48].hex(" "))
            # candidate record sizes
            for rec in (30, 32, 31, 16):
                if len(d) % rec == 0:
                    print("   divisible by %d -> %d entries" % (rec, len(d) // rec))
            break
    else:
        print("%-10s no dddata.bin" % ts)
