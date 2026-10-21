import sys, os, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import sc_archive
ar = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
cands = ["tileset\\badlands.dddata.bin","tileset\\Badlands.dddata.bin","tileset\\badlands\\dddata.bin",
         "tileset\\badlands.dddata.BIN","tileset\\platform.dddata.bin","tileset\\ashworld.dddata.bin"]
for c in cands:
    try:
        d,g = ar.read_with_gaps(c); print(f"  {c}: OK {len(d)}B gaps={len(g)}")
    except Exception as e:
        print(f"  {c}: {type(e).__name__}")
print()
print("=== local dddata.bin copies already on disk ===")
for p in glob.glob(r"F:\KF\XJZB\**\*.dddata.bin", recursive=True)[:20]:
    print(f"  {os.path.getsize(p):8d}  {p}")
for p in glob.glob(r"F:\KF\XJZB\**\dddata.bin", recursive=True)[:20]:
    print(f"  {os.path.getsize(p):8d}  {p}")
