public class _Dbg231c {
    public static void main(String[] a) throws Exception {
        GameDesktop.readManifestPublic();
        GameDesktop.readMapPublic("bloodbath");
        int[][] profiles = {{0,0,0},{1,3,0},{2,5,1}};
        for (int[] pr : profiles) {
            com.xjzb.rts.core.LockstepLink.Hub hub = new com.xjzb.rts.core.LockstepLink.Hub(
                    2, pr[0], pr[1], pr[2] != 0, 4242L);
            com.xjzb.rts.core.Game ga = GameDesktop.cleanGame("terran");
            com.xjzb.rts.core.Game gb = GameDesktop.cleanGame("terran");
            com.xjzb.rts.core.LockstepPeer pa = new com.xjzb.rts.core.LockstepPeer(ga, 0, 2, hub.end(0));
            com.xjzb.rts.core.LockstepPeer pb = new com.xjzb.rts.core.LockstepPeer(gb, 1, 2, hub.end(1));
            java.util.List<com.xjzb.rts.core.Game.Ent> scvs = new java.util.ArrayList<>();
            for (com.xjzb.rts.core.Game.Ent e : ga.ents)
                if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);
            int firstDiff = -1, turnDiff = -1;
            for (int t = 0; t < 30 * 20; t++) {
                String aCmd = "";
                if (t % 150 == 0 && !scvs.isEmpty()) {
                    int tx = 400 + (t / 150) * 40, ty = 400 + (t / 150) * 30;
                    aCmd = ga.commandFor("move", scvs, tx + " " + ty);
                }
                pa.receiveFrame(); pb.receiveFrame();
                pa.sendFrame(aCmd); pb.sendFrame("");
                hub.tick();
                long ha = pa.stepFrame(1f / 30f);
                long hb = pb.stepFrame(1f / 30f);
                if (ha != hb && firstDiff < 0) firstDiff = t;
                if (pa.turnsReleased() != pb.turnsReleased() && turnDiff < 0) turnDiff = t;
            }
            System.out.println("profile lat=" + pr[0] + " jit=" + pr[1] + " reo=" + pr[2]
                    + " firstHashDiff=" + firstDiff + " firstTurnDiff=" + turnDiff
                    + " paTurn=" + pa.turnsReleased() + " pbTurn=" + pb.turnsReleased()
                    + " paCmds=" + pa.commands().size() + " pbCmds=" + pb.commands().size());
        }
    }
}