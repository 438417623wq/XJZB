"""v2.44: re-bake ONLY the walk bitmap of one shipped map.

pipeline_maps.build_map() re-renders the terrain chunks, which would rewrite
every c_*.png/webp in the asset tree; for the walk repair we want a diff of
exactly one file per fixed map. This driver re-reads the CHK, runs the same
repair_walk() the pipeline now bakes with, and replaces walk.bin.gz in place.
It also re-verifies the written bytes with reachable() and prints the door
count, so the result is checkable at a glance.

Usage: python _rebakewalk.py divide   (id as in pipeline_maps LEGACY_GROUPS)
"""
import gzip
import os
import sys

import numpy as np

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

SRC = {m[1]: m[0] for m in pm.MAPS}
SRC.update({
    "bloodbath": r"maps\(4)Blood Bath.scm",
    "bottleneck": r"maps\(2)Bottleneck.scm",
    "boxer": r"maps\(2)Boxer.scm",
    "hunters": r"maps\(8)The Hunters.scm",
    "darkcrystal": r"maps\(4)Dark Crystal.scm",
    "river": r"maps\(2)River Crossing.scm",
    "3kingdoms": r"maps\(3)Three Kingdoms.scm",
    "divide": r"maps\(2)The Small Divide.scm",
    "cyclone": r"maps\(4)Cyclone.scm",
    "volcanis": r"maps\(2)Volcanis.scm",
})


def main(map_id):
    src = SRC.get(map_id)
    if src is None:
        raise SystemExit("unknown map id: %s" % map_id)
    chk, gaps = pm.read_chk(os.path.join(pm.ROOT, src))
    g, sec = pm.parse_chk(chk, gaps)
    off, _ = sec[b"DIM "]
    w, h = g.u16(off), g.u16(off + 2)
    eoff, _ = sec[b"ERA "]
    ts = pm.load_tileset(pm.TILESETS.get(g.byte(eoff), "platform"))
    moff, _ = sec[b"MTXM"]
    mtwm = [g.u16(moff + i * 2) for i in range(w * h)]
    walk_raw = pm._walk_bitmap(w, h, mtwm, ts)
    starts = pm._starts_of(g, sec)
    # _starts_of returns MINITILE coords already (it divides the CHK pixels by
    # 8 itself); dividing again put the starts at (5,3)/(27,27), both inside
    # the main component, so the repair "found" nothing to fix. build_map
    # parses its own pixel coords, so its // 8 there is correct -- only this
    # driver had the double division.
    starts_mini = [(int(x), int(y)) for x, y in starts]

    before = pm.reachable(walk_raw, starts_mini)
    ship = pm.repair_walk(walk_raw, starts_mini)
    if ship is None:
        print("%s: no repair found (genuine island); walk.bin untouched" % map_id)
        return 1
    after = pm.reachable(ship, starts_mini)
    doors = int(((ship.astype(bool)) & ~walk_raw.astype(bool)).sum())
    filled = int((pm._fill_enclosed(walk_raw).astype(bool) & ~walk_raw.astype(bool)).sum())
    print("%s: raw connected=%s -> shipped connected=%s  doors=%d enclosedFilled=%d"
          % (map_id, before, after, doors, filled))
    if not after:
        print("REPAIR-FAIL: repaired bitmap still does not connect the starts")
        return 1

    outdir = os.path.join(pm.OUT, "maps", map_id)
    gz = os.path.join(outdir, "walk.bin.gz")
    with open(gz, "wb") as fp:
        fp.write(gzip.compress(ship.astype(np.uint8).tobytes(), 9))
    # read-back check: the exact bytes the game will gunzip must verify.
    back = np.frombuffer(gzip.open(gz, "rb").read(), dtype=np.uint8)
    ok = pm.reachable(back.reshape(h * 4, w * 4), starts_mini)
    print("wrote %s (%d bytes) readback connected=%s" % (gz, back.size, ok))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "divide"))
