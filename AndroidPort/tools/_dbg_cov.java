public class _dbg_cov {
    public static void main(String[] a) {
        int cs = 512, wPx = 128 * 32, H = 720;
        float centerY = 360f;
        for (float z : new float[]{0.85f, 1.3f}) {
            for (float camY : new float[]{0f, 1000f, 4096f, 4096f - 720f / 0.85f}) {
                float halfBot = (H - centerY) / z;
                float cam = Math.min(Math.max(camY, centerY / z),
                        Math.max(centerY / z, wPx - halfBot));
                int cy0 = Math.max(0, (int) Math.floor((cam - centerY / z) / cs));
                int cy1 = Math.min((wPx - 1) / cs, (int) Math.floor((cam + (H - centerY) / z) / cs));
                System.out.printf("z=%.2f camY=%.0f cam=%.2f cy0=%d cy1=%d%n", z, camY, cam, cy0, cy1);
                for (int cy = cy0; cy <= cy1; cy++) {
                    int dy0 = (int) Math.floor((cy * cs - cam) * z + centerY);
                    int dy1 = (int) Math.floor((Math.min(cy * cs + cs, wPx) - cam) * z + centerY) + 4;
                    System.out.printf("   cy=%d dy0=%d dy1=%d%n", cy, dy0, dy1);
                }
            }
        }
    }
}
