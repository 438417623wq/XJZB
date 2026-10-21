"""Dump marine.grp sector table under both sector-size hypotheses."""
import struct
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
name = "unit\\terran\\marine.grp"
bi = SD.find(name)
o, cs, fs, flags, rel = SD.block_table[bi]
print("fs=%d cs=%d flags=0x%08X sector_size=%d" % (fs, cs, flags, SD.sector_size))
key = sc_archive.hash_string("marine.grp", sc_archive.HASH_FILE_KEY)
key = ((key + rel) ^ fs) & 0xFFFFFFFF
SD.fp.seek(o)
raw = SD.fp.read(cs)

for tag, sec_size in (("4096", 4096), ("512", 512)):
    num = (fs + sec_size - 1) // sec_size
    table = sc_archive.decrypt(raw[: (num + 1) * 4 + 16], (key - 1) & 0xFFFFFFFF)
    offs = [struct.unpack_from("<I", table, i * 4)[0] for i in range(num + 1)]
    mono = all(offs[i] <= offs[i + 1] for i in range(num))
    print("%s: num=%d first=%s last=%d mono=%s last==cs:%s" % (
        tag, num, offs[:4], offs[-1], mono, offs[-1] == cs))
    # sector masks under this interpretation
    masks = []
    for i in range(min(num, 6)):
        sec = raw[offs[i]:offs[i + 1]]
        sec = sc_archive.decrypt(sec, (key + i) & 0xFFFFFFFF)
        masks.append(sec[0])
    print("   masks:", [hex(m) for m in masks])
