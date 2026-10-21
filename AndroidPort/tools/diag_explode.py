"""Debug the short-explode: trace the final symbols of marine sector 0."""
import struct
import sc_archive
from pkware import Bits, decode, _LENCODE, _LITCODE, _DISTCODE, BASE, EXTRA, END_CODE

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
sec = sc_archive.decrypt(raw[offs[0]:offs[1]], key & 0xFFFFFFFF)
data = sec[1:]  # strip DCL header mask byte... wait: DCL header is raw (lit, dict)
print("sector0 compressed len:", len(data))
lit = data[0]
dic = data[1]
print("lit=%d dict=%d" % (lit, dic))

br = Bits(data[2:])
out = bytearray()
WANT = 4096
try:
    while len(out) < WANT:
        if br.bits(1):
            symbol = decode(br, _LENCODE)
            length = BASE[symbol] + br.bits(EXTRA[symbol])
            if length == END_CODE:
                print("END CODE at out len", len(out), "bits left:", br.cnt, "bytes left:", len(data) - 2 - br.p)
                break
            sym2 = 2 if length == 2 else dic
            dist = (decode(br, _DISTCODE) << sym2) + br.bits(sym2) + 1
            src = len(out) - dist
            for i in range(length):
                out.append(out[src + i])
        else:
            out.append(decode(br, _LITCODE) if lit else br.bits(8))
except EOFError as e:
    print("EOFError at out len", len(out), "want", WANT)
    print("bytes consumed:", br.p + 2, "of", len(data), "bits in buffer:", br.cnt)
