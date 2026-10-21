import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.util.HashMap;
import java.util.Map;

/**
 * HUD layout verification: mirrors the geometry in GameView.drawHud so the
 * console can be inspected on the desktop at realistic phone resolutions
 * before it ships. The constants below are copied verbatim from GameView;
 * if you change one, change the other.
 *
 * Run:  java HudPreview
 */
public class HudPreview {

    static final String A = "F:/KF/XJZB/AndroidPort/app/app/src/main/assets";
    static final String OUT = "F:/KF/XJZB/AndroidPort/tools/out/";
    static {
        // Shipped assets are lossless WEBP; the TwelveMonkeys plugin on the
        // classpath teaches ImageIO to read them.
        javax.imageio.ImageIO.scanForPlugins();
    }

    // ---- copied from GameView.drawHud ----
    static final int PANEL_DARK = new Color(24, 28, 40).getRGB();
    static final int PANEL_MID = new Color(46, 54, 76).getRGB();
    static final int PANEL_LITE = new Color(88, 100, 128).getRGB();
    static final int PANEL_EDGE = new Color(130, 145, 175).getRGB();
    static final int SLOT_DARK = new Color(14, 18, 30).getRGB();
    static final int SLOT_EDGE = new Color(70, 82, 108).getRGB();
    // v2.23 batch B: the command-card separator and the opaque chip colours,
    // mirroring GameView (the translucent palette and its bevel are gone).
    static final int CARD_SEP = new Color(56, 66, 90).getRGB();
    static final int CHIP_DARK = new Color(12, 16, 26).getRGB();

    static final Map<String, BufferedImage> cache = new HashMap<>();

    static BufferedImage img(String path) {
        BufferedImage b = cache.get(path);
        if (b != null) return b;
        // v2.44: prefer the PNG mirror (tools/harness_sprites, built by
        // make_harness_sprites.py). The TwelveMonkeys webp plugin on this
        // classpath drops VP8L alpha, so every WEBP sheet read directly came
        // back opaque with garbage background RGB; the mirror is what makes
        // the previews show the shipped art.
        if (path.startsWith("sprites/") && path.endsWith(".webp")) {
            try {
                b = ImageIO.read(new File("F:/KF/XJZB/AndroidPort/tools/"
                        + "harness_sprites/"
                        + path.substring(8, path.length() - 5) + ".png"));
                if (b != null) {
                    cache.put(path, b);
                    return b;
                }
            } catch (Exception e) {
                b = null;
            }
        }
        // v2.42: the slim pipeline renamed everything to .webp -- try it first,
        // the raw .png second, so previews show art instead of "NO WIRE".
        for (String p : new String[]{path, path.endsWith(".png")
                ? path.substring(0, path.length() - 4) + ".webp" : path}) {
            try {
                b = ImageIO.read(new File(A + "/" + p));
                if (b != null) break;
            } catch (Exception e) {
                b = null;
            }
        }
        cache.put(path, b);
        return b;
    }

    public static void main(String[] args) throws Exception {
        // representative Android phones (landscape, game is landscape-locked).
        // The 1280x720 @ uiScale=2 case is the tight one: a budget 720p phone
        // is only 360dp tall, which is where the adaptive cell size kicks in.
        draw(2400, 1080, 2, 7, "hud_2400x1080_marine.png");
        draw(1920, 1080, 2, 5, "hud_1920x1080_tank.png");
        draw(1280, 720, 2, 41, "hud_1280x720_budget.png");
        draw(1280, 720, 1, 37, "hud_1280x720_ui1.png");
        draw(800, 480, 1, 43, "hud_800x480_lowend.png");
        draw(2400, 1080, 2, 106, "hud_2400x1080_cc.png");
        // v2.5 #4: with nothing selected the strip collapses to the 1/2/3
        // formation slots and no panel is drawn at all.
        drawEmpty(1280, 720, 2, "hud_1280x720_empty.png");
        drawEmpty(800, 480, 1, "hud_800x480_empty.png");
        // v2.5 batch-6: the two SCV command pages
        drawScv(1280, 720, 2, 0, "hud_1280x720_scv0.png");
        drawScv(1280, 720, 2, 1, "hud_1280x720_scv1.png");
        // v2.11 batch C: the terran page 2 that holds starport/armory/sciencefac
        drawScv(1280, 720, 2, 2, "hud_1280x720_scv2.png");
        drawUnit(1280, 720, 2, "hud_1280x720_unit.png");
        // v2.10: the protoss build page, the widest name+price card in the game
        drawScv(1280, 720, 2, -3, "hud_1280x720_protoss.png");
        drawScv(800, 480, 1, -3, "hud_800x480_protoss.png");
        // v2.14: the spell cards -- the vessel is the widest text-label card,
        // the ghost stands in for the one-spell-cell cruisers/corsair
        drawScv(1280, 720, 2, -4, "hud_1280x720_vessel.png");
        drawScv(800, 480, 1, -4, "hud_800x480_vessel.png");
        drawScv(1280, 720, 2, -5, "hud_1280x720_ghost.png");
        // v2.23 batch A/B: the three states the UI sweep changed -- empty
        // selection (only the opaque formation chips), a single selection
        // (opaque card + info panel), and a build page -- plus an audit image
        // that marks the whole screen as "no translucent layer".
        drawEmpty(1280, 720, 2, "hud_v223_empty.png");
        draw(1280, 720, 2, 7, "hud_v223_single.png");
        drawScv(1280, 720, 2, 0, "hud_v223_build.png");
        transparencyAudit();
        // v2.41: the six independent widgets and the "gaps are battlefield"
        // claim, annotated on one frame.
        widgetsAudit();
        // v2.25: the two new ability cards and an add-on card. drawScv passes
        // its page code through, so the negative pages above cover them.
        drawScv(1280, 720, 2, -6, "hud_v225_scan.png");
        drawScv(1280, 720, 2, -7, "hud_v225_nuke.png");
        drawScv(1280, 720, 2, -8, "hud_v225_addon.png");
        // v2.17 problem 4: the world-space health-bar floor at both zoom extremes
        worldBarFrame();
        layoutPresetsFrame();
        // v2.20 step 3: the custom layout, at the same size as the preset strip
        layoutCustomFrame();
        // v2.42: the selection card is capped in every selection state. The
        // device report was five SCVs; a uniform group and a mixed one are
        // drawn side by side at the same screen size so the widths compare.
        drawMulti(2608, 1200, 2, 5, 1, "SCV x5", "hud_v242_multi_scv.png");
        drawMulti(2608, 1200, 2, 5, 3, "SCV x3 + 机枪兵 x2", "hud_v242_multi_mixed.png");
        drawMulti(2608, 1200, 2, 6, 6, "六种单位 x1", "hud_v242_multi_six.png");
        drawMulti(1280, 720, 2, 5, 1, "SCV x5", "hud_v242_multi_720p.png");
        System.out.println("hud previews written");
    }

    static void draw(int W, int H, int uiScale, int unitId, String out) throws Exception {
        drawImpl(W, H, uiScale, unitId, out, false, -1);
    }

    static void drawEmpty(int W, int H, int uiScale, String out) throws Exception {
        drawImpl(W, H, uiScale, 0, out, true, -1);
    }

    /** scvPage: -1 = not an SCV card, 0 = SCV orders, 1 = SCV build submenu. */
    static void drawScv(int W, int H, int uiScale, int scvPage, String out) throws Exception {
        drawImpl(W, H, uiScale, 7, out, false, scvPage);
    }

    /** A plain combat unit card: attack / attack-move / stop / patrol. */
    static void drawUnit(int W, int H, int uiScale, String out) throws Exception {
        drawImpl(W, H, uiScale, 0, out, false, -2);
    }

    /**
     * v2.42: the width cap for the selection card, mirroring
     * GameView.drawBottomWidgets. A uniform selection -- one marine, or five
     * SCVs -- stops at 165dp. A mixed group is allowed past it only by the
     * filter row it has to draw: one cell per kind, six kinds maximum, and
     * those cells grow with the panel but never past 30dp.
     */
    static float infoCap(int kinds, float panelH, float uiScale) {
        float cap = 165f * uiScale;
        if (kinds > 1) {
            float cellS = Math.max(18 * uiScale,
                    Math.min(30 * uiScale, panelH - 48 * uiScale));
            cap = Math.max(cap,
                    20 * uiScale + kinds * cellS + Math.max(0, kinds - 1) * 5 * uiScale);
        }
        return cap;
    }

