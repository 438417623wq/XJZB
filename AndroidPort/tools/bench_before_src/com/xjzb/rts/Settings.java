package com.xjzb.rts;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * Player-tunable settings (v2.7 batch 7.2).
 *
 * These used to be scattered constants: the drag slop and box-select hold were
 * private fields on GameView with a comment saying "the plan's 10px felt wrong
 * on a real phone, retune DRAG_SLOP_DP", and volume was a 5-step cycle with no
 * way to sit between steps. They now live here, persist to SharedPreferences,
 * and are read through one object so the touch code and the pause menu cannot
 * disagree about the current value.
 */
public class Settings {

    private static final String FILE = "xjzb_settings";

    private static final String K_SLOP = "drag_slop_dp";
    private static final String K_HOLD = "box_hold_ms";
    private static final String K_VOL = "volume";
    private static final String K_EDGE = "edge_scroll";
    private static final String K_ALWAYS_HP = "always_show_hp";
    private static final String K_FOG = "fog_style";
    private static final String K_ZOOM = "zoom_level";
    private static final String K_LAYOUT = "hud_layout";
    private static final String K_LAYOUT_NORM = "hud_layout_norm";
    private static final String K_LAYOUT_EDIT = "hud_layout_edit";
    private static final String K_DIAG = "render_diag";

    /** Drag slop in dp: below ~6dp a tap reads as a drag on most panels. */
    public static final float SLOP_MIN = 4f, SLOP_MAX = 20f;
    /** Hold-still time before the box select arms. */
    public static final int HOLD_MIN = 120, HOLD_MAX = 500;

    public float dragSlopDp = 8f;
    public int boxHoldMs = 250;
    public float volume = 1f;
    public boolean edgeScroll = true;
    /** v2.17: draw the world-space health bar even at full health. */
    public boolean alwaysShowHp = false;

    /**
     * v2.18 batch A: the fog/vision model.
     *   FOG_SC  -- classic StarCraft: unexplored is opaque black, explored is
     *              dimmed, and enemies standing on explored ground still draw.
     *   FOG_HOK -- the mobile-MOBA model the player asked for: terrain is always
     *              fully visible (no overlay at all) and an enemy only appears
     *              once it walks into a friendly unit or building vision.
     * Default is HOK; SC stays available and is byte-for-byte the old render.
     */
    public static final int FOG_SC = 0, FOG_HOK = 1;
    public int fogStyle = FOG_HOK;

    /**
     * v2.18 batch B: the zoom preset. The multiplier scales the base default
     * (1.3), floor (1.0) and ceiling (2.0) together, so a phone that finds the
     * default too tight or too close can shift the whole range without losing
     * the "small units must stay readable" floor.
     */
    public static final int ZOOM_LOW = 0, ZOOM_NORMAL = 1, ZOOM_HIGH = 2;
    public int zoomLevel = ZOOM_NORMAL;

    /**
     * v2.19 batch C: which console arrangement to use. Default and
     * mirrored are the classic bottom bar (mirrored swaps the minimap
     * and the command card); compact floats the minimap under the top
     * bar and leaves only the card on the console.
     */
    public static final int HUD_DEFAULT = 0, HUD_MIRRORED = 1, HUD_COMPACT = 2;
    /** v2.20 step 3: the saved custom layout (see layoutNorm). */
    public static final int HUD_CUSTOM = 3;
    public int hudPreset = HUD_DEFAULT;

    /**
     * v2.19 batch C step 3: the custom layout, stored normalised to the
     * playfield (x, y, size) per panel so it survives any screen size. Empty
     * means "no custom layout -- use hudPreset". A 3x3 float array flattened
     * to a comma string: minimap x,y,s ; card x,y,s ; info x,y,s.
     */
    public String layoutNorm = "";
    /** True when the player has saved a custom layout (hudPreset ignored). */
    public boolean layoutCustom = false;

    /**
     * v2.42 batch B: the on-device chunk-pipeline diagnostic. On: every visible
     * terrain chunk gets a 1px frame (colour = row+col parity), still-decoding
     * placeholders flash magenta, and the renderer logs hit/miss at 0.5 Hz --
     * so a screenshot of the reported black bar directly answers whether it
     * lives inside a chunk, between chunks, or over everything.
     */
    public boolean renderDiag = false;

    private final SharedPreferences prefs;

