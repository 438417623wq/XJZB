"""Verify every sector decompresses to EXACTLY the expected size."""
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
    bad = 0
    out_len = 0
    for i in range(num):
        sec = raw[offs[i]:offs[i + 1]]
        sec = sc_archive.decrypt(sec, (key + i) & 0xFFFFFFFF)
        want = min(SD.sector_size, fs - out_len)
        got = sc_archive.decompress_sector(sec, want)
        if len(got) != want:
            print("%s sector %d: want=%d got=%d (mask=0x%02X)" % (name, i, want, len(got), sec[0]))
            bad += 1
        out_len += len(got)
    print("%s: %d/%d sectors short, total=%d (fs=%d)" % (name, bad, num, out_len, fs))
