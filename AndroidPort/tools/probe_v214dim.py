import sc_archive, grp as grpm
ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(ROOT + r"\StarDat.mpq")
BD = sc_archive.Archive(ROOT + r"\BrooDat.mpq")
PT = sc_archive.Archive(ROOT + r"\patch_rt.mpq")
def dec(p):
    for a in (PT,SD,BD):
        if a.has(p):
            d,g = a.read_with_gaps(p)
            return grpm.decode_grp(d,g)
    return None
for p in [r"unit\thingy\emp.grp", r"unit\thingy\disrupt.grp", r"unit\thingy\plasma.grp",
          r"unit\thingy\ehaMed.grp", r"unit\bullet\blastcan.grp"]:
    r = dec(p)
    if r is None:
        print(p, "MISSING"); continue
    frames, mw, mh = r
    print("=== %s  n=%d maxcell=%dx%d" % (p, len(frames), mw, mh))
    sizes = {}
    for i,f in enumerate(frames):
        sizes.setdefault((f["w"],f["h"]), []).append(i)
    for k in sorted(sizes, key=lambda k: sizes[k][0]):
        idx = sizes[k]
        print("    %dx%d x%d  frames %s" % (k[0], k[1], len(idx),
              str(idx) if len(idx) <= 20 else str(idx[:8])+"..."+str(idx[-3:])))
