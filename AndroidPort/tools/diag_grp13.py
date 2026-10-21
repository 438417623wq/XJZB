import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")

# raw dump: frame 8 (working, off=3613) vs frame 10 (failing, off=4044)
for fi, off, h in ((8, 3613, 25), (10, 4044, 25)):
    print("=== frame %d off=%d h=%d table bytes:" % (fi, off, h))
    print(d[off:off + 2 * h].hex())
    print("row0@off+%d:" % int.from_bytes(d[off:off + 2], "little"),
          d[off + 50:off + 66].hex())

# Also verify frame 9 == frame 8 data (offsets identical) and frame 11 == 10
print("f9 head:", d[6 + 9 * 8:6 + 10 * 8].hex())
print("f10 head:", d[6 + 10 * 8:6 + 11 * 8].hex())
print("f11 head:", d[6 + 11 * 8:6 + 12 * 8].hex())
