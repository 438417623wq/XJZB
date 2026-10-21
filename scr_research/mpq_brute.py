import sys, os, struct, zlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import mpq
from mpq import MPQ, _decrypt, hash_string, HASH_FILE_KEY
root = r"F:\KF\XJZB"
m = MPQ(os.path.join(root,"StarDat.mpq"))
name = "tileset\\badlands.cv5"
bi = m.find(name)
off, csize, fsize, flags, rel = m.block_table[bi]
h = hash_string(name, HASH_FILE_KEY)
variants = {
  "hash": h,
  "fix(rel)": ((h + rel) ^ fsize) & 0xFFFFFFFF,
  "fix(off)": ((h + off) ^ fsize) & 0xFFFFFFFF,
  "fix-nofsize": (h + rel) & 0xFFFFFFFF,
  "hash^fsize": (h ^ fsize) & 0xFFFFFFFF,
}
m.fp.seek(off); raw = m.fp.read(csize)
num = (fsize + m.sector_size - 1)//m.sector_size
for vn, key in variants.items():
    for kdelta in (0, -1):
        k = (key + kdelta) & 0xFFFFFFFF
        for label, table in (("plain", raw), ("dec", _decrypt(raw, k))):
            for osize in (4,2):
                if (num+1)*osize > len(table): continue
                cand = [int.from_bytes(table[i*osize:(i+1)*osize],"little") for i in range(num+1)]
                if m._valid_offsets(cand, num, csize):
                    print(f"VALID {vn} kdelta={kdelta} {label} osize={osize} first={cand[:4]}")
print("done")