    static void drawImpl(int W, int H, int uiScale, int unitId, String out,
                         boolean empty, int scvPage) throws Exception {
        BufferedImage im = renderImpl(W, H, uiScale, unitId, empty, scvPage);
        if (out != null) ImageIO.write(im, "png", new File(OUT + out));
    }

    /**
     * v2.42: count = how many units are selected, kinds = how many distinct
     * kinds they are. The card caps its width from kinds (a mixed group needs
     * one filter cell per kind), but draws the filter row whenever count > 1 --
     * five SCVs are one kind and still get a row, with a single "x5" cell.
     */
    static void drawMulti(int W, int H, int uiScale, int count, int kinds,
                          String label, String out) throws Exception {
        BufferedImage im = renderImpl(W, H, uiScale, 7, false, -1, kinds, label, count);
        if (out != null) ImageIO.write(im, "png", new File(OUT + out));
    }

    static BufferedImage renderImpl(int W, int H, int uiScale, int unitId,
                                    boolean empty, int scvPage) throws Exception {
        return renderImpl(W, H, uiScale, unitId, empty, scvPage, 1);
    }

    /**
     * v2.42: kinds = how many distinct unit kinds the selection holds, i.e. the
     * number of filter cells drawSelInfo will draw. 1 means a uniform
     * selection (one SCV, or five of them) and takes the 165dp cap; more means
     * a mixed group, which is the only case allowed past it.
     */
    static BufferedImage renderImpl(int W, int H, int uiScale, int unitId,
                                    boolean empty, int scvPage, int kinds) throws Exception {
        return renderImpl(W, H, uiScale, unitId, empty, scvPage, kinds, null);
    }

    static BufferedImage renderImpl(int W, int H, int uiScale, int unitId,
                                    boolean empty, int scvPage, int kinds,
                                    String label) throws Exception {
        return renderImpl(W, H, uiScale, unitId, empty, scvPage, kinds, label, 1);
    }

