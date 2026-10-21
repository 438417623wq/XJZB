import mpyq

a = mpyq.MPQArchive(r"F:\KF\XJZB\StarDat.mpq", listfile=False)
d = a.read_file("tileset\\jungle.wpe")
print("wpe len:", len(d) if d else d)
if d:
    print(d[:32].hex())
d2 = a.read_file("unit\\terran\\marine.grp")
print("marine via mpyq:", len(d2) if d2 else d2)
