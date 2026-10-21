import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()
old = '''                long ha = pa.step(aCmd, 1f / 30f);
                long hb = pb.step("", 1f / 30f);
                hub.tick();
                if (ha != hb) same = false;
'''
new = '''                // The three phases are separated deliberately: both peers
                // receive, then both send, then both step. See LockstepPeer.
                pa.receiveFrame();
                pb.receiveFrame();
                pa.sendFrame(aCmd);
                pb.sendFrame("");
                hub.tick();
                long ha = pa.stepFrame(1f / 30f);
                long hb = pb.stepFrame(1f / 30f);
                if (ha != hb) same = false;
'''
assert src.count(old) == 1, src.count(old)
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
print("patched")