    static BufferedImage renderImpl(int W, int H, int uiScale, int unitId,
                                    boolean empty, int scvPage, int kinds,
                                    String label, int count) throws Exception {
        BufferedImage im = new BufferedImage(W, H, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = im.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION,
                RenderingHints.VALUE_INTERPOLATION_NEAREST_NEIGHBOR);

        // fake terrain behind the HUD
        g.setColor(new Color(52, 48, 40));
        g.fillRect(0, 0, W, H);
        g.setColor(new Color(70, 64, 52));
        for (int y = 0; y < H; y += 32)
            for (int x = 0; x < W; x += 32)
                if (((x / 32) + (y / 32)) % 2 == 0) g.fillRect(x, y, 32, 32);

        float hud = 40 * uiScale;
        // must mirror HudLayout.cardCell(): 3 rows of adaptive cells
        // (50dp preferred, 46dp floor), capped at 50% of screen height
        int CARD_ROWS = 3, CARD_COLS = 3;
        float CELL_DP = 50f, CELL_MIN_DP = 46f, GAP_DP = 4f, PAD_DP = 10f;
        float want = CELL_DP * uiScale;
        float budget = H * 0.50f - PAD_DP * uiScale - (CARD_ROWS - 1) * GAP_DP * uiScale;
        float fit = budget / CARD_ROWS;
        if (fit < want) want = Math.max(CELL_MIN_DP * uiScale, fit);
        float cell = want;

        // ---- v2.41 top chips: four independent opaque chips, NO band, NO
        // hairline; the gaps between them are live battlefield. Geometry from
        // HudLayout.topChips (CHIP_H_DP 26, pause = topH-10dp square at 6,5;
        // res 180dp after the pause chip; clock 64dp centred; tally 104dp
        // right-aligned).
        float chipH = 26 * uiScale, chipTop = (hud - chipH) / 2f;
        float pauseS = hud - 10 * uiScale;
        Rectangle pause = new Rectangle((int) (6 * uiScale), (int) (5 * uiScale),
                (int) pauseS, (int) pauseS);
        bevelPanel(g, pause, uiScale);
        g.setColor(new Color(220, 232, 250));
        float bw = pauseS * 0.16f;
        g.fillRect((int) (pause.x + pauseS * 0.28f), (int) (pause.y + pauseS * 0.24f),
                (int) bw, (int) (pauseS * 0.52f));
        g.fillRect((int) (pause.x + pauseS * 0.72f - bw), (int) (pause.y + pauseS * 0.24f),
                (int) bw, (int) (pauseS * 0.52f));
        Rectangle resChip = new Rectangle((int) (pause.x + pause.width + 10 * uiScale),
                (int) chipTop, (int) (180 * uiScale), (int) chipH);
        bevelPanel(g, resChip, uiScale);
        Rectangle clockChip = new Rectangle((int) (W / 2f - 32 * uiScale),
                (int) chipTop, (int) (64 * uiScale), (int) chipH);
        bevelPanel(g, clockChip, uiScale);
        Rectangle tallyChip = new Rectangle((int) (W - 8 * uiScale - 104 * uiScale),
                (int) chipTop, (int) (104 * uiScale), (int) chipH);
        bevelPanel(g, tallyChip, uiScale);
        g.setFont(new Font("SansSerif", Font.PLAIN, (int) (12 * uiScale)));
        FontMetrics chipFm = g.getFontMetrics();
        g.setColor(new Color(140, 220, 255));
        g.drawString("晶体 1240", resChip.x + 6 * uiScale,
                resChip.y + (resChip.height + chipFm.getAscent() - chipFm.getDescent()) / 2);
        g.setColor(new Color(150, 255, 150));
        g.drawString("瓦斯 320", resChip.x + resChip.width / 2 - 30 * uiScale,
                resChip.y + (resChip.height + chipFm.getAscent() - chipFm.getDescent()) / 2);
        g.setColor(new Color(220, 230, 250));
        g.drawString("人口 12/20", resChip.x + resChip.width - 74 * uiScale,
                resChip.y + (resChip.height + chipFm.getAscent() - chipFm.getDescent()) / 2);
        String clock = "03:24";
        g.setColor(new Color(230, 236, 248));
        g.drawString(clock, clockChip.x + (clockChip.width - chipFm.stringWidth(clock)) / 2,
                clockChip.y + (clockChip.height + chipFm.getAscent() - chipFm.getDescent()) / 2);
        String tally = "我方 8  敌方 14";
        g.setColor(new Color(220, 230, 250));
        g.drawString(tally, tallyChip.x + (tallyChip.width - chipFm.stringWidth(tally)) / 2,
                tallyChip.y + (tallyChip.height + chipFm.getAscent() - chipFm.getDescent()) / 2);
        System.out.printf("   [chips] pause=%dx%d res=%dx%d clock=%dx%d tally=%dx%d"
                        + " (gaps are battlefield)%n",
                pause.width, pause.height, resChip.width, resChip.height,
                clockChip.width, clockChip.height, tallyChip.width, tallyChip.height);

        // ---- bottom widgets (default preset, v2.42): minimap bottom-left,
        // then the control-group block (its OWN widget now), then the slim
        // info panel, then the card. All bottom-aligned; gaps are battlefield.
        float slotS = 150 * uiScale + 6 * uiScale;
        float mmL = 8 * uiScale, mmT = H - 8 * uiScale - slotS;
        Rectangle mmFrame = new Rectangle((int) mmL, (int) mmT,
                (int) slotS, (int) slotS);
        bevelSlot(g, mmFrame, uiScale);
        Rectangle mm = new Rectangle(mmFrame.x + 3 * uiScale, mmFrame.y + 3 * uiScale,
                mmFrame.width - 6 * uiScale, mmFrame.height - 6 * uiScale);
        BufferedImage mini = img("maps/bloodbath/minimap.png");
        if (mini != null) g.drawImage(mini, mm.x, mm.y, mm.width, mm.height, null);
        g.setColor(new Color(60, 255, 60));
        g.setStroke(new BasicStroke(1.5f));
        g.drawRect(mm.x + mm.width / 4, mm.y + mm.height / 4, mm.width / 3, mm.height / 3);
        g.setStroke(new BasicStroke(1f));

        // v2.42 batch C: the control-group block between the minimap and the
        // info panel. It draws in EVERY selection state -- the info panel no
        // longer carries a private copy of the grid.
        float cardW = 3 * cell + 2 * GAP_DP * uiScale;
        // the production-queue strip is reserved exactly when it will be drawn.
        // GameView.queueStripW() returns 0 unless a completed building with a
        // non-empty queue is selected, so neither the empty nor the SCV preview
        // may reserve it.
        boolean queueShown = !empty && scvPage < 0 && scvPage != -2;
        float queueW = queueShown ? cell * 0.62f + 7 * uiScale : 0;
        float gw = 5 * 26 * uiScale + 4 * 4 * uiScale + 8 * uiScale;
        float gh = 2 * 26 * uiScale + 4 * uiScale + 8 * uiScale;
        float cardL = W - 12 * uiScale - cardW - queueW;
        float gx0 = mmFrame.x + mmFrame.width + 10 * uiScale;
        float gMaxL = cardL - 22 * uiScale - gw;
        if (gx0 > gMaxL) gx0 = gMaxL;
        Rectangle groupsR = new Rectangle((int) gx0, (int) (H - 8 * uiScale - gh),
                (int) gw, (int) gh);
        float gCellS = (groupsR.width - 8 * uiScale - 16 * uiScale) / 5f;
        float gRowH = gCellS + 4 * uiScale;
        float gTop = groupsR.y + groupsR.height / 2f - (2 * gCellS + 4 * uiScale) / 2f;
        g.setFont(new Font("SansSerif", Font.PLAIN, (int) (gCellS * 0.34f)));
        FontMetrics gfm = g.getFontMetrics();
        for (int gidx = 0; gidx < 10; gidx++) {
            int col = gidx % 5, row = gidx / 5;
            Rectangle gr = new Rectangle(
                    (int) (groupsR.x + 4 * uiScale + col * (gCellS + 4 * uiScale)),
                    (int) (gTop + row * gRowH), (int) gCellS, (int) gCellS);
            bevelPanel(g, gr, uiScale);
            g.setColor(new Color(200, 220, 245));
            String gs = String.valueOf(gidx + 1);
            g.drawString(gs, gr.x + (gr.width - gfm.stringWidth(gs)) / 2,
                    gr.y + (gr.height + gfm.getAscent() - gfm.getDescent()) / 2);
        }
        System.out.printf("   [groups] rect=%dx%d at x=%d (own widget, always drawn)%n",
                groupsR.width, groupsR.height, groupsR.x);

        // info panel (v2.42 batch C): slim and content-hugging -- 72dp tall,
        // bottom-anchored, no group grid inside, no English subtitle.
        // v2.42: the width is CAPPED for every selection state. A multi-select
        // used to claim the whole middle strip, so five SCVs drew a 1310px hp
        // bar inside a 1540px slab on a real device. Only a mixed group may
        // exceed the cap, and only by the per-kind filter row it must draw.
        float infoL = groupsR.x + groupsR.width + 10 * uiScale;
        float infoR = cardL - 22 * uiScale;
        float infoH = 72 * uiScale;
        float infoW = empty ? 0 : Math.min(infoR - infoL, infoCap(kinds, infoH, uiScale));
        Rectangle info = new Rectangle((int) infoL,
                (int) (H - 8 * uiScale - infoH),
                (int) Math.max(0, infoW), (int) infoH);
        if (!empty) {
            bevelPanel(g, info, uiScale);            // v2.21 #3: the info panel is opaque now;
        }

        // wireframe portrait (panel-height sized, no bottom strip any more).
        // Skipped when empty: there is no selection to show (v2.5 #4).
        BufferedImage wire = empty ? null : img("ui/wire/wire_" + unitId + ".png");
        float ws = info.height - 14 * uiScale;
        Rectangle wr = new Rectangle((int) (info.x + 10 * uiScale), (int) (info.y + 7 * uiScale),
                (int) ws, (int) ws);
        if (!empty) {
            bevelSlot(g, wr, uiScale);
            if (wire != null) {
                float pad = 4 * uiScale;
                g.drawImage(wire, (int) (wr.x + pad), (int) (wr.y + pad),
                        (int) (wr.width - 2 * pad), (int) (wr.height - 2 * pad), null);
            } else {
                g.setColor(Color.RED);
                g.drawString("NO WIRE " + unitId, wr.x + 8, wr.y + 24);
            }
        }

        float tx = wr.x + wr.width + 12 * uiScale;
        float tyy = info.y + 22 * uiScale;
        if (!empty) {
            g.setColor(new Color(255, 220, 130));
            g.setFont(new Font("SansSerif", Font.PLAIN, (int) (15 * uiScale)));
            g.drawString(label != null ? label : "机枪兵 x3", tx, tyy);
            // v2.42: the English subtitle is gone -- the Chinese name is the
            // label the panel shows, the second line read as clutter.

            float frac = 0.72f;
            int hc = frac > 2f / 3f ? new Color(80, 230, 80).getRGB()
                    : frac > 1f / 3f ? new Color(240, 220, 60).getRGB()
                    : new Color(250, 70, 50).getRGB();
            float barY = tyy + 10 * uiScale;
            float barW = info.x + info.width - 10 * uiScale - tx;
            g.setColor(Color.BLACK);
            g.fillRect((int) tx, (int) barY, (int) barW, (int) (9 * uiScale));
            g.setColor(new Color(hc));
            g.fillRect((int) tx, (int) barY, (int) (barW * frac), (int) (9 * uiScale));
            g.setColor(new Color(PANEL_LITE));
            g.drawRect((int) tx, (int) barY, (int) barW, (int) (9 * uiScale));
            g.setColor(Color.WHITE);
            g.drawString("32/45", tx + barW - 24 * uiScale, barY + 8 * uiScale);

            if (count > 1) {
                // the per-kind filter row, mirrored from drawSelInfo: drawn
                // whenever more than one unit is selected (five SCVs are one
                // kind and still get a row, with a single "x5" cell), one cell
                // per kind. This row is the ONLY reason a card may pass the
                // 165dp cap.
                float cellS = Math.max(18 * uiScale,
                        Math.min(30 * uiScale, info.height - 48 * uiScale));
                float cy2 = info.y + info.height - cellS - 6 * uiScale;
                float cx = info.x + 10 * uiScale;
                g.setFont(new Font("SansSerif", Font.PLAIN, (int) (cellS * 0.5f)));
                FontMetrics kfm = g.getFontMetrics();
                for (int i = 0; i < kinds && i < 6; i++) {
                    Rectangle kr = new Rectangle((int) cx, (int) cy2,
                            (int) cellS, (int) cellS);
                    bevelSlot(g, kr, uiScale);
                    // the app draws the count at the cell's bottom-right corner
                    String ks = "x" + (i == 0 ? count : 1);
                    g.setColor(new Color(190, 205, 230));
                    g.setFont(new Font("SansSerif", Font.PLAIN, (int) (9 * uiScale)));
                    FontMetrics nfm = g.getFontMetrics();
                    g.drawString(ks, kr.x + kr.width - 2 * uiScale - nfm.stringWidth(ks),
                            kr.y + kr.height - 2 * uiScale);
                    cx += cellS + 5 * uiScale;
                }
            } else {
                // v2.23 batch 0: the caster energy row, mirrored from GameView
                // drawSelInfo. A fresh caster sits at 50/200 and the row is the
                // whole point of watching whether the next storm is affordable,
                // so the preview shows the same shape the game does.
                g.setColor(new Color(120, 180, 255));
                g.setFont(new Font("SansSerif", Font.PLAIN, (int) (11 * uiScale)));
                g.drawString("能量 50/200", tx, barY + 20 * uiScale);
            }
        }

        // command card. Each cell mirrors GameView v2.5 #2/#3: icon on top, and
        // a shared bottom bar carrying the Chinese name (left) + cost (right).
        float cs = cell, gap = GAP_DP * uiScale;
        int cols = CARD_COLS, rows = CARD_ROWS;
        float gridW = cols * cs + (cols - 1) * gap;
        float gridH = rows * cs + (rows - 1) * gap;
        float gx = W - 12 * uiScale - gridW;
        float gy = H - 6 * uiScale - gridH;
        String[] icons = {"ic_attack", "ic_stop", "ic_siege",
                          "ic_cc", "ic_depot", "ic_barracks",
                          "ic_refinery", "ic_factory", "ic_turret"};
        String[] names = {"攻击", "停止", "架塔",
                          "基地", "补给", "兵营",
                          "炼油", "重工", "炮塔"};
        String[] costs = {null, null, null,
                          "400", "100", "150",
                          "100+50", "200+100", "100+50"};
        if (scvPage >= 0) {
            // The worker card pages, copied from GameView.drawCmdCard. Page 0
            // is the economy/opening set; page 2 is the terran tech set. The
            // last cell is always 更多/返回 so the card geometry matches.
            if (scvPage == 0) {
                icons = new String[]{"ic_attack", "ic_stop", "ic_patrol",
                                     "ic_repair", null, null, null, null, null};
                names = new String[]{"攻击", "停止", "巡逻",
                                     "修理", "建造", null, null, null, null};
                costs = new String[]{null, null, null, null, null, null, null, null, null};
            } else if (scvPage == 2) {
                icons = new String[]{"ic_starport", "ic_armory", null,
                                     "ic_cancel", null, null, null, null, null};
                names = new String[]{"星港", "军械库", "科学设施",
                                     "返回", null, null, null, null, null};
                costs = new String[]{"150+100", "100+50", "100+150",
                                     null, null, null, null, null, null};
            } else {
                icons = new String[]{"ic_cc", "ic_depot", "ic_barracks",
                                     "ic_refinery", "ic_factory", "ic_turret",
                                     "ic_cancel", null, null};
                names = new String[]{"基地", "补给", "兵营",
                                     "炼油", "重工", "炮塔",
                                     "更多", null, null};
                costs = new String[]{"400", "100", "150",
                                     "100+50", "200+100", "100+50",
                                     null, null, null};
            }
        } else if (scvPage == -3) {
            // v2.10 protoss page: the widest name+price cells in the game.
            icons = new String[]{"ic_nexus", "ic_pylon", null,
                                 "ic_gateway", "ic_forge", "ic_photon",
                                 "ic_cancel", null, null};
            names = new String[]{"枢纽", "水晶塔", "吸收站",
                                 "传送门", "锻造厂", "光子炮",
                                 "更多", null, null};
            costs = new String[]{"400", "100", "100",
                                 "150", "150", "150",
                                 null, null, null};
        } else if (scvPage == -4) {
            // v2.14 vessel: the two science spells, both text-only labels.
            icons = new String[]{null, null, null, null, null, null, null, null, null};
            names = new String[]{"电磁脉冲", "辐射", null, null, null, null, null, null, null};
            costs = new String[]{null, null, null, null, null, null, null, null, null};
        } else if (scvPage == -5) {
            // v2.14 ghost: one spell cell.
            icons = new String[]{null, null, null, null, null, null, null, null, null};
            names = new String[]{"锁定", null, null, null, null, null, null, null, null};
            costs = new String[]{null, null, null, null, null, null, null, null, null};
        } else if (scvPage == -2) {
            // combat unit: 攻击移动 has no verified icon, so it is text-only
            icons = new String[]{"ic_attack", null, "ic_stop", "ic_patrol",
                                 null, null, null, null, null};
            names = new String[]{"攻击", "攻击移动", "停止", "巡逻",
                                 null, null, null, null, null};
            costs = new String[]{null, null, null, null, null, null, null, null, null};
        } else if (scvPage == -6) {
            // v2.25: the comsat's scanner sweep. One energy cell (blue badge).
            icons = new String[]{"ic_scan", null, null, null, null, null, null, null, null};
            names = new String[]{"扫描", null, null, null, null, null, null, null, null};
            costs = new String[]{"50", null, null, null, null, null, null, null, null};
        } else if (scvPage == -7) {
            // v2.25: the ghost's nuclear strike.
            icons = new String[]{"ic_nukestrike", null, null, null, null, null, null, null, null};
            names = new String[]{"核弹打击", null, null, null, null, null, null, null, null};
            costs = new String[]{null, null, null, null, null, null, null, null, null};
        } else if (scvPage == -8) {
            // v2.25: a science facility's card: train nothing, so it shows its
            // two add-on cells (physics lab and nuclear silo).
            icons = new String[]{"ic_physicslab", "ic_nukesilo", null,
                                 null, null, null, null, null, null};
            names = new String[]{"建造物理实验室", "建造核弹井", null,
                                 null, null, null, null, null, null};
            costs = new String[]{"50+25", "100+100", null, null, null, null, null, null, null};
        }
        for (int i = 0; i < cols * rows; i++) {
            float x = gx + (i % cols) * (cs + gap);
            float y = gy + (i / cols) * (cs + gap);
            Rectangle r = new Rectangle((int) x, (int) y, (int) cs, (int) cs);
            // v2.23 batch B: an unused cell draws NOTHING (GameView skips it
            // before any draw), and the panel is drawn once behind the grid.
            if (names[i] == null) continue;
            if (i == 0) {
                float pad = 2 * uiScale;
                bevelPanel(g, new Rectangle((int) (gx - pad), (int) (gy - pad),
                        (int) (gridW + 2 * pad), (int) (gridH + 2 * pad)), uiScale);
            }
            gridCell(g, r, i, cols, rows, (int) uiScale);

            float barH = cs >= 46 * uiScale ? 10 * uiScale : 9 * uiScale;
            float iconBottom = r.y + r.height - barH;
            BufferedImage ic = img("sprites/" + icons[i] + ".png");
            if (ic != null) {
                float pad = 2 * uiScale;
                g.drawImage(ic, (int) (r.x + pad), (int) (r.y + pad),
                        (int) (r.width - 2 * pad), (int) (iconBottom - r.y - pad * 1.5f), null);
            }

            Rectangle bar = new Rectangle(r.x + (int) uiScale, (int) (r.y + r.height - barH),
                    r.width - (int) (2 * uiScale), (int) barH - (int) uiScale);
            // v2.23 batch B: opaque deep chip, matching GameView.
            g.setColor(new Color(CHIP_DARK));
            g.fillRect(bar.x, bar.y, bar.width, bar.height);

            boolean afford = costs[i] == null || i < 6 || i != 8;   // one cell shown unaffordable
            FontMetrics fm = g.getFontMetrics();
            float nameMaxW = bar.width - 6 * uiScale;
            if (costs[i] != null) {
                g.setFont(new Font("SansSerif", Font.PLAIN, (int) (9f * uiScale)));
                fm = g.getFontMetrics();
                float costW = fm.stringWidth(costs[i]);
                g.setColor(afford ? new Color(140, 220, 255) : new Color(255, 110, 90));
                g.drawString(costs[i], bar.x + bar.width - (int) (3 * uiScale) - costW,
                        bar.y + (bar.height + fm.getAscent() - fm.getDescent()) / 2);
                nameMaxW = bar.width - 6 * uiScale - costW - 3 * uiScale;
            }
            g.setFont(new Font("SansSerif", Font.PLAIN, (int) (9.5f * uiScale)));
            fm = g.getFontMetrics();
            g.setColor(afford ? new Color(215, 232, 250) : new Color(150, 160, 175));
            String nm = names[i];
            while (nm.length() > 1 && fm.stringWidth(nm) > nameMaxW) {
                nm = nm.substring(0, nm.length() - 2) + "…";
            }
            g.drawString(nm, bar.x + (int) (3 * uiScale),
                    bar.y + (bar.height + fm.getAscent() - fm.getDescent()) / 2);
        }

        // production queue column (v2.5 #3): small icons, each with its Chinese
        // name strip, to the left of the card. Mirrors drawQueueColumn.
        String[] qKeys = {"scv", "marine", "firebat"};
        float qs = cs * 0.62f;
        float qx = gx - qs - 7 * uiScale;
        for (int i = 0; i < (queueShown ? qKeys.length : 0); i++) {
            Rectangle qr = new Rectangle((int) qx, (int) (gy + i * (qs + 4 * uiScale)),
                    (int) qs, (int) qs);
            bevelSlot(g, qr, uiScale);
            float qBarH = 9.5f * uiScale;
            float qIconBottom = qr.y + qr.height - qBarH;
            BufferedImage qic = img("sprites/ic_" + qKeys[i] + ".png");
            if (qic != null) {
                float pad = 2.5f * uiScale;
                g.drawImage(qic, (int) (qr.x + pad), (int) (qr.y + pad),
                        (int) (qr.width - 2 * pad), (int) (qIconBottom - qr.y - pad), null);
            }
            Rectangle qbar = new Rectangle(qr.x, qr.y + qr.height - (int) qBarH,
                    qr.width, (int) qBarH);
            g.setColor(new Color(12, 16, 26, 200));
            g.fillRect(qbar.x, qbar.y, qbar.width, qbar.height);
            if (i == 0) {                       // progress line on the active item
                g.setColor(new Color(80, 230, 80));
                g.fillRect(qr.x, qr.y + qr.height - 2, (int) (qr.width * 0.4f), 2);
            }
            g.setFont(new Font("SansSerif", Font.PLAIN, (int) (8 * uiScale)));
            FontMetrics qfm = g.getFontMetrics();
            String qn = qKeys[i];
            while (qn.length() > 1 && qfm.stringWidth(qn) > qbar.width - 3 * uiScale) {
                qn = qn.substring(0, qn.length() - 2) + "…";
            }
            g.setColor(new Color(215, 232, 250));
            g.drawString(qn, qbar.x + (qbar.width - qfm.stringWidth(qn)) / 2,
                    qbar.y + (qbar.height + qfm.getAscent() - qfm.getDescent()) / 2);
        }

        // sanity report: the panel only spans infoL..infoR when several unit
        // kinds are selected, so check the WIDEST case against the card.
        // v2.41: the playfield is 100% of the screen; the report pins the
        // bottom widgets to the screen edges instead.
        boolean overlap = infoR > gx;
        System.out.printf("%dx%d uiScale=%d cell=%.0f  info.right=%d(widest=%d) card.left=%d  %s%n",
                W, H, uiScale, cell, (int) (info.x + info.width), (int) infoR, (int) gx,
                overlap ? "*** OVERLAP ***" : "ok");
        System.out.printf("   card bottom=%d (screen H=%d, %s)  minimap bottom=%d (%s)"
                        + " | battlefield 100%%  %s%n",
                (int) (gy + gridH), H, (gy + gridH > H) ? "*** OFFSCREEN ***" : "ok",
                (int) (mmT + slotS), (mmT + slotS > H) ? "*** OFFSCREEN ***" : "ok",
                "ok");

        return im;
    }

