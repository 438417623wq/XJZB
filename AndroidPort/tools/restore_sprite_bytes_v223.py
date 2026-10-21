"""v2.23 asset gate fix: restore every shipped sprite WEBP whose bytes drifted.

Re-running pipeline_sprites rewrote every sheet as PNG and slim_assets
re-encoded it to WEBP. The pixels are identical (verified: 358/358 PNG-WEBP
pairs matched the shipped art exactly), but Pillow's encoder is not
bit-reproducible across runs, so 239 files changed bytes for no visual reason.
The iron rule is a byte-level diff=0, so the v2.22 bytes are written back for
every sprite that already existed. Only the genuinely new sheets
(goliath, dropship) and the regenerated manifest are left alone.
"""
import hashlib, os, zipfile

OLD = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.22.apk"
DISK = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"

z = zipfile.ZipFile(OLD)
old = {}
for n in z.namelist():
    if n.startswith("assets/sprites/") and not n.endswith("/"):
        old[n[len("assets/"):]] = z.read(n)

restored = 0
kept = 0
for rel, data in sorted(old.items()):
    p = os.path.join(DISK, rel.replace("/", os.sep))
    if not os.path.exists(p):
        kept += 1
        continue
    cur = open(p, "rb").read()
    if hashlib.sha256(cur).hexdigest() == hashlib.sha256(data).hexdigest():
        continue
    with open(p, "wb") as fp:
        fp.write(data)
    restored += 1
print("restored %d drifted sprite files; %d v2.22 sprites had no disk file"
      % (restored, kept))
