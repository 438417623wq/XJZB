"""Batch E probe: the plan wanted Battle.net race emblems, which this repack
does not ship (_e14). The closest real, race-distinct art we DO have is the
console wireframe set -- wire_0 Marine / wire_37 Zergling / wire_65 Zealot.
Render them to decide whether they read as emblems at row size."""
import os
from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
PICK = [("terran", 0), ("zerg", 37), ("protoss", 65)]

Z = 4
sheet = Image.new("RGB", (64 * Z * len(PICK), 64 * Z), (16, 16, 20))
for i, (race, uid) in enumerate(PICK):
    p = os.path.join(ASSETS, "ui", "wire", "wire_%d.webp" % uid)
    im = Image.open(p).convert("RGBA")
    bg = Image.new("RGB", im.size, (16, 16, 20))
    bg.paste(im, (0, 0), im)
    sheet.paste(bg.resize((64 * Z, 64 * Z), Image.NEAREST), (i * 64 * Z, 0))
    print("%-8s wire_%d %s %s" % (race, uid, im.size, p.split(os.sep)[-1]))
sheet.save(os.path.join(OUT, "_e17_wires.png"))
print("sheet", sheet.size)
