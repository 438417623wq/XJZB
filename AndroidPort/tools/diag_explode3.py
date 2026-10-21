"""Compare my explode with the literal blast.c port on marine sector 0."""
import struct
import sc_archive
import blast_ref
from pkware import explode

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
body = sec[1:]  # strip MPQ compression mask byte 0x08

ref_out, err, bitcnt, inpos = blast_ref.blast(body)
mine = explode(body, 4096)
print("ref: err=%d out=%d (bit left=%d, bytes unconsumed=%d)" % (err, len(ref_out), bitcnt, len(body) - inpos))
print("mine: out=%d" % len(mine))
n = min(len(ref_out), len(mine))
diff = next((i for i in range(n) if ref_out[i] != mine[i]), None)
print("first diff at:", diff)
print("ref  tail:", ref_out[-16:].hex())
print("mine tail:", mine[-16:].hex())
print("ref total vs fs-sector0: ref=%d" % len(ref_out))
