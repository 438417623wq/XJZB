import collections, os
lines = open("images_tbl2.txt", encoding="utf8", errors="replace").read().splitlines()
print("total lines:", len(lines))
print("--- 550..600 ---")
for l in lines[550:601]: print(l)
print("--- 690..719 ---")
for l in lines[690:719]: print(l)
print()
d = collections.Counter()
for l in lines:
    if "\t" not in l: continue
    i, p = l.split("\t", 1)
    if "thingy\\tileset" in p.lower():
        parts = p.split("\\")
        d[parts[2] if len(parts) > 2 else "?"] += 1
print("thingy dir counts:", dict(d), "sum", sum(d.values()))
print()
root = r"F:\KF\XJZB\AndroidPort\extracted\expand\doodads"
print("doodads dir exists:", os.path.isdir(root))
if os.path.isdir(root):
    fs = sorted(os.listdir(root))
    print("files:", len(fs))
    print(fs[:40])
