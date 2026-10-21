package com.xjzb.rts.core;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Rect;

import java.io.InputStream;
import java.util.HashMap;

/**
 * Loads the sprite sheets produced by tools/pipeline_sprites.py and hands out
 * per-frame bitmaps.
 *
 * manifest.txt row: key,kind,walkCount,hasAttack,frames,cols
 *
 *   kind 0 = unit sheet   17 direction columns; rows = walkCount + hasAttack
 *   kind 1 = sheet        `frames` cells laid out `cols` per row
 *   kind 2 = icon         single cell, no team variant
 *
 * kind 1 covers both buildings and multi-frame animations (explosions, death
 * sequences) and the siege tank, whose 6 poses are a flat animation rather
 * than 17 directions.
 *
 * v2.15: DECODE IS LAZY. The v2.9-era bank decoded every manifest row (both
 * team variants) in the constructor, which was survivable at 144 rows but hit
 * ~340 MB of decoded bitmaps once the v2.10-14 roster landed -- past Android's
 * default heap. The failure was silent and devastating on device: BitmapFactory
 * catches its own OutOfMemoryError and returns null, so every row past the
 * heap ceiling simply did not exist. Invisible units ("no enemies"), black
 * terrain ("mission 1 has no map") and identical-looking races on the device
 * were all that one root cause. Now the constructor only parses metadata (and
 * eagerly decodes the tiny command icons the card needs); a sheet decodes on
 * first get() and stays cached. The enemy variant decodes on its own first
 * request instead of always riding along.
 */
public class SpriteBank {

    public static final int KIND_UNIT = 0, KIND_SHEET = 1, KIND_ICON = 2;

    /** Manifest metadata for one not-yet-decoded sheet. */
    private static class Row {
        int kind, walk, atk, frames, cols;
    }

    public static class Sprite {
        public Bitmap sheet;
        public int kind;
        public int fw, fh;          // cell size
        public int cols, rows;
        public int dirs = 1;        // 17 for units
        public int walkRows;        // walk-cycle rows (row = one 17-dir block)
        public int attackRow = -1;  // row index of the attack animation
        public int frames;          // animation frame count (kind 1)
        public boolean team;        // has _b/_r variants
    }

    private final HashMap<String, Row> rows = new HashMap<>();
    /** Decoded sheets, keyed by base key (blue) and key#e (red). A cached
     * null means "tried and missing", so a miss costs one attempt ever. */
    private final HashMap<String, Sprite> sprites = new HashMap<>();
    private final HashMap<String, Bitmap> icons = new HashMap<>();
    private final android.content.Context ctx;

    public SpriteBank(android.content.Context ctx, String manifestCsv) {
        this.ctx = ctx;
        for (String raw : manifestCsv.split("\n")) {
            String line = raw.trim();
            if (line.isEmpty()) continue;
            String[] p = line.split(",");
            if (p.length < 6) continue;
            String key = p[0];
            int kind = Integer.parseInt(p[1]);
            int walk = Integer.parseInt(p[2]);
            int atk = Integer.parseInt(p[3]);
            int frames = Integer.parseInt(p[4]);
            int cols = Integer.parseInt(p[5]);
            if (kind == KIND_ICON) {
                Bitmap b = loadBitmap("sprites/" + key);
                if (b != null) icons.put(key, b);
                continue;
            }
            Row r = new Row();
            r.kind = kind;
            r.walk = walk;
            r.atk = atk;
            r.frames = frames;
            r.cols = cols;
            rows.put(key, r);
        }
    }

