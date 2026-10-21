public class _Dbg231 {
    public static void main(String[] a) throws Exception {
        GameDesktop.readManifestPublic();
        GameDesktop.readMapPublic("bloodbath");
        com.xjzb.rts.core.LockstepLink.Hub hub = new com.xjzb.rts.core.LockstepLink.Hub(2, 0, 0, false, 1L);
        com.xjzb.rts.core.Game ga = GameDesktop.cleanGame("terran");
        com.xjzb.rts.core.Game gb = GameDesktop.cleanGame("terran");
        com.xjzb.rts.core.LockstepPeer pa = new com.xjzb.rts.core.LockstepPeer(ga, 0, 2, hub.end(0));
        com.xjzb.rts.core.LockstepPeer pb = new com.xjzb.rts.core.LockstepPeer(gb, 1, 2, hub.end(1));
        System.out.println("seed equal=" + (ga.stateHash() == gb.stateHash()));
        java.util.List<com.xjzb.rts.core.Game.Ent> scvs = new java.util.ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : ga.ents)
            if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);
        System.out.println("scvs=" + scvs.size());
        for (int t = 0; t < 6; t++) {
            String aCmd = (t == 0 && !scvs.isEmpty())
                    ? ga.commandFor("move", scvs, "400 400") : "";
            pa.receiveFrame();
            pb.receiveFrame();
            pa.sendFrame(aCmd);
            pb.sendFrame("");
            hub.tick();
            long ha = pa.stepFrame(1f / 30f);
            long hb = pb.stepFrame(1f / 30f);
            System.out.println("t=" + t + " aCmd='" + aCmd + "' paTurn=" + pa.turnsReleased()
                    + " pbTurn=" + pb.turnsReleased()
                    + " paCmds=" + pa.commands().size() + " pbCmds=" + pb.commands().size()
                    + " ha=" + ha + " hb=" + hb + " same=" + (ha == hb));
        }
    }
}