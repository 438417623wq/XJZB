"""v2.10: the merged sfx table drops the first character of some entries.

probe_v210u merged SD's table with BD's and produced names like
'orsair\\PCoRdy00.wav'. That is either a BD table quirk or a merge bug. Dump
each table on its own and search for the suspicious stems so the lookup rule is
fixed for real.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))


def parse_tbl(data):
    n, = struct.unpack_from("<H", data, 0)
    offs = struct.unpack_from("<%dH" % n, data, 2)
    return [data[offs[i]:data.find(b"\0", offs[i])].decode("latin1")
            for i in range(n)]


for tag, ar in (("SD", SD), ("BD", BD)):
    data = ar.read("arr\\sfxdata.tbl")
    names = parse_tbl(data)
    n, = struct.unpack_from("<H", data, 0)
    print("=== %s entries=%d bytes=%d" % (tag, n, len(data)))
    for probe in ("orsair", "ardy", "dawht", "dayes", "darktemplar", "darchon"):
        hits = [s for s in names if probe in s.lower()]
        print("  %-12s %d %s" % (probe, len(hits), hits[:6]))
    # entries whose first char is lowercase while the rest is a path
    odd = [s for s in names if s[:1].islower() and "\\" in s]
    print("  lowercase-first entries: %d  e.g. %s" % (len(odd), odd[:6]))
