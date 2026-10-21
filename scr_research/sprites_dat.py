import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import sc_archive
R = r"F:\KF\XJZB"
T = r"F:\KF\XJZB\AndroidPort\tools"
img = {}
for l in open(os.path.join(T,"images_tbl2.txt"), encoding="utf-8", errors="replace"):
    a,b = l.rstrip("\n").split("\t",1); img[int(a)] = b
for arch in ("StarDat.mpq","BrooDat.mpq"):
    a = sc_archive.Archive(os.path.join(R, arch))
    data, gaps = a.read_with_gaps("arr\\sprites.dat")
    size = a.info("arr\\sprites.dat")["size"]
    print(f"=== {arch} sprites.dat size={size} gaps={len(gaps)}")
    for recsz in (8, 10):
        n = size//recsz
        print(f"   recsize {recsz}: {n} records")
    # try 8-byte records: u16 image, ...
    n8 = size//8
    hits = 0
    print("   first 24 records as 8-byte (u16 image, u8 x, u8 y, u16 hpbar, u16 flags):")
    for r in range(min(24, n8)):
        u = struct.unpack_from("<HBBHH", data, r*8)
        print(f"     sprite {r:3d}: image={u[0]:5d} {img.get(u[0],'?')[:44]:46s} rest={u[1:]}")
    a.close()
