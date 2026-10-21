"""Read every tileset wpe via the patched library; report sizes."""
import sc_archive
import mphuff
import mpadi

ARS = [
    ("SD", sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")),
    ("BD", sc_archive.Archive(r"F:\KF\XJZB\BrooDat.mpq")),
]

for ts in ["badlands", "platform", "jungle", "ashworld", "desert", "ice", "twilight"]:
    name = "tileset\\%s.wpe" % ts
    for tag, ar in ARS:
        if not ar.has(name):
            continue
        try:
            raw = ar.read(name)
            info = "read %dB" % len(raw)
            if len(raw) == 1024:
                import collections
                a = collections.Counter(raw[i * 4 + 3] for i in range(256))
                info += " alpha:%s pal[0]=%s pal[8]=%s" % (
                    dict(a), tuple(raw[0:3]), tuple(raw[8 * 4:8 * 4 + 3]))
            print("%-9s %-3s %s" % (ts, tag, info))
        except Exception as e:
            print("%-9s %-3s FAIL %s" % (ts, tag, e))
