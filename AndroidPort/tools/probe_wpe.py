"""Diagnose the jungle.wpe read failure: flags, keys, compression byte."""
import struct
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")

bi = SD.find("tileset\\jungle.wpe")
o, cs, fs, flags, rel = SD.block_table[bi]
print("block %d: offset=%d csize=%d size=%d flags=0x%08X rel=%d" % (bi, o, cs, fs, flags, rel))
print("sector size:", SD.sector_size)

fp = SD.fp
fp.seek(o)
raw = fp.read(cs)
print("first raw bytes:", raw[:16].hex())

# try plain (no decrypt) decompress
try:
    out = sc_archive.decompress_sector(raw, fs)
    print("plain decompress OK:", len(out), out[:8].hex())
except Exception as e:
    print("plain decompress FAIL:", e)

# try with decrypt (both key rules)
name = "jungle.wpe"
key = sc_archive.hash_string(name, sc_archive.HASH_FILE_KEY)
k2 = ((key + rel) ^ fs) & 0xFFFFFFFF
for tag, kk in (("plain-key", key), ("fix-key", k2)):
    dec = sc_archive.decrypt(raw, kk)
    try:
        out = sc_archive.decompress_sector(dec, fs)
        print(tag, "decompress OK:", len(out), out[:8].hex())
    except Exception as e:
        print(tag, "decompress FAIL:", e, "first bytes:", dec[:8].hex())
