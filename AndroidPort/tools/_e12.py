"""Batch E probe 12: are the six race score panels the same index map with six
palettes (i.e. recoloured chrome), or six different drawings? Compare index
arrays, not colours. Also print the top palette entries per panel."""
import os, sys
from collections import Counter

sys.path.insert(0, ".")
import sc_archive
import pipeline_score as psc

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

idx = {}
pals = {}
for race in ("P", "T", "Z"):
    for suf in ("d", "v"):
        key = "Score%s%s" % (race, suf)
        p = "glue\\%s\\pMain.pcx" % key
        arc = SD if SD.has(p) else BD
        data, _ = arc.read_with_gaps(p)
        px, pal, w, h = psc.pcx_decode(data)
        idx[key] = px
        pals[key] = [(pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2]) for i in range(256)]
        top = Counter(px).most_common(4)
        print("%-8s top indices %s" % (key, [(i, n, pals[key][i]) for i, n in top]))

print()
keys = list(idx)
for i in range(len(keys)):
    for j in range(i + 1, len(keys)):
        a, b = idx[keys[i]], idx[keys[j]]
        diff = sum(1 for k in range(len(a)) if a[k] != b[k])
        print("%-8s vs %-8s index-diff = %d / %d" % (keys[i], keys[j], diff, len(a)))
