"""Segment each tileset's dddata.bin into non-zero clusters (runs of non-zero
u16 pairs separated by >=32 zero bytes) and print offset + extent. If cluster
order == DD2 id order, the cluster's coordinate extent fingerprints the
doodad's on-map size, which can be matched against the extracted doodad art.
"""
import struct

import numpy as np

import sc_archive
from gapio import GapReader

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")

for ts in ("platform", "badlands", "ashworld", "jungle", "install"):
    d, gaps = SD.read_with_gaps("tileset\\%s\\dddata.bin" % ts)
    arr = np.frombuffer(d, dtype=np.uint8)
    # u16 pairs view
    n2 = len(arr) // 2
    vals = arr[: n2 * 2].reshape(n2, 2)
    nz = (vals[:, 0] | vals[:, 1]) != 0
    # cluster: non-zero run, split on >=16 consecutive zero u16s
    clusters = []
    i = 0
    while i < n2:
        if nz[i]:
            j = i
            while j < n2 and not (not nz[j] and all(not nz[j + k] for k in range(min(16, n2 - j)))):
                j += 1
            seg = vals[i:j]
            mx = int(seg[:, 0].max()), int(seg[:, 1].max())
            clusters.append((i * 2, j * 2, len(seg), mx))
            i = j + 16
        else:
            i += 1
    print("=== %s: %d clusters ===" % (ts, len(clusters)))
    for off, end, cnt, mx in clusters[:40]:
        print("  off=%7d..%-7d u16s=%-4d maxpair=%s" % (off, end, cnt, mx))
