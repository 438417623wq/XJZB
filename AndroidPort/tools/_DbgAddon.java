import java.util.*;
public class _DbgAddon {
    public static void main(String[] a) throws Exception {
        Class<?> gd = Class.forName("GameDesktop");
        java.lang.reflect.Method readManifest = gd.getDeclaredMethod("readManifest");
        java.lang.reflect.Method readMap = gd.getDeclaredMethod("readMap");
        readManifest.setAccessible(true); readMap.setAccessible(true);
        readManifest.invoke(null); readMap.invoke(null);
        java.lang.reflect.Field fw = gd.getDeclaredField("mapW"); fw.setAccessible(true);
        java.lang.reflect.Field fh = gd.getDeclaredField("mapH"); fh.setAccessible(true);
        java.lang.reflect.Field fwalk = gd.getDeclaredField("walk"); fwalk.setAccessible(true);
        java.lang.reflect.Field felev = gd.getDeclaredField("elev"); felev.setAccessible(true);
        java.lang.reflect.Field fst = gd.getDeclaredField("starts"); fst.setAccessible(true);
        java.lang.reflect.Field fun = gd.getDeclaredField("units"); fun.setAccessible(true);
        int mapW = fw.getInt(null), mapH = fh.getInt(null);
        boolean[] walk = (boolean[]) fwalk.get(null);
        byte[] elev = (byte[]) felev.get(null);
        List<int[]> starts = (List<int[]>) fst.get(null);
        List<Object[]> units = (List<Object[]>) fun.get(null);
        com.xjzb.rts.core.Game g = new com.xjzb.rts.core.Game(mapW, mapH, walk, elev, starts, units, "terran");
        List<com.xjzb.rts.core.Game.Ent> drop = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : g.ents) if (e.team != 0) drop.add(e);
        g.ents.removeAll(drop);
        System.out.println("minerals=" + g.mineralsPlayer + " gas=" + g.gasPlayer);
        float sx = -1, sy = -1;
        outer:
        for (int ty = 4; ty < g.hTiles - 4; ty++)
            for (int tx = 4; tx < g.wTiles - 4; tx++) {
                float wx = tx * 32f + 16, wy = ty * 32f + 16;
                boolean ok = true;
                for (int k = 0; k < 400; k += 8) if (!g.passMini((int)((wx+k)/8), (int)(wy/8))) { ok = false; break; }
                if (ok) { sx = wx; sy = wy; break outer; }
            }
        System.out.println("spot=" + sx + "," + sy);
        com.xjzb.rts.core.Game.Ent ac = g.spawn("academy", 0, sx, sy + 200, true);
        System.out.println("academy at " + ac.x + "," + ac.y);
        System.out.println("addonError(academy,comsat)=" + g.addonError(ac, "comsat"));
        float[] pad = com.xjzb.rts.core.Game.addonPad(ac, 0);
        System.out.println("pad=" + pad[0] + "," + pad[1]);
        for (int my = -1; my <= 1; my += 2)
            for (int mx = -1; mx <= 1; mx += 2)
                System.out.println("  corner " + mx + "," + my + " mini=("
                    + (int)((pad[0]+mx*24)/8) + "," + (int)((pad[1]+my*24)/8) + ") pass="
                    + g.passMini((int)((pad[0]+mx*24)/8), (int)((pad[1]+my*24)/8)));
        com.xjzb.rts.core.Game.Ent cs = g.buildAddon(ac, "comsat");
        System.out.println("comsat=" + cs);
    }
}