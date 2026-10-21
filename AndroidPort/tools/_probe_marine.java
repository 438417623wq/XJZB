import javax.imageio.ImageIO;
import java.io.File;
public class _probe_marine {
    public static void main(String[] a) throws Exception {
        ImageIO.scanForPlugins();
        for (String p : new String[]{"sprites/marine_b.webp", "sprites/marine_b.png"}) {
            try {
                java.awt.image.BufferedImage im = ImageIO.read(new File(
                        "F:/KF/XJZB/AndroidPort/app/app/src/main/assets/" + p));
                System.out.println(p + " -> " + (im == null ? "NULL" : im.getWidth() + "x" + im.getHeight()));
            } catch (Exception e) {
                System.out.println(p + " -> EXC " + e);
            }
        }
    }
}
