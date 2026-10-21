import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import mpq
from mpq import MPQ, _decrypt, hash_string, HASH_FILE_KEY
root = r"F:\KF\XJZB"
m = MPQ(os.path.join(root,"StarDat.mpq"))
print("sector_shift gives sector_size =", m.sector_size, " hash_size", m.hash_table_size, " block_size", m.block_table_size)
for name in ["tileset\\badlands.cv5", "tileset\\badlands\\dddata.bin"]:
    bi = m.find(name)
    off, csize, fsize, flags, rel = m.block_table[bi]
    print("="*30, name, "bi",bi,"off",off,"csize",csize,"fsize",fsize,"flags",hex(flags),"rel",rel)
    key = hash_string(name, HASH_FILE_KEY)
    if flags & mpq.FLAG_FIX_KEY:
        key = ((key + rel) ^ fsize) & 0xFFFFFFFF
    m.fp.seek(off); raw = m.fp.read(csize)
    num = (fsize + m.sector_size - 1)//m.sector_size
    print("  num sectors", num)
    for label, table in (("plain", raw), ("dec", _decrypt(raw, (key-1)&0xFFFFFFFF))):
        for osize in (4,2):
            if (num+1)*osize > len(table): continue
            cand = [int.from_bytes(table[i*osize:(i+1)*osize],"little") for i in range(num+1)]
            ok = m._valid_offsets(cand, num, csize)
            print(f"   {label} osize={osize} valid={ok} first5={cand[:5]} last={cand[-1]} csize={csize}")
