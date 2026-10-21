# _e21.py -- pick walkable spawn spots for the batch-E portrait showcase fixture.
# Reads maps/divide/walk.bin.gz (the slimmed walk map the app actually ships)
# and reports walkability at candidate pixel positions, so the temp mission's
# startUnits do not land inside a wall.
import gzip, os

A = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
MID = "divide"
meta = {}
for line in open(os.path.join(A, "maps", MID, "meta.txt"), encoding="utf-8"):
    line = line.strip()
    if "=" in line:
        k, v = line.split("=", 1)
        meta.setdefault(k, []).append(v)
w, h = int(meta["w"][0]), int(meta["h"][0])
walk = gzip.decompress(open(os.path.join(A, "maps", MID, "walk.bin.gz"), "rb").read())
print("map %s %dx%d tiles  walk bytes=%d  expect=%d" % (MID, w, h, len(walk), w * 4 * h * 4))

wMini = w * 4


def ok(px, py):
    mx, my = int(px) // 8, int(py) // 8
    if mx < 0 or my < 0 or mx >= wMini or my >= h * 4:
        return None
    return walk[my * wMini + mx] == 1


print("starts:", meta.get("start"))
print("cc  (320,240) ->", ok(320, 240))
for i, x in enumerate((120, 180, 240, 300, 360, 420)):
    print("  row y=360 x=%3d -> %s" % (x, ok(x, 360)))
for i, x in enumerate((120, 180, 240, 300, 360, 420)):
    print("  row y=300 x=%3d -> %s" % (x, ok(x, 300)))
