"""Decompress sectors WITHOUT the size cap to test variable plain sizes."""
import struct
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")

for name in ("unit\\terran\\marine.grp", "unit\\terran\\SCV.grp", "unit\\terran\\control.grp"):
    bi = SD.find(name)
    o, cs, fs, flags, rel = SD.block_table[bi]
    key = sc_archive.hash_string(name.split("\\")[-1], sc_archive.HASH_FILE_KEY)
    key = ((key + rel) ^ fs) & 0xFFFFFFFF
    SD.fp.seek(o)
    raw = SD.fp.read(cs)
    num = (fs + SD.sector_size - 1) // SD.sector_size
    table = sc_archive.decrypt(raw, (key - 1) & 0xFFFFFFFF)
    offs = [struct.unpack_from("<I", table, i * 4)[0] for i in range(num + 1)]
    total = 0
    sizes = []
    for i in range(num):
        sec = raw[offs[i]:offs[i + 1]]
        sec = sc_archive.decrypt(sec, (key + i) & 0xFFFFFFFF)
        body = sec[1:]  # strip mask
        from pkware import explode
        out = explode(body, None)  # uncapped
        sizes.append(len(out))
        total += len(out)
    print("%s: fs=%d natural sizes=%s total=%d %s" % (
        name, fs, sizes, total, "<== MATCHES fs" if total == fs else ""))
