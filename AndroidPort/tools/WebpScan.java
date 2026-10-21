import javax.imageio.ImageIO;
import java.io.File;
import java.nio.file.*;
import java.util.*;
import java.awt.image.BufferedImage;

/** v2.42 收尾诊断: 全量扫描 assets/maps 下的 c_*.webp, 报告无法解码的文件。 */
public class WebpScan {
  public static void main(String[] a) throws Exception {
    Path root = Paths.get(a[0]);
    List<Path> files = new ArrayList<>();
    try (java.util.stream.Stream<Path> s = Files.walk(root)) {
      s.filter(p -> p.toString().endsWith(".webp"))
       .filter(p -> p.getFileName().toString().startsWith("c_"))
       .forEach(files::add);
    }
    Collections.sort(files);
    List<String> bad = new ArrayList<>();
    for (Path p : files) {
      try {
        BufferedImage im = ImageIO.read(p.toFile());
        if (im == null) bad.add(p.getParent().getFileName() + "/" + p.getFileName() + " NULL");
      } catch (Throwable t) {
        String m = t.getMessage();
        if (t.getCause() != null && t.getCause().getMessage() != null) m = t.getCause().getMessage();
        bad.add(p.getParent().getFileName() + "/" + p.getFileName() + " EX:" + m);
      }
    }
    System.out.println("scanned=" + files.size() + " bad=" + bad.size());
    for (String b : bad) System.out.println("  " + b);
  }
}
