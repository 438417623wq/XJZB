import io
p = r"F:\KF\XJZB\AndroidPort\tools\_Dbg231e.java"
src = io.open(p, encoding="utf-8").read()
src = src.replace(
'''            pa.sendFrame(aCmd);
            pb.sendFrame("");
            hub.tick();''',
'''            pa.sendFrame(aCmd);
            pb.sendFrame("");
            System.out.println("    pre-step readyA=" + pa.session.ready()
                    + " readyB=" + pb.session.ready()
                    + " ga.lockstep=" + (ga.lockstep != null)
                    + " gb.lockstep=" + (gb.lockstep != null)
                    + " sameObj=" + (ga.lockstep == pa.session));
            hub.tick();''')
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("ok")