"""Unified StarCraft asset extraction library.

Ties together the three pieces that were reverse-engineered from the archives:

  1. MPQ container parsing (hash/block tables, stream cipher)
  2. The file-key rule:  hash(BARE_FILENAME, MPQ_HASH_FILE_KEY),
     then (key + block_offset) ^ uncompressed_size when MPQ_FILE_FIX_KEY is set
  3. Sector decompression: PKWARE DCL implode (0x08), zlib (0x02), stored

Public API:
    Archive(path)              -- open a .mpq / .scm archive
    ar.read(name)              -- decompress an entry by its internal name
    ar.has(name) / ar.info(name)
"""

from __future__ import annotations

import os
import struct
import zlib

from pkware import explode

HASH_TABLE_OFFSET = 0
HASH_NAME_A = 1
HASH_NAME_B = 2
HASH_FILE_KEY = 3

FLAG_IMPLODE = 0x00000100
FLAG_COMPRESS = 0x00000200
FLAG_ENCRYPTED = 0x00010000
FLAG_FIX_KEY = 0x00020000
FLAG_PATCH_FILE = 0x00100000
FLAG_SINGLE_UNIT = 0x01000000
FLAG_DELETE_MARKER = 0x02000000
FLAG_SECTOR_CRC = 0x04000000
FLAG_EXISTS = 0x80000000


def _build_crypt_table():
    seed = 0x00100001
    table = [0] * 0x500
    for i in range(0x100):
        index = i
        for _ in range(5):
            seed = (seed * 125 + 3) % 0x2AAAAB
            hi = (seed & 0xFFFF) << 16
            seed = (seed * 125 + 3) % 0x2AAAAB
            lo = seed & 0xFFFF
            table[index] = (hi | lo) & 0xFFFFFFFF
            index += 0x100
    return table


_CRYPT = _build_crypt_table()


class MPQError(Exception):
    pass


