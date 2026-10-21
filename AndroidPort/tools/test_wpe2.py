"""Try key variants for jungle.wpe and check the mask byte."""
import sc_archive
import mphuff

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
print("header offset:", SD.header_offset)

bi = SD.find("tileset\\jungle.wpe")
o, cs, fs, flags, rel = SD.block_table[bi]
base = sc_archive.hash_string("jungle.wpe", sc_archive.HASH_FILE_KEY)
print("flags=0x%08X rel=%d abs=%d cs=%d fs=%d" % (flags, rel, o, cs, fs))

cands = {
    "base": base,
    "(b+rel)^fs": ((base + rel) ^ fs) & 0xFFFFFFFF,
    "(b+abs)^fs": ((base + o) ^ fs) & 0xFFFFFFFF,
    "(b+rel)^cs": ((base + rel) ^ cs) & 0xFFFFFFFF,
    "(b+abs)^cs": ((base + o) ^ cs) & 0xFFFFFFFF,
    "b+rel": (base + rel) & 0xFFFFFFFF,
    "b+abs": (base + o) & 0xFFFFFFFF,
}
SD.fp.seek(o)
raw = SD.fp.read(cs)
for tag, k in cands.items():
    dec = sc_archive.decrypt(raw, k)
    m = dec[0]
    ok = "  <== looks valid" if m in (0x01, 0x02, 0x08, 0x10) or (m & 0x0F) in (1, 2, 4) else ""
    print("%-12s mask=0x%02X%s" % (tag, m, ok))
