/** Run only GameDesktop.v225Tests, skipping the sprite sheets (which are the
 *  harness's memory hog) so the new assertions can run on a loaded machine. */
public class _RunV225 {
    public static void main(String[] a) throws Exception {
        Class<?> gd = Class.forName("GameDesktop");
        for (String m : new String[]{"readManifest", "readMap"}) {
            java.lang.reflect.Method x = gd.getDeclaredMethod(m);
            x.setAccessible(true); x.invoke(null);
        }
        java.lang.reflect.Method t = gd.getDeclaredMethod("v225Tests");
        t.setAccessible(true); t.invoke(null);
    }
}