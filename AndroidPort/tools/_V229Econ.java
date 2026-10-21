import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import com.xjzb.rts.core.*;

/** v2.29 probe: does a campaign mission give the player an economy, and does
 * the enemy keep producing? Prints the numbers the mission design must respect. */
public class _V229Econ {
    static final String ASSETS = "F:/KF/XJZB/AndroidPort/app/app/src/main/assets";

    public static void main(String[] a) throws Exception {
        for (String id : new String[]{"m01","m02","m05"}) {
            String json = new String(Files.readAllBytes(
                    Paths.get(ASSETS + "/missions/" + id + ".json")), StandardCharsets.UTF_8);
            Mission m = Mission.parse(json);
            GameDesktop.readMapPublic(m.map);
            Game g = new Game(GameDesktop.mapW, GameDesktop.mapH, GameDesktop.walk,
                    GameDesktop.elev, GameDesktop.starts, GameDesktop.units, "terran");
            g.setMission(m);
            int p0 = g.mineralsPlayer;
            System.out.println(id + " map=" + m.map + " mineralFields=" + g.minerals.size()
                    + " playerMinerals=" + p0 + " supply=" + g.supplyUsed + "/" + g.supplyCap);
            for (int i = 0; i < 30 * 180; i++) g.update(1f / 30f);
            int pUnits = 0, pB = 0, eUnits = 0, eB = 0;
            for (Game.Ent e : g.ents) {
                if (!e.alive()) continue;
                if (e.team == 0) { if (e.isBuilding()) pB++; else pUnits++; }
                else { if (e.isBuilding()) eB++; else eUnits++; }
            }
            System.out.println("    after 180s: player " + pUnits + "u/" + pB + "b  enemy "
                    + eUnits + "u/" + eB + "b  minerals=" + g.mineralsPlayer
                    + " mined=" + g.mineralsMined + " status='" + g.status + "'");
        }
    }
}