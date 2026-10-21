package com.xjzb.rts;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Rect;

import java.io.InputStream;

/**
 * End-of-game score panel chrome, decoded from the original
 * glue\ScorePd\*.pcx + iScore.grp by tools/pipeline_score.py.
 *
 *   ui/score/pmain.png     640x480 panel background
 *   ui/score/pinset.png    588x37  title inset strip
 *   ui/score/scorebox.png  96x30   one row's score box
 *   ui/score/untab.png     93x4    tab underline
 *   ui/score/iscore.png    54 glyphs, 8 per row, 28px cells
 *
 * Every bitmap is optional: a missing file just leaves the field null and the
 * caller falls back to the code-drawn panel, so a stripped asset set still
 * runs instead of crashing on the results screen.
 */
public class ScoreAssets {

    public final Bitmap pmain, pinset, scorebox, untab, iscore;
    private static final int ICON_COLS = 8;
    private static final int ICON_CELL = 28;

    public ScoreAssets(Context ctx) {
        pmain = load(ctx, "ui/score/pmain.png");
        pinset = load(ctx, "ui/score/pinset.png");
        scorebox = load(ctx, "ui/score/scorebox.png");
        untab = load(ctx, "ui/score/untab.png");
        iscore = load(ctx, "ui/score/iscore.png");
    }

    private static Bitmap load(Context ctx, String path) {
        try (InputStream in = ctx.getAssets().open(path)) {
            BitmapFactory.Options o = new BitmapFactory.Options();
            o.inPreferredConfig = Bitmap.Config.ARGB_8888;
            return BitmapFactory.decodeStream(in, null, o);
        } catch (Exception e) {
            return null;
        }
    }

    /** Source rect of score glyph `i` inside iscore.png, or null when absent. */
    public Rect iconRect(int i) {
        if (iscore == null || i < 0 || i >= ICON_COLS * (iscore.getHeight() / ICON_CELL))
            return null;
        int cx = (i % ICON_COLS) * ICON_CELL;
        int cy = (i / ICON_COLS) * ICON_CELL;
        return new Rect(cx, cy, cx + ICON_CELL, cy + ICON_CELL);
    }

    public boolean ready() {
        return pmain != null;
    }
}