import os, glob, struct
root = r"F:\KF\XJZB"
found = []
for dirpath, dirnames, filenames in os.walk(root):
    if 'scr_research' in dirpath: continue
    for fn in filenames:
        if fn.lower().endswith(('.scm','.scx','.chk')):
            found.append(os.path.join(dirpath, fn))
print("candidate map files:", len(found))
def sections(data):
    i=0; out=[]
    while i+8 <= len(data):
        tag=data[i:i+4]; size=struct.unpack_from('<i',data,i+4)[0]
        out.append((tag,size,i))
        if size<0: break
        i += 8+size
    return out
for f in found:
    d=open(f,'rb').read()
    if d[:4]==b'MPQ\x1a':
        print("MPQ  ", os.path.relpath(f,root)); continue
    tags=[t.decode('latin1') for t,_,_ in sections(d)]
    print("CHK  ", os.path.relpath(f,root), "|", " ".join(sorted(set(tags))))
