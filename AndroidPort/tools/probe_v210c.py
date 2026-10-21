"""v2.10 probe 3: resolve the protoss voice set batch A needs.

For each unit we want ready/what/ack/die (and probe's build/error lines).
Candidates come from the StarDat/BrooDat sfxdata.tbl entry lists; the actual
WAV is looked up in the MPQ by name so a truncated tbl string cannot produce a
false positive.
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
    out = []
    for i in range(n):
        end = data.find(b"\0", offs[i])
        out.append(data[offs[i]:end].decode("latin1"))
    return out


entries = []
for ar, tag in ((SD, "SD"), (BD, "BD")):
    try:
        for e in parse_tbl(ar.read("arr\\sfxdata.tbl")):
            entries.append((tag, e))
    except Exception as ex:
        print("FAIL", tag, ex)

# group by directory for the protoss units we care about
WANT_DIRS = ["probe", "zealot", "dragoon", "templar", "high templar", "archon",
             "shuttle", "scout", "arbiter", "carrier", "reaver", "observer",
             "corsair", "dark templar", "dark archon", "interceptor"]
print("=== sfxdata.tbl entries under Protoss\\ ===")
for tag, e in entries:
    if "protoss" in e.lower():
        print("%-3s %s" % (tag, e))
