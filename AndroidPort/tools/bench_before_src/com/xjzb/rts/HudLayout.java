package com.xjzb.rts;

import android.graphics.RectF;

/**
 * v2.41: the match HUD as SIX INDEPENDENT WIDGETS on a full-screen battlefield.
 *
 * History: before this class the geometry lived in three spots; v2.19 batch C
 * made this the single generation point; v2.23 deleted the scrims but kept the
 * "top bar band + console band" skeleton -- two full-width strips with no
 * background, which the player read as two big transparent windows. v2.41
 * removes the band model itself: there is no band top, no band height, no
 * playfield-between-bars any more. The camera covers the whole screen and
 * every HUD element is a self-contained opaque chip that floats on the map:
 *
 *   P_MINIMAP (bottom-left by default)   P_CARD (bottom-right)
 *   P_GROUPS (between minimap and info)  P_INFO (slim, bottom-centre)
 *   P_PAUSE (fixed top-left)             P_CLOCK (top-centre)
 *   P_RES   (top, after the pause chip)
 *
 * A fixed TALLY chip (我方/敌方) is generated too but is not an editable
 * panel; the view hides it when a custom layout parks the clock over it.
 *
 * The custom-layout spec is EIGHTEEN floats -- (centre x, centre y, size) per
 * editable panel in the P_ order -- normalised to the screen so the layout
 * survives a different viewport. parseSpec (GameView) migrates a legacy
 * 15-float save by appending the default groups anchor, and a legacy 9-float
 * save by appending the clock/res/groups anchors.
 */
class HudLayout {

    static final int PRESET_DEFAULT = 0, PRESET_MIRRORED = 1, PRESET_COMPACT = 2;
    static final int PRESET_CUSTOM = 3;

    /** Panel indices for the custom-layout spec. */
    static final int P_MINIMAP = 0, P_CARD = 1, P_INFO = 2, P_CLOCK = 3, P_RES = 4,
            P_GROUPS = 5;
    static final int PANEL_COUNT = 6;
    /** Spec length: (cx, cy, size) per editable panel. */
    static final int SPEC_LEN = PANEL_COUNT * 3;
    /** S/M/L size multipliers, indexed by a panel spec size 0/1/2. */
    static final float[] SIZE_SCALE = {0.8f, 1.0f, 1.25f};
    /** Base panel sizes in dp, before the size multiplier. */
    static final float MINIMAP_DP = 150f, CARD_CELL_DP = 50f, INFO_W_DP = 150f,
            INFO_H_DP = 72f;
    // v2.42 batch C: the control-group block joins the editable set. Ten chips
    // in two rows of five (a single row of ten is a 20px target on a phone);
    // the block sits between the minimap and the info panel by default and is
    // its own panel everywhere else.
    static final float GROUP_CELL_DP = 26f, GROUP_GAP_DP = 4f;
    // v2.41 top chips. The widths are fixed so the rects are stable frame to
    // frame; the text drawn inside shrinks to fit (GameView draws the chips).
    static final float CLOCK_W_DP = 64f, CHIP_H_DP = 26f,
            RES_W_DP = 180f, TALLY_W_DP = 104f;

    /** v2.42 batch C: the group block's size in dp (chip block + 4dp margins),
     * before any size scale. drawFormationOnly derives its chip edge from the
     * placed rect, so the two can never disagree. */
    static float groupsW(float dp) {
        return 5 * GROUP_CELL_DP * dp + 4 * GROUP_GAP_DP * dp + 8 * dp;
    }

    static float groupsH(float dp) {
        return 2 * GROUP_CELL_DP * dp + GROUP_GAP_DP * dp + 8 * dp;
    }

    // ---- chip metrics ----
    static final int CARD_COLS = 3, CARD_ROWS = 3;
    static final float CARD_GAP_DP = 4f;
    static final float CARD_PAD_DP = 10f;
    /** Preferred / minimum command-cell size in dp (v2.5 #2 grew 44 -> 50). */
    static final float CELL_DP = 50f;
    static final float CELL_MIN_DP = 46f;

    // ---- outputs, screen px, valid after compute() ----
    final RectF minimapSlot = new RectF();   // the recessed frame
    final RectF minimap = new RectF();       // the inner drawable area
    final RectF card = new RectF();          // the 3x3 grid
    final RectF middle = new RectF();        // the selection info panel
    final RectF pause = new RectF();         // v2.41: the fixed pause chip
    final RectF clock = new RectF();         // v2.41: the time chip
    final RectF res = new RectF();           // v2.41: the resource chip
    final RectF tally = new RectF();         // v2.41: the fixed team-tally chip
    final RectF groups = new RectF();        // v2.42: the control-group block

