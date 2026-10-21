"""Read every tileset wpe with the standard key rule; report masks and try huffman."""
import sc_archive
import mphuff

ARS = [
    ("SD", sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")),
    ("BD", sc_archive.Archive(r"F:\KF\XJZB\BrooDat.mpq")),
]

for ts in ["badlands", "platform", "jungle", "ashworld", "desert", "ice", "twilight"]:
    name = "tileset\\%s.wpe" % ts
    for tag, ar in ARS:
        if not ar.has(name):
            continue
        bi = ar.find(name)
        o, cs, fs, flags, rel = ar.block_table[bi]
        base = sc_archive.hash_string(name.split("\\")[-1], sc_archive.HASH_FILE_KEY)
        key = ((base + rel) ^ fs) & 0xFFFFFFFF
        ar.fp.seek(o)
        raw = ar.fp.read(cs)
        dec = sc_archive.decrypt(raw, key) if (flags & 0x00010000) else raw
        m = dec[0]
        info = "mask=0x%02X" % m
        if m & 0x01:
            try:
                payload = mphuff.decompress(dec[1:], 1 << 20)
                info += " huffman->%dB dtypeOK first=%s" % (len(payload), payload[:8].hex())
                if m & 0x40:
                    import mpadi
                    payload2 = mpadi.decompress_adi_mono(payload, fs)
                    info += " adi->%dB" % len(payload2)
            except Exception as e:
                info += " huffman FAIL(%s)" % e
        elif m == 0x02:
            import zlib
            try:
                out = zlib.decompress(dec[1:])
                info += " zlib->%dB" % len(out)
            except Exception as e:
                info += " zlib FAIL"
        elif m == 0x08:
            from pkware import explode
            try:
                out = explode(dec[1:], fs)
                info += " pkware->%dB" % len(out)
            except Exception as e:
                info += " pkware FAIL"
        print("%-9s %-3s fs=%4d cs=%4d %s" % (ts, tag, fs, cs, info))
