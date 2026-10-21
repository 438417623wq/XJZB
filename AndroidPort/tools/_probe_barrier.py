import gzip, os, collections
MAPS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"
mid = "divide"; wT = hT = 64; wMini = hMini = 256
walk = gzip.open(os.path.join(MAPS, mid, "walk.bin.gz"), "rb").read()
for n in ("void.bin.gz", "elev.bin.gz"):
    p = os.path.join(MAPS, mid, n)
    d = gzip.open(p, "rb").read()
    print(f"{n}: decompressed {len(d)} bytes; distinct={sorted(set(d))[:10]}")

DX=[1,-1,0,0,1,1,-1,-1]; DY=[0,0,1,-1,1,-1,1,-1]
lab=[-1]*(wMini*hMini); sizes=[]
for i in range(wMini*hMini):
    if walk[i]==0 or lab[i]!=-1: continue
    cid=len(sizes); lab[i]=cid; q=collections.deque([i]); n=0
    while q:
        cur=q.popleft(); n+=1; cx,cy=cur%wMini,cur//wMini
        for d in range(8):
            nx,ny=cx+DX[d],cy+DY[d]
            if 0<=nx<wMini and 0<=ny<hMini:
                ni=ny*wMini+nx
                if walk[ni] and lab[ni]==-1: lab[ni]=cid; q.append(ni)
    sizes.append(n)

# how thick is the barrier between comp0 and comp1? scan rows, measure run lengths
print("\nrun-length of blocked spans between comp0 and comp1 (minitile rows 40..90):")
for my in range(40, 92, 4):
    row = [walk[my*wMini+mx] for mx in range(wMini)]
    # find transitions
    runs=[]; cur=row[0]; start=0
    for mx in range(1,wMini):
        if row[mx]!=cur:
            runs.append((cur,start,mx-1)); cur=row[mx]; start=mx
    runs.append((cur,start,wMini-1))
    blocked=[(a,b) for v,a,b in runs if not v]
    widths=[b-a+1 for a,b in blocked if a<200]
    print(f"  my={my:3d} blocked spans(width) first 6: {widths[:6]}")

# zoom view of the 0/1 boundary, minitiles, 1 char = 1 minitile
print("\nZOOM minitile view: rows 60..110, cols 60..170  ('0'/'1'=comp, '#'=blocked)")
print("      " + "".join(str((c//10)%10) for c in range(60,170)))
print("      " + "".join(str(c%10) for c in range(60,170)))
for my in range(60, 111):
    r=[]
    for mx in range(60,170):
        i=my*wMini+mx
        r.append("#" if walk[i]==0 else str(lab[i]%10))
    print(f"{my:4d}  "+"".join(r))

# does any blocked minitile have both comp0 and comp1 as orthogonal neighbours?
print("\nbarrier thickness histogram: for each blocked minitile on the 0|1 frontier, "
      "count how many blocked minitiles are in its 8-neighbourhood")
cnt=collections.Counter()
for my in range(1,hMini-1):
    for mx in range(1,wMini-1):
        i=my*wMini+mx
        if walk[i]: continue
        nb=[lab[(my+dy)*wMini+(mx+dx)] for dx,dy in zip(DX,DY)]
        if 0 in nb and 1 in nb:
            b=sum(1 for dx,dy in zip(DX,DY) if not walk[(my+dy)*wMini+(mx+dx)])
            cnt[b]+=1
print("  ", dict(sorted(cnt.items())))
