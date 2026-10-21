"""Test reading real StarCraft assets and report compression types used."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"

TARGETS = {
    "StarDat.mpq": [
        "tileset\\badlands.vr4", "tileset\\badlands.cv5", "tileset\\badlands.vx4",
        "tileset\\badlands.wpe", "tileset\\jungle.vr4", "tileset\\platform.vr4",
        "arr\\units.dat", "arr\\flingy.dat", "arr\\sprites.dat", "arr\\images.dat",
        "arr\\weapons.dat", "arr\\orders.dat", "scripts\\iscript.bin",
    ],
    "BrooDat.mpq": [
        "tileset\\ice.vr4", "tileset\\desert.vr4", "tileset\\twilight.vr4",
    ],
    "patch_rt.mpq": [],
}


def compression_type(data):
    if len(data) < 1:
        return None
    return data[0]


def main():
    for arc, names in TARGETS.items():
        path = os.path.join(ROOT, arc)
        if not os.path.exists(path):
            continue
        print("=== %s ===" % arc)
        with MPQ(path) as m:
            for n in names:
                info = m.info(n)
                if not info:
                    print("  %-28s MISSING" % n)
                    continue
                try:
                    data = m.read(n)
                    head = data[:16].hex(" ")
                    print("  %-28s OK  len=%-8d head=%s" % (n, len(data), head))
                except Exception as e:
                    print("  %-28s FAIL %r" % (n, e))
        print()


if __name__ == "__main__":
    main()
