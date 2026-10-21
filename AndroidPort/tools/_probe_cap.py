import gzip, os, json, glob, heapq, collections

ROOT = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
MAPS = os.path.join(ROOT, "maps"); MISS = os.path.join(ROOT, "missions")

def read_meta(mid):
    d = {}; starts = []
    for line in open(os.path.join(MAPS, mid, "meta.txt"), encoding="utf-8").read().splitlines():
        if line.startswith("start="):
            a, b = line[6:].split(","); starts.append((int(a), int(b)))
        elif "=" in line:
            k, v = line.split("=", 1); d[k] = v
    return int(d["w"]), int(d["h"]), starts

def load_walk(mid, wT, hT):
    for n in ("walk.bin.gz", "walk.gz"):
        p = os.path.join(MAPS, mid, n)
        if os.path.exists(p): return gzip.open(p, "rb").read()
    return open(os.path.join(MAPS, mid, "walk.bin"), "rb").read()

DX=[1,-1,0,0,1,1,-1,-1]; DY=[0,0,1,-1,1,-1,1,-1]

def nearest(pm,x,y,maxR=24):
    for r in range(0,maxR+1):
        for dy in range(-r,r+1):
            for dx in range(-r,r+1):
                if max(abs(dx),abs(dy))!=r: continue
                if pm(x+dx,y+dy): return (x+dx,y+dy)
    return None

def astar(pm,wMini,hMini,sx,sy,gx,gy,cap):
    if not pm(gx,gy):
        a=nearest(pm,gx,gy,24)
        if a is None: return None,-1
        gx,gy=a
    if not pm(sx,sy):
        a=nearest(pm,sx,sy,24)
        if a is None: return None,-1
        sx,sy=a
    def h(x,y):
        dx,dy=abs(x-gx),abs(y-gy); return (dx+dy)+(1.4142-2.0)*min(dx,dy)
    n=wMini*hMini; g=[float("inf")]*n; fr=[-1]*n; closed=[False]*n
    st=sy*wMini+sx; go=gy*wMini+gx
    g[st]=0; H=[(h(sx,sy),st)]; exp=0; found=-1
    while H and exp<cap:
        f,cur=heapq.heappop(H)
        if closed[cur]: continue
        closed[cur]=True; exp+=1
        if cur==go: found=cur; break
        cx,cy=cur%wMini,cur//wMini
        for d in range(8):
            nx,ny=cx+DX[d],cy+DY[d]
            if not pm(nx,ny): continue
            if d>=4 and (not pm(cx+DX[d],cy) or not pm(cx,cy+DY[d])): continue
            ni=ny*wMini+nx
            if closed[ni]: continue
            ng=g[cur]+(1.4142 if d>=4 else 1.0)
            if ng<g[ni]:
                g[ni]=ng; fr[ni]=cur
                heapq.heappush(H,(ng+h(nx,ny),ni))
    if found<0: return None,exp
    # true path length in minitile steps
    L=0.0; c=found
    while c!=-1 and c!=st:
        p=fr[c]
        if p==-1: break
        dx=abs(c%wMini-p%wMini); dy=abs(c//wMini-p//wMini)
        L+= 1.4142 if (dx and dy) else 1.0
        c=p
    return L,exp

print("=== unreachable vs cap-exhausted ===   (cap=60000 like Game.findPath)")
print(f"{'mis':5s} {'map':15s} {'cc':14s} {'hatch':14s} {'same?':6s} "
      f"{'cap60k':8s} {'exp@60k':8s} {'unlim_found':12s} {'true_len':9s} {'exp_unlim':9s}")
print("-"*118)
for mf in sorted(glob.glob(os.path.join(MISS,"*.json"))):
    j=json.load(open(mf,encoding="utf-8")); mid=j["id"]; mp=j["map"]
    wT,hT,starts=read_meta(mp); walk=load_walk(mp,wT,hT)
    wMini,hMini=wT*4,hT*4
    def pm(x,y): return 0<=x<wMini and 0<=y<hMini and walk[y*wMini+x]!=0
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
    cc=starts[0]
    hatch=None
    for su in j.get("startUnits",[]):
        if su.get("type")=="hatchery" and su.get("team")==1: hatch=(su["x"],su["y"]); break
    cm=nearest(pm,cc[0]//8,cc[1]//8); hm=nearest(pm,hatch[0]//8,hatch[1]//8)
    same = lab[cm[1]*wMini+cm[0]]==lab[hm[1]*wMini+hm[0]]
    L1,e1=astar(pm,wMini,hMini,hm[0],hm[1],cm[0],cm[1],60000)
    L2,e2=astar(pm,wMini,hMini,hm[0],hm[1],cm[0],cm[1],3000000)
    print(f"{mid:5s} {mp:15s} {str(cc):14s} {str(hatch):14s} {str(same):6s} "
          f"{str(L1 is not None):8s} {e1:<8d} {str(L2 is not None):12s} "
          f"{(f'{L2:.0f}' if L2 else '-'):9s} {e2:<9d}")
