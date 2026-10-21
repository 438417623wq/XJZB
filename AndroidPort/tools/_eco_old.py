import io, json
# m01 promises "the workers will mine", m04 tells the player to "stand by the
# ore vein", m05 tells them to manage supply for production. All three are
# factual claims about the map's economy, which setMission had removed
# (probe: minerals.size()==0 on every campaign level). m02/m03 describe a
# tactical strike with the force you are given and read correctly without one.
for mid in ("m01", "m04", "m05"):
    p = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\missions\%s.json" % mid
    raw = io.open(p, encoding="utf-8").read()
    obj = json.loads(raw)
    assert "economy" not in obj
    # keep the key order m01 already uses: insert after difficulty
    out = {}
    for k, v in obj.items():
        out[k] = v
        if k == "difficulty":
            out["economy"] = True
    txt = json.dumps(out, indent=1, ensure_ascii=False) + "\n"
    io.open(p, "w", encoding="utf-8", newline="\n").write(txt)
    print("enabled economy on", mid, "fields=", len([1 for _ in range(1)]))