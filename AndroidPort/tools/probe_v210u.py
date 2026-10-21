"""v2.10: list the Protoss voice entries the sfx table actually exposes.

pipeline_sounds.py resolves a sound by looking up its name in arr\\sfxdata.tbl
and then reading the MPQ path it points at. Before adding a single Protoss
voice to WANT we need the exact table names, because a wrong name silently
writes nothing and the unit ends up mute on the phone.
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


names = parse_tbl(SD.read("arr\\sfxdata.tbl"))
for extra in (BD,):
    try:
        for nm in parse_tbl(extra.read("arr\\sfxdata.tbl")):
            if nm.lower() not in {s.lower() for s in names}:
                names.append(nm)
    except Exception as e:
        print("BD tbl:", e)

print("total sfx entries:", len(names))
prot = [n for n in names if "protoss" in n.lower()]
print("protoss entries:", len(prot))
for n in sorted(prot):
    print("   ", n)
