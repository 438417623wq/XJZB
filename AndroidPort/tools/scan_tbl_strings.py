"""Extract every null-terminated string from the raw images.tbl data and find minerals."""
import re
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
data = SD.read("arr\\images.tbl")
print("tbl size:", len(data))

strs = set()
for m in re.finditer(rb"[\x20-\x7e]{3,}", data):
    for part in m.group(0).split(b"\x00"):
        if len(part) >= 3:
            strs.add(part.decode("latin1").lower())

hits = [s for s in strs if any(k in s for k in ("min", "bunk", "mineral", "geys", "cmd"))]
for h in sorted(hits):
    print(h)
