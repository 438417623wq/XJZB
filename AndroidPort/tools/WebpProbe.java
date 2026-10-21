import javax.imageio.ImageIO;
import java.io.File;
import java.awt.image.BufferedImage;
public class WebpProbe {
  public static void main(String[] a) throws Exception {
    for (String f : a) {
      File file = new File(f);
      try {
        BufferedImage im = ImageIO.read(file);
        System.out.println(f + " -> " + (im == null ? "NULL" : im.getWidth() + "x" + im.getHeight()));
      } catch (Throwable t) {
        System.out.println(f + " -> EX " + t);
      }
    }
  }
}
