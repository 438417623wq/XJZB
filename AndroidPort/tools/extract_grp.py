"""Extract and validate real GRP sprites using the true internal names."""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\extracted"


def grp_info(data):
    """Parse a StarCraft GRP sprite sheet header."""
    if len(data) < 6:
        return None
    frames, w, h = struct.unpack_from("<HHH", data, 0)
    if not (0 < frames < 4000) or not (0 < w <= 512) or not (0 < h <= 512):
        return None
    if 6 + frames * 8 > len(data):
        return None
    fr = []
    for i in range(frames):
        x, y, fw, fh, off = struct.unpack_from("<BBBB I".replace(" ", ""), data, 6 + i * 8)
        fr.append((x, y, fw + 1, fh + 1, off))
    return dict(frames=frames, w=w, h=h, frame_headers=fr)


def main():
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(ROOT, "BrooDat.mpq")
    with Archive(path) as a:
        names = [n for n in a.read("(listfile)").decode("latin-1")
                 .replace("\r", "\n").split("\n") if n.strip()]
        grps = [n for n in names if n.lower().endswith(".grp")]
        print("GRPs in listfile: %d" % len(grps))

        # pick out recognisable units
        interesting = [n for n in grps if any(k in n.lower() for k in
                       ("zergling", "marine", "zealot", "hydra", "scv", "drone",
                        "probe", "overlord", "firebat", "medic", "lurker"))]
        print("interesting: %s" % interesting[:15])

        ok = 0
        for n in (interesting[:10] or grps[:10]):
            try:
                data = a.read(n)
            except Exception as e:
                print("  %-40s READ FAIL %r" % (n, e))
                continue
            gi = grp_info(data)
            if gi:
                ok += 1
                print("  %-40s %7d bytes  frames=%-4d %dx%d"
                      % (n, len(data), gi["frames"], gi["w"], gi["h"]))
                # save it
                safe = n.replace("\\", "_")
                with open(os.path.join(OUT, safe), "wb") as fh:
                    fh.write(data)
            else:
                print("  %-40s %7d bytes  NOT A GRP (head=%s)"
                      % (n, len(data), data[:12].hex(" ")))
        print("\nvalid GRPs: %d" % ok)


if __name__ == "__main__":
    main()
