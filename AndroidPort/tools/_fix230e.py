import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()

old = '''        // ---- #6: the wire round-trips --------------------------------------
        String complex = "build 0,2,5 barracks 640 480";
        com.xjzb.rts.core.Lockstep.Cmd enc = new com.xjzb.rts.core.Lockstep.Cmd(417, 3, complex);
        com.xjzb.rts.core.Lockstep.Cmd dec = com.xjzb.rts.core.Lockstep.decode(enc.toString());
        boolean wire = dec != null && dec.turn == 417 && dec.player == 3
                && dec.cmd.equals(complex);
        ok &= wire;
        sb.append(" wire=").append(wire);
'''
new = '''        // ---- #6: the wire round-trips, heartbeat included -------------------
        // The heartbeat is the message every peer sends every single turn, so
        // it is the one that must survive the wire. It encodes with no trailing
        // field ("L 5 1"), and an earlier decode() that required a third field
        // dropped it -- which is a peer that has nothing to say looking exactly
        // like a peer that is not there.
        String complex = "build 0,2,5 barracks 640 480";
        com.xjzb.rts.core.Lockstep.Cmd enc = new com.xjzb.rts.core.Lockstep.Cmd(417, 3, complex);
        com.xjzb.rts.core.Lockstep.Cmd dec = com.xjzb.rts.core.Lockstep.decode(enc.toString());
        com.xjzb.rts.core.Lockstep.Cmd beatWire = com.xjzb.rts.core.Lockstep.decode(
                com.xjzb.rts.core.Lockstep.encode(5, 1, ""));
        boolean wire = dec != null && dec.turn == 417 && dec.player == 3
                && dec.cmd.equals(complex)
                && beatWire != null && beatWire.turn == 5 && beatWire.player == 1
                && beatWire.cmd.isEmpty();
        ok &= wire;
        sb.append(" wire=").append(wire);
'''
assert src.count(old) == 1, src.count(old)
src = src.replace(old, new)

old2 = '''        boolean tolerant = com.xjzb.rts.core.Lockstep.decode(null) == null
                && com.xjzb.rts.core.Lockstep.decode("") == null
                && com.xjzb.rts.core.Lockstep.decode("HELLO") == null
                && com.xjzb.rts.core.Lockstep.decode("L 12") == null
                && com.xjzb.rts.core.Lockstep.decode("L x 1 move 0 1 1") == null
                && com.xjzb.rts.core.Lockstep.decode("cmd 5 move 0 1 1") == null;
'''
new2 = '''        boolean tolerant = com.xjzb.rts.core.Lockstep.decode(null) == null
                && com.xjzb.rts.core.Lockstep.decode("") == null
                && com.xjzb.rts.core.Lockstep.decode("HELLO") == null
                && com.xjzb.rts.core.Lockstep.decode("L 12") == null
                && com.xjzb.rts.core.Lockstep.decode("L 12 0") != null
                && com.xjzb.rts.core.Lockstep.decode("L x 1 move 0 1 1") == null
                && com.xjzb.rts.core.Lockstep.decode("cmd 5 move 0 1 1") == null;
'''
assert src.count(old2) == 1, src.count(old2)
src = src.replace(old2, new2)
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("patched")