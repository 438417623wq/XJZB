import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import sc_archive
sd = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
data, gaps = sd.read_with_gaps("tileset\\platform.cv5")
mine = open(r"F:\KF\XJZB\scr_research\tileset\platform.cv5", "rb").read()
print("data len", len(data), "gaps", gaps, "mine len", len(mine))
# hypothesis A: mine == data zero-padded at gap positions (correct)
def pad(data, gaps, total):
    out = bytearray(); prev = 0
    for pos, size in gaps:
        out += data[prev:pos]
        out += bytes(size)
        prev = pos
    out += data[prev:]
    out += bytes(total - len(out))
    return bytes(out)
A = pad(data, gaps, 78676)
print("hypothesis A (pad at gaps) matches mine:", A == mine)
# hypothesis B: mine == data then zero tail
B = data + bytes(78676 - len(data))
print("hypothesis B (zeros at end) matches mine:", B == mine)
# where do they differ
for i in range(len(mine)):
    if A[i] != mine[i]:
        print("first A-vs-mine diff at", i, "A", A[i:i+8].hex(), "mine", mine[i:i+8].hex()); break
else:
    print("A == mine everywhere")