def hash_string(name, hash_type):
    seed1 = 0x7FED7FED
    seed2 = 0xEEEEEEEE
    for ch in name.upper().replace("/", "\\"):
        c = ord(ch)
        seed1 = (_CRYPT[(hash_type << 8) + c] ^ ((seed1 + seed2) & 0xFFFFFFFF)) & 0xFFFFFFFF
        seed2 = (c + seed1 + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
    return seed1


def plausible_mask(m):
    """True if the byte can be a real MPQ v1 compression mask. SC-era WAV files
    are stored raw but carry the COMPRESS flag, so the first byte of a RIFF
    ('R' = 0x52) must not be mistaken for a mask."""
    if m == 0x00:                  # per-sector "stored" marker
        return True
    if m & (0x40 | 0x80):          # ADI must ride on Huffman
        return bool(m & 0x01)
    return bool(m & (0x01 | 0x02 | 0x08 | 0x10 | 0x20))


def bare_name(name):
    """Bare filename with separators normalised (the archive key rule)."""
    return name.replace("/", chr(92)).split(chr(92))[-1]


def decrypt(data, key):
    seed1 = key & 0xFFFFFFFF
    seed2 = 0xEEEEEEEE
    n = len(data) // 4
    out = bytearray(n * 4)
    for i in range(n):
        seed2 = (seed2 + _CRYPT[0x400 + (seed1 & 0xFF)]) & 0xFFFFFFFF
        chunk = struct.unpack_from("<I", data, i * 4)[0]
        plain = (chunk ^ ((seed1 + seed2) & 0xFFFFFFFF)) & 0xFFFFFFFF
        struct.pack_into("<I", out, i * 4, plain)
        old = seed1
        seed1 = ((((~old) & 0xFFFFFFFF) << 21) + 0x11111111) & 0xFFFFFFFF
        seed1 = (seed1 | (old >> 11)) & 0xFFFFFFFF
        seed2 = (plain + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
    return bytes(out)


def decompress_sector(data, expected):
    """Decompress one MPQ sector.

    The leading byte is a *bitmask* of compression methods, not a single id:
    StormLib applies every set method in turn. We peel them off until the
    buffer reaches the expected size.
    """
    if not data:
        return b""
    if len(data) >= expected:
        return data[:expected]

    ctype = data[0]
    if not plausible_mask(ctype):          # raw stored payload
        return data[:expected]
    body = data[1:]

    # Methods are applied outer-to-inner; resolve the common combinations.
    if ctype & 0x01:                      # Huffman (rare, unsupported)
        raise MPQError("Huffman compression (0x%02X) not supported" % ctype)

    if ctype & 0x02:                      # zlib / deflate
        try:
            return zlib.decompress(body)[:expected]
        except zlib.error:
            pass

    if ctype & 0x08:                      # PKWARE DCL implode
        return explode(body, expected)

    if ctype & 0x10:                      # bzip2
        import bz2
        return bz2.decompress(body)[:expected]

    if ctype == 0x00:                     # stored
        return body[:expected]

    raise MPQError("unsupported compression type 0x%02X" % ctype)


def is_stored_sector(sec, want):
    """True when a sector is stored verbatim rather than compressed.

    StormLib's rule is positional, not content-based: a sector whose stored
    length already equals its expected output length cannot have been made
    smaller, so it was written raw. Its first byte is then real payload, not a
    compression mask -- and for tile imagery that byte is frequently an
    implausible mask (0x20/0x3c/0xa4 ...). Judging by the mask alone made
    `full_decompress` explode raw pixels and mis-flag sectors as truncated.
    """
    return bool(sec) and len(sec) >= want


def full_decompress(sec):
    """Fully decompress one decrypted sector, applying every masked method in
    StormLib's v1 table order (pkware, zlib, huffman, adpcm). Uncapped."""
    if not sec:
        return b""
    m = sec[0]
    if not plausible_mask(m):
        return sec
    if m == 0x00:                  # stored sector: mask byte then raw data
        return sec[1:]
    body = sec[1:]
    if m & 0x08:
        from pkware import explode
        body = explode(body, None)
    if m & 0x02:
        body = zlib.decompress(body)
    if m & 0x01:
        import mphuff
        body = mphuff.decompress(body, 1 << 26)
    if m & 0x40:
        import mpadi
        body = mpadi.decompress_adi_mono(body, 1 << 26)
    if not (m & 0x0F or m & 0xC0):
        body = body  # stored
    return body


class Archive:
    """A StarCraft-format MPQ archive."""

    def __init__(self, path):
        self.path = path
        self.fp = open(path, "rb")
        try:
            self._parse()
        except Exception:
            self.fp.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        try:
            self.fp.close()
        except Exception:
            pass

    def _parse(self):
        fp = self.fp
        fp.seek(0)
        blob = fp.read(4096)
        off = blob.find(b"MPQ\x1a")
        if off < 0:
            raise MPQError("not an MPQ archive: %s" % self.path)
        fp.seek(off)
        (_magic, _hsize, asize, fmt, shift,
         hpos, bpos, hcount, bcount) = struct.unpack("<4sIIHHIIII", fp.read(32))

        self.header_offset = off
        self.sector_size = 512 << shift
        self.hash_table_size = hcount

        fp.seek(hpos + off)
        raw = decrypt(fp.read(hcount * 16), hash_string("(hash table)", HASH_FILE_KEY))
        self.hash_table = [struct.unpack_from("<IIHHI", raw, i * 16) for i in range(hcount)]

        fp.seek(bpos + off)
        raw = decrypt(fp.read(bcount * 16), hash_string("(block table)", HASH_FILE_KEY))
        self.block_table = []
        for i in range(bcount):
            o, cs, fs, flags = struct.unpack_from("<IIII", raw, i * 16)
            self.block_table.append((o + off, cs, fs, flags, o))

    # ------------------------------------------------------------------ lookup

    def find(self, name):
        h_a = hash_string(name, HASH_NAME_A)
        h_b = hash_string(name, HASH_NAME_B)
        start = hash_string(name, HASH_TABLE_OFFSET) & (self.hash_table_size - 1)
        for i in range(self.hash_table_size):
            idx = (start + i) & (self.hash_table_size - 1)
            a, b, _loc, _plat, bi = self.hash_table[idx]
            if bi == 0xFFFFFFFF:
                return None
            if a == h_a and b == h_b:
                return bi
        return None

    def has(self, name):
        return self.find(name) is not None

    def info(self, name):
        bi = self.find(name)
        if bi is None:
            return None
        o, cs, fs, flags, rel = self.block_table[bi]
        return {"offset": o, "csize": cs, "size": fs, "flags": flags}

    # -------------------------------------------------------------------- read

    def read(self, name):
        """Read and decompress an entry.

        The archive key is derived from the BARE filename (no directory),
        which is what StarCraft's archives actually use.
        """
        bi = self.find(name)
        if bi is None:
            raise KeyError(name)
        return self.read_block(bi, bare_name(name))

    def _try_sector_table(self, raw, key, flags, num, sec_size):
        """Parse the sector offset table for `num` sectors; None if invalid."""
        if not raw:
            return None
        table = decrypt(raw, (key - 1) & 0xFFFFFFFF) if (flags & FLAG_ENCRYPTED) else raw
        for osize in (4, 2):
            if (num + 1) * osize > len(table):
                continue
            cand = [int.from_bytes(table[i * osize:(i + 1) * osize], "little")
                    for i in range(num + 1)]
            if (cand[0] == (num + 1) * osize          # entry 0 = table size
                    and cand[-1] == len(raw)
                    and all(cand[i] <= cand[i + 1] for i in range(num))):
                return cand
        return None

    def read_with_gaps(self, name):
        """Read an entry and return (data, gaps).

        The warez repack truncated the tail of some compressed sectors, so the
        natural per-sector outputs concatenate to fewer bytes than the recorded
        file size. `gaps` lists (original_position, size) of the missing bytes
        so callers can keep structured reads aligned (see gapio.GapReader).
        """
        bi = self.find(name)
        if bi is None:
            raise KeyError(name)
        o, cs, fs, flags, rel = self.block_table[bi]
        key = 0
        if flags & FLAG_ENCRYPTED:
            key = hash_string(bare_name(name), HASH_FILE_KEY)
            if flags & FLAG_FIX_KEY:
                key = ((key + rel) ^ fs) & 0xFFFFFFFF

        self.fp.seek(o)
        raw = self.fp.read(cs)

        gaps = []
        out = bytearray()

        num_default = max(1, (fs + self.sector_size - 1) // self.sector_size)
        cands = [num_default]
        if fs <= self.sector_size:
            cands.append(max(1, (fs + 511) // 512))
        offs = None
        used_num = num_default
        for num in cands:
            offs = self._try_sector_table(raw, key, flags, num, self.sector_size)
            if offs:
                used_num = num
                break

        # Detect files that are stored raw despite the COMPRESS flag (SC-era
        # WAVs). This is a whole-file property, so it needs every sector to be
        # stored -- judging by sector 0 alone misfires on tilesets like
        # badlands.vx4 whose first sector is raw but whose remainder is
        # imploded, and would silently return the compressed bytes verbatim.
        stored_file = False
        if flags & FLAG_COMPRESS:
            if offs is None:
                s0 = raw
                if flags & FLAG_ENCRYPTED:
                    s0 = decrypt(s0, key)
                stored_file = is_stored_sector(s0, fs)
            else:
                stored_file = True
                for i in range(used_num):
                    sec = raw[offs[i]:offs[i + 1]]
                    if flags & FLAG_ENCRYPTED:
                        sec = decrypt(sec, (key + i) & 0xFFFFFFFF)
                    want = (self.sector_size if i < used_num - 1
                            else fs - self.sector_size * (used_num - 1))
                    want = max(0, min(self.sector_size, want))
                    if not is_stored_sector(sec, want):
                        stored_file = False
                        break

        if offs is None:
            # table-less single sector
            sec = decrypt(raw, key) if (flags & FLAG_ENCRYPTED) else raw
            if flags & FLAG_COMPRESS and not stored_file:
                try:
                    nat = len(full_decompress(sec))
                    if nat < fs:
                        gaps.append((nat, fs - nat))
                except Exception:
                    gaps.append((0, fs))
                    out += bytes(fs)
                    return bytes(out[:fs]), gaps
                out += decompress_sector(sec, fs)
            else:
                out += sec[:fs]
            return bytes(out[:fs]), gaps

        for i in range(used_num):
            sec = raw[offs[i]:offs[i + 1]]
            if flags & FLAG_ENCRYPTED:
                sec = decrypt(sec, (key + i) & 0xFFFFFFFF)
            # Positional, NOT `fs - len(out)`: earlier sectors legitimately
            # decompress short (repack truncation), which would otherwise
            # inflate this bound past a full sector and make a stored final
            # sector look compressed.
            want = self.sector_size if i < used_num - 1 else fs - self.sector_size * (used_num - 1)
            want = max(0, min(self.sector_size, want))
            if flags & FLAG_COMPRESS and not stored_file and not is_stored_sector(sec, want):
                try:
                    nat = len(full_decompress(sec))
                except Exception:
                    gaps.append((len(out), want))
                    out += bytes(want)
                    continue
                if nat < want:
                    gaps.append((len(out) + nat, want - nat))
                out += decompress_sector(sec, want)
            else:
                out += sec[:want]
        return bytes(out[:fs]), gaps

    def read_block(self, bi, key_name):
        o, cs, fs, flags, rel = self.block_table[bi]
        key = 0
        if flags & FLAG_ENCRYPTED:
            key = hash_string(key_name, HASH_FILE_KEY)
            if flags & FLAG_FIX_KEY:
                key = ((key + rel) ^ fs) & 0xFFFFFFFF

        self.fp.seek(o)
        raw = self.fp.read(cs)

        num_default = max(1, (fs + self.sector_size - 1) // self.sector_size)
        cands = [num_default]
        if fs <= self.sector_size:
            cands.append(max(1, (fs + 511) // 512))
        offs = None
        used_num = num_default
        for num in cands:
            offs = self._try_sector_table(raw, key, flags, num, self.sector_size)
            if offs:
                used_num = num
                break

        stored_file = False
        if flags & FLAG_COMPRESS:
            if offs is None:
                s0 = raw
                if flags & FLAG_ENCRYPTED:
                    s0 = decrypt(s0, key)
                stored_file = is_stored_sector(s0, fs)
            else:
                stored_file = True
                for i in range(used_num):
                    sec = raw[offs[i]:offs[i + 1]]
                    if flags & FLAG_ENCRYPTED:
                        sec = decrypt(sec, (key + i) & 0xFFFFFFFF)
                    want = (self.sector_size if i < used_num - 1
                            else fs - self.sector_size * (used_num - 1))
                    want = max(0, min(self.sector_size, want))
                    if not is_stored_sector(sec, want):
                        stored_file = False
                        break

        if offs is None:
            sec = decrypt(raw, key) if (flags & FLAG_ENCRYPTED) else raw
            if flags & FLAG_COMPRESS and not stored_file:
                return decompress_sector(sec, fs)
            return sec[:fs]

        out = bytearray()
        for i in range(used_num):
            sec = raw[offs[i]:offs[i + 1]]
            if flags & FLAG_ENCRYPTED:
                sec = decrypt(sec, (key + i) & 0xFFFFFFFF)
            want = self.sector_size if i < used_num - 1 else fs - self.sector_size * (used_num - 1)
            want = max(0, min(self.sector_size, want))
            if flags & FLAG_COMPRESS and not stored_file and not is_stored_sector(sec, want):
                out += decompress_sector(sec, want)
            else:
                out += sec[:want]
        return bytes(out[:fs])
