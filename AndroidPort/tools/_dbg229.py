import io
path = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(path, encoding="utf-8").read()
subs = [
 ('                if (x < 0 || y < 0 || x >= mw * 32 || y >= mh * 32) offMap++;\n                else if (!walkM[((int) (y / 8)) * mw * 4 + (int) (x / 8)]) blocked++;',
  '                if (x < 0 || y < 0 || x >= mw * 32 || y >= mh * 32) { offMap++; System.out.println("    OFFMAP start " + id + " " + key + " " + x + "," + y + " map=" + mw + "x" + mh); }\n                else if (!walkM[((int) (y / 8)) * mw * 4 + (int) (x / 8)]) { blocked++; System.out.println("    BLOCKED start " + id + " " + key + " " + x + "," + y); }'),
 ('                    if (pt != null && (pt[0] < 0 || pt[1] < 0\n                            || pt[0] >= mw * 32 || pt[1] >= mh * 32)) offMap++;',
  '                    if (pt != null && (pt[0] < 0 || pt[1] < 0\n                            || pt[0] >= mw * 32 || pt[1] >= mh * 32)) { offMap++; System.out.println("    OFFMAP event " + id + " " + e.action + " " + pt[0] + "," + pt[1] + " map=" + mw + "x" + mh); }'),
]
for a, b in subs:
    assert src.count(a) == 1, (src.count(a), a[:60])
    src = src.replace(a, b)
io.open(path, "w", encoding="utf-8", newline="\n").write(src)
print("patched")