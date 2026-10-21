import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
T = r"F:\KF\XJZB\AndroidPort\tools"
# images_tbl2.txt: index -> path
img = {}
for line in open(os.path.join(T, "images_tbl2.txt"), encoding="latin1"):
    line = line.rstrip("\n")
    if "\t" in line:
        a, b = line.split("\t", 1)
        if a.strip().isdigit(): img[int(a)] = b.strip()
print("images_tbl2 entries:", len(img))
for i in range(557, 563): print("  img", i, img.get(i))
print()
# sprites.dat from StarDat
sys.path.insert(0, T)
import sc_archive
sd = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
sp, gaps = sd.read_with_gaps("arr\\sprites.dat")
print("sprites.dat len", len(sp), "gaps", gaps, "recs", len(sp)//8)
names = ["JUbush3s","LDtree3s","tree02","tree04","dd027","dd076","dd204","Dish1Sha","Glob02","Towr01",
         "LBSign01","LBSign05","SPThin01","HDRock02","HDRock04","LDTree1S","LDTree4S","LCShop03",
         "LCShop07","LCSign01","LCSign09","CLPlate2","DCFan1","DIDoor1"]
for i in range(25):
    im, x, y, hp, fl = struct.unpack_from("<HBBHH", sp, i*8)
    nm = names[i] if i < len(names) else "?"
    print(f"  sprite {i:2d} image={im:4d} ({img.get(im,'?')})  guess={nm}")
