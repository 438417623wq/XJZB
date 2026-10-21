import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()
old = '''            lockstepHeld = same && pa.turnsReleased() == pb.turnsReleased()
                    && pa.turnsReleased() > 100;
'''
new = '''            lockstepHeld = same && pa.turnsReleased() == pb.turnsReleased()
                    && pa.turnsReleased() > 100;
            sb.append(" same=").append(same)
              .append(" aTurns=").append(pa.turnsReleased())
              .append(" bTurns=").append(pb.turnsReleased());
'''
assert src.count(old) == 1
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
print("debug added")