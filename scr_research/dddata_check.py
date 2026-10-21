import sys, os, struct, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
d = r"F:\KF\XJZB\scr_research\tileset"
def nonempty(t):
    b = open(os.path.join(d, f"{t}.dddata.bin"), "rb").read()
    return {e for e in range(512) if any(struct.unpack_from("<256H", b, e*512))}
plat = nonempty("platform")
ash  = nonempty("ashworld")
print("platform non-empty count:", len(plat))
for i in (137, 256, 257):
    print(f"  platform id {i}: {'PRESENT' if i in plat else 'ABSENT'}")
print("platform non-empty ids:", sorted(plat))
print()
print("ashworld non-empty count:", len(ash), "max:", max(ash))
print("  is 142 present?", 142 in ash)
print("ashworld non-empty ids:", sorted(ash))
print()
# what rows do 256/257 have? show the required-tiles row pattern (nonzero cells)
b = open(os.path.join(d, "platform.dddata.bin"), "rb").read()
for i in (137, 256, 257):
    row = struct.unpack_from("<256H", b, i*512)
    nz = [k for k,v in enumerate(row) if v]
    print(f"platform dddata[{i}] nonzero cells={len(nz)} first={nz[:8]} vals={[row[k] for k in nz[:8]]}")