    /**
     * v2.41: playfield envelope is the WHOLE screen. The world may sit under
     * any widget (the standard MOBA trade) and the gaps between widgets are
     * live, tappable battlefield.
     */
    float centerX, centerY, halfW, halfH;
    /**
     * v2.21 #3: how much the info panel's CONTENT (text, portrait padding)
     * should grow inside the placed rect. 1 for the three presets; the custom
     * layout's S/M/L multiplier otherwise, so a size change scales what is
     * drawn instead of only the box around it.
     */
    float infoScale = 1f;

    /**
     * Command-cell edge in px. On a short screen (a 720p phone at density 2 is
     * only 360dp tall) three rows of 50dp would eat a third of the viewport,
     * so the cell is squeezed to CELL_MIN_DP. That floor is deliberate:
     * shrinking further would make the buttons untappable.
     */
    static float cardCell(int H, float dp) {
        float want = CELL_DP * dp;
        if (H > 0) {
            float budget = H * 0.50f - CARD_PAD_DP * dp
                    - (CARD_ROWS - 1) * CARD_GAP_DP * dp;
            float fit = budget / CARD_ROWS;
            if (fit < want) want = Math.max(CELL_MIN_DP * dp, fit);
        }
        return want;
    }

    /** Place the fixed top chips (pause / clock / res / tally) and the two
     *  shared envelope fields. Used by every preset branch. */
    private void topChips(int W, int H, float topH, float dp, float zoom) {
        float chipH = CHIP_H_DP * dp;
        float chipTop = (topH - chipH) / 2f;
        float pauseS = topH - 10 * dp;
        pause.set(6 * dp, 5 * dp, 6 * dp + pauseS, 5 * dp + pauseS);
        res.set(pause.right + 10 * dp, chipTop,
                pause.right + 10 * dp + RES_W_DP * dp, chipTop + chipH);
        clock.set(W / 2f - CLOCK_W_DP * dp / 2f, chipTop,
                W / 2f + CLOCK_W_DP * dp / 2f, chipTop + chipH);
        tally.set(W - 8 * dp - TALLY_W_DP * dp, chipTop, W - 8 * dp, chipTop + chipH);
        centerX = W / 2f;
        centerY = H / 2f;
        halfW = W / 2f / zoom;
        halfH = H / 2f / zoom;
    }

    void compute(int W, int H, float topH, float dp, float zoom,
                 int preset, float[] custom) {
        if (preset == PRESET_CUSTOM && custom != null && custom.length >= SPEC_LEN) {
            computeCustom(W, H, dp, zoom, custom);
            topChips(W, H, topH, dp, zoom);
            // the editable clock/res chips follow the spec, not the default row
            place(clock, custom[9] * W, custom[10] * H,
                    CLOCK_W_DP * dp * SIZE_SCALE[sizeIdx(custom[11])],
                    CHIP_H_DP * dp * SIZE_SCALE[sizeIdx(custom[11])], W, H, dp);
            place(res, custom[12] * W, custom[13] * H,
                    RES_W_DP * dp * SIZE_SCALE[sizeIdx(custom[14])],
                    CHIP_H_DP * dp * SIZE_SCALE[sizeIdx(custom[14])], W, H, dp);
            return;
        }
        topChips(W, H, topH, dp, zoom);
        float cs = cardCell(H, dp);
        float gap = CARD_GAP_DP * dp;
        float gridW = CARD_COLS * cs + (CARD_COLS - 1) * gap;
        float gridH = CARD_ROWS * cs + (CARD_ROWS - 1) * gap;
        float gw = groupsW(dp) * SIZE_SCALE[1];
        float gh = groupsH(dp) * SIZE_SCALE[1];
        float infoH = INFO_H_DP * dp;

        if (preset == PRESET_COMPACT) {
            // v2.19 compact: the minimap floats at the top-left under the top
            // chips (the MOBA convention) and the bottom holds card + info.
            // v2.42: the group block sits left of the info panel on the same
            // bottom strip, both bottom-aligned with the card.
            float ms = Math.min(120 * dp, W * 0.18f);
            minimapSlot.set(8 * dp, topH + 8 * dp, 8 * dp + ms + 6 * dp,
                    topH + 8 * dp + ms + 6 * dp);
            float gx = W - 12 * dp - gridW;
            float gy = H - 6 * dp - gridH;
            card.set(gx, gy, gx + gridW, gy + gridH);
            groups.set(8 * dp, card.bottom - gh, 8 * dp + gw, card.bottom);
            middle.set(groups.right + 10 * dp, card.bottom - infoH,
                    card.left - 10 * dp, card.bottom);
        } else {
            boolean mirror = preset == PRESET_MIRRORED;
            float slotS = MINIMAP_DP * dp + 6 * dp;
            float mmL = mirror ? W - 8 * dp - slotS : 8 * dp;
            minimapSlot.set(mmL, H - 8 * dp - slotS, mmL + slotS, H - 8 * dp);
            float gx = mirror ? 12 * dp : W - 12 * dp - gridW;
            float gy = H - 6 * dp - gridH;
            card.set(gx, gy, gx + gridW, gy + gridH);
            if (!mirror) {
                // v2.42: minimap | groups | info | card, all bottom-aligned.
                // On an ultra-narrow screen the strip cannot hold all four, so
                // the group block yields first (it keeps clear of the card),
                // and the info panel clamps to whatever width is left.
                float gL = minimapSlot.right + 10 * dp;
                float gMax = card.left - 22 * dp - gw;
                if (gL > gMax) gL = gMax;
                groups.set(gL, H - 8 * dp - gh, gL + gw, H - 8 * dp);
                float mL = Math.min(groups.right + 10 * dp, card.left - 22 * dp);
                float mR = Math.max(mL, card.left - 22 * dp);
                middle.set(mL, H - 8 * dp - infoH, mR, H - 8 * dp);
            } else {
                float gL = card.right + 10 * dp;
                float gMax = minimapSlot.left - 10 * dp - gw;
                if (gL > gMax) gL = gMax;
                groups.set(gL, H - 8 * dp - gh, gL + gw, H - 8 * dp);
                float mL = Math.min(groups.right + 10 * dp, minimapSlot.left - 10 * dp);
                float mR = Math.max(mL, minimapSlot.left - 10 * dp);
                middle.set(mL, H - 8 * dp - infoH, mR, H - 8 * dp);
            }
        }
        minimap.set(minimapSlot.left + 3 * dp, minimapSlot.top + 3 * dp,
                minimapSlot.right - 3 * dp, minimapSlot.bottom - 3 * dp);
        infoScale = 1f;
    }