    static void bevelPanel(Graphics2D g, Rectangle r, int s) {
        g.setColor(new Color(PANEL_MID));
        g.fillRect(r.x, r.y, r.width, r.height);
        g.setColor(new Color(PANEL_LITE));
        g.fillRect(r.x, r.y, r.width, 2 * s);
        g.fillRect(r.x, r.y, 2 * s, r.height);
        g.setColor(new Color(PANEL_DARK));
        g.fillRect(r.x, r.y + r.height - 2 * s, r.width, 2 * s);
        g.fillRect(r.x + r.width - 2 * s, r.y, 2 * s, r.height);
        g.setColor(new Color(PANEL_EDGE));
        g.drawRect(r.x, r.y, r.width, r.height);
    }

    /**
     * v2.23 batch B: one command-card cell -- a flat well with a single 1px
     * separator on the right/bottom of every non-last column/row. No per-cell
     * bevel: the depth and frame come from the one opaque bevelPanel behind the
     * grid, which is what stops the nine cells reading as boxes in a box.
     */
    static void gridCell(Graphics2D g, Rectangle r, int i, int cols, int rows, int s) {
        int col = i % cols, row = i / cols;
        g.setColor(new Color(SLOT_DARK));
        g.fillRect(r.x, r.y, r.width, r.height);
        g.setColor(new Color(CARD_SEP));
        if (col < cols - 1) g.fillRect(r.x + r.width - s, r.y, s, r.height);
        if (row < rows - 1) g.fillRect(r.x, r.y + r.height - s, r.width, s);
    }

