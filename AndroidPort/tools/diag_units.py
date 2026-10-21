"""Debug the UNIT section of bloodbath in original coordinates."""
import os
import sc_archive
from pipeline_maps import read_chk, parse_chk

ROOT = r"F:\KF\XJZB"
chk, gaps = read_chk(os.path.join(ROOT, "maps\\(4)Blood Bath.scm"))
g, sec = parse_chk(chk, gaps)
for tag, (off, size) in sorted(sec.items(), key=lambda t: t[1][0]):
    print("%s off=%6d size=%6d head=%s" % (tag, off, size, g.bytes_at(off, 16).hex()))

if b"UNIT" in sec:
    off, size = sec[b"UNIT"]
    print("\nUNIT count u16:", g.u16(off))
    # try: maybe entries are fixed 26? print first 64 bytes
    print("first 64:", g.bytes_at(off, 64).hex())
