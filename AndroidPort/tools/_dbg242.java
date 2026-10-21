import java.nio.file.*;
import java.nio.charset.StandardCharsets;

public class _dbg242 {
    public static void main(String[] a) throws Exception {
        String root = "F:/KF/XJZB/AndroidPort/";
        String gv = new String(Files.readAllBytes(Paths.get(
                root + "app/app/src/main/java/com/xjzb/rts/GameView.java")),
                StandardCharsets.UTF_8);
        String hl = new String(Files.readAllBytes(Paths.get(
                root + "app/app/src/main/java/com/xjzb/rts/HudLayout.java")),
                StandardCharsets.UTF_8);
        System.out.println("hl P_GROUPS=" + hl.contains("P_GROUPS = 5"));
        System.out.println("hl PANEL6=" + hl.contains("PANEL_COUNT = 6"));
        System.out.println("hl SPEC=" + hl.contains("SPEC_LEN = PANEL_COUNT * 3"));
        System.out.println("hl case=" + hl.contains("case P_GROUPS: return groups;"));
        System.out.println("gv draw=" + gv.contains("drawFormationOnly(c, hud.groups);"));
        System.out.println("hl place=" + hl.contains("place(groups, c[15] * W, c[16] * H, gW, gH, W, H, dp);"));
        System.out.println("gv noGCell=" + !gv.contains("float gCell = (cellS - 2 * k) / 2f;"));

        // coverage debug
        boolean coverage = true;
        int cs = 512;
        int wPx = 128 * 32;
        for (float z : new float[]{0.85f, 1.0f, 1.3f, 1.56f, 2.0f}) {
            for (float camY = 0; camY <= wPx; camY += 39.5f) {
                float centerY = 360f;
                int H = 720;
                float halfBot = (H - centerY) / z;
                float cam = Math.min(Math.max(camY, centerY / z),
                        Math.max(centerY / z, wPx - halfBot));
                int cy0 = Math.max(0, (int) Math.floor((cam - centerY / z) / cs));
                int cy1 = Math.min((wPx - 1) / cs,
                        (int) Math.floor((cam + (H - centerY) / z) / cs));
                for (int cy = cy0; cy <= cy1; cy++) {
                    int dy0 = (int) Math.floor((cy * cs - cam) * z + centerY);
                    int dy1 = (int) Math.floor((Math.min(cy * cs + cs, wPx) - cam) * z + centerY);
                    if (cy * cs + cs < wPx) dy1 += 4;
                    if (cy == cy0 && dy0 > 0)
                        System.out.println("TOP GAP z=" + z + " cam=" + camY + "->" + cam + " cy0=" + cy0 + " dy0=" + dy0);
                    if (cy == cy1 && dy1 < H)
                        System.out.println("BOT GAP z=" + z + " cam=" + camY + "->" + cam + " cy1=" + cy1 + " dy1=" + dy1);
                }
            }
        }
        System.out.println("coverage debug done");
    }
}
