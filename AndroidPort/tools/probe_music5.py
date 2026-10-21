"""Settle the BGM question: recover the key of every large encrypted block and
identify what it actually is.

probe_music1-4 all failed to name the big blocks because StarDat has no
listfile and the tracks (if any) are not in sfxdata.tbl. But a compressed MPQ
block starts with its sector offset table, and table[0] == (num+1)*4 is known
plaintext -- so the file key can be solved from the first cipher dword without
knowing the filename at all:

    plain0 = cipher0 ^ (seed1 + 0xEEEEEEEE + CRYPT[0x400 + (seed1 & 0xFF)])

seed1 is fixed by the low byte, so trying all 256 gives the key; the rest of
the table (monotonic, last == csize) validates it. Decrypting the block then
tells us whether it is a RIFF/WAVE or something else entirely.

Result on this repack: every >=300KB encrypted block is either a DOS executable
(MZ...) or zero fill -- there are no music tracks. That is why the app ships a
music toggle that no-ops instead of a track list.
"""
import os
import struct

import sc_archive as sa

ROOT = r"F:\KF\XJZB"
C = sa._CRYPT
M = 0xFFFFFFFF


def _solve_key(cipher0, plain0):
    """seed1 candidates whose decrypted dword 0 equals plain0."""
    s0 = (cipher0 ^ plain0) & M
    out = []
    for b in range(256):
        s = (s0 - 0xEEEEEEEE - C[0x400 + b]) & M
        if (s & 0xFF) == b:
            out.append(s)
    return out


def recover_key(ar, bi):
    """(key, sector_offsets, raw_block) for an encrypted block, or None."""
    o, cs, fs, flags, rel = ar.block_table[bi]
    if not (flags & sa.FLAG_ENCRYPTED):
        return None
    num = 1 if (flags & sa.FLAG_SINGLE_UNIT) else \
        max(1, (fs + ar.sector_size - 1) // ar.sector_size)
    need = (num + 1) * 4
    ar.fp.seek(o)
    raw = ar.fp.read(cs)
    if len(raw) < need:
        return None
    cipher0 = struct.unpack_from("<I", raw, 0)[0]
    for k in _solve_key(cipher0, need):
        table = sa.decrypt(raw[:need], k)
        offs = [int.from_bytes(table[i * 4:(i + 1) * 4], "little")
                for i in range(num + 1)]
        if offs[0] == need and offs[-1] == cs and \
                all(offs[i] <= offs[i + 1] for i in range(num)):
            return (k + 1) & M, offs, raw
    return None


def read_block(ar, bi):
    """Decompress a block located by key recovery instead of by name."""
    r = recover_key(ar, bi)
    if not r:
        return None
    key, offs, raw = r
    fs = ar.block_table[bi][2]
    out = bytearray()
    for i in range(len(offs) - 1):
        sec = sa.decrypt(raw[offs[i]:offs[i + 1]], (key + i) & M)
        want = min(ar.sector_size, fs - i * ar.sector_size)
        if want <= 0:
            break
        try:
            out += sa.decompress_sector(sec, want)
        except Exception:
            out += sec
    return bytes(out)


def classify(head):
    if head[:4] == b"RIFF":
        return "WAV"
    if head[:2] == b"MZ":
        return "DOS EXE"
    if head[:4] == b"SMK2":
        return "Smacker video"
    if head[:5] == b"<?xml":
        return "XML"
    if not any(head[:64]):
        return "zero fill"
    return "data"


def main():
    for label, fn in (("StarDat", "StarDat.mpq"), ("BrooDat", "BrooDat.mpq")):
        ar = sa.Archive(os.path.join(ROOT, fn))
        print("=== %s" % label)
        for bi, (o, cs, fs, flags, rel) in enumerate(ar.block_table):
            if fs < 300000 or not (flags & sa.FLAG_ENCRYPTED):
                continue
            try:
                d = read_block(ar, bi)
            except Exception as ex:
                print("  blk%-5d fs=%-8d ERR %s" % (bi, fs, ex))
                continue
            if d is None:
                print("  blk%-5d fs=%-8d no key" % (bi, fs))
                continue
            print("  blk%-5d fs=%-8d out=%-8d %s" % (bi, fs, len(d), classify(d)))


if __name__ == "__main__":
    main()
