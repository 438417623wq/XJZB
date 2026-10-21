import javax.imageio.ImageIO;
import java.io.File;
import java.awt.image.BufferedImage;

public class ProbeArt {
    public static void main(String[] a) throws Exception {
        ImageIO.scanForPlugins();
        String[] ks = {"emp", "ehamed", "dweb", "elect02", "b_blastcan", "plasma"};
        for (String k : ks) {
            File f = new File("F:/KF/XJZB/AndroidPort/app/app/src/main/assets/sprites/" + k + "_b.webp");
            BufferedImage im = null;
            String err = "";
            try {
                im = ImageIO.read(f);
            } catch (Exception e) {
                err = " EX:" + e;
            }
            System.out.println(k + " exists=" + f.exists() + " len=" + f.length()
                    + " img=" + (im == null ? "NULL" : im.getWidth() + "x" + im.getHeight())
                    + " animFrames=" + com.xjzb.rts.core.Game.animFrames(k) + err);
        }
    }
}
