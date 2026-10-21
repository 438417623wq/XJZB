import javax.imageio.ImageIO;
import java.io.File;
import java.awt.image.BufferedImage;
import java.util.Iterator;
import javax.imageio.ImageReader;

public class _ProbeWebpAlpha {
    public static void main(String[] a) throws Exception {
        ImageIO.scanForPlugins();
        String f = "F:/KF/XJZB/AndroidPort/app/app/src/main/assets/sprites/cc_b.webp";
        BufferedImage im = ImageIO.read(new File(f));
        System.out.println("reader plugins:");
        Iterator<ImageReader> it = ImageIO.getImageReaders(new File(f).toURI().toURL().openStream());
        while (it.hasNext()) System.out.println("  " + it.next().getClass().getName());
        System.out.println("decoded: " + (im == null ? "NULL" : im.getWidth() + "x" + im.getHeight() + " type=" + im.getType()));
        if (im != null) {
            System.out.println("alpha raster? " + im.getColorModel().hasAlpha());
            int w = im.getWidth(), h = im.getHeight();
            // sample corners and center
            System.out.println("corner(0,0)=" + Integer.toHexString(im.getRGB(0,0)));
            System.out.println("corner(2,2)=" + Integer.toHexString(im.getRGB(2,2)));
            System.out.println("center=" + Integer.toHexString(im.getRGB(w/2,h/2)));
            // histogram: most common colors
            java.util.Map<Integer,Integer> hist = new java.util.HashMap<>();
            for (int y=0;y<h;y+=3) for (int x=0;x<w;x+=3) {
                int rgb = im.getRGB(x,y);
                hist.merge(rgb & 0xFFFFFF, 1, Integer::sum);
            }
            hist.entrySet().stream().sorted((e1,e2)->e2.getValue()-e1.getValue()).limit(6)
                .forEach(e -> System.out.println("color " + String.format("%06x", e.getKey()) + " x" + e.getValue()));
        }
    }
}
