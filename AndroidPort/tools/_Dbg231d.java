public class _Dbg231d {
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
            java.util.Map<Integer, Long> A = new java.util.HashMap<>(), B = new java.util.HashMap<>();
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
                A.put(pa.turnsReleased(), ha);
                B.put(pb.turnsReleased(), hb);
            }
            int diff = 0, common = 0;
            for (java.util.Map.Entry<Integer, Long> e : A.entrySet()) {
                Long o = B.get(e.getKey());
                if (o == null) continue;
                common++;
                if (o.longValue() != e.getValue().longValue()) {
                    if (diff < 4) System.out.println("   turn " + e.getKey()
                            + " A=" + e.getValue() + " B=" + o);
                    diff++;
                }
            }
            System.out.println("profile " + pr[0] + "/" + pr[1] + "/" + pr[2]
                    + " commonTurns=" + common + " diffTurns=" + diff
                    + " paTurn=" + pa.turnsReleased() + " pbTurn=" + pb.turnsReleased()
                    + " paCmds=" + pa.commands().size() + " pbCmds=" + pb.commands().size());
            for (int i = 0; i < pa.commands().size(); i++) {
                com.xjzb.rts.core.Lockstep.Cmd x = pa.commands().get(i);
                System.out.println("   A cmd[" + i + "] t" + x.turn + " p" + x.player + " '" + x.cmd + "'");
            }
            for (int i = 0; i < pb.commands().size(); i++) {
                com.xjzb.rts.core.Lockstep.Cmd x = pb.commands().get(i);
                System.out.println("   B cmd[" + i + "] t" + x.turn + " p" + x.player + " '" + x.cmd + "'");
            }
        }
    }
}