import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.File;
import java.util.*;

/** Forensics only: decode webp via the SAME ImageIO stack GameDesktop uses,
 *  dump per-color stats and write a PNG so we can compare with Pillow. */
public class WebpDump {
  public static void main(String[] a) throws Exception {
    for (String f : a) {
      File file = new File(f);
      BufferedImage im;
      try {
        im = ImageIO.read(file);
      } catch (Throwable t) {
        System.out.println(f + " -> EX " + t);
        continue;
      }
      if (im == null) { System.out.println(f + " -> NULL"); continue; }
      int w = im.getWidth(), h = im.getHeight();
      HashMap<Integer,Integer> hist = new HashMap<>();
      int teal = 0, tealOpaque = 0, transparent = 0;
      for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++) {
          int argb = im.getRGB(x, y);
          int al = (argb >>> 24) & 255;
          int rgb = argb & 0xFFFFFF;
          hist.merge(rgb, 1, Integer::sum);
          if (al < 8) transparent++;
          if (rgb == 0x18ACB8) { teal++; if (al > 200) tealOpaque++; }
        }
      List<Map.Entry<Integer,Integer>> e = new ArrayList<>(hist.entrySet());
      e.sort((p, q) -> q.getValue() - p.getValue());
      StringBuilder sb = new StringBuilder();
      for (int i = 0; i < Math.min(8, e.size()); i++) {
        int rgb = e.get(i).getKey();
        sb.append(String.format("(%d,%d,%d)=%d ", (rgb>>16)&255, (rgb>>8)&255, rgb&255, e.get(i).getValue()));
      }
      System.out.println(file.getName() + " " + w + "x" + h
          + " type=" + im.getType()
          + " hasAlpha=" + im.getColorModel().hasAlpha()
          + " transparent=" + transparent
          + " teal(24,172,184)=" + teal + " tealOpaque=" + tealOpaque);
      System.out.println("    top: " + sb);
      File out = new File(file.getParentFile(), "_dump_" + file.getName().replace(".webp", "") + ".png");
      ImageIO.write(im, "png", out);
      System.out.println("    wrote " + out);
    }
  }
}
