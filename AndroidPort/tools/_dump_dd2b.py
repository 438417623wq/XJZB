import os, sys, glob, re
sys.path.insert(0, ".")
import pipeline_maps as pm
TILESET = {0:"badlands",1:"platform",2:"install",3:"ashworld",4:"jungle"}

targets = ["hunters", "river", "divide", "bloodbath", "volcanis"]
cands = sorted(glob.glob(r"F:\KF\XJZB\maps\**\*.sc*", recursive=True))
for p in cands:
    bn = os.path.splitext(os.path.basename(p))[0].lower()
    bn = re.sub(r"^\(\d+\)", "", bn).strip()
    if bn not in targets: continue
    r = pm.read_chk(p)
    if not r: continue
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    if b"DD2 " not in sec: continue
    o,s = sec[b"DIM "]; b=g.bytes_at(o,s); W=b[0]|(b[1]<<8); H=b[2]|(b[3]<<8)
    o2,s2 = sec[b"ERA "]; b2=g.bytes_at(o2,s2); ts=b2[0]|(b2[1]<<8)
    off, sz = sec[b"DD2 "]
    print(f"### {os.path.basename(p)}  {W}x{H} ts={ts}({TILESET.get(ts)})  DD2 off={off} size={sz}  size%8={sz%8} gaps={gaps}")
    raw = g.bytes_at(off, min(sz, 160))
    for i in range(0, len(raw), 16):
        chunk = raw[i:i+16]
        hx = " ".join("%02x" % c for c in chunk)
        desc = ""
        if len(chunk) >= 8:
            t = chunk[0]|(chunk[1]<<8); x = chunk[2]|(chunk[3]<<8); y = chunk[4]|(chunk[5]<<8)
            desc = f"  t={t} x={x} y={y}"
        print(f"  {i:4d}  {hx:<48}{desc}")
    print()
