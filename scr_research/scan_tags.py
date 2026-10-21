import sys, os, glob, struct, collections
root = r'F:\KF\XJZB'
maps = glob.glob(os.path.join(root,'maps','*.scm')) + glob.glob(os.path.join(root,'maps','*.scx'))
print('maps found:', len(maps))
def sections(data):
    i = 0
    out = []
    while i + 8 <= len(data):
        tag = data[i:i+4]
        size = struct.unpack_from('<i', data, i+4)[0]
        out.append((tag, size, i))
        if size < 0: break
        i += 8 + size
    return out
tags = collections.Counter()
for m in maps:
    data = open(m,'rb').read()
    for tag,size,off in sections(data):
        tags[tag] += 1
for t,c in tags.most_common(60):
    print(repr(t), c)
