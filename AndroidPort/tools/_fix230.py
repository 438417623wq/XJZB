import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()

old = '''        com.xjzb.rts.core.Game live = cleanGame("terran");
        live.lockstep = new Lockstep(2);
        live.lockstepPlayer = 0;
        java.util.List<com.xjzb.rts.core.Game.Ent> scvs = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : live.ents)
            if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);
        java.util.List<Long> a = new ArrayList<>();
        for (int t = 0; t < 30 * 40; t++) {
            // both peers must report every turn, so the harness stands in for
            // the second machine: player 0 speaks every 10 s, player 1 never.
            if (live.lockstep.turn == live.lockstep.turn) {
                if (t % 300 == 0 && !scvs.isEmpty())
                    live.recordOrder("move", scvs, (400 + t) + " " + (400 + t));
                live.lockstep.submit(1, "");
            }
            live.update(1f / 30f);
            if (t % 30 == 29) a.add(live.stateHash());
        }
'''
new = '''        com.xjzb.rts.core.Game live = cleanGame("terran");
        com.xjzb.rts.core.Lockstep sess = new com.xjzb.rts.core.Lockstep(2);
        live.lockstep = sess;
        live.lockstepPlayer = 0;
        java.util.List<com.xjzb.rts.core.Game.Ent> scvs = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : live.ents)
            if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);
        java.util.List<Long> a = new ArrayList<>();
        for (int t = 0; t < 30 * 40; t++) {
            // The harness stands in for the second machine: player 0 issues an
            // order every 10 s, player 1 only ever sends the heartbeat. Both
            // reports must land before update() will advance the turn.
            if (t % 300 == 0 && !scvs.isEmpty())
                live.recordOrder("move", scvs, (400 + t) + " " + (400 + t));
            sess.submit(1, "");
            live.update(1f / 30f);
            if (t % 30 == 29) a.add(live.stateHash());
        }
'''
assert src.count(old) == 1, src.count(old)
src = src.replace(old, new)

old2 = '''        boolean cmdsSeen = live.lockstep.commands().size() >= 3;

        String body = live.lockstep.serialize();
'''
new2 = '''        boolean cmdsSeen = sess.commands().size() >= 3;

        String body = sess.serialize();
'''
assert src.count(old2) == 1, src.count(old2)
src = src.replace(old2, new2)

old3 = '''        sb.append(" session=").append(session).append(" cmds=")
          .append(live.lockstep.commands().size()).append(" samples=").append(a.size());
'''
new3 = '''        sb.append(" session=").append(session).append(" cmds=")
          .append(sess.commands().size()).append(" samples=").append(a.size());
'''
assert src.count(old3) == 1, src.count(old3)
src = src.replace(old3, new3)

# Lockstep is in the same package as Game but GameDesktop only imports Game.
src = src.replace("        Lockstep ls = new Lockstep(2);",
                  "        com.xjzb.rts.core.Lockstep ls = new com.xjzb.rts.core.Lockstep(2);")
src = src.replace("        Lockstep gate = new Lockstep(2);",
                  "        com.xjzb.rts.core.Lockstep gate = new com.xjzb.rts.core.Lockstep(2);")
src = src.replace("        Lockstep quiet = new Lockstep(2);",
                  "        com.xjzb.rts.core.Lockstep quiet = new com.xjzb.rts.core.Lockstep(2);")
src = src.replace("        Lockstep dup = new Lockstep(2);",
                  "        com.xjzb.rts.core.Lockstep dup = new com.xjzb.rts.core.Lockstep(2);")
src = src.replace("        Lockstep.Cmd enc = new Lockstep.Cmd(417, 3, complex);",
                  "        com.xjzb.rts.core.Lockstep.Cmd enc = new com.xjzb.rts.core.Lockstep.Cmd(417, 3, complex);")
src = src.replace("        Lockstep.Cmd dec = Lockstep.decode(enc.toString());",
                  "        com.xjzb.rts.core.Lockstep.Cmd dec = com.xjzb.rts.core.Lockstep.decode(enc.toString());")
src = src.replace("        Lockstep ds = new Lockstep(2);",
                  "        com.xjzb.rts.core.Lockstep ds = new com.xjzb.rts.core.Lockstep(2);")
src = src.replace("            java.util.List<Lockstep.Cmd> out = ls.release();",
                  "            java.util.List<com.xjzb.rts.core.Lockstep.Cmd> out = ls.release();")
src = src.replace("            for (Lockstep.Cmd c : out) sig.append(c.player)",
                  "            for (com.xjzb.rts.core.Lockstep.Cmd c : out) sig.append(c.player)")
src = src.replace("        java.util.List<Lockstep.Cmd> one = gate.release();",
                  "        java.util.List<com.xjzb.rts.core.Lockstep.Cmd> one = gate.release();")
src = src.replace("        java.util.List<Lockstep.Cmd> dl = dup.release();",
                  "        java.util.List<com.xjzb.rts.core.Lockstep.Cmd> dl = dup.release();")
src = src.replace("                && Lockstep.decode(\"HELLO\") == null\n                && Lockstep.decode(\"L 12\") == null\n                && Lockstep.decode(\"L x 1 move 0 1 1\") == null\n                && Lockstep.decode(\"cmd 5 move 0 1 1\") == null;",
                  "                && com.xjzb.rts.core.Lockstep.decode(\"HELLO\") == null\n                && com.xjzb.rts.core.Lockstep.decode(\"L 12\") == null\n                && com.xjzb.rts.core.Lockstep.decode(\"L x 1 move 0 1 1\") == null\n                && com.xjzb.rts.core.Lockstep.decode(\"cmd 5 move 0 1 1\") == null;")
src = src.replace("        boolean tolerant = Lockstep.decode(null) == null",
                  "        boolean tolerant = com.xjzb.rts.core.Lockstep.decode(null) == null")
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("patched")