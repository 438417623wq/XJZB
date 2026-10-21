"""v2.10: dry-run every Protoss voice we intend to add to pipeline_sounds.WANT.

grab() resolves names through arr\\sfxdata.tbl and writes nothing when a name is
absent, so a typo would leave a unit mute with no error. This checks membership
case-insensitively first, and also hunts for the Corsair group, which the table
dump did not show under a 'protoss' path.
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


names = parse_tbl(SD.read("arr\\sfxdata.tbl"))
for nm in parse_tbl(BD.read("arr\\sfxdata.tbl")):
    if nm.lower() not in {s.lower() for s in names}:
        names.append(nm)
low = {s.lower(): s for s in names}

CAND = []
for unit, pre in [("probe", "Protoss\\PROBE\\PPr"), ("zealot", "Protoss\\ZEALOT\\PZe"),
                  ("dragoon", "Protoss\\DRAGOON\\PDr"), ("templar", "Protoss\\TEMPLAR\\PTe"),
                  ("dtemplar", "Protoss\\DARKTEMPLAR\\PDT"),
                  ("archon", "Protoss\\ARCHON\\PAr"),
                  ("scout", "Protoss\\Scout\\PSc"), ("carrier", "Protoss\\Carrier\\PCa"),
                  ("shuttle", "Protoss\\SHUTTLE\\PSh"), ("arbiter", "Protoss\\ARBITER\\PAb"),
                  ("reaver", "Protoss\\TRILOBYTE\\PTr"), ("observer", "Protoss\\Witness\\PWi")]:
    CAND.append((unit, "ready", pre + "Rdy00.WAV"))
    CAND.append((unit, "what", pre + "Wht00.WAV"))
    CAND.append((unit, "ack", pre + "Yes00.WAV"))
    CAND.append((unit, "die", pre + "Dth00.WAV"))

CAND.append(("darchon", "ready", "Protoss\\darchon\\pdardy00.wav"))
CAND.append(("darchon", "what", "Protoss\\darchon\\pdawht00.wav"))
CAND.append(("darchon", "ack", "Protoss\\darchon\\pdayes00.wav"))
CAND.append(("protoss", "error", "Protoss\\Advisor\\PAdErr00.WAV"))
CAND.append(("corsair", "ready", "sound\\protoss\\corsair\\pcordy00.wav"))
CAND.append(("corsair", "what", "sound\\protoss\\corsair\\pcowht00.wav"))
CAND.append(("corsair", "ack", "sound\\protoss\\corsair\\pcoyes00.wav"))
CAND.append(("corsair", "die", "sound\\protoss\\corsair\\pcopss00.wav"))

miss = 0
for unit, kind, nm in CAND:
    hit = low.get(nm.lower())
    if hit is None:
        miss += 1
        print("MISS %-9s %-5s %s" % (unit, kind, nm))
    else:
        print("ok   %-9s %-5s %s" % (unit, kind, hit))

print("--- candidates:", len(CAND), "miss:", miss)
print("--- table names containing 'cor':")
for s in names:
    if "cor" in s.lower():
        print("   ", s)
