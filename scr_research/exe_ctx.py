import sys, os, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"F:\KF\XJZB\StarEdit.exe"
d = open(p, "rb").read()
def strings_near(needle, before=80, after=200, limit=12):
    out=[]
    i=0
    while True:
        j=d.find(needle,i)
        if j<0: break
        out.append(j); i=j+1
        if len(out)>=limit: break
    return out
for needle in (b"DD2 ", b"dddata.bin"):
    print("="*20, needle)
    for off in strings_near(needle):
        seg = d[max(0,off-120):off+160]
        txt = re.sub(rb"[^\x20-\x7e]", b".", seg).decode("ascii")
        print(f"  @{off:#x}: {txt}")
