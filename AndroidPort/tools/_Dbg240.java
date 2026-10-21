/** v2.39 probe: in a LAN match both peers build the same Game (player base at
 * starts[0], AI enemy at starts[1]). Question: what does a command from the
 * SECOND peer actually do? If both peers issue team-0 orders the match is
 * cooperative; if the joiner is meant to own starts[1] then team mirroring is
 * needed and is not implemented. */
public class _Dbg240 {
    public static void main(String[] a) throws Exception {
        GameDesktop.readManifestPublic();
        GameDesktop.readMapPublic("bloodbath");
        com.xjzb.rts.core.Game ga = GameDesktop.cleanGame("terran");
        com.xjzb.rts.core.Game gb = GameDesktop.cleanGame("terran");
        com.xjzb.rts.core.LockstepPeer pa = new com.xjzb.rts.core.LockstepPeer(
                ga, 0, 2, new com.xjzb.rts.core.LockstepLink.Link() {
                    public void send(String s) { }
                    public java.util.List<String> poll() { return new java.util.ArrayList<>(); }
                });
        // how many entities per team, and what a team-1 index would be
        int t0 = 0, t1 = 0;
        for (com.xjzb.rts.core.Game.Ent e : ga.ents) { if (e.team == 0) t0++; else t1++; }
        System.out.println("entities: team0=" + t0 + " team1=" + t1 + " total=" + ga.ents.size());
        // a joiner command would carry indices into ITS ents list. Is the list
        // order the same on both peers? (it must be, for index-based commands)
        boolean sameOrder = ga.ents.size() == gb.ents.size();
        for (int i = 0; i < ga.ents.size() && sameOrder; i++) {
            if (!ga.ents.get(i).type.key.equals(gb.ents.get(i).type.key)) sameOrder = false;
            if (ga.ents.get(i).team != gb.ents.get(i).team) sameOrder = false;
        }
        System.out.println("both peers' ents identical in order+team: " + sameOrder);
        // what does applyCommand do with an index that is team 1?
        System.out.println("NOTE: team1 = the AI's army (aiUpdate drives it).");
        System.out.println("=> a command from peer 1 would move the AI's units, not a"
                + " human opponent's, unless the AI is disabled and teams are mirrored.");
    }
}