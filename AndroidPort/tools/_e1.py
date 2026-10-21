"""Batch E probe 1: exact glue sfx table spellings + what GameView plays now."""
import os, sys
sys.path.insert(0, ".")
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))


def parse_tbl(data):
    n, = __import__("struct").unpack_from("<H", data, 0)
    offs = __import__("struct").unpack_from("<%dH" % n, data, 2)
    out = []
    for i in range(n):
        end = data.find(b"\0", offs[i])
        out.append(data[offs[i]:end].decode("latin1"))
    return out


seen = []
for tag, ar in (("SD", SD), ("BD", BD)):
    for nm in parse_tbl(ar.read("arr\\sfxdata.tbl")):
        low = nm.lower()
        if "glue" in low and nm not in [s[1] for s in seen]:
            seen.append((tag, nm))
print("=== glue entries (%d)" % len(seen))
for tag, nm in seen:
    mpq = "sound/" + nm.replace("\\", "/")
    where = [t for t, ar in (("SD", SD), ("BD", BD)) if ar.has(mpq)]
    size = ""
    for t, ar in (("SD", SD), ("BD", BD)):
        if ar.has(mpq):
            size = ar.info(mpq)["size"]
            break
    print("  %-4s %-34s %-6s %s" % (tag, nm, size, where))
