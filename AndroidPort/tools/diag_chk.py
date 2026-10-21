"""Debug bloodbath CHK sections."""
import os
import sc_archive
from pipeline_maps import read_chk, parse_chk

ROOT = r"F:\KF\XJZB"
chk, gaps = read_chk(os.path.join(ROOT, "maps\\(4)Blood Bath.scm"))
g, sec = parse_chk(chk, gaps)
print("sections:", len(sec))
for tag, (off, size) in sec.items():
    print("  %-8s off=%6d size=%6d  head=%s" % (tag, off, size, chk[off:off + 16].hex()))
