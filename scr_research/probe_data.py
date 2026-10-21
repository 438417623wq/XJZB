import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import sc_archive
R = r"F:\KF\XJZB"
cands = ["arr\\sprites.dat","scripts\\sprites.dat","sprites.dat","arr\\images.dat","arr\\units.dat",
         "arr\\images.tbl","rez\\stat_txt.tbl","arr\\flingy.dat","scripts\\images.dat"]
for arch in ["StarDat.mpq","BrooDat.mpq","BroodWar.mpq","patch_rt.mpq"]:
    p = os.path.join(R, arch)
    try:
        a = sc_archive.Archive(p)
    except Exception as e:
        print(arch, "OPEN FAIL", e); continue
    found = []
    for c in cands:
        try:
            if a.has(c):
                found.append((c, a.info(c).get("size")))
        except Exception as e:
            pass
    print(arch, "->", found)
