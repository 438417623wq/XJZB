import gzip, os
A = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
walk=gzip.decompress(open(os.path.join(A,"maps","divide","walk.bin.gz"),"rb").read())
wMini=64*4
def ok(px,py):
    mx,my=int(px)//8,int(py)//8
    if mx<0 or my<0 or mx>=wMini or my>=64*4: return None
    return walk[my*wMini+mx]==1
print("row y=400:")
for x in range(120, 761, 40):
    print("   x=%3d -> %s" % (x, ok(x,400)))
