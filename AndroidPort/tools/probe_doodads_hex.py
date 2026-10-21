"""Eyeball the StarEdit.exe doodad-sprite-dense region: dump bytes around
0x9f0cc with several stride hypotheses so the record structure can be read
by eye. Also annotate u16s that are doodad sprite ids (0..95 art range)."""
import struct

DENSE = list(range(0, 96)) + [301, 302, 321, 374, 375, 376]

blob = open(r"F:\KF\XJZB\StarEdit.exe", "rb").read()
base = 0x9F000
for row in range(base, base + 0x300, 16):
    bs = blob[row:row + 16]
    hexs = " ".join("%02x" % b for b in bs)
    ann = []
    for k in range(0, 16, 2):
        v = bs[k] | (bs[k + 1] << 8)
        mark = "*" if v in DENSE else " "
        ann.append("%4d%s" % (v, mark))
    print("%06x  %s  | %s" % (row, hexs, " ".join(ann)))
