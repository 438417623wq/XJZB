/** Does the shipped m05 (and the new chapters) really stand its units on
 * blocked ground? Ask the engine, not a side reader. */
public class _V229Walk {
    public static void main(String[] a) throws Exception {
        GameDesktop.readManifestPublic();
        for (String id : new String[]{"m01","m02","m03","m04","m05","m06","m07","m08",
                                      "m09","m10","m11","m12","m13","m14","m15"}) {
            com.xjzb.rts.core.Game g = GameDesktop.missionGame(id);
            int bad = 0;
            StringBuilder who = new StringBuilder();
            for (com.xjzb.rts.core.Game.Ent e : g.ents) {
                if (!g.passMini((int) (e.x / 8), (int) (e.y / 8))) {
                    bad++;
                    who.append(" ").append(e.type.key).append("@").append((int) e.x)
                       .append(",").append((int) e.y).append("t").append(e.team);
                }
            }
            System.out.println(id + " map=" + g.mission.map + " ents=" + g.ents.size()
                    + " blocked=" + bad + who);
        }
    }
}