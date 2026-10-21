import zipfile, os, json
A = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.41.apk"
DISK = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
za = zipfile.ZipFile(A)
n = "assets/maps/divide/meta.json"
a = za.read(n); b = open(os.path.join(DISK, "maps", "divide", "meta.json"), "rb").read()
print("v241 len=%d  v242 len=%d  bytes-equal=%s" % (len(a), len(b), a == b))
ja, jb = json.loads(a), json.loads(b)
print("semantic-equal =", ja == jb)
for k in sorted(set(ja) | set(jb)):
    if ja.get(k) != jb.get(k):
        print("  ~ %s: %r -> %r" % (k, ja.get(k), jb.get(k)))
# text order check
print("v241 head:", a[:120])
print("v242 head:", b[:120])
# now compare all 52 semantically
bad = 0
for nn in za.namelist():
    if not nn.endswith("/meta.json"): continue
    mid = nn.split("/")[-2]
    p = os.path.join(DISK, "maps", mid, "meta.json")
    ja = json.loads(za.read(nn)); jb = json.loads(open(p, encoding="utf8").read())
    if ja != jb:
        bad += 1
        if bad <= 5:
            for k in sorted(set(ja) | set(jb)):
                if ja.get(k) != jb.get(k):
                    print("  %s ~ %s: %r -> %r" % (mid, k, ja.get(k), jb.get(k)))
print("meta.json semantic mismatches = %d" % bad)
