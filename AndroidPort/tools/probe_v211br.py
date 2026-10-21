"""v2.11: the repack re-sorted images.tbl's OFFSET TABLE, but the string BLOB
is probably still in the original file order. Read the blob sequentially:
that order should be the original ImageTypes order.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
ENUM_TXT = os.path.join(
    r"C:\Users\XiaoXin\AppData\Local\Temp\dsh-spill-y8WfPh\session-cb4a4d09e0b0",
    "254abc3c9a02-web_fetch.txt")

txt = open(ENUM_TXT, encoding="utf8", errors="replace").read()
i = txt.find("enum struct ImageTypes")
j = txt.find("enum struct Sounds", i)
ENUM = re.findall(r"IMAGEID_([A-Za-z0-9_]+)", txt[i:j])
print("enum names:", len(ENUM))

for tag, fn in (("SD", "StarDat.mpq"), ("BD", "BrooDat.mpq")):
    ar = sc_archive.Archive(os.path.join(ROOT, fn))
    data, gaps = ar.read_with_gaps("arr\\images.tbl")
    cnt = data[0] | (data[1] << 8)
    offs = [data[2 + 2 * k] | (data[3 + 2 * k] << 8) for k in range(cnt)]
    blob_start = min(offs)
    blob = data[blob_start:]
    # split sequentially
    seq = []
    cur = bytearray()
    for b in blob:
        if b == 0:
            if cur:
                seq.append(cur.decode("cp1252", "replace"))
                cur = bytearray()
        else:
            cur.append(b)
    print()
    print("=== %s: cnt=%d bytes=%d blobStart=%d blobSeq=%d ==="
          % (tag, cnt, len(data), blob_start, len(seq)))
    for k in range(min(80, len(seq))):
        e = ENUM[k] if k < len(ENUM) else "?"
        print("  blob%-4d %-40s  enum%-4d %s" % (k, seq[k], k, e))
    ar.close()
