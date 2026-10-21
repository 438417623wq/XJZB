"""Test wpe reading: decrypt with fix-key, then huffman-decode the payload."""
import sc_archive
import mphuff

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")

bi = SD.find("tileset\\jungle.wpe")
o, cs, fs, flags, rel = SD.block_table[bi]
key = sc_archive.hash_string("jungle.wpe", sc_archive.HASH_FILE_KEY)
key = ((key + rel) ^ fs) & 0xFFFFFFFF
SD.fp.seek(o)
raw = SD.fp.read(cs)
dec = sc_archive.decrypt(raw, key)
print("mask byte after decrypt: 0x%02X" % dec[0], "fs:", fs)

payload = dec[1:]
try:
    out = mphuff.decompress(payload, fs)
    print("huffman-only ->", len(out), "bytes; first 32:", out[:32].hex())
    if len(out) == 1024:
        # sanity: alpha (4th byte of BGRA) should be 0 everywhere
        alphas = [out[i * 4 + 3] for i in range(256)]
        print("alpha values nonzero:", sum(1 for a in alphas if a) if len(alphas) == 256 else "n/a")
        for i in range(8, 16):
            print("  pal[%d] B=%d G=%d R=%d" % (i, out[i * 4], out[i * 4 + 1], out[i * 4 + 2]))
except Exception as e:
    print("huffman-only FAILED:", type(e).__name__, e)
