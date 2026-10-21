import java.util.ArrayList;
import java.util.List;

/**
 * Renders the same scene twice -- once with the v2.3 alpha leak and once with
 * the fix -- so the transparency regression is visible side by side.
 *
 * Reuses GameDesktop's map/manifest loading so the sprites and terrain are the
 * real ones.
 */
public class ShadowProof {
    public static void main(String[] args) throws Exception {
        GameDesktop.readManifestPublic();
        GameDesktop.readMapPublic("bloodbath");
        com.xjzb.rts.core.Game game = GameDesktop.game;

        float cx = game.wPx / 2f, cy = game.hPx / 2f;
        List<com.xjzb.rts.core.Game.Ent> ents = new ArrayList<>();
        String[] keys = {"marine", "firebat", "vulture", "tank", "scv", "ghost", "cc", "barracks"};
        for (int i = 0; i < keys.length; i++) {
            try {
                com.xjzb.rts.core.Game.Ent e =
                        game.spawn(keys[i], 0, cx + (i % 4) * 110 - 165, cy + (i / 4) * 120 - 60, true);
                if (e != null) ents.add(e);
            } catch (Throwable t) {
                System.out.println("  skip " + keys[i] + ": " + t);
            }
        }
        System.out.println("entities rendered: " + ents.size());
        GameDesktop.camX = cx;
        GameDesktop.camY = cy;
        GameDesktop.viewW = 700;
        GameDesktop.viewH = 440;
        GameDesktop.renderWithShadows(ents,
                "F:/KF/XJZB/AndroidPort/tools/out/shadow_bug.png", true);
        GameDesktop.renderWithShadows(ents,
                "F:/KF/XJZB/AndroidPort/tools/out/shadow_fixed.png", false);
    }
}
