import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()
old = '''        // ---- #5: a duplicate packet cannot run twice -----------------------
        com.xjzb.rts.core.Lockstep dup = new com.xjzb.rts.core.Lockstep(2);
        dup.submit(0, "move 0 100 100");
        dup.submit(0, "move 0 200 200");   // second report ignored
        dup.submit(1, "");
        java.util.List<com.xjzb.rts.core.Lockstep.Cmd> dl = dup.release();
        boolean once = dl.size() == 1 && dl.get(0).cmd.equals("move 0 100 100");
        ok &= once;
        sb.append(" dedup=").append(once);
'''
new = '''        // ---- #5: duplicates and out-of-order heartbeats ---------------------
        // Two rules, and the second one was a real bug: a genuine duplicate
        // packet must not run a command twice, AND a heartbeat that arrives
        // BEFORE the real command (a reordering link does this) must not
        // suppress it -- storing the empty placeholder and dropping the order
        // would silently desync one machine from the other.
        com.xjzb.rts.core.Lockstep dup = new com.xjzb.rts.core.Lockstep(2);
        dup.submit(0, "move 0 100 100");
        dup.submit(0, "move 0 200 200");   // second report ignored
        dup.submit(1, "");
        java.util.List<com.xjzb.rts.core.Lockstep.Cmd> dl = dup.release();
        boolean once = dl.size() == 1 && dl.get(0).cmd.equals("move 0 100 100");

        com.xjzb.rts.core.Lockstep rw = new com.xjzb.rts.core.Lockstep(2);
        rw.submit(0, "");                              // heartbeat lands first
        rw.submit(0, "build 4 barracks 300 300");      // real order lands second
        rw.submit(1, "");
        java.util.List<com.xjzb.rts.core.Lockstep.Cmd> rl = rw.release();
        boolean keepOrder = rl.size() == 1
                && rl.get(0).cmd.equals("build 4 barracks 300 300");
        // and the other way round: the heartbeat cannot overwrite the order
        com.xjzb.rts.core.Lockstep rw2 = new com.xjzb.rts.core.Lockstep(2);
        rw2.submit(0, "build 4 barracks 300 300");
        rw2.submit(0, "");
        rw2.submit(1, "");
        java.util.List<com.xjzb.rts.core.Lockstep.Cmd> rl2 = rw2.release();
        boolean keepOrder2 = rl2.size() == 1
                && rl2.get(0).cmd.equals("build 4 barracks 300 300");
        ok &= once && keepOrder && keepOrder2;
        sb.append(" dedup=").append(once)
          .append(" heartbeatFirst=").append(keepOrder)
          .append(" heartbeatLast=").append(keepOrder2);
'''
assert src.count(old) == 1, src.count(old)
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
print("patched")