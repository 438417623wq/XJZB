"""For each candidate map: the mineral/geyser cluster nearest each start point,
so a mission can put the player base where the map actually has an economy."""
import gzip, os, sys, math

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"

def load(mid):
    meta = {}; starts, units = [], []
    for line in open(os.path.join(ASSETS, "maps", mid, "meta.txt"), encoding="utf-8"):
        line = line.strip()
        if line.startswith("w="): meta["w"] = int(line[2:])
        elif line.startswith("h="): meta["h"] = int(line[2:])
        elif line.startswith("start="):
            p = line[6:].split(","); starts.append((int(p[0]), int(p[1])))
        elif line.startswith("unit="):
            p = line[5:].split(","); units.append((int(p[0]), float(p[1]), float(p[2])))
    return meta["w"], meta["h"], starts, units

def main(mids):
    for mid in mids:
        w, h, starts, units = load(mid)
        print("%-14s %dx%d" % (mid, w, h))
        for i, (sx, sy) in enumerate(starts):
            near = sorted(units, key=lambda u: math.hypot(u[1] - sx, u[2] - sy))
            mins = [u for u in near if u[0] == 1][:8]
            geys = [u for u in near if u[0] == 2][:2]
            print("   start%d(%4d,%4d) minerals(%d): %s" % (
                i, sx, sy, len(mins),
                " ".join("(%d,%d)" % (u[1], u[2]) for u in mins)))
            print("        geysers: %s" % " ".join("(%d,%d)" % (u[1], u[2]) for u in geys))

if __name__ == "__main__":
    main(sys.argv[1:])
