"""v2.43 section 2: fold the repeated bench runs into one min-per-cell table.

The render column is pure noise on this host (the same build varied 18.3 vs
26.9 ms/tick between runs), so a single run cannot support any claim. Taking
the minimum over N runs is the usual way to squeeze the scheduler out of a
microbenchmark: the fastest observed pass is the one least interfered with.

Counters (auraQ/auraS/acqQ/.../pathD) and the state hash are deterministic --
they must be identical in every run of the same column set, and a mismatch
means the build changed mid-measurement, which this script reports as a
failure rather than silently averaging away.
"""

import glob
import sys

COLS = ["upd_avg", "upd_p95", "upd_max", "ren_avg", "ren_p95", "ren_max",
        "ents", "auraQ", "auraS", "acqQ", "acqS", "gridQ", "gridC",
        "pathQ", "pathD", "hash"]
FLOAT_COLS = set(COLS[:6])


def readtext(p):
    """PowerShell's `>` writes UTF-16LE with a BOM on this host, but a run
    captured through a pipe comes out UTF-8. Sniff instead of guessing."""
    raw = open(p, "rb").read()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


def parse(paths):
    rows = {}
    for p in paths:
        for line in readtext(p).splitlines():
            f = line.split()
            if len(f) != 2 + len(COLS):
                continue
            try:
                n = int(f[0])
            except ValueError:
                continue
            key = (n, f[1])
            vals = dict(zip(COLS, f[2:]))
            rows.setdefault(key, []).append((vals, p))
    return rows


def main():
    tag = sys.argv[1]
    paths = sorted(glob.glob("out/_bench_%s*.txt" % tag))
    if not paths:
        print("no runs for %s" % tag)
        return 1
    print("[%s] runs=%d" % (tag, len(paths)))
    for p in paths:
        print("   " + p)
    rows = parse(paths)
    print("  n  phase        upd_avg upd_p95 upd_max ren_avg ren_p95 ren_max"
          "  ents  auraQ  auraS  acqQ  acqS  gridQ  gridC  pathQ  pathD  hash")
    bad = 0
    for key in sorted(rows):
        runs = rows[key]
        n, phase = key
        out = []
        for c in COLS:
            vs = [r[0][c] for r in runs]
            if c in FLOAT_COLS:
                out.append(min(float(v) for v in vs))
            else:
                uniq = set(vs)
                if len(uniq) != 1:
                    bad += 1
                    print("  !! %s %s column %s differs across runs: %s"
                          % (n, phase, c, sorted(uniq)))
                out.append(int(vs[0]))
        print("  %3d  %-12s %6.3f  %6.3f  %6.3f  %6.3f  %6.3f  %6.3f"
              " %5d %6d %6d %6d %6d %6d %7d %6d %6d  %s"
              % (n, phase, out[0], out[1], out[2], out[3], out[4], out[5],
                 out[6], out[7], out[8], out[9], out[10], out[11], out[12],
                 out[13], out[14], out[15]))
    if bad:
        print("[%s] FAIL: %d non-deterministic counter cells" % (tag, bad))
        return 1
    print("[%s] OK: counters identical in every run" % tag)
    return 0


if __name__ == "__main__":
    sys.exit(main())
