public class _dbg_cov2 {
    public static void main(String[] a) {
        int cs = 512, wPx = 128 * 32, H = 720;
        float centerY = 360f;
        for (float z : new float[]{0.85f}) {
            for (float camY : new float[]{0f, 39.5f, 276.5f}) {
                float halfBot = (H - centerY) / z;
                float cam = Math.min(Math.max(camY, centerY / z),
                        Math.max(centerY / z, wPx - halfBot));
                int cy0 = Math.max(0, (int) Math.floor((cam - centerY / z) / cs));
                int cy1 = Math.min((wPx - 1) / cs, (int) Math.floor((cam + (H - centerY) / z) / cs));
                System.out.printf("camY=%.1f cam=%.3f cy0=%d cy1=%d%n", camY, cam, cy0, cy1);
                for (int cy = cy0; cy <= cy1; cy++) {
                    int dy0 = (int) Math.floor((cy * cs - cam) * z + centerY);
                    int dy1 = (int) Math.floor((Math.min(cy * cs + cs, wPx) - cam) * z + centerY);
                    dy1 += 4;
                    int next0 = cy < cy1 ? (int) Math.floor(((cy + 1) * cs - cam) * z + centerY)
                                         : (int) Math.floor((wPx - cam) * z + centerY);
                    boolean topBad = (cy == cy0 && dy0 > 0);
                    boolean gapBad = dy1 < next0;
                    boolean botBad = (cy == cy1 && cam >= wPx - halfBot - 0.5f && dy1 < H);
                    System.out.printf("   cy=%d dy0=%d dy1=%d next0=%d topBad=%b gapBad=%b botBad=%b%n",
                            cy, dy0, dy1, next0, topBad, gapBad, botBad);
                }
            }
        }
    }
}
