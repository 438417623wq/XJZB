"""wpe pipeline with the CORRECT order: huffman first, then ADI mono."""
import sc_archive
import mphuff
import mpadi

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")


def read_wpe(name):
    bi = SD.find(name)
    o, cs, fs, flags, rel = SD.block_table[bi]
    key = sc_archive.hash_string(name.split("\\")[-1], sc_archive.HASH_FILE_KEY)
    key = ((key + rel) ^ fs) & 0xFFFFFFFF
    SD.fp.seek(o)
    dec = sc_archive.decrypt(SD.fp.read(cs), key)
    mask = dec[0]
    payload = dec[1:]
    print(name, "mask=0x%02X" % mask)
    if mask & 0x01:
        payload = mphuff.decompress(payload, 1 << 20)
        print("  after huffman:", len(payload), payload[:8].hex())
    if mask & 0x40:
        payload = mpadi.decompress_adi_mono(payload, fs)
        print("  after ADI:", len(payload))
    return payload[:fs]


out = read_wpe("tileset\\jungle.wpe")
print("result:", len(out), "bytes")
if len(out) == 1024:
    import collections
    alphas = collections.Counter(out[i * 4 + 3] for i in range(256))
    print("alpha distribution:", dict(alphas))
    print("entries 0-17 (B,G,R,A):")
    for i in range(18):
        print("  %3d  %3d %3d %3d %3d" % (i, out[i * 4], out[i * 4 + 1], out[i * 4 + 2], out[i * 4 + 3]))