    /**
     * v2.41: place the five editable panels from a 15-float spec -- (centre x,
     * centre y, size) per panel in the P_ order, centre normalised to the
     * screen. Panels are clamped to stay on screen; the caller rejects an
     * overlapping save. There is no band computation any more: the playfield
     * is the whole screen regardless of where the panels sit.
     * v2.42: six panels -- P_GROUPS rides entries 15..17 of the 18-float spec
     * (parseSpec migrates a legacy 15-float save by parking it on the default
     * bottom strip).
     */
    private void computeCustom(int W, int H, float dp, float zoom, float[] c) {
        float mmS = MINIMAP_DP * dp * SIZE_SCALE[sizeIdx(c[2])];
        float cell = CARD_CELL_DP * dp * SIZE_SCALE[sizeIdx(c[5])];
        float cardW = CARD_COLS * cell + (CARD_COLS - 1) * CARD_GAP_DP * dp;
        float infoW = INFO_W_DP * dp * SIZE_SCALE[sizeIdx(c[8])];
        float infoH = INFO_H_DP * dp * SIZE_SCALE[sizeIdx(c[8])];
        float gScale = SIZE_SCALE[sizeIdx(c[17])];
        float gW = groupsW(dp) * gScale;
        float gH = groupsH(dp) * gScale;
        place(minimapSlot, c[0] * W, c[1] * H, mmS, mmS, W, H, dp);
        place(card, c[3] * W, c[4] * H, cardW, cardW, W, H, dp);
        place(middle, c[6] * W, c[7] * H, infoW, infoH, W, H, dp);
        place(groups, c[15] * W, c[16] * H, gW, gH, W, H, dp);
        minimap.set(minimapSlot.left + 3 * dp, minimapSlot.top + 3 * dp,
                minimapSlot.right - 3 * dp, minimapSlot.bottom - 3 * dp);
        infoScale = SIZE_SCALE[sizeIdx(c[8])];

        centerX = W / 2f;
        centerY = H / 2f;
        halfW = W / 2f / zoom;
        halfH = H / 2f / zoom;
    }

    static int sizeIdx(float s) {
        int i = Math.round(s);
        return i < 0 ? 0 : (i > 2 ? 2 : i);
    }

    /** Centre a w x h rect on (cx, cy) and clamp it inside the screen. */
    private static void place(RectF out, float cx, float cy, float w, float h,
                              int W, int H, float dp) {
        float l = cx - w / 2f, t = cy - h / 2f;
        float margin = 4 * dp;
        if (l < margin) l = margin;
        if (t < margin) t = margin;
        if (l + w > W - margin) l = W - margin - w;
        if (t + h > H - margin) t = H - margin - h;
        out.set(l, t, l + w, t + h);
    }

    /** Panel rect for a given panel index (used by the editor hit-tests). */
    RectF panel(int which) {
        switch (which) {
            case P_MINIMAP: return minimapSlot;
            case P_CARD: return card;
            case P_INFO: return middle;
            case P_CLOCK: return clock;
            case P_GROUPS: return groups;
            default: return res;
        }
    }
}
