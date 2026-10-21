import io
p = r"F:\KF\XJZB\AndroidPort\tools\_V229Smoke.java"
src = io.open(p, encoding="utf-8").read()
old = '''            System.out.printf("%-5s %-14s %-8s %-6d %-22s %s%s%n", id, g.mission.map,
                    race, min, s60, s360,
                    g.mission.finished ? ("  [" + (g.mission.victory ? "WIN" : "LOSE")
                            + " t=" + (int) g.mission.elapsed() + "]") : "");
'''
new = '''            String tail = g.mission.finished
                    ? ("  [" + (g.mission.victory ? "WIN" : "LOSE")
                       + " t=" + (int) g.mission.elapsed() + "]")
                    : "";
            System.out.printf("%-5s %-14s %-8s %-6d %-22s %s%s%n", id, g.mission.map,
                    race, min, s60, s360, tail);
'''
assert src.count(old) == 1
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
print("fixed")