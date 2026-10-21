import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm, sc_archive
for name in [r"F:\KF\XJZB\maps\(4)Inferno.scm", r"F:\KF\XJZB\maps\(4)Blood Bath.scm"]:
    print("#"*20, name)
    ar = sc_archive.Archive(name)
    print("has chk:", ar.has("staredit\\scenario.chk"))
    data, gaps = ar.read_with_gaps("staredit\\scenario.chk")
    print("read len", len(data), "recorded", ar.info("staredit\\scenario.chk")["size"], "gaps", gaps)
    g, sec = pm.parse_chk(data, gaps)
    print("tags", sorted(t.decode(errors="replace") for t in sec))
    off, sz = sec[b"DD2 "]
    print("DD2 off", off, "size", sz, "recs", sz//8)
    raw = g.bytes_at(off, sz)
    recs = [struct.unpack_from("<HHHBB", raw, i) for i in range(0, sz, 8)]
    bad = [(i,r) for i,r in enumerate(recs) if r[0] > 511]
    print("ids>511:", len(bad), bad[:6])
    print("first 20:", recs[:20])
    print("raw first 64:", raw[:64].hex(" "))
