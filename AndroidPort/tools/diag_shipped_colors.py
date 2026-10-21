"""Compute the dominant colour of shipped assets, to sanity-check the palette.

Canonical StarCraft colours (ground truth):
  mineral crystals  = blue/cyan
  vespene geyser    = green gas over grey rock
  terran armour/CC  = blue-grey
  desert terrain    = tan/sand

If the shipped assets disagree with all of these, the palette channel order in
the pipeline is swapped.
"""
import os
from collections import Counter
from PIL import Image

SPR = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
MAPS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"


def dom(path, top=3, minlum=40):
    im = Image.open(path).convert("RGBA")
    c = Counter()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            if a > 128 and (r + g + b) > minlum:
                c[(r, g, b)] += 1
    return c.most_common(top), im.size


print("=== shipped sprite dominant colours ===")
for k in ("mineral_b", "mineral2_b", "mineral3_b", "geyser_b",
          "marine_b", "scv_b", "zergling_b", "hydra_b",
          "cc_b", "barracks_b", "depot_b", "tank_b"):
    p = os.path.join(SPR, k + ".png")
    if not os.path.exists(p):
        print("%-14s MISS" % k); continue
    d, size = dom(p)
    print("%-14s %-10s %s" % (k, "%dx%d" % size, d))

print("\n=== shipped terrain chunks (first chunk of each map) ===")
for mid in ("hunters", "bloodbath", "volcanis", "3kingdoms"):
    p = os.path.join(MAPS, mid, "c_0_0.png")
    if not os.path.exists(p):
        print("%-12s MISS" % mid); continue
    d, size = dom(p)
    print("%-12s %-10s %s" % (mid, "%dx%d" % size, d))
