public class _Dbg231f {
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
        for (int t = 0; t < 16; t++) {
            String aCmd = (t == 0 && !scvs.isEmpty())
                    ? ga.commandFor("move", scvs, "400 400") : "";
            pa.receiveFrame();
            pb.receiveFrame();
            pa.sendFrame(aCmd);
            pb.sendFrame("");
            System.out.println("frame " + t + " hub=" + hub.frame()
                    + " preA=" + pa.session.ready() + " preB=" + pb.session.ready()
                    + " aCmd='" + aCmd + "'");
            hub.tick();
            pa.stepFrame(1f / 30f);
            pb.stepFrame(1f / 30f);
            System.out.println("    A.turn=" + pa.session.turn + " A.cmds=" + pa.commands().size()
                    + " | B.turn=" + pb.session.turn + " B.cmds=" + pb.commands().size());
        }
        System.out.println("A log: " + pa.session.serialize().replace("\n", " / "));
        System.out.println("B log: " + pb.session.serialize().replace("\n", " / "));
    }
}