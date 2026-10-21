import sys, os, struct, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = r"F:\KF\XJZB\scr_research\tileset"
T = r"F:\KF\XJZB\AndroidPort\tools"
lines = open(os.path.join(T,"images_tbl2.txt"), encoding="utf-8", errors="replace").read().splitlines()
dd = {}
for l in lines:
    if "\\dd" not in l.lower(): continue
    idx, name = l.split("\t")
    m = re.search(r"dd(\d{3})\.grp$", name, re.I)
    if m:
        dd.setdefault(name.split("\\")[2].lower(), {})[int(m.group(1))] = int(idx)
for ts, mp in dd.items():
    b = open(os.path.join(D, ts + ".dddata.bin"),"rb").read()
    nz = set()
    for e in range(512):
        row = b[e*512:(e+1)*512]
        if any(row): nz.add(e)
    ids = sorted(mp)
    print(f"--- {ts}: ddNNN ids={ids}")
    print(f"    all present in {ts}.dddata.bin? {all(i in nz for i in ids)}   missing={[i for i in ids if i not in nz]}")
    print(f"    images.tbl idx for these: {[mp[i] for i in ids]}")
