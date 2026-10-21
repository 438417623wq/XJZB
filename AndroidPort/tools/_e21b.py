import gzip, os
A = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
MID="divide"
walk=gzip.decompress(open(os.path.join(A,"maps",MID,"walk.bin.gz"),"rb").read())
wMini=64*4
def ok(px,py):
    mx,my=int(px)//8,int(py)//8
    return walk[my*wMini+mx]==1
for y in (400,430,460):
    row=" ".join("%d:%s"%(x,ok(x,y)) for x in range(100,520,60))
    print("y=%d  %s"%(y,row))
