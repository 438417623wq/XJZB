import io
p = r"F:\KF\XJZB\AndroidPort\tools\_gen_v229_missions.py"
src = io.open(p, encoding="utf-8").read()
subs = [
 # a wave origin must be strictly inside the map: the engine clamps a spawn to
 # the world rect, so x == wPx is already off the edge.
 ('        if not (0 <= su["x"] <= w * 32 and 0 <= su["y"] <= h * 32):',
  '        if not (0 <= su["x"] < w * 32 and 0 <= su["y"] < h * 32):'),
 ('                if not (0 <= x <= w * 32 and 0 <= y <= h * 32):',
  '                if not (0 <= x < w * 32 and 0 <= y < h * 32):'),
 # riverlethe is 128x192, so y = 5904 + 240 = 6144 is exactly hPx -- one pixel
 # past the edge. Aim the second enemy base's push 120 px out instead.
 ('         wave(210, ["zergling"] * 5 + ["lurker"], (v2[0] - 80, v2[1] + 240), v0, 0.35),',
  '         wave(210, ["zergling"] * 5 + ["lurker"], (v2[0] - 80, v2[1] + 120), v0, 0.35),'),
]
for a, b in subs:
    assert src.count(a) == 1, (src.count(a), a[:70])
    src = src.replace(a, b)
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("generator patched")