"""Try name variants for the wpe file key."""
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
name = "tileset\\jungle.wpe"
bi = SD.find(name)
o, cs, fs, flags, rel = SD.block_table[bi]
SD.fp.seek(o)
raw = SD.fp.read(cs)

VALID = {0x01, 0x02, 0x08, 0x10, 0x40, 0x41, 0x80, 0x81, 0x82, 0x88, 0x22, 0x48, 0x84, 0x42}

names = ["jungle.wpe", "jungle", "tileset\\jungle.wpe", "tileset\\jungle", "wpe", "WPE",
         "tileset\\jungle.wpe.wpe", "jungle.wpe.wpe", ".wpe", "tileset\\jungle.wpe ",
         "JUNGLE.WPE", "tileset\\Jungle.wpe", "tileset\\jungle.WPE"]
for nm in names:
    base = sc_archive.hash_string(nm, sc_archive.HASH_FILE_KEY)
    for tag, k in [("plain", base), ("^fs", ((base + rel) ^ fs) & 0xFFFFFFFF),
                   ("^cs", ((base + rel) ^ cs) & 0xFFFFFFFF)]:
        dec = sc_archive.decrypt(raw, k)
        m = dec[0]
        if m in VALID:
            print("HIT %-24s %-6s mask=0x%02X" % (nm, tag, m))
print("done")