    public Settings(Context ctx) {
        prefs = ctx.getSharedPreferences(FILE, Context.MODE_PRIVATE);
        dragSlopDp = prefs.getFloat(K_SLOP, dragSlopDp);
        boxHoldMs = prefs.getInt(K_HOLD, boxHoldMs);
        volume = prefs.getFloat(K_VOL, volume);
        edgeScroll = prefs.getBoolean(K_EDGE, edgeScroll);
        alwaysShowHp = prefs.getBoolean(K_ALWAYS_HP, alwaysShowHp);
        fogStyle = prefs.getInt(K_FOG, fogStyle);
        zoomLevel = prefs.getInt(K_ZOOM, zoomLevel);
        hudPreset = prefs.getInt(K_LAYOUT, hudPreset);
        layoutNorm = prefs.getString(K_LAYOUT_NORM, layoutNorm);
        layoutCustom = prefs.getBoolean(K_LAYOUT_EDIT, layoutCustom);
        renderDiag = prefs.getBoolean(K_DIAG, renderDiag);
    }

    public void save() {
        prefs.edit()
                .putFloat(K_SLOP, dragSlopDp)
                .putInt(K_HOLD, boxHoldMs)
                .putFloat(K_VOL, volume)
                .putBoolean(K_EDGE, edgeScroll)
                .putBoolean(K_ALWAYS_HP, alwaysShowHp)
                .putInt(K_FOG, fogStyle)
                .putInt(K_ZOOM, zoomLevel)
                .putInt(K_LAYOUT, hudPreset)
                .putString(K_LAYOUT_NORM, layoutNorm)
                .putBoolean(K_LAYOUT_EDIT, layoutCustom)
                .putBoolean(K_DIAG, renderDiag)
                .apply();
    }

    /** Named presets so the player does not have to reason in dp. */
    public static final int SENS_SLOW = 0, SENS_NORMAL = 1, SENS_FAST = 2;

    public int sensitivity() {
        if (dragSlopDp <= 6f) return SENS_FAST;
        if (dragSlopDp >= 12f) return SENS_SLOW;
        return SENS_NORMAL;
    }

    public void setSensitivity(int level) {
        switch (level) {
            case SENS_FAST: dragSlopDp = 5f; break;
            case SENS_SLOW: dragSlopDp = 14f; break;
            default: dragSlopDp = 8f; break;
        }
    }

    public static String sensitivityName(int level) {
        switch (level) {
            case SENS_FAST: return "灵敏";
            case SENS_SLOW: return "稳重";
            default: return "标准";
        }
    }

    public int holdLevel() {
        if (boxHoldMs <= 180) return 0;
        if (boxHoldMs >= 350) return 2;
        return 1;
    }

    public void setHoldLevel(int level) {
        switch (level) {
            case 0: boxHoldMs = 160; break;
            case 2: boxHoldMs = 420; break;
            default: boxHoldMs = 250; break;
        }
    }

    public static String holdName(int level) {
        switch (level) {
            case 0: return "很快";
            case 2: return "较慢";
            default: return "标准";
        }
    }

    // ------------------------------------------------------- v2.18 fog style
    public static String fogStyleName(int style) {
        return style == FOG_SC ? "经典" : "王者";
    }

    // ------------------------------------------------------- v2.18 zoom preset
    /** Base default / floor / ceiling, before the preset multiplier. */
    public static final float ZOOM_BASE = 1.3f;
    public static final float ZOOM_MIN_BASE = 1.0f;
    public static final float ZOOM_MAX_BASE = 2.0f;

    /** Multiplier for a zoom preset level. */
    public static float zoomMult(int level) {
        switch (level) {
            case ZOOM_LOW: return 0.85f;
            case ZOOM_HIGH: return 1.2f;
            default: return 1.0f;
        }
    }

    public static float zoomDefault(int level) { return ZOOM_BASE * zoomMult(level); }
    public static float zoomMin(int level) { return ZOOM_MIN_BASE * zoomMult(level); }
    public static float zoomMax(int level) { return ZOOM_MAX_BASE * zoomMult(level); }

    // ----------------------------------------------------- v2.19 layout preset
    public static String layoutName(int preset) {
        switch (preset) {
            case HUD_MIRRORED: return "左右互换";
            case HUD_COMPACT: return "紧凑";
            case HUD_CUSTOM: return "自定义";
            default: return "默认";
        }
    }

    public static String zoomName(int level) {
        switch (level) {
            case ZOOM_LOW: return "低";
            case ZOOM_HIGH: return "高";
            default: return "标准";
        }
    }
}
