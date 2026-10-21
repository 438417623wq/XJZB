"""Try full-path key for wpe; validate by huffman dtype byte."""
import sc_archive
import mphuff

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")

name_full = "tileset\\jungle.wpe"
bi = SD.find(name_full)
o, cs, fs, flags, rel = SD.block_table[bi]
SD.fp.seek(o)
raw = SD.fp.read(cs)

variants = {}
for tag, nm in (("bare", "jungle.wpe"), ("full", name_full)):
    base = sc_archive.hash_string(nm, sc_archive.HASH_FILE_KEY)
    variants[tag + " plain"] = base
    variants[tag + " ^fs"] = ((base + rel) ^ fs) & 0xFFFFFFFF
    variants[tag + " ^cs"] = ((base + rel) ^ cs) & 0xFFFFFFFF
    variants[tag + " +rel"] = (base + rel) & 0xFFFFFFFF

for tag, k in variants.items():
    dec = sc_archive.decrypt(raw, k)
    m = dec[0]
    dtype = None
    info = ""
    if m in (0x01, 0x41):
        payload = dec[1:]
        try:
            out = mphuff.decompress(payload, fs)
            info = " huffman-> %d bytes: %s..." % (len(out), out[:16].hex())
        except Exception as e:
            info = " huffman FAIL %s" % e
    elif m == 0x02:
        import zlib
        try:
            out = zlib.decompress(dec[1:])
            info = " zlib-> %d bytes" % len(out)
        except Exception as e:
            info = " zlib FAIL"
    elif m == 0x08:
        from pkware import explode
        try:
            out = explode(dec[1:], fs)
            info = " pkware-> %d bytes" % len(out)
        except Exception as e:
            info = " pkware FAIL"
    print("%-12s mask=0x%02X%s" % (tag, m, info))
