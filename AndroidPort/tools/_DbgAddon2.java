import java.util.*;
public class _DbgAddon2 {
    static int mapW, mapH; static boolean[] walk; static byte[] elev;
    static List<int[]> starts; static List<Object[]> units;
    public static void main(String[] a) throws Exception {
        Class<?> gd = Class.forName("GameDesktop");
        java.lang.reflect.Method rm = gd.getDeclaredMethod("readManifest");
        java.lang.reflect.Method rp = gd.getDeclaredMethod("readMap");
        rm.setAccessible(true); rp.setAccessible(true);
        rm.invoke(null); rp.invoke(null);
        mapW = f(gd, "mapW"); mapH = f(gd, "mapH");
        walk = (boolean[]) fld(gd, "walk"); elev = (byte[]) fld(gd, "elev");
        starts = (List<int[]>) fld(gd, "starts"); units = (List<Object[]>) fld(gd, "units");
        com.xjzb.rts.core.Game g = new com.xjzb.rts.core.Game(mapW, mapH, walk, elev, starts, units, "terran");
        List<com.xjzb.rts.core.Game.Ent> drop = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : g.ents) if (e.team != 0) drop.add(e);
        g.ents.removeAll(drop);
        int tiles = 3, margin = 4, half = tiles / 2;
        float bx = -1, by = -1;
        outer:
        for (int ty = g.hTiles - 4 - tiles; ty >= 4; ty--)
            for (int tx = g.wTiles - 4 - tiles - 2; tx >= 4; tx--) {
                float wx = tx * 32f + 16, wy = ty * 32f + 16;
                boolean ok = true;
                for (int dy = -half - margin; dy <= half + margin && ok; dy++)
                    for (int dx = -half - margin; dx <= half + 2 + margin && ok; dx++)
                        if (!g.passMini((int)((wx+dx*32)/8), (int)((wy+dy*32)/8))) ok = false;
                if (!ok) continue;
                boolean clear = true;
                for (com.xjzb.rts.core.Game.Ent e : g.ents)
                    if (e.alive() && Math.abs(e.x-wx) < (tiles+2)*32 && Math.abs(e.y-wy) < (tiles+2)*32) { clear = false; break; }
                if (!clear) continue;
                for (com.xjzb.rts.core.Game.Mineral m : g.minerals)
                    if (Math.abs(m.x-wx) < (tiles+3)*32 && Math.abs(m.y-wy) < (tiles+3)*32) { clear = false; break; }
                if (!clear) continue;
                bx = wx; by = wy; break outer;
            }
        System.out.println("clearGround -> " + bx + "," + by);
        com.xjzb.rts.core.Game.Ent ac = g.spawn("academy", 0, bx, by, true);
        System.out.println("academy snapped to " + ac.x + "," + ac.y);
        System.out.println("addonError=" + g.addonError(ac, "comsat"));
        float[] pad = com.xjzb.rts.core.Game.addonPad(ac, 0);
        System.out.println("pad=" + pad[0] + "," + pad[1]);
        for (int my = -1; my <= 1; my += 2)
            for (int mx = -1; mx <= 1; mx += 2)
                System.out.println("  corner " + mx + "," + my + " pass=" + g.passMini((int)((pad[0]+mx*24)/8), (int)((pad[1]+my*24)/8)));
        com.xjzb.rts.core.Game.Ent cs = g.buildAddon(ac, "comsat");
        System.out.println("comsat=" + cs);
    }
    static int f(Class<?> c, String n) throws Exception { java.lang.reflect.Field x = c.getDeclaredField(n); x.setAccessible(true); return x.getInt(null); }
    static Object fld(Class<?> c, String n) throws Exception { java.lang.reflect.Field x = c.getDeclaredField(n); x.setAccessible(true); return x.get(null); }
}