    /** Builds the Sprite from a decoded sheet, using the bitmap for geometry
     * (the pipelines guarantee both team variants share the same grid). */
    private Sprite build(String key, Bitmap blue, Row r) {
        Sprite s = new Sprite();
        s.sheet = blue;
        s.kind = r.kind;
        s.team = true;
        if (r.kind == KIND_UNIT) {
            int rws = Math.max(1, r.walk + r.atk);
            s.cols = 17;
            s.rows = rws;
            s.dirs = 17;
            s.fw = blue.getWidth() / 17;
            s.fh = blue.getHeight() / rws;
            s.walkRows = r.walk;
            s.attackRow = r.atk > 0 ? r.walk : -1;
            s.frames = rws * 17;
        } else {
            s.cols = Math.max(1, r.cols);
            s.frames = Math.max(1, r.frames);
            s.rows = (s.frames + s.cols - 1) / s.cols;
            s.fw = blue.getWidth() / s.cols;
            s.fh = blue.getHeight() / s.rows;
        }
        return s;
    }

    /**
     * Returns the sprite for `key`, decoding it on first use. The enemy
     * variant decodes from key_r on its own first request and falls back to
     * the blue sheet when the file is absent (neutral props have no _r).
     */
    public Sprite get(String key, boolean enemy) {
        String cacheKey = enemy ? key + "#e" : key;
        if (sprites.containsKey(cacheKey)) return sprites.get(cacheKey);
        Row r = rows.get(key);
        if (r == null) {
            sprites.put(cacheKey, null);   // known missing
            return null;
        }
        Bitmap b = loadBitmap("sprites/" + key + (enemy ? "_r" : "_b"));
        Sprite s = null;
        if (b != null) {
            s = build(key, b, r);
        } else if (enemy) {
            // no red variant: fall back to whatever the blue side has
            s = get(key, false);
        }
        sprites.put(cacheKey, s);
        return s;
    }

    public boolean has(String key) {
        return rows.containsKey(key) || icons.containsKey(key);
    }

    public Bitmap icon(String name) {
        return icons.get(name);
    }

    /** Cell rect for a unit sheet: direction column, animation row. */
    public Rect unitFrame(Sprite s, int dir, int row, int frame) {
        int col = dir & 15;
        int x = col * s.fw;
        int y = (row * 17 + frame) * s.fh;
        return new Rect(x, y, x + s.fw, y + s.fh);
    }

    /** Cell rect for any kind-1 sheet, by frame index. */
    public Rect frameRect(Sprite s, int index) {
        return frameRect(s, index, new Rect());
    }

    /**
     * v2.43 P1: same cell rect, written into a caller-owned Rect.
     *
     * frameRect is called once per visible sprite per frame -- every unit,
     * corpse, animation, storm, swarm, ensnare and effect -- so the two-int
     * allocation above was a steady stream of garbage on the render thread.
     * Callers that draw one sprite at a time can hand in a scratch Rect and
     * allocate nothing; the allocating overload stays for the one-shot uses
     * (HUD icons, the layout preview) where a single Rect per call is noise.
     */
    public Rect frameRect(Sprite s, int index, Rect out) {
        index = Math.max(0, Math.min(s.frames - 1, index));
        int cx = index % s.cols, cy = index / s.cols;
        out.set(cx * s.fw, cy * s.fh, cx * s.fw + s.fw, cy * s.fh + s.fh);
        return out;
    }

    /**
     * Loads a sprite sheet, preferring the .webp the slimming step writes and
     * falling back to the .png the pipelines emit.
     *
     * OutOfMemoryError is caught beside Exception on purpose: BitmapFactory
     * converts heap exhaustion into a null return on its own in most paths,
     * but a direct allocation failure throws the Error, and one oversized
     * sheet must never take the whole game thread down with it.
     */
    private Bitmap loadBitmap(String pathNoExt) {
        for (String ext : new String[]{".webp", ".png"}) {
            try (InputStream in = ctx.getAssets().open(pathNoExt + ext)) {
                BitmapFactory.Options o = new BitmapFactory.Options();
                o.inPreferredConfig = Bitmap.Config.ARGB_8888;
                return BitmapFactory.decodeStream(in, null, o);
            } catch (Exception ignored) {
            } catch (OutOfMemoryError ignored) {
                android.util.Log.w("XJZB", "OOM decoding " + pathNoExt + ext);
                return null;
            }
        }
        return null;
    }
}