    static void bevelSlot(Graphics2D g, Rectangle r, int s) {
        g.setColor(new Color(SLOT_DARK));
        g.fillRect(r.x, r.y, r.width, r.height);
        g.setColor(new Color(PANEL_DARK));
        g.fillRect(r.x, r.y, r.width, 2 * s);
        g.fillRect(r.x, r.y, 2 * s, r.height);
        g.setColor(new Color(PANEL_LITE));
        g.fillRect(r.x, r.y + r.height - 2 * s, r.width, 2 * s);
        g.fillRect(r.x + r.width - 2 * s, r.y, 2 * s, r.height);
        g.setColor(new Color(SLOT_EDGE));
        g.drawRect(r.x, r.y, r.width, r.height);
    }

    /**
     * v2.41: the widget audit. One default-preset frame at two resolutions;
     * every widget rect is outlined in green and labelled, and a note marks
     * what changed from v2.23: no band, no hairline rule, gaps are live map.
     */
    static void widgetsAudit() throws Exception {
        int[][] sizes = {{1280, 720}, {2400, 1080}};
        int gap = 24, pad = 12;
        int W = pad + sizes[0][0] + gap + sizes[1][0] + pad;
        int H = pad + sizes[0][1] + gap + sizes[1][1] + pad + 40;
        BufferedImage im = new BufferedImage(W, H, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = im.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(new Color(24, 26, 34));
        g.fillRect(0, 0, W, H);
        g.setColor(new Color(120, 230, 150));
        g.setFont(new Font("SansSerif", Font.BOLD, 20));
        g.drawString("v2.42 audit: eight independent opaque widgets on a full-screen"
                + " battlefield -- no band, no hairline, gaps are live map", pad, 30);
        String[] labels = {"暂停", "资源", "时间", "战况", "小地图", "编队", "信息", "九宫格"};
        for (int r = 0; r < sizes.length; r++) {
            int W2 = sizes[r][0], H2 = sizes[r][1], s = r == 0 ? 2 : 2;
            BufferedImage one = renderImpl(W2, H2, s, 7, false, -1);
            int ox = pad, oy = 44 + r * (sizes[0][1] + gap);
            if (r == 1) ox = pad + sizes[0][0] + gap;
            if (r == 1) oy = 44;
            g.drawImage(one, ox, oy, null);
            Graphics2D og = one.createGraphics();
            og.setStroke(new BasicStroke(2f));
            og.setFont(new Font("SansSerif", Font.BOLD, 16));
            // the eight rects, in HudLayout terms (default preset)
            float topH = 40 * s;
            float chipH = 26 * s, chipTop = (topH - chipH) / 2f;
            float pauseS = topH - 10 * s;
            float gw = 5 * 26 * s + 4 * 4 * s + 8 * s;
            float gh = 2 * 26 * s + 4 * s + 8 * s;
            float infoH = 72 * s;
            Rectangle[] rects = {
                    new Rectangle((int) (6 * s), (int) (5 * s), (int) pauseS, (int) pauseS),
                    new Rectangle((int) (6 * s + pauseS + 10 * s), (int) chipTop,
                            (int) (180 * s), (int) chipH),
                    new Rectangle((int) (W2 / 2f - 32 * s), (int) chipTop,
                            (int) (64 * s), (int) chipH),
                    new Rectangle((int) (W2 - 8 * s - 104 * s), (int) chipTop,
                            (int) (104 * s), (int) chipH),
                    new Rectangle((int) (8 * s), (int) (H2 - 8 * s - 156 * s),
                            (int) (156 * s), (int) (156 * s)),
                    new Rectangle((int) (8 * s + 156 * s + 10 * s),
                            (int) (H2 - 8 * s - gh), (int) gw, (int) gh),
                    new Rectangle((int) (8 * s + 156 * s + 10 * s + gw + 10 * s),
                            (int) (H2 - 8 * s - infoH),
                            (int) (150 * s), (int) infoH),
                    new Rectangle((int) (W2 - 12 * s - 3 * 50 * s - 2 * 4 * s),
                            (int) (H2 - 6 * s - (3 * 50 * s + 2 * 4 * s)),
                            (int) (3 * 50 * s + 2 * 4 * s), (int) (3 * 50 * s + 2 * 4 * s)),
            };
            for (int i = 0; i < rects.length; i++) {
                og.setColor(new Color(60, 255, 60));
                og.drawRect(rects[i].x, rects[i].y, rects[i].width - 1, rects[i].height - 1);
                og.setColor(new Color(150, 255, 170));
                og.drawString(labels[i], rects[i].x + 4, rects[i].y - 4);
            }
            og.dispose();
            g.setColor(Color.WHITE);
            g.setFont(new Font("SansSerif", Font.BOLD, 16));
            g.drawString(sizes[r][0] + "x" + sizes[r][1] + "  uiScale=" + s,
                    ox + 10, oy + 24);
        }
        ImageIO.write(im, "png", new File(OUT + "hud_v242_widgets.png"));
        System.out.println("audit: hud_v242_widgets.png");
    }

    /**
     * v2.23 batch A: the transparency audit. Three phone resolutions, each with
     * the three states the sweep touched (empty selection / single selection /
     * build page). The frame is annotated with the rule: the only translucent
     * pixels on the screen belong to the 3px minimap frame bevel; every panel,
     * chip, name strip and price badge is opaque. Drawn so the reviewer can see
     * the claim rather than take it on faith.
     */
    static void transparencyAudit() throws Exception {
        int[][] sizes = {{1280, 720}, {1920, 1080}, {2400, 1080}};
        int[] scales = {2, 2, 2};
        String[] stateName = {"空选", "单选", "建造页"};
        int cw = 1280, chh = 720, gap = 16, pad = 8;
        int cols = 3, rows = sizes.length;
        int W = pad + cols * (cw + gap);
        int H = pad + rows * (chh + gap) + 40;
        BufferedImage im = new BufferedImage(W, H, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = im.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(new Color(24, 26, 34));
        g.fillRect(0, 0, W, H);
        g.setColor(new Color(120, 230, 150));
        g.setFont(new Font("SansSerif", Font.BOLD, 20));
        g.drawString("v2.23 audit: persistent HUD has no translucent fill"
                + " (only the minimap frame bevel uses alpha)", pad, 28);
        for (int r = 0; r < rows; r++) {
            for (int col = 0; col < cols; col++) {
                BufferedImage one = renderState(sizes[r][0], sizes[r][1], scales[r], col);
                int ox = pad + col * (cw + gap);
                int oy = 40 + pad + r * (chh + gap);
                g.drawImage(one, ox, oy, cw, chh, null);
                g.setColor(Color.WHITE);
                g.setFont(new Font("SansSerif", Font.BOLD, 16));
                g.drawString(sizes[r][0] + "x" + sizes[r][1] + "  " + stateName[col],
                        ox + 10, oy + 22);
            }
        }
        ImageIO.write(im, "png", new File(OUT + "hud_transparency_audit.png"));
        System.out.println("audit: hud_transparency_audit.png");
    }

    /**
     * Render one (resolution, state) pair at 1:1 and return it. state:
     * 0 = empty selection, 1 = single selection, 2 = build page. The tiny
     * wrappers below exist only so drawImpl's signature stays as it was.
     */
    static BufferedImage renderState(int W, int H, int uiScale, int state) throws Exception {
        // renderImpl is the drawing path drawImpl writes to disk, minus the
        // write, so the audit image is exactly what ships.
        if (state == 0) return renderImpl(W, H, uiScale, 0, true, -1);
        if (state == 1) return renderImpl(W, H, uiScale, 7, false, -1);
        return renderImpl(W, H, uiScale, 7, false, 0);
    }

    /**
     * v2.17 problem 4: the world-space health bar floor, eyeballed at both zoom
     * extremes. Before v2.17 the bar was 4*zoom px tall with NO width floor, so
     * at 0.7 zoom a marine bar was ~3 px tall and ~13 px wide -- unreadable.
     * The columns are full hp (only drawn when the new "always show hp" setting
     * is on), hurt, and shield-stripped; the rows are zoom 0.7 and 2.0. The
     * geometry is copied from GameView.render's selection-ring/health block.
     */
    static void worldBarFrame() throws Exception {
        int uiScale = 2;
        float[] zooms = {0.7f, 2.0f};
        String[] labels = {"满血(开关开)", "掉血", "掉盾"};
        int cellW = 260, cellH = 190, padTop = 46, padLeft = 40;
        int W = padLeft + labels.length * cellW + 20;
        int H = padTop + zooms.length * cellH + 20;
        BufferedImage im = new BufferedImage(W, H, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = im.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(new Color(148, 138, 108));
        g.fillRect(0, 0, W, H);
        g.setColor(Color.WHITE);
        g.setFont(new Font("SansSerif", Font.BOLD, 14));
        g.drawString("v2.17 world health bar: h=max(4*zoom,3dp) w=max(r*1.9,16dp)", 12, 24);
        // marine radius from Game.TYPES (9), tiles 0
        float radius = 9f;
        for (int row = 0; row < zooms.length; row++) {
            float zoom = zooms[row];
            for (int c = 0; c < labels.length; c++) {
                int cx = padLeft + c * cellW + cellW / 2;
                int cy = padTop + row * cellH + cellH / 2 + 20;
                g.setColor(new Color(70, 90, 60));
                float rr = radius * zoom;
                g.fillOval((int) (cx - rr), (int) (cy - rr), (int) (rr * 2), (int) (rr * 2));
                float bh = Math.max(4 * zoom, 3f * uiScale);
                float bw = Math.max(rr * 1.9f, 16f * uiScale);
                float barX = cx - bw / 2f;
                if (c == 2) {
                    g.setColor(Color.BLACK);
                    g.fillRect((int) barX, (int) (cy - rr - 14 * zoom), (int) bw, (int) bh);
                    g.setColor(new Color(90, 200, 255));
                    g.fillRect((int) barX, (int) (cy - rr - 14 * zoom), (int) (bw * 0.5f), (int) bh);
                }
                float f = c == 1 ? 0.5f : 1.0f;
                int hc = f > 2f / 3f ? new Color(90, 230, 110).getRGB()
                        : f > 1f / 3f ? new Color(240, 220, 60).getRGB()
                        : new Color(240, 80, 70).getRGB();
                g.setColor(Color.BLACK);
                g.fillRect((int) barX, (int) (cy - rr - 9 * zoom), (int) bw, (int) bh);
                g.setColor(new Color(hc));
                g.fillRect((int) barX, (int) (cy - rr - 9 * zoom), (int) (bw * f), (int) bh);
                g.setColor(Color.BLACK);
                g.setFont(new Font("SansSerif", Font.PLAIN, 12));
                g.drawString(labels[c], cx - 40, cy + 70);
                g.setFont(new Font("SansSerif", Font.PLAIN, 11));
                g.drawString(String.format("zoom=%.1f bar=%.0fx%.0f", zoom, bw, bh),
                        cx - 58, cy + 88);
            }
        }
        ImageIO.write(im, "png", new File(OUT + "hud_worldbars.png"));
        System.out.println("world-bar preview: hud_worldbars.png");
    }

    /**
     * v2.19 batch C: the three console layout presets side by side. Mirrors the
     * same geometry as drawImpl (default), plus the mirrored and compact
     * variants from HudLayout. Visual QA only -- the arithmetic is pinned by
     * GameDesktop's [layout] assertions.
     */
    static void layoutPresetsFrame() throws Exception {
        int uiScale = 2;
        int W = 1280, H = 720;
        int gap = 20;
        BufferedImage im = new BufferedImage(W * 3 + gap * 4, H + gap * 2,
                BufferedImage.TYPE_INT_RGB);
        Graphics2D g = im.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(new Color(24, 26, 34));
        g.fillRect(0, 0, im.getWidth(), im.getHeight());
        String[] labels = {"默认", "左右互换", "紧凑"};
        for (int p = 0; p < 3; p++) {
            BufferedImage one = new BufferedImage(W, H, BufferedImage.TYPE_INT_RGB);
            Graphics2D gg = one.createGraphics();
            gg.setRenderingHint(RenderingHints.KEY_ANTIALIASING,
                    RenderingHints.VALUE_ANTIALIAS_ON);
            drawLayoutMock(gg, W, H, uiScale, p);
            gg.dispose();
            int ox = gap + p * (W + gap);
            g.drawImage(one, ox, gap, null);
            g.setColor(Color.WHITE);
            g.setFont(new Font("SansSerif", Font.BOLD, 22));
            g.drawString(labels[p], ox + 16, gap - 4);
        }
        ImageIO.write(im, "png", new File(OUT + "hud_layout_presets.png"));
        System.out.println("layout preview: hud_layout_presets.png");
    }

    /**
     * v2.20 batch C step 3: the custom layout editor's result. Mirrors
     * HudLayout.computeCustom with the same sample spec GameDesktop's
     * [layout] assertions use, so the picture and the arithmetic are the same
     * arrangement. Visual QA only.
     */
    static void layoutCustomFrame() throws Exception {
        int uiScale = 2;
        int W = 1280, H = 720;
        int gap = 20;
        // five samples side by side: the plan's default-ish custom, a
        // mirrored custom, the sizes at L, and two v2.41 chip arrangements.
        // v2.42: 18 floats -- the group block rides entries 15..17.
        float[][] specs = {
                {0.12f, 0.86f, 1f, 0.88f, 0.86f, 1f, 0.50f, 0.86f, 1f,
                 0.50f, 0.05f, 1f, 0.28f, 0.05f, 1f, 0.32f, 0.93f, 1f},
                {0.88f, 0.86f, 1f, 0.12f, 0.86f, 1f, 0.50f, 0.86f, 1f,
                 0.50f, 0.05f, 1f, 0.72f, 0.05f, 1f, 0.68f, 0.93f, 1f},
                {0.15f, 0.80f, 2f, 0.85f, 0.80f, 2f, 0.50f, 0.90f, 0f,
                 0.50f, 0.05f, 2f, 0.28f, 0.05f, 0f, 0.40f, 0.88f, 2f},
        };
        String[] labels = {"自定义样本 A", "自定义样本 B", "自定义样本 C(S/L)"};
        BufferedImage im = new BufferedImage(W * 3 + gap * 4, H + gap * 2,
                BufferedImage.TYPE_INT_RGB);
        Graphics2D g = im.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(new Color(24, 26, 34));
        g.fillRect(0, 0, im.getWidth(), im.getHeight());
        for (int p = 0; p < specs.length; p++) {
            BufferedImage one = new BufferedImage(W, H, BufferedImage.TYPE_INT_RGB);
            Graphics2D gg = one.createGraphics();
            gg.setRenderingHint(RenderingHints.KEY_ANTIALIASING,
                    RenderingHints.VALUE_ANTIALIAS_ON);
            drawCustomMock(gg, W, H, uiScale, specs[p]);
            gg.dispose();
            int ox = gap + p * (W + gap);
            g.drawImage(one, ox, gap, null);
            g.setColor(Color.WHITE);
            g.setFont(new Font("SansSerif", Font.BOLD, 22));
            g.drawString(labels[p], ox + 16, gap - 4);
        }
        ImageIO.write(im, "png", new File(OUT + "hud_layout_custom.png"));
        System.out.println("layout preview: hud_layout_custom.png");
    }

    /** Terrain + one custom arrangement; mirrors HudLayout.computeCustom. */
    static void drawCustomMock(Graphics2D g, int W, int H, int uiScale, float[] c) {
        g.setColor(new Color(148, 138, 108));
        g.fillRect(0, 0, W, H);
        g.setColor(new Color(196, 182, 138));
        for (int y = 0; y < H; y += 64)
            for (int x = 0; x < W; x += 64)
                if (((x + y) / 64) % 2 == 0) g.fillRect(x, y, 64, 64);
        float topH = 40 * uiScale;

        float[] sc = {0.8f, 1.0f, 1.25f};
        float mmS = 150f * uiScale * sc[sizeIdx(c[2])];
        float cell = 50f * uiScale * sc[sizeIdx(c[5])];
        float cardW = 3 * cell + 2 * 4f * uiScale;
        float infoW = 150f * uiScale * sc[sizeIdx(c[8])];
        float infoH = 72f * uiScale * sc[sizeIdx(c[8])];
        float clockW = 64f * uiScale * sc[sizeIdx(c[11])];
        float chipH = 26f * uiScale * sc[sizeIdx(c[11])];
        float resW = 180f * uiScale * sc[sizeIdx(c[14])];
        float gW = (5 * 26f + 4 * 4f + 8f) * uiScale * sc[sizeIdx(c[17])];
        float gH = (2 * 26f + 4f + 8f) * uiScale * sc[sizeIdx(c[17])];
        float[] mm = place(c[0] * W, c[1] * H, mmS, mmS, W, H, topH, uiScale);
        float[] cd = place(c[3] * W, c[4] * H, cardW, cardW, W, H, topH, uiScale);
        float[] inf = place(c[6] * W, c[7] * H, infoW, infoH, W, H, topH, uiScale);
        float[] ck = place(c[9] * W, c[10] * H, clockW, chipH, W, H, topH, uiScale);
        float[] rs = place(c[12] * W, c[13] * H, resW, chipH, W, H, topH, uiScale);
        float[] grp = c.length >= 18
                ? place(c[15] * W, c[16] * H, gW, gH, W, H, topH, uiScale)
                : null;

        // v2.42: no band, no hairline -- six floating panels on the full map
        drawWidgetMock(g, uiScale, mm, cd, inf, ck, rs);
        if (grp != null) drawGroupsMock(g, uiScale, grp);
    }

    /** v2.42: the ten group chips inside a placed group block (custom layouts). */
    static void drawGroupsMock(Graphics2D g, int uiScale, float[] grp) {
        float gCellS = ((grp[2] - grp[0]) - 8 * uiScale - 16 * uiScale) / 5f;
        float gRowH = gCellS + 4 * uiScale;
        float gTop = (grp[1] + grp[3]) / 2f - (2 * gCellS + 4 * uiScale) / 2f;
        g.setFont(new Font("SansSerif", Font.PLAIN, (int) (gCellS * 0.34f)));
        FontMetrics gfm = g.getFontMetrics();
        for (int gidx = 0; gidx < 10; gidx++) {
            int col = gidx % 5, row = gidx / 5;
            Rectangle gr = new Rectangle(
                    (int) (grp[0] + 4 * uiScale + col * (gCellS + 4 * uiScale)),
                    (int) (gTop + row * gRowH), (int) gCellS, (int) gCellS);
            bevelPanel(g, gr, uiScale);
            g.setColor(new Color(200, 220, 245));
            String gs = String.valueOf(gidx + 1);
            g.drawString(gs, gr.x + (gr.width - gfm.stringWidth(gs)) / 2,
                    gr.y + (gr.height + gfm.getAscent() - gfm.getDescent()) / 2);
        }
    }

    /** Draw the minimap/card/info/clock/res mock rects (v2.41 shared). */
    static void drawWidgetMock(Graphics2D g, int uiScale, float[] mm, float[] cd,
                               float[] inf, float[] ck, float[] rs) {
        // minimap
        bevelSlot(g, new Rectangle((int) mm[0], (int) mm[1], (int) (mm[2] - mm[0]),
                (int) (mm[3] - mm[1])), uiScale);
        g.setColor(new Color(30, 40, 30));
        g.fillRect((int) mm[0] + 3 * uiScale, (int) mm[1] + 3 * uiScale,
                (int) (mm[2] - mm[0]) - 6 * uiScale, (int) (mm[3] - mm[1]) - 6 * uiScale);
        // card
        float pad = 2 * uiScale;
        float cell = (cd[2] - cd[0] - 2 * 4f * uiScale) / 3f;
        bevelPanel(g, new Rectangle((int) (cd[0] - pad), (int) (cd[1] - pad),
                (int) (cd[2] - cd[0] + 2 * pad), (int) (cd[3] - cd[1] + 2 * pad)), uiScale);
        float gap2 = 4 * uiScale;
        for (int i = 0; i < 9; i++) {
            float x = cd[0] + (i % 3) * (cell + gap2);
            float y = cd[1] + (i / 3) * (cell + gap2);
            gridCell(g, new Rectangle((int) x, (int) y, (int) cell, (int) cell),
                    i, 3, 3, (int) uiScale);
        }
        // info panel
        bevelPanel(g, new Rectangle((int) inf[0], (int) inf[1],
                (int) (inf[2] - inf[0]), (int) (inf[3] - inf[1])), uiScale);
        g.setColor(new Color(120, 140, 175));
        g.setFont(new Font("SansSerif", Font.PLAIN, 12 * uiScale));
        g.drawString("信息", (int) inf[0] + 8, (int) inf[1] + 20 * uiScale);
        // clock + res chips
        if (ck != null) {
            bevelPanel(g, new Rectangle((int) ck[0], (int) ck[1],
                    (int) (ck[2] - ck[0]), (int) (ck[3] - ck[1])), uiScale);
            g.setColor(new Color(230, 236, 248));
            g.setFont(new Font("SansSerif", Font.PLAIN, 12 * uiScale));
            g.drawString("03:24", (int) ck[0] + 8, (int) ck[1] + 18 * uiScale);
        }
        if (rs != null) {
            bevelPanel(g, new Rectangle((int) rs[0], (int) rs[1],
                    (int) (rs[2] - rs[0]), (int) (rs[3] - rs[1])), uiScale);
            g.setColor(new Color(140, 220, 255));
            g.setFont(new Font("SansSerif", Font.PLAIN, 11 * uiScale));
            g.drawString("晶体 1240", (int) rs[0] + 8, (int) rs[1] + 17 * uiScale);
        }
    }

    static int sizeIdx(float v) {
        int i = Math.round(v);
        return i < 0 ? 0 : (i > 2 ? 2 : i);
    }

    /** Mirror of HudLayout.place (v2.41: screen margin only, no top clamp). */
    static float[] place(float cx, float cy, float w, float h,
                         int W, int H, float topH, int dp) {
        float l = cx - w / 2f, t = cy - h / 2f;
        float margin = 4 * dp;
        if (l < margin) l = margin;
        if (t < margin) t = margin;
        if (l + w > W - margin) l = W - margin - w;
        if (t + h > H - margin) t = H - margin - h;
        return new float[]{l, t, l + w, t + h};
    }

    /** Terrain + one of the three console arrangements, for the preset strip. */
    static void drawLayoutMock(Graphics2D g, int W, int H, int uiScale, int preset) {
        g.setColor(new Color(148, 138, 108));
        g.fillRect(0, 0, W, H);
        g.setColor(new Color(196, 182, 138));
        for (int y = 0; y < H; y += 64)
            for (int x = 0; x < W; x += 64)
                if (((x + y) / 64) % 2 == 0) g.fillRect(x, y, 64, 64);
        float topH = 40 * uiScale;

        float cs = 50 * uiScale;
        float gap = 4 * uiScale;
        float gridW = 3 * cs + 2 * gap, gridH = 3 * cs + 2 * gap;
        float mmS, mmL, mmT;
        if (preset == 2) {
            mmS = Math.min(120 * uiScale, W * 0.18f) + 6 * uiScale;
            mmL = 8 * uiScale; mmT = topH + 8 * uiScale;
        } else {
            mmS = 150 * uiScale + 6 * uiScale;
            mmL = preset == 1 ? W - 8 * uiScale - mmS : 8 * uiScale;
            mmT = H - 8 * uiScale - mmS;
        }
        float cardL = preset == 1 ? 12 * uiScale : W - 12 * uiScale - gridW;
        float cardT = H - 6 * uiScale - gridH;

        // v2.41 top chips (fixed positions, same in every preset)
        float chipH = 26 * uiScale, chipTop = (topH - chipH) / 2f;
        float pauseS = topH - 10 * uiScale;
        Rectangle pause = new Rectangle((int) (6 * uiScale), (int) (5 * uiScale),
                (int) pauseS, (int) pauseS);
        bevelPanel(g, pause, uiScale);
        Rectangle clockChip = new Rectangle((int) (W / 2f - 32 * uiScale),
                (int) chipTop, (int) (64 * uiScale), (int) chipH);
        bevelPanel(g, clockChip, uiScale);
        Rectangle tallyChip = new Rectangle((int) (W - 8 * uiScale - 104 * uiScale),
                (int) chipTop, (int) (104 * uiScale), (int) chipH);
        bevelPanel(g, tallyChip, uiScale);
        g.setColor(new Color(230, 236, 248));
        g.setFont(new Font("SansSerif", Font.PLAIN, 12 * uiScale));
        g.drawString("03:24", clockChip.x + 14, clockChip.y + 18 * uiScale);
        g.setColor(new Color(140, 220, 255));
        g.drawString("晶体 1240", pause.x + pause.width + 10 * uiScale,
                (int) (chipTop + 18 * uiScale));

        float[] mm = {mmL, mmT, mmL + mmS, mmT + mmS};
        float[] cd = {cardL, cardT, cardL + gridW, cardT + gridH};
        // v2.42: the group block rides between the minimap and the info panel,
        // bottom-aligned with the strip; the info panel is slim (72dp) and
        // starts right of the block. Compact parks the block bottom-left
        // (under the floating minimap), mirroring HudLayout.compute.
        float gW = 5 * 26 * uiScale + 4 * 4 * uiScale + 8 * uiScale;
        float gH = 2 * 26 * uiScale + 4 * uiScale + 8 * uiScale;
        float gL, gRef;
        if (preset == 2) {
            gL = 8 * uiScale;
            gRef = cd[3];                       // card bottom
        } else {
            gL = preset == 1 ? cd[2] + 10 * uiScale : mm[2] + 10 * uiScale;
            float gMaxL = preset == 1 ? mm[0] - 10 * uiScale - gW : cd[0] - 22 * uiScale - gW;
            if (gL > gMaxL) gL = gMaxL;
            gRef = H - 8 * uiScale;
        }
        float[] grp = {gL, gRef - gH, gL + gW, gRef};
        float midL = grp[2] + 10 * uiScale;
        float midR = preset == 1 ? mm[0] - 10 * uiScale : cd[0] - 22 * uiScale;
        float[] inf = {midL, gRef - 72 * uiScale, midR, gRef};
        drawWidgetMock(g, uiScale, mm, cd, inf, null, null);
        // the ten group chips inside the block (mirrors drawFormationOnly)
        float gCellS = (gW - 8 * uiScale - 16 * uiScale) / 5f;
        float gRowH = gCellS + 4 * uiScale;
        float gTop = (grp[1] + grp[3]) / 2f - (2 * gCellS + 4 * uiScale) / 2f;
        g.setFont(new Font("SansSerif", Font.PLAIN, (int) (gCellS * 0.34f)));
        FontMetrics gfm = g.getFontMetrics();
        for (int gidx = 0; gidx < 10; gidx++) {
            int col = gidx % 5, row = gidx / 5;
            Rectangle gr = new Rectangle(
                    (int) (grp[0] + 4 * uiScale + col * (gCellS + 4 * uiScale)),
                    (int) (gTop + row * gRowH), (int) gCellS, (int) gCellS);
            bevelPanel(g, gr, uiScale);
            g.setColor(new Color(200, 220, 245));
            String gs = String.valueOf(gidx + 1);
            g.drawString(gs, gr.x + (gr.width - gfm.stringWidth(gs)) / 2,
                    gr.y + (gr.height + gfm.getAscent() - gfm.getDescent()) / 2);
        }
    }
}
