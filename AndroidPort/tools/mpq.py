"""Minimal MPQ (Mo'PaQ) archive reader for StarCraft 1.x data archives.

Targets the format-0 archives shipped with StarCraft / Brood War:
    StarDat.mpq, BrooDat.mpq, BroodWar.mpq, patch_rt.mpq

Implements:
  * the classic MPQ hash (crypt) table and filename hashing
  * the MPQ stream cipher (hash table, block table, encrypted files)
  * sector-based decompression: stored, zlib/deflate, bzip2
"""

from __future__ import annotations

import bz2
import struct
import zlib


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


def _decrypt(data, key):
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


def _decompress_sector(data, expected_size):
    """Decompress one MPQ sector. Returns at most `expected_size` bytes."""
    if len(data) >= expected_size:
        return data[:expected_size]
    if not data:
        return b""
    ctype = data[0]
    body = data[1:]
    if ctype == 0x02:
        return zlib.decompress(body)
    if ctype == 0x10:
        return bz2.decompress(body)
    if ctype == 0x08:
        raise NotImplementedError("PKWARE implode (0x08) not implemented")
    if ctype == 0x01:
        raise NotImplementedError("Huffman (0x01) not implemented")
    raise MPQError("unknown compression type 0x%02X" % ctype)


class MPQ:
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
        blob = fp.read(2048)
        off = blob.find(b"MPQ\x1a")
        if off < 0:
            raise MPQError("not an MPQ archive: %s" % self.path)

        fp.seek(off)
        head = fp.read(32)
        (magic, header_size, archive_size, fmt, sector_shift,
         hash_pos, block_pos, hash_size, block_size) = struct.unpack("<4sIIHHIIII", head)

        self.header_offset = off
        self.archive_size = archive_size
        self.format_version = fmt
        self.sector_size = 512 << sector_shift
        self.hash_table_size = hash_size
        self.block_table_size = block_size

        if fmt >= 1:
            fp.seek(off + 32)
            hi_pos, hi_size = struct.unpack("<QQ", fp.read(16))
            self.hi_block_table_pos = hi_pos + off if hi_pos else None
        else:
            self.hi_block_table_pos = None

        # ---- hash table (encrypted with key of "(hash table)")
        fp.seek(hash_pos + off)
        raw = fp.read(hash_size * 16)
        raw = _decrypt(raw, hash_string("(hash table)", HASH_FILE_KEY))
        self.hash_table = [
            struct.unpack_from("<IIHHI", raw, i * 16) for i in range(hash_size)
        ]

        # ---- block table (encrypted with key of "(block table)")
        fp.seek(block_pos + off)
        raw = fp.read(block_size * 16)
        raw = _decrypt(raw, hash_string("(block table)", HASH_FILE_KEY))
        self.block_table = []
        for i in range(block_size):
            o, cs, fs, flags = struct.unpack_from("<IIII", raw, i * 16)
            if self.hi_block_table_pos:
                fp.seek(self.hi_block_table_pos + i * 8)
                hi = struct.unpack("<Q", fp.read(8))[0]
                o |= hi << 32
            # `o` is relative to the MPQ header; FLAG_FIX_KEY requires exactly
            # that relative value, so keep it alongside the absolute offset.
            self.block_table.append((o + off, cs, fs, flags, o))

    # ------------------------------------------------------------------ lookup

    def find(self, name):
        """Return the block index for `name`, or None."""
        h_a = hash_string(name, HASH_NAME_A)
        h_b = hash_string(name, HASH_NAME_B)
        h_o = hash_string(name, HASH_TABLE_OFFSET)
        start = h_o & (self.hash_table_size - 1)
        for i in range(self.hash_table_size):
            idx = (start + i) & (self.hash_table_size - 1)
            a, b, _locale, _platform, block_index = self.hash_table[idx]
            if block_index == 0xFFFFFFFF:
                return None
            if a == h_a and b == h_b:
                return block_index
        return None

    def has(self, name):
        return self.find(name) is not None

    def info(self, name):
        bi = self.find(name)
        if bi is None:
            return None
        offset, csize, fsize, flags, rel = self.block_table[bi]
        return {"offset": offset, "csize": csize, "size": fsize, "flags": flags}

    # -------------------------------------------------------------------- read

    def read(self, name):
        bi = self.find(name)
        if bi is None:
            raise KeyError(name)
        offset, csize, fsize, flags, rel = self.block_table[bi]

        key = 0
        if flags & FLAG_ENCRYPTED:
            key = hash_string(name, HASH_FILE_KEY)
            if flags & FLAG_FIX_KEY:
                # FLAG_FIX_KEY mixes in the block's offset *relative to the
                # MPQ header*, not its absolute file position.
                key = ((key + rel) ^ fsize) & 0xFFFFFFFF

        self.fp.seek(offset)
        raw = self.fp.read(csize)

        multi = (
            (flags & FLAG_COMPRESS)
            and not (flags & FLAG_SINGLE_UNIT)
            and fsize > self.sector_size
        )
        if multi:
            num = (fsize + self.sector_size - 1) // self.sector_size
            table = raw
            if flags & FLAG_ENCRYPTED:
                table = _decrypt(raw, (key - 1) & 0xFFFFFFFF)

            # Classic (format 0) archives store 4-byte sector offsets; some
            # writers use 2-byte offsets. Pick whichever validates.
            offsets = None
            for osize in (4, 2):
                if (num + 1) * osize > len(table):
                    continue
                cand = [
                    int.from_bytes(table[i * osize:(i + 1) * osize], "little")
                    for i in range(num + 1)
                ]
                if self._valid_offsets(cand, num, csize):
                    offsets = cand
                    break
            if offsets is None:
                raise MPQError("could not parse sector offset table for %s" % name)

            out = bytearray()
            for i in range(num):
                s, e = offsets[i], offsets[i + 1]
                sector = raw[s:e]
                if flags & FLAG_ENCRYPTED:
                    sector = _decrypt(sector, (key + i) & 0xFFFFFFFF)
                want = min(self.sector_size, fsize - len(out))
                out += _decompress_sector(sector, want)
            return bytes(out[:fsize])

        if flags & FLAG_ENCRYPTED:
            raw = _decrypt(raw, key)
        if (flags & FLAG_COMPRESS) and not (flags & FLAG_SINGLE_UNIT):
            return _decompress_sector(raw, fsize)
        return raw[:fsize]

    @staticmethod
    def _valid_offsets(offsets, num, csize):
        """A sector offset table must start past itself, be non-decreasing,
        and end exactly at the compressed size."""
        if len(offsets) != num + 1:
            return False
        if offsets[0] < (num + 1) * 2 or offsets[0] > csize:
            return False
        if offsets[-1] != csize:
            return False
        return all(offsets[i] <= offsets[i + 1] for i in range(num))

    # --------------------------------------------------------------- listfile

    def listfile(self):
        """Best-effort read of the embedded (listfile).

        The hash table stores no names, so a lookup can in principle land on a
        colliding entry; treat any failure as "no listfile" rather than fatal.
        """
        for cand in ("(listfile)", "(LISTFILE)", "listfile", "Listfile"):
            try:
                data = self.read(cand)
            except Exception:
                continue
            if not data:
                continue
            text = data.decode("latin-1", "replace")
            names = [ln.strip() for ln in text.replace("\r", "\n").split("\n")]
            names = [n for n in names if n]
            # A real listfile is plain text; reject binary garbage from collisions.
            if names and all(all(32 <= ord(ch) < 127 for ch in n) for n in names[:50]):
                return names
        return []
