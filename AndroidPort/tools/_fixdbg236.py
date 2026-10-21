import io
p = r"F:\KF\XJZB\AndroidPort\tools\_Dbg236b.java"
src = io.open(p, encoding="utf-8").read()
old = '''                int X = (int) (e.x / 8), Y = (int) (e.y / 8);
                if (seen[Y * g.wMini + X]) hit++;
                else unreach.append(" (").append(X).append(",").append(Y).append(")");'''
new = '''                // The hatchery's own tile is blocked by its footprint, so ask
                // for the nearest walkable tile rather than testing the tile it
                // stands on -- otherwise every level looks unreachable.
                int[] fs = g.nearestPassMini((int) (e.x / 8), (int) (e.y / 8), 40);
                if (fs != null && seen[fs[1] * g.wMini + fs[0]]) hit++;
                else unreach.append(" (").append(fs == null ? "null" : fs[0] + "," + fs[1]).append(")");'''
assert src.count(old) == 1
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
print("fixed")