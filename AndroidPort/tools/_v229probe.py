"""v2.29 campaign-expansion probe: report each map's start positions and how
much open ground surrounds them, so new missions can place start units on
terrain that actually walks. Prints one line per start plus a resource tally."""
import gzip, os, sys

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"

def load(mid):
    meta = {}
    starts, units = [], []
    for line in open(os.path.join(ASSETS, "maps", mid, "meta.txt"), encoding="utf-8"):
        line = line.strip()
        if line.startswith("w="): meta["w"] = int(line[2:])
        elif line.startswith("h="): meta["h"] = int(line[2:])
        elif line.startswith("start="):
            p = line[6:].split(","); starts.append((int(p[0]), int(p[1])))
        elif line.startswith("unit="):
            p = line[5:].split(","); units.append((int(p[0]), float(p[1]), float(p[2])))
    raw = gzip.decompress(open(os.path.join(ASSETS, "maps", mid, "walk.bin.gz"), "rb").read())
    return meta["w"], meta["h"], raw, starts, units

def open_pct(raw, wm, hm, x, y, r):
    n = ok = 0
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            xx, yy = x + dx, y + dy
            if xx < 0 or yy < 0 or xx >= wm or yy >= hm: continue
            n += 1
            if raw[yy * wm + xx]: ok += 1
    return (ok / n * 100.0) if n else 0.0

def main(mids):
    for mid in mids:
        try:
            w, h, raw, starts, units = load(mid)
        except Exception as e:
            print("%-16s LOAD FAIL %s" % (mid, e)); continue
        wm, hm = w * 4, h * 4
        mins = sum(1 for u in units if u[0] == 1)
        geys = sum(1 for u in units if u[0] == 2)
        print("%-16s %3dx%-3d mini %3dx%-3d  min=%d geys=%d" % (mid, w, h, wm, hm, mins, geys))
        for i, (sx, sy) in enumerate(starts):
            print("    start%d (%4d,%4d) walk@pt=%d  r32=%.0f%% r64=%.0f%% r128=%.0f%%"
                  % (i, sx, sy, raw[(sy // 8) * wm + (sx // 8)],
                     open_pct(raw, wm, hm, sx // 8, sy // 8, 4),
                     open_pct(raw, wm, hm, sx // 8, sy // 8, 8),
                     open_pct(raw, wm, hm, sx // 8, sy // 8, 16)))

if __name__ == "__main__":
    main(sys.argv[1:])
