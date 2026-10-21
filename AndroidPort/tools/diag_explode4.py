"""Aligned trace: does sector 0's stream end with an explicit END CODE?"""
import struct
import sc_archive
import blast_ref

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
body = sec[1:]  # strip mask 0x08

s = blast_ref.State(body)
lit = s.bits(8)
dic = s.bits(8)
print("lit=%d dict=%d input=%d bytes" % (lit, dic, len(body)))
ops = 0
import pkware
try:
    while True:
        if s.bits(1):
            symbol = blast_ref.decode(s, blast_ref.LENCODE)
            ln = blast_ref.BASE[symbol] + s.bits(blast_ref.EXTRA[symbol])
            if ln == 519:
                print("END CODE after %d ops at out=%d, input left=%d bytes" % (ops, len(s.out), len(body) - s.inpos))
                break
            sym2 = 2 if ln == 2 else dic
            dist = (blast_ref.decode(s, blast_ref.DISTCODE) << sym2) + s.bits(sym2) + 1
            if s.first and dist > s.next:
                print("dist-too-far at out=%d" % len(s.out))
                break
            while ln:
                to = s.next
                frm = to - dist
                cp = blast_ref.MAXWIN
                if s.next < dist:
                    frm += cp
                    cp = dist
                cp -= s.next
                if cp > ln:
                    cp = ln
                ln -= cp
                s.next += cp
                while cp:
                    s.out.append(s.out[frm])
                    frm += 1
                    cp -= 1
                if s.next == blast_ref.MAXWIN:
                    s.next = 0
                    s.first = 0
        else:
            c = s.bits(8)
            s.out.append(c)
            s.next += 1
            if s.next == blast_ref.MAXWIN:
                s.next = 0
                s.first = 0
        ops += 1
except EOFError:
    print("EOF at out=%d input left=%d" % (len(s.out), len(body) - s.inpos))
print("final out:", len(s.out))
