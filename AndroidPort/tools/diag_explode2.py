"""Trace the final symbols with bit positions to find the over-consumption."""
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
data = sec
lit, dic = data[0], data[1]
br = Bits(data[2:])
out = bytearray()
WANT = 4096
log = []
try:
    while len(out) < WANT:
        pos0 = br.p * 8 - br.cnt
        if br.bits(1):
            symbol = decode(br, _LENCODE)
            length = BASE[symbol] + br.bits(EXTRA[symbol])
            if length == END_CODE:
                log.append(("END", pos0, len(out)))
                break
            sym2 = 2 if length == 2 else dic
            dist = (decode(br, _DISTCODE) << sym2) + br.bits(sym2) + 1
            log.append(("match len=%d dist=%d" % (length, dist), pos0, len(out)))
            src = len(out) - dist
            for i in range(length):
                out.append(out[src + i])
        else:
            c = br.bits(8)
            log.append(("lit %02x" % c, pos0, len(out)))
            out.append(c)
except EOFError:
    log.append(("EOF", br.p * 8 - br.cnt, len(out)))

for e in log[-14:]:
    print(e)
print("total input bits:", len(data) * 8, "consumed:", log[-1][1])
