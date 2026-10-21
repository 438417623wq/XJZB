import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()
old = '''                // The three phases are separated deliberately: both peers
                // receive, then both send, then both step. See LockstepPeer.
                pa.receiveFrame();
                pb.receiveFrame();
                pa.sendFrame(aCmd);
                pb.sendFrame("");
                hub.tick();
'''
new = '''                // The three phases are separated deliberately: both peers
                // receive, then both send, then both step. See LockstepPeer.
                // sendFrame() is a no-op once the peer has reported this turn,
                // so calling it every frame still puts exactly one report per
                // turn on the wire -- which is the protocol contract.
                pa.receiveFrame();
                pb.receiveFrame();
                pa.queue(aCmd);
                pa.sendFrame();
                pb.sendFrame();
                hub.tick();
'''
assert src.count(old) == 1, src.count(old)
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
print("patched")