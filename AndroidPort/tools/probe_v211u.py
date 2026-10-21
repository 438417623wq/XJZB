"""v2.11 batch B: locate the dat chain files and their sizes.

Visual matching failed (every zerg wireframe is the same purple smudge at 36x34;
shape IoU recovered only 2 of 6 known-good pairs), so the identities have to
come from the data files the modding tools read:

    units.dat  --flingy id-->  flingy.dat  --sprite id-->  sprites.dat
               --image id-->  images.tbl  -->  GRP file name

Archive has no directory listing, so this probes candidate paths directly.

Usage: python probe_v211u.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

WANT = [
    "arr\\units.dat",
    "arr\\flingy.dat",
    "arr\\sprites.dat",
    "arr\\images.tbl",
    "arr\\images.dat",
    "arr\\upgrades.dat",
    "arr\\weapons.dat",
    "arr\\orders.dat",
    "arr\\sfxdata.tbl",
    "arr\\sprites.tbl",
    "rez\\stat_txt.tbl",
    "rez\\images.tbl",
    "unit\\images.tbl",
]

print("%-24s %-10s %-10s %s" % ("path", "patch_rt", "StarDat", "BrooDat"))
for path in WANT:
    sizes = []
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, _ = ar.read_with_gaps(path)
            sizes.append(str(len(data)))
        else:
            sizes.append("-")
    print("%-24s %-10s %-10s %s" % (path, sizes[0], sizes[1], sizes[2]))
