import sc_archive, grp as grpm
ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(ROOT + r"\StarDat.mpq")
BD = sc_archive.Archive(ROOT + r"\BrooDat.mpq")
PT = sc_archive.Archive(ROOT + r"\patch_rt.mpq")
paths = [
 r"unit\thingy\emp.grp",
 r"unit\thingy\disrupt.grp",
 r"unit\thingy\dweb.grp",
 r"unit\thingy\plasma.grp",
 r"unit\thingy\ehaMed.grp",
 r"unit\bullet\blastcan.grp",
 r"unit\thingy\psiStorm.grp",
]
for p in paths:
    where = [n for n,a in (("PT",PT),("SD",SD),("BD",BD)) if a.has(p)]
    n = None
    for a in (PT,SD,BD):
        if a.has(p):
            try:
                d,g = a.read_with_gaps(p)
                f,mw,mh = grpm.decode_grp(d,g)
                n = (len(f), mw, mh)
            except Exception as e:
                n = "ERR " + str(e)
            break
    print("%-34s %-12s %s" % (p, ",".join(where) or "MISSING", n))
