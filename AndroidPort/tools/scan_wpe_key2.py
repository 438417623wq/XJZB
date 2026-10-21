"""Relaxed full-space key scan for jungle.wpe (numpy, two-pass)."""
import numpy as np
import struct
import sc_archive

M32 = np.uint64(0xFFFFFFFF)

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
name = "tileset\\jungle.wpe"
bi = SD.find(name)
o, cs, fs, flags, rel = SD.block_table[bi]
SD.fp.seek(o)
raw = SD.fp.read(cs)
raw_dw = np.array(struct.unpack("<%dI" % (len(raw) // 4), raw[:len(raw) // 4 * 4]), dtype=np.uint64)
tbl = np.array(sc_archive._CRYPT, dtype=np.uint64)

MASKSET = np.array([0x01, 0x02, 0x08, 0x10, 0x40, 0x41, 0x80, 0x81], dtype=np.uint64)


def decrypt_vector(keys, raw_dw):
    """Vectorized MPQ stream decrypt. keys: u64 array. Returns (n, dwords)."""
    n = len(keys)
    seed1 = keys & M32
    seed2 = np.full(n, 0xEEEEEEEE, dtype=np.uint64)
    out = np.empty((n, len(raw_dw)), dtype=np.uint32)
    for r in range(len(raw_dw)):
        seed2 = (seed2 + tbl[0x400 + (seed1 & np.uint64(0xFF))]) & M32
        plain = raw_dw[r] ^ ((seed1 + seed2) & M32)
        out[:, r] = plain.astype(np.uint32)
        old = seed1
        seed1 = ((((~old) & M32) << np.uint64(21)) & M32)
        seed1 = ((seed1 + np.uint64(0x11111111)) & M32) | (old >> np.uint64(11))
        seed2 = (plain + seed2 + (seed2 << np.uint64(5)) + np.uint64(3)) & M32
    return out


CHUNK = 1 << 26
survivors = []
for lo in range(0, 1 << 32, CHUNK):
    K = np.arange(lo, lo + CHUNK, dtype=np.uint64)
    s2 = (np.uint64(0xEEEEEEEE) + tbl[0x400 + (K & np.uint64(0xFF))]) & M32
    g = (K + s2) & M32
    p = raw_dw[0] ^ g
    b0 = p & np.uint64(0xFF)
    b3 = (p >> np.uint64(24)) & np.uint64(0xFF)
    m = np.isin(b0, MASKSET) & (b3 == 0)
    idx = np.nonzero(m)[0]
    if len(idx):
        survivors.extend((int(lo) + int(i)) for i in idx)
print("pass1 survivors:", len(survivors), flush=True)

arr = np.array(survivors, dtype=np.uint64)
final = []
BATCH = 150000
for i in range(0, len(arr), BATCH):
    keys = arr[i:i + BATCH]
    plains = decrypt_vector(keys, raw_dw[:64])          # first 64 dwords is plenty
    ok = (plains[:, 1] >> np.uint32(24) == 0) & (plains[:, 5] >> np.uint32(24) == 0) & (plains[:, 9] >> np.uint32(24) == 0)
    for gidx in np.nonzero(ok)[0]:
        final.append(int(keys[gidx]))
print("pass2 survivors:", len(final), flush=True)

import mphuff
import mpadi
for key in final:
    keys = np.array([key], dtype=np.uint64)
    plains = decrypt_vector(keys, raw_dw)
    dec = b"".join(struct.pack("<I", int(v)) for v in plains[0])
    m = dec[0]
    payload = dec[1:]
    tag = "mask=0x%02X" % m
    try:
        if m & 0x01:
            payload = mphuff.decompress(payload, 1 << 20)
            tag += " huff->%d" % len(payload)
        if m & 0x40:
            payload = mpadi.decompress_adi_mono(payload, fs)
            tag += " adi->%d" % len(payload)
    except Exception as e:
        tag += " FAIL(%s)" % e
        continue
    if len(payload) >= fs:
        print("CANDIDATE key=0x%08X %s" % (key, tag), payload[:16].hex())
np.save("wpe_keys.npy", np.array(final, dtype=np.uint64))
