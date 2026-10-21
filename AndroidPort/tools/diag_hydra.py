"""Debug hydra.grp sector masks."""
import struct
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
name = "unit\\zerg\\hydra.grp"
bi = SD.find(name)
o, cs, fs, flags, rel = SD.block_table[bi]
print("fs=%d cs=%d flags=0x%08X" % (fs, cs, flags))
key = sc_archive.hash_string("hydra.grp", sc_archive.HASH_FILE_KEY)
key = ((key + rel) ^ fs) & 0xFFFFFFFF
SD.fp.seek(o)
raw = SD.fp.read(cs)
num = (fs + SD.sector_size - 1) // SD.sector_size
tbl = SD._try_sector_table(raw, key, flags, num, SD.sector_size)
print("sectors:", num, "tbl ok:", bool(tbl))
masks = []
for i in range(num):
    sec = raw[tbl[i]:tbl[i + 1]]
    sec = sc_archive.decrypt(sec, (key + i) & 0xFFFFFFFF)
    masks.append(sec[0])
print("masks:", [hex(m) for m in masks])
