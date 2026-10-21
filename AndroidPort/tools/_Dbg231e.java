public class _Dbg231e {
    public static void main(String[] a) throws Exception {
        GameDesktop.readManifestPublic();
        GameDesktop.readMapPublic("bloodbath");
        com.xjzb.rts.core.LockstepLink.Hub hub =
                new com.xjzb.rts.core.LockstepLink.Hub(2, 2, 5, true, 4242L);
        com.xjzb.rts.core.Game ga = GameDesktop.cleanGame("terran");
        com.xjzb.rts.core.Game gb = GameDesktop.cleanGame("terran");
        com.xjzb.rts.core.LockstepPeer pa = new com.xjzb.rts.core.LockstepPeer(ga, 0, 2, hub.end(0));
        com.xjzb.rts.core.LockstepPeer pb = new com.xjzb.rts.core.LockstepPeer(gb, 1, 2, hub.end(1));
        java.util.List<com.xjzb.rts.core.Game.Ent> scvs = new java.util.ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : ga.ents)
            if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);
        for (int t = 0; t < 12; t++) {
            String aCmd = (t == 0 && !scvs.isEmpty())
                    ? ga.commandFor("move", scvs, "400 400") : "";
            System.out.println("--- frame " + t + " hubFrame=" + hub.frame()
                    + " A.turn=" + pa.session.turn + " B.turn=" + pb.session.turn
                    + " aCmd='" + aCmd + "'");
            java.util.List<String> inA = pa.link.poll(), inB = pb.link.poll();
            System.out.println("    A recv " + inA + "   B recv " + inB);
            for (String s : inA) { com.xjzb.rts.core.Lockstep.Cmd c = com.xjzb.rts.core.Lockstep.decode(s);
                pb.session.submitAt(c.player, c.turn, c.cmd); }
            for (String s : inB) { com.xjzb.rts.core.Lockstep.Cmd c = com.xjzb.rts.core.Lockstep.decode(s);
                pa.session.submitAt(c.player, c.turn, c.cmd); }
            pa.sendFrame(aCmd);
            pb.sendFrame("");
            System.out.println("    pre-step readyA=" + pa.session.ready()
                    + " readyB=" + pb.session.ready()
                    + " ga.lockstep=" + (ga.lockstep != null)
                    + " gb.lockstep=" + (gb.lockstep != null)
                    + " sameObj=" + (ga.lockstep == pa.session));
            hub.tick();
            long ha = pa.stepFrame(1f / 30f);
            long hb = pb.stepFrame(1f / 30f);
            System.out.println("    after: A.turn=" + pa.session.turn + " B.turn=" + pb.session.turn
                    + " A.cmds=" + pa.commands().size() + " B.cmds=" + pb.commands().size());
        }
    }
}