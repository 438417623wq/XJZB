import sys, os, struct
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import sc_archive
D = r"F:\KF\XJZB\scr_research\tileset"
for ts, arch in [("badlands","StarDat.mpq"),("jungle","StarDat.mpq"),("twilight","BrooDat.mpq")]:
    a = sc_archive.Archive(os.path.join(r"F:\KF\XJZB", arch))
    data, gaps = a.read_with_gaps("tileset\\%s.cv5" % ts)
    size = a.info("tileset\\%s.cv5" % ts)["size"]
    print(f"=== {ts}: recorded size={size} groups={size//52} gaps={gaps}")
    for gp, gl in gaps:
        print(f"    gap bytes {gp}..{gp+gl-1} -> groups {gp//52}..{(gp+gl-1)//52}")
    b = open(os.path.join(D, ts + ".cv5"),"rb").read()
    n = len(b)//52
    print("    --- group 1024 and 1100 hexdump:")
    for g in (1024, 1100, 1200):
        if g < n:
            print(f"     g{g}: {b[g*52:g*52+30].hex(' ')}")
            print(f"          u16: {struct.unpack_from('<15H', b, g*52)}")
