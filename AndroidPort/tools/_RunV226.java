/** Run only GameDesktop.v226Tests, skipping the sprite sheets. */
public class _RunV226 {
    public static void main(String[] a) throws Exception {
        Class<?> gd = Class.forName("GameDesktop");
        for (String m : new String[]{"readManifest", "readMap"}) {
            java.lang.reflect.Method x = gd.getDeclaredMethod(m);
            x.setAccessible(true); x.invoke(null);
        }
        java.lang.reflect.Method t = gd.getDeclaredMethod("v226Tests");
        t.setAccessible(true); t.invoke(null);
    }
}