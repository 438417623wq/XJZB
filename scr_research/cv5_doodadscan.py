import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = r"F:\KF\XJZB\scr_research\tileset"
for ts, targets in [("platform", {137, 256, 257}), ("ashworld", set(range(0,143)))]:
    b = open(os.path.join(D, ts + ".cv5"), "rb").read()
    n = len(b)//52
    hits = []
    for g in range(n):
        base = g*52
        f = struct.unpack_from("<10H", b, base)
        # f[0]=index f[1]=flags f[2]=overlay f[3]=remastered f[4]=name f[5]=unk f[6]=ddData f[7]=w f[8]=h f[9]=unk2
        if f[6] in targets and 1 <= f[7] <= 16 and 1 <= f[8] <= 16 and f[4] != 0:
            hits.append((g, f))
    print(f"### {ts}: groups={n} doodad-shaped hits={len(hits)}")
    for g, f in hits[:25]:
        print(f"   g{g}: idx={f[0]} flags=0x{f[1]:04x} overlay={f[2]} remastered={f[3]} name={f[4]} ddData={f[6]} w={f[7]} h={f[8]}")
