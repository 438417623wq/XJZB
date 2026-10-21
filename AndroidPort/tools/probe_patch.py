"""Check patch_rt.mpq for arr data files and verify images.dat read."""
import struct
import sc_archive

PT = sc_archive.Archive(r"F:\KF\XJZB\patch_rt.mpq")
SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")

for n in ["arr\\images.dat", "arr\\images.tbl", "arr\\units.dat", "arr\\sprites.dat",
          "arr\\flingy.dat", "arr\\weapons.dat", "arr\\orders.dat", "arr\\upgrades.dat",
          "arr\\techdata.dat", "arr\\iscript.bin", "arr\\mapdata.tbl", "stat_txt.tbl",
          "rez\\stat_txt.tbl", "arr\\images.tbl"]:
    for tag, ar in (("PT", PT), ("SD", SD)):
        i = ar.info(n)
        if i:
            print("%s %8d %s" % (tag, i["size"], n))

d = PT.read("arr\\images.dat")
print("PT images.dat len:", len(d))
print("first bytes:", d[:16].hex())
n, = struct.unpack_from("<H", d, 0)
print("u16 at 0:", n, "-> (len-2)/%d" % n, (len(d) - 2) / n if n else 0)
for rec in (16, 17, 20, 24, 26, 27, 28, 30):
    c = (len(d) - 2) / rec
    if c == int(c):
        print("rec", rec, "count", int(c))

d2 = SD.read("arr\\images.dat")
print("SD images.dat len:", len(d2))
