import javax.imageio.ImageIO;
import java.io.File;
import java.awt.image.BufferedImage;

public class ProbeWp3 {
    public static void main(String[] a) throws Exception {
        ImageIO.scanForPlugins();
        File d = new File("F:/KF/XJZB/AndroidPort/tools/out/wp3");
        File[] fs = d.listFiles();
        java.util.Arrays.sort(fs);
        for (File f : fs) {
            String r;
            try {
                BufferedImage im = ImageIO.read(f);
                r = im == null ? "NULL" : im.getWidth() + "x" + im.getHeight();
            } catch (Throwable t) {
                r = "FAIL " + t.getClass().getSimpleName() + ": " + t.getMessage();
            }
            System.out.println("  " + f.getName() + " -> " + r);
        }
    }
}
