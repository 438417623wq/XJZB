import javax.imageio.ImageIO;
import java.io.File;
import java.awt.image.BufferedImage;
import java.util.Arrays;

/** Decode every sprite sheet with the same TwelveMonkeys reader the harness uses. */
public class ProbeAllWebp {
    static int bad = 0, n = 0;

    public static void main(String[] a) throws Exception {
        ImageIO.scanForPlugins();
        File dir = new File(a.length > 0 ? a[0]
                : "F:/KF/XJZB/AndroidPort/app/app/src/main/assets");
        walk(dir);
        System.out.println("sweep: " + n + " webp, " + bad + " undecodable");
    }

    static void walk(File d) {
        File[] fs = d.listFiles();
        if (fs == null) return;
        java.util.Arrays.sort(fs);
        for (File f : fs) {
            if (f.isDirectory()) { walk(f); continue; }
            if (!f.getName().endsWith(".webp")) continue;
            n++;
            try {
                BufferedImage im = ImageIO.read(f);
                if (im == null) { System.out.println("NULL  " + f.getPath()); bad++; }
            } catch (Throwable t) {
                System.out.println("FAIL  " + f.getPath() + "  " + t.getMessage());
                bad++;
            }
        }
    }
}
