import sc_archive, itertools
ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(ROOT + r"\StarDat.mpq")
BD = sc_archive.Archive(ROOT + r"\BrooDat.mpq")
PT = sc_archive.Archive(ROOT + r"\patch_rt.mpq")
arch = [("SD", SD), ("BD", BD), ("PT", PT)]
words = ["covert", "cover", "covrt", "cvert", "covertop", "covops", "covop", "ops", "spy",
         "controlt", "ctower", "ctowr", "tower", "ctrl", "control", "cntrl", "towr",
         "science", "scifac", "physics", "phys", "machin", "mach", "shop", "silo",
         "nuke", "comsat", "comsta"]
sufs = [".grp"]
found = []
for w in words:
    for s in sufs:
        n = "unit\\terran\\" + w + s
        for tag, A in arch:
            try:
                if A.has(n):
                    found.append(tag + " " + n)
                    break
            except Exception:
                pass
for f in sorted(set(found)):
    print("  " + f)
print("count", len(set(found)))
SD.close(); BD.close(); PT.close()
