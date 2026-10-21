"""Identify music blocks by decoding their first sector.

Names for StarDat's music are unknown (no listfile, not in sfxdata.tbl), but a
WAV's first sector decodes to "RIFF" regardless. Enumerate every large block,
decompress its first sector, and classify by the RIFF fmt header (sample rate /
channels / bit depth tell music from voice: SC1 music is 22 kHz 16-bit stereo,
voice is 22 kHz 8-bit mono).
"""
import os
import struct
import sc_archive

ROOT = r"F:\KF\XJZB"


def first_sector(ar, bi):
    o, cs, fs, flags, rel = ar.block_table[bi]
    ar.fp.seek(o)
    raw = ar.fp.read(cs)
    # sector table (first (n+1) u32) then sector 0
    if not (flags & 0x01000000):          # not a single-unit file
        pass
    key = 0
    if flags & 0x00000200:                # encrypted
        from sc_archive import hash_string, HASH_FILE_KEY, bare_name
        key = hash_string("", HASH_FILE_KEY)   # unknown name; try unencrypted path below
    # try the archive's own reader via a fake name is impossible; instead parse
    # the sector table assuming unencrypted (music is not encrypted in practice)
    num = max(1, (fs + ar.sector_size - 1) // ar.sector_size)
    offs = None
    for osize in (4, 2):
        if (num + 1) * osize > len(raw):
            continue
        cand = [int.from_bytes(raw[i * osize:(i + 1) * osize], "little")
                for i in range(num + 1)]
        if (cand[0] == (num + 1) * osize and cand[-1] == len(raw)
                and all(cand[i] <= cand[i + 1] for i in range(num))):
            offs = cand
            break
    if not offs:
        return None
    return sc_archive.decompress_sector(raw[offs[0]:offs[1]], min(ar.sector_size, fs))


for label, fname in (("StarDat", "StarDat.mpq"), ("BrooDat", "BrooDat.mpq")):
    ar = sc_archive.Archive(os.path.join(ROOT, fname))
    print("=== %s ===" % label)
    for i, (o, cs, fs, flags, rel) in enumerate(ar.block_table):
        if fs < 300000:
            continue
        try:
            sec = first_sector(ar, i)
        except Exception as ex:
            print("  blk%-5d fsize=%-8d ERR %s" % (i, fs, ex))
            continue
        if sec is None:
            print("  blk%-5d fsize=%-8d no-sector-table (stored?)" % (i, fs))
            continue
        if sec[:4] != b"RIFF":
            print("  blk%-5d fsize=%-8d head=%s" % (i, fs, sec[:8].hex()))
            continue
        # parse fmt chunk
        ch = sec[8:12]
        pos = 12
        fmt = b""
        while pos + 8 <= len(sec):
            cid, ln = struct.unpack_from("<4sI", sec, pos)
            if cid == b"fmt ":
                fmt = sec[pos + 8:pos + 8 + min(16, ln)]
                break
            pos += 8 + ln + (ln & 1)
        if len(fmt) >= 16:
            tag, chn, rate, _brate, _align, bits = struct.unpack("<HHIIHH", fmt)
            kind = "STEREO" if chn > 1 else "mono"
            print("  blk%-5d fsize=%-8d WAV %dHz %d-bit %s  (%.1f s) %s"
                  % (i, fs, rate, bits, kind, fs / (rate * chn * bits / 8),
                     "RAW-RIFF" if sec[8:12] == b"WAVE" else ""))
