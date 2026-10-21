import struct
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
for n in ["unit\\protoss\\dragoon.grp", "unit\\zerg\\zbrShad.grp", "unit\\terran\\marine.grp"]:
    try:
        d = SD.read(n)
    except Exception as e:
        print(n, "FAIL", e)
        continue
    fc, mw, mh = struct.unpack_from("<HHH", d, 0)
    print("%s fc=%d wxh=%dx%d size=%d" % (n, fc, mw, mh, len(d)))
    print("  bytes 6..46:", d[6:46].hex())
    cnt = min(fc, 6)
    offs = struct.unpack_from("<%dI" % cnt, d, 6)
    print("  offs:", offs)
