"""Read the real (listfile)s now that implode works, and locate unit sprites."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"


def main():
    for arc in ("BrooDat.mpq", "StarDat.mpq", "BroodWar.mpq", "patch_rt.mpq"):
        path = os.path.join(ROOT, arc)
        if not os.path.exists(path):
            continue
        with Archive(path) as a:
            print("=" * 74)
            print(arc)
            lf = []
            for cand in ("(listfile)", "(LISTFILE)"):
                try:
                    data = a.read(cand)
                    lf = [n for n in data.decode("latin-1").replace("\r", "\n").split("\n") if n.strip()]
                    break
                except Exception:
                    continue
            print("  listfile entries: %d" % len(lf))
            if lf:
                grps = [n for n in lf if n.lower().endswith(".grp")]
                pcx = [n for n in lf if n.lower().endswith(".pcx")]
                wavs = [n for n in lf if n.lower().endswith(".wav")]
                print("  grp=%d pcx=%d wav=%d" % (len(grps), len(pcx), len(wavs)))
                print("  sample grp: %s" % grps[:12])
                print("  sample other: %s" % [n for n in lf if not n.lower().endswith('.grp')][:12])


if __name__ == "__main__":
    main()
