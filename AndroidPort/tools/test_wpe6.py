"""More key formulas for wpe + a numpy-based key scan fallback."""
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")

name = "tileset\\jungle.wpe"
bi = SD.find(name)
o, cs, fs, flags, rel = SD.block_table[bi]
SD.fp.seek(o)
raw = SD.fp.read(cs)
base = sc_archive.hash_string("jungle.wpe", sc_archive.HASH_FILE_KEY)
full = sc_archive.hash_string(name, sc_archive.HASH_FILE_KEY)

VALID = {0x01, 0x02, 0x08, 0x10, 0x20, 0x40, 0x41, 0x80, 0x81, 0x82, 0x88,
         0x22, 0x48, 0x84, 0x42, 0x21, 0x0A, 0x03, 0x09, 0x12, 0x60, 0xC0}

for tag, k in [("base", base), ("base^fs", base ^ fs), ("base^cs", base ^ cs),
               ("base^rel", base ^ rel), ("full^fs", full ^ fs),
               ("(base+rel)^fs", ((base + rel) ^ fs) & 0xFFFFFFFF),
               ("(full+rel)^fs", ((full + rel) ^ fs) & 0xFFFFFFFF),
               ("(base+fs)^rel", ((base + fs) ^ rel) & 0xFFFFFFFF)]:
    dec = sc_archive.decrypt(raw, k)
    m = dec[0]
    print("%-16s 0x%08X mask=0x%02X %s" % (tag, k, m, "<== VALID" if m in VALID else ""))
