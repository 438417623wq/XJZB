import zipfile, hashlib, os
A = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.41.apk"
B = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.42.apk"
za, zb = zipfile.ZipFile(A), zipfile.ZipFile(B)
na = {i.filename: i for i in za.infolist()}
nb = {i.filename: i for i in zb.infolist()}
onlyA = sorted(set(na) - set(nb))
onlyB = sorted(set(nb) - set(na))
print("entries: v241=%d v242=%d" % (len(na), len(nb)))
print("only in v2.41: %d" % len(onlyA))
for x in onlyA[:20]: print("   -", x)
print("only in v2.42: %d" % len(onlyB))
for x in onlyB[:20]: print("   +", x)

def h(z, n):
    return hashlib.sha256(z.read(n)).hexdigest()

changed = []
for n in sorted(set(na) & set(nb)):
    if na[n].file_size != nb[n].file_size:
        changed.append(n)
        continue
    if h(za, n) != h(zb, n):
        changed.append(n)
print("size/hash-changed entries: %d" % len(changed))
groups = {}
for n in changed:
    top = "/".join(n.split("/")[:3])
    groups[top] = groups.get(top, 0) + 1
for k in sorted(groups, key=lambda k: -groups[k])[:25]:
    print("   %-40s %d" % (k, groups[k]))
print("--- non-asset changed entries ---")
for n in changed:
    if not n.startswith("assets/"):
        print("   ", n)
