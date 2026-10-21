import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe_v216walkimg as wi
for name in [r"maps\ladder\(4)Dire Straits.scm", r"maps\(2)The Small Divide.scm"]:
    w,h,walk,starts=wi.walk_of(name)
    W,H=w*4,h*4
    print("=== ", os.path.basename(name), w,h, "starts", starts)
    step=4  # sample every 16 px -> 32 cols for 128 tile map
    for y in range(0,H,step*4):
        row=[]
        for x in range(0,W,step*4):
            row.append("#" if walk[y*W+x] else ".")
        s="".join(row)
        # mark starts
        marks=list(s)
        for sx,sy in starts:
            if abs(sy-y)<step*4:
                ci=sx//(step*4)
                if 0<=ci<len(marks): marks[ci]="S"
        print("".join(marks))
