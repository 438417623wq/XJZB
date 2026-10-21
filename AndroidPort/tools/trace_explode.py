"""Tracing explode: print every symbol to see where the stream desyncs."""
import struct
import sc_archive
from pkware import _LITLEN, _LENLEN, _DISTLEN, _Huff, Bits, BASE, EXTRA, END_CODE

LIT = _Huff(_LITLEN)
LEN = _Huff(_LENLEN)
DIST = _Huff(_DISTLEN)


def decode_sym(br, h, trace):
    code = 0
    first = 0
    index = 0
    length = 1
    bits_used = []
    while length <= 13:
        b = br.bits(1)
        bits_used.append(b)
        code |= b ^ 1
        c = h.count[length]
        if code < first + c:
            sym = h.symbol[index + (code - first)]
            trace.append(("sym", sym, length, bits_used))
            return sym
        index += c
        first += c
        first <<= 1
        code <<= 1
        length += 1
    raise ValueError("bad code")


def trace_explode(data, n_ops=40, out_target=80):
    br = Bits(data)
    lit = br.bits(8)
    dic = br.bits(8)
    print("lit=%d dict=%d" % (lit, dic))
    out = bytearray()
    for op in range(n_ops):
        if len(out) >= out_target:
            break
        try:
            flag = br.bits(1)
        except EOFError:
            print("EOF")
            break
        if flag:
            tr = []
            symbol = decode_sym(br, LEN, tr)
            length = BASE[symbol] + br.bits(EXTRA[symbol])
            if length == END_CODE:
                print("op%2d END" % op)
                break
            symbol2 = 2 if length == 2 else dic
            tr2 = []
            dist = (decode_sym(br, DIST, tr2) << symbol2) + br.bits(symbol2) + 1
            print("op%2d MATCH len=%d dist=%d" % (op, length, dist))
            src = len(out) - dist
            for i in range(length):
                out.append(out[src + i])
        else:
            tr = []
            if lit:
                b = decode_sym(br, LIT, tr)
            else:
                b = br.bits(8)
            out.append(b)
            if op < 30:
                print("op%2d LIT %3d '%s'" % (op, b, chr(b) if 32 <= b < 127 else ""))
    print("out:", out[:80].hex())
    print("as text:", bytes(out[:80]))


SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
name = "unit\\terran\\marine.grp"
bi = SD.find(name)
o, cs, fs, flags, rel = SD.block_table[bi]
key = sc_archive.hash_string("marine.grp", sc_archive.HASH_FILE_KEY)
key = ((key + rel) ^ fs) & 0xFFFFFFFF
SD.fp.seek(o)
raw = SD.fp.read(cs)
table = sc_archive.decrypt(raw, (key - 1) & 0xFFFFFFFF)
offs = [struct.unpack_from("<I", table, i * 4)[0] for i in range(16)]
print("offsets:", offs[:5])
sec = raw[offs[0]:offs[1]]
sec = sc_archive.decrypt(sec, key & 0xFFFFFFFF)
print("sector0 compressed:", len(sec), "mask:", hex(sec[0]))
trace_explode(sec[1:], n_ops=60, out_target=120)
