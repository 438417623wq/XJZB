"""Full 32-bit key scan for the wpe file using first-dword structural constraints.

Constraints on plaintext dword0 = raw0 ^ (K + 0xEEEEEEEE + CRYPT[0x400 + K&0xFF]):
  byte0 = compression mask  in {0x01,0x02,0x08,0x10,0x40,0x41,0x80,0x81}
  byte1 = huffman DataType  in {1,2,3,4}        (if mask has huffman bit)
  byte3 = wpe alpha byte    == 0
"""
import numpy as np
import struct
import sc_archive
import mphuff
import mpadi

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
name = "tileset\\jungle.wpe"
bi = SD.find(name)
o, cs, fs, flags, rel = SD.block_table[bi]
SD.fp.seek(o)
raw = SD.fp.read(cs)
raw0 = struct.unpack_from("<I", raw, 0)[0]

crypt = np.array(sc_archive._CRYPT, dtype=np.uint32)
MASKSET = np.array([0x01, 0x02, 0x08, 0x10, 0x40, 0x41, 0x80, 0x81], dtype=np.uint32)

CHUNK = 1 << 26
survivors = []
for lo in range(0, 1 << 32, CHUNK):
    K = np.arange(lo, lo + CHUNK, dtype=np.uint32)
    s2 = (np.uint32(0xEEEEEEEE) + crypt[0x400 + (K & np.uint32(0xFF))]) & np.uint32(0xFFFFFFFF)
    g = (K + s2) & np.uint32(0xFFFFFFFF)
    p = raw0 ^ g
    b0 = p & np.uint32(0xFF)
    b1 = (p >> np.uint32(8)) & np.uint32(0xFF)
    b3 = (p >> np.uint32(24)) & np.uint32(0xFF)
    m = np.isin(b0, MASKSET) & np.isin(b1, np.arange(1, 5, dtype=np.uint32)) & (b3 == 0)
    idx = np.nonzero(m)[0]
    for i in idx:
        survivors.append(int(lo) + int(i))
    if lo % (1 << 30) == 0:
        print("scanned up to 0x%08X, survivors so far: %d" % (lo, len(survivors)))

print("total survivors:", len(survivors))

# full validation of survivors
def try_key(key):
    dec = sc_archive.decrypt(raw, key)
    m = dec[0]
    payload = dec[1:]
    try:
        if m & 0x01:
            payload = mphuff.decompress(payload, 1 << 20)
        if m & 0x40:
            payload = mpadi.decompress_adi_mono(payload, fs)
        if len(payload) >= fs:
            return m, payload[:fs]
    except Exception:
        return None, None
    return None, None

good = 0
for key in survivors:
    m, payload = try_key(key)
    if payload is not None and len(payload) == fs:
        print("KEY FOUND 0x%08X mask=0x%02X payload[0:16]=%s" % (key, m, payload[:16].hex()))
        good += 1
        if good > 4:
            break
print("validated:", good)
