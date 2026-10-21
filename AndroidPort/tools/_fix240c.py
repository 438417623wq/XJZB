import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()
old = '''            lockstepHeld = same && pa.turnsReleased() == pb.turnsReleased()
                    && pa.turnsReleased() > 100;
            sb.append(" same=").append(same)
              .append(" aTurns=").append(pa.turnsReleased())
              .append(" bTurns=").append(pb.turnsReleased());
'''
new = '''            // A real socket costs a frame of round-trip per turn: a report
            // written at frame N is only readable by the peer during frame N+1's
            // receive, so ~180 frames releases ~90 turns, not 180. What must
            // hold is that the count is substantial AND identical on both sides
            // -- the exact ratio is a property of the loop, not of the protocol.
            lockstepHeld = same && pa.turnsReleased() == pb.turnsReleased()
                    && pa.turnsReleased() > 60;
'''
assert src.count(old) == 1
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
print("threshold fixed")