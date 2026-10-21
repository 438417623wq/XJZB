import sc_archive
ROOT = r"F:\KF\XJZB"
for mpq in ("StarDat.mpq", "BrooDat.mpq", "patch_rt.mpq"):
    A = sc_archive.Archive(ROOT + "\\" + mpq)
    for nm in ("arr\\images.tbl", "arr\\images.dat", "scripts\\images.tbl"):
        try:
            if A.has(nm):
                d = A.read(nm)
                print(mpq, nm, "len", len(d))
        except Exception as e:
            print(mpq, nm, "ERR", e)
    A.close()
