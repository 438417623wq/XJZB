public class _Dbg7 {
    public static void main(String[] a) throws Exception {
        Class<?> gd = Class.forName("GameDesktop");
        for (String m : new String[]{"readManifest", "readMap"}) {
            java.lang.reflect.Method x = gd.getDeclaredMethod(m); x.setAccessible(true); x.invoke(null);
        }
        java.lang.reflect.Method cg = gd.getDeclaredMethod("cleanGame", String.class); cg.setAccessible(true);
        com.xjzb.rts.core.Game rg = (com.xjzb.rts.core.Game) cg.invoke(null, "protoss");
        System.out.println("reaver ammoCap=" + com.xjzb.rts.core.Game.TYPES.get("reaver").ammoCap);
        com.xjzb.rts.core.Game.Ent rv = rg.spawn("reaver", 0, 600, 600, true);
        System.out.println("reaver ammo=" + rv.ammo + " cd=" + rv.cd + " dmg=" + rv.type.dmg + " range=" + rv.type.range);
        com.xjzb.rts.core.Game.Ent zl = rg.spawn("zergling", 1, 640, 600, true);
        System.out.println("zergling hp=" + zl.hp + " alive=" + zl.alive());
        for (int i = 0; i < 5; i++) {
            rv.cd = 0;
            rg.update(1f/30f);
            System.out.println("  i=" + i + " ammo=" + rv.ammo + " target=" + (rv.target != null ? rv.target.type.key : "null")
                + " zlHp=" + zl.hp + " zlAlive=" + zl.alive());
        }
    }
}