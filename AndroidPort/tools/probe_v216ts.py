import os,sys
sys.path.insert(0,'.')
import pipeline_maps as pm
for ts in ['jungle','platform','ice','twilight','desert','badlands','install','ashworld']:
    def rd(n):
        for ar in (pm.SD, pm.BD):
            p='tileset\\%s.%s'%(ts,n)
            if ar.has(p): return ar.read_with_gaps(p)
        return None,None
    vx4,g2=rd('vx4'); vf4,g4=rd('vf4'); vr4,g3=rd('vr4')
    def cnt(buf,gaps,size):
        if buf is None: return -1
        return (len(buf)+sum(s for _,s in (gaps or [])))//size
    print('%-9s vx4=%5d(g%2d) vf4=%5d(g%2d) vr4=%5d  vx4len=%7d vf4len=%7d' % (
        ts, cnt(vx4,g2,32), len(g2 or []), cnt(vf4,g4,32), len(g4 or []), cnt(vr4,g3,64),
        len(vx4 or b''), len(vf4 or b'')))
