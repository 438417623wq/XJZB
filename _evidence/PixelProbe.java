import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.awt.image.Raster;
import java.io.File;

/** Forensics: compare Java (TwelveMonkeys) decode of one pixel against the
 *  raw raster samples, to separate "alpha lost" from "RGB changed". */
public class PixelProbe {
  public static void main(String[] a) throws Exception {
    File f = new File(a[0]);
    BufferedImage im = ImageIO.read(f);
    System.out.println(f.getName() + " " + im.getWidth() + "x" + im.getHeight()
        + " type=" + im.getType() + " cm=" + im.getColorModel());
    Raster r = im.getRaster();
    System.out.println("numBands=" + r.getNumBands());
    int[][] pts = {{0,0},{5,5},{128,48},{250,90},{1000,100}};
    for (int[] p : pts) {
      if (p[0] >= im.getWidth() || p[1] >= im.getHeight()) continue;
      int argb = im.getRGB(p[0], p[1]);
      StringBuilder s = new StringBuilder();
      for (int b = 0; b < r.getNumBands(); b++) s.append(r.getSample(p[0], p[1], b)).append(' ');
      System.out.printf("  (%d,%d) getRGB=#%08X bands=[%s]%n", p[0], p[1], argb, s.toString().trim());
    }
    // alpha histogram
    int[] hist = new int[256];
    for (int y = 0; y < im.getHeight(); y++)
      for (int x = 0; x < im.getWidth(); x++) hist[(im.getRGB(x, y) >>> 24) & 255]++;
    StringBuilder h = new StringBuilder();
    for (int i = 0; i < 256; i++) if (hist[i] > 0) h.append(i).append(':').append(hist[i]).append(' ');
    System.out.println("  alpha hist: " + h);
  }
}
