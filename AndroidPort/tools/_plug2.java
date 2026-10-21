import javax.imageio.ImageIO;
import java.io.File;
import java.awt.image.BufferedImage;

public class _plug2 {
    public static void main(String[] a) throws Exception {
        ImageIO.scanForPlugins();
        String dir = "F:/KF/XJZB/AndroidPort/tools/_webp_test/";
        String[] files = {"cc.png", "cc_l6.webp", "cc_l6exact.webp", "cc_lossy.webp", "cc_lossy100.webp"};
        for (String f : files) {
            BufferedImage im = ImageIO.read(new File(dir + f));
            if (im == null) { System.out.println(f + " -> NULL"); continue; }
            int corner = im.getRGB(0, 0);
            int w = im.getWidth(), h = im.getHeight();
            int trans = 0;
            for (int y = 0; y < h; y += 4) for (int x = 0; x < w; x += 4)
                if ((im.getRGB(x, y) >>> 24) == 0) trans++;
            System.out.printf("%-18s corner=%08x transparentSamples=%d%n", f, corner, trans);
        }
    }
}
