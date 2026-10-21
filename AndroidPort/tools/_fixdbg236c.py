import io
p = r"F:\KF\XJZB\AndroidPort\tools\_Dbg236c.java"
src = io.open(p, encoding="utf-8").read()
old = '''        int[][] probes = {{336,176},{2368,240},{3200,3136},{384,3696},{3712,3760}};
        for (int[] p : probes)
            System.out.println("   probe (" + p[0] + "," + p[1] + ") -> comp "
                    + lab[(p[1] / 8) * w + (p[0] / 8)]);'''
new = '''        int[][] probes = {{336,176},{2368,240},{3200,3200},{384,3696},{3712,3760}};
        for (int[] p : probes) {
            int[] s = g.nearestPassMini(p[0] / 8, p[1] / 8, 40);
            System.out.println("   probe (" + p[0] + "," + p[1] + ") nearestPass="
                    + (s == null ? "null" : s[0] * 8 + "," + s[1] * 8)
                    + " -> comp " + (s == null ? -1 : lab[s[1] * w + s[0]]));
        }'''
assert src.count(old) == 1
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
print("fixed")