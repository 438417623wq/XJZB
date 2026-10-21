import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")


def dump(tag, a, b):
    print("%s [%d..%d]:" % (tag, a, b))
    for p in range(a, b, 16):
        row = d[p:min(p + 16, b)]
        print("  %5d: %s" % (p, row.hex()))


dump("f0 area", 1826, 1902)
dump("f10 area", 4034, 4110)
