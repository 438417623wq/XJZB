import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"F:\KF\XJZB\AndroidPort\assets_src\maps\(1)Enslavers01.chk"
b = open(p,"rb").read()
i = 0
n = 0
while i + 8 <= len(b) and n < 60:
    tag = b[i:i+4]
    size = struct.unpack_from("<I", b, i+4)[0]
    ok = i+8+size <= len(b)
    print(f"{n:3d} at {i:8d} tag={tag!r} size={size} ok={ok}")
    if not ok:
        print("   OVERRUN -> stop")
        break
    i += 8 + size
    n += 1
