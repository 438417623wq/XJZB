import gzip, os, sys
ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
def load(mid):
    meta={}; starts=[]; units=[]
    for line in open(os.path.join(ASSETS,"maps",mid,"meta.txt"), encoding="utf-8"):
        line=line.strip()
        if line.startswith("w="): meta["w"]=int(line[2:])
        elif line.startswith("h="): meta["h"]=int(line[2:])
        elif line.startswith("start="):
            p=line[6:].split(","); starts.append((int(p[0]),int(p[1])))
        elif line.startswith("unit="):
            p=line[5:].split(","); units.append((int(p[0]),float(p[1]),float(p[2])))
    raw=gzip.decompress(open(os.path.join(ASSETS,"maps",mid,"walk.bin.gz"),"rb").read())
    return meta["w"],meta["h"],raw,starts,units
mid=sys.argv[1]; sx=int(sys.argv[2]); sy=int(sys.argv[3])
w,h,raw,starts,units=load(mid); wm,hm=w*4,h*4
x0,y0=max(0,sx-192),max(0,sy-96); x1,y1=min(w*32,sx+320),min(h*32,sy+320)
print("%s around (%d,%d)  '#'=walk '.'=blocked  each char=8px"%(mid,sx,sy))
print("     "+"".join(str(((x//8)//10)%10) for x in range(x0,x1,8)))
for y in range(y0,y1,8):
    row="".join("#" if raw[(y//8)*wm+(x//8)] else "." for x in range(x0,x1,8))
    print("%4d %s"%(y,row))
print("x labels are (x/8) tens digit; x from %d to %d"%(x0,x1))
