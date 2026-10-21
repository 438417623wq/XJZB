"""PKWARE DCL "implode" decompressor (MPQ compression type 0x08).

Faithful Python port of Mark Adler's blast.c (zlib contrib), which is the
reference decoder for the PKWARE Data Compression Library stream format.

Format notes (from blast.c):
  * First byte: 0 = literals uncoded, 1 = literals Huffman coded.
  * Second byte: 4, 5 or 6 = log2(dictionary size) - 6.
  * Bits are stored LSB-first within each byte.
  * The Huffman tables for literals/lengths/distances are *static* -- they are
    part of the format, not carried in the stream.
  * Codes are bit-reversed, so each bit pulled while decoding is inverted.
  * A 1-bit flag precedes each item: 0 = literal, 1 = length/distance pair.
  * A length of 519 is the end-of-stream code.
"""

from __future__ import annotations

MAXBITS = 13
MAXWIN = 4096

# --- static code tables (rle-compressed: high nibble = count-1, low = length)
_LITLEN = [
    11, 124, 8, 7, 28, 7, 188, 13, 76, 4, 10, 8, 12, 10, 12, 10, 8, 23, 8,
    9, 7, 6, 7, 8, 7, 6, 55, 8, 23, 24, 12, 11, 7, 9, 11, 12, 6, 7, 22, 5,
    7, 24, 6, 11, 9, 6, 7, 22, 7, 11, 38, 7, 9, 8, 25, 11, 8, 11, 9, 12,
    8, 12, 5, 38, 5, 38, 5, 11, 7, 5, 6, 21, 6, 10, 53, 8, 7, 24, 10, 27,
    44, 253, 253, 253, 252, 252, 252, 13, 12, 45, 12, 45, 12, 61, 12, 45,
    44, 173,
]
_LENLEN = [2, 35, 36, 53, 38, 23]
_DISTLEN = [2, 20, 53, 230, 247, 151, 248]

BASE = [3, 2, 4, 5, 6, 7, 8, 9, 10, 12, 16, 24, 40, 72, 136, 264]
EXTRA = [0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8]

END_CODE = 519


class _Huff:
    __slots__ = ("count", "symbol")

    def __init__(self, rep):
        length = []
        for b in rep:
            cnt = (b >> 4) + 1
            ln = b & 15
            length.extend([ln] * cnt)
        n = len(length)

        count = [0] * (MAXBITS + 1)
        for ln in length:
            count[ln] += 1

        offs = [0] * (MAXBITS + 2)
        for ln in range(1, MAXBITS + 1):
            offs[ln + 1] = offs[ln] + count[ln]

        symbol = [0] * n
        for sym in range(n):
            ln = length[sym]
            if ln:
                symbol[offs[ln]] = sym
                offs[ln] += 1

        self.count = count
        self.symbol = symbol


_LITCODE = _Huff(_LITLEN)
_LENCODE = _Huff(_LENLEN)
_DISTCODE = _Huff(_DISTLEN)


class Bits:
    """LSB-first bit reader (blast.c bits())."""

    __slots__ = ("d", "p", "buf", "cnt")

    def __init__(self, data):
        self.d = data
        self.p = 0
        self.buf = 0
        self.cnt = 0

    def bits(self, need):
        val = self.buf
        cnt = self.cnt
        p = self.p
        d = self.d
        while cnt < need:
            if p >= len(d):
                raise EOFError("out of input")
            val |= d[p] << cnt
            p += 1
            cnt += 8
        self.p = p
        self.buf = val >> need
        self.cnt = cnt - need
        return val & ((1 << need) - 1)


def decode(br, h):
    """Decode one symbol (blast.c decode(): bits are inverted)."""
    code = 0
    first = 0
    index = 0
    length = 1
    count = h.count
    symbol = h.symbol
    while length <= MAXBITS:
        code |= br.bits(1) ^ 1
        c = count[length]
        if code < first + c:
            return symbol[index + (code - first)]
        index += c
        first += c
        first <<= 1
        code <<= 1
        length += 1
    return -9


def explode(data, out_size=None):
    """Decompress a PKWARE implode stream.

    blast.c uses a 4 KB sliding window purely to bound memory; decoding into a
    single linear buffer is equivalent and removes the wrap-around copy logic.
    Overlapping copies (length > distance) work naturally because the source
    index reads bytes appended earlier in the same loop.
    """
    br = Bits(data)
    lit = br.bits(8)
    if lit > 1:
        raise ValueError("bad literal-mode byte %d" % lit)
    dic = br.bits(8)
    if dic < 4 or dic > 6:
        raise ValueError("bad dictionary byte %d" % dic)

    out = bytearray()
    append = out.append

    while out_size is None or len(out) < out_size:
        try:
            if br.bits(1):
                symbol = decode(br, _LENCODE)
                length = BASE[symbol] + br.bits(EXTRA[symbol])
                if length == END_CODE:
                    break
                symbol = 2 if length == 2 else dic
                dist = (decode(br, _DISTCODE) << symbol) + br.bits(symbol) + 1
                if dist > len(out):
                    raise ValueError("distance too far back (%d > %d)" % (dist, len(out)))
                src = len(out) - dist
                for i in range(length):
                    append(out[src + i])
            else:
                append(decode(br, _LITCODE) if lit else br.bits(8))
        except EOFError:
            # An MPQ sector's implode stream can end exactly at the sector
            # boundary without an explicit end code; keep what we decoded.
            break

    if out_size is not None:
        return bytes(out[:out_size])
    return bytes(out)
