"""Brute-force the bare filenames of the unnamed music blocks.

MPQ encryption derives the sector key from the BARE filename (no directory), so
the directory is irrelevant for decryption. For every unnamed block we try a
dictionary of SC1 track names; the correct one yields a self-consistent sector
offset table whose first sector decodes to a RIFF/WAVE header.
"""
import os
import struct
import sc_archive
from sc_archive import hash_string, HASH_FILE_KEY, FLAG_FIX_KEY, FLAG_ENCRYPTED

ROOT = r"F:\KF\XJZB"

BASES = []
for race in ("t", "z", "p", "terran", "zerg", "protoss"):
    for n in ("", "1", "2", "3", "4", "5", "6"):
        BASES.append(race + n)
BASES += ["title", "title1", "title2", "ttitle", "ztitle", "ptitle",
          "radio", "radiofree", "radiofreezerg", "rfz",
          "victory", "defeat", "tvictory", "zvictory", "pvictory",
          "tdefeat", "zdefeat", "pdefeat",
          "brief", "brie", "tbrie", "zbrie", "pbrie",
          "game", "gam", "tgam", "zgam", "pgam", "theme",
          "ttheme", "ztheme", "ptheme", "music", "song"]
EXTS = [".wav", ".WAV", ".wave"]


def sector_table(ar, bi, bare):
    """Return the decrypted sector offset table, or None if the key is wrong."""
    o, cs, fs, flags, rel = ar.block_table[bi]
    if not (flags & FLAG_ENCRYPTED):
        key = 0
    else:
        key = hash_string(bare, HASH_FILE_KEY)
        if flags & FLAG_FIX_KEY:
            key = ((key + rel) ^ fs) & 0xFFFFFFFF
    ar.fp.seek(o)
    raw = ar.fp.read(cs)
    num = max(1, (fs + ar.sector_size - 1) // ar.sector_size)
    for osize in (4, 2):
        if (num + 1) * osize > len(raw):
            continue
        buf = raw
        if key:
            table = sc_archive.decrypt(raw[:(num + 1) * osize], (key - 1) & 0xFFFFFFFF)
        else:
            table = raw[:(num + 1) * osize]
        cand = [int.from_bytes(table[i * osize:(i + 1) * osize], "little")
                for i in range(num + 1)]
        if (cand[0] == (num + 1) * osize and cand[-1] == len(raw)
                and all(cand[i] <= cand[i + 1] for i in range(num))):
            return cand, key, raw
    return None


def first_sector(ar, bi, bare):
    st = sector_table(ar, bi, bare)
    if not st:
        return None
    offs, key, raw = st
    return sc_archive.decompress_sector(raw[offs[0]:offs[1]],
                                        min(ar.sector_size, ar.block_table[bi][2]),
                                        ) if key == 0 else \
        sc_archive.decrypt(raw[offs[0]:offs[1]], key)


for label, fname, want in (("StarDat", "StarDat.mpq", None),
                           ("BrooDat", "BrooDat.mpq", None)):
    ar = sc_archive.Archive(os.path.join(ROOT, fname))
    print("=== %s ===" % label)
    named = set()
    try:
        import pipeline_sounds as ps
        for n in ps.sfx:
            bi = ar.find("sound/" + n.replace("\\", "/"))
            if bi is not None:
                named.add(bi)
    except Exception:
        pass
    lf = os.path.join(ROOT, "AndroidPort", "tools", "listfile_BrooDat.txt")
    if os.path.exists(lf):
        for n in [l.strip() for l in open(lf, encoding="utf8", errors="ignore") if l.strip()]:
            bi = ar.find(n)
            if bi is not None:
                named.add(bi)
    for bi, (o, cs, fs, flags, rel) in enumerate(ar.block_table):
        if fs < 400000 or bi in named:
            continue
        hit = None
        for b in BASES:
            for ext in EXTS:
                bare = b + ext
                try:
                    st = sector_table(ar, bi, bare)
                except Exception:
                    continue
                if not st:
                    continue
                offs, key, raw = st
                sec = sc_archive.decrypt(raw[offs[0]:offs[1]], key) if key else raw[offs[0]:offs[1]]
                if sec[:4] == b"RIFF":
                    hit = (bare, sec)
                    break
            if hit:
                break
        if hit:
            bare, sec = hit
            pos, fmt = 12, b""
            while pos + 8 <= len(sec):
                cid, ln = struct.unpack_from("<4sI", sec, pos)
                if cid == b"fmt ":
                    fmt = sec[pos + 8:pos + 8 + 16]
                    break
                pos += 8 + ln + (ln & 1)
            if len(fmt) >= 16:
                tag, chn, rate, _b, _a, bits = struct.unpack("<HHIIHH", fmt)
                print("  blk%-5d fsize=%-8d BARE=%-16s %dHz %dbit %s  ~%.0fs"
                      % (bi, fs, bare, rate, bits, "stereo" if chn > 1 else "mono",
                         fs / (rate * chn * bits / 8)))
        else:
            print("  blk%-5d fsize=%-8d no name matched" % (bi, fs))
