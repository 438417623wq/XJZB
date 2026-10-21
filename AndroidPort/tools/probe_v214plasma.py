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

# candidate lockdown / irradiate / emp-effect paths
cands = [r"unit\thingy\Lockdown.grp", r"unit\thingy\lockdown.grp",
         r"unit\thingy\Irradiate.grp", r"unit\thingy\irradiate.grp",
         r"unit\thingy\irrad.grp", r"unit\thingy\ehaMed.grp",
         r"unit\thingy\EMP.grp", r"unit\bullet\lockdown.grp"]
print("--- candidate effect GRPs ---")
for p in cands:
    w = [n for n,a in (("PT",PT),("SD",SD),("BD",BD)) if a.has(p)]
    print("  %-34s %s" % (p, ",".join(w) or "MISSING"))

def diff(a,b):
    A,B = a["px"], b["px"]
    n = min(len(A),len(B))
    return sum(abs(A[i]-B[i]) for i in range(n))/float(n)

r = dec(r"unit\thingy\plasma.grp")
frames, mw, mh = r
print("--- plasma layout test (n=%d) ---" % len(frames))
# hypothesis A: frame = dir*8 + step  -> steps for dir0 are 0..7
da = [diff(frames[i],frames[i+1]) for i in range(0,7)]
print("  A consecutive 0..7      : %s  mean=%.2f" % (["%.1f"%v for v in da], sum(da)/len(da)))
# hypothesis B: frame = step*17 + dir -> steps for dir0 are 0,17,34,...
db = [diff(frames[i*17],frames[(i+1)*17]) for i in range(0,7)]
print("  B step*17 (0,17,34,..)  : %s  mean=%.2f" % (["%.1f"%v for v in db], sum(db)/len(db)))
# control: random far-apart
dc = [diff(frames[i],frames[i+17]) for i in range(0,7)]
print("  C i vs i+17             : %s  mean=%.2f" % (["%.1f"%v for v in dc], sum(dc)/len(dc)))
