package com.xjzb.rts;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.HashMap;

/**
 * Console-UI assets extracted from the original MPQs by tools/pipeline_ui.py:
 *
 *   ui/wire/wire_<unitID>.png   wireframe portrait, 64x64, units.dat indexed
 *   ui/unitnames.txt            "<unitID> <official name>" (rez/stat_txt.tbl)
 *
 * All lookups are by units.dat unit id, the same convention the wireframe GRP
 * and stat_txt.tbl use natively.
 */
public class UiAssets {

    private final Context ctx;
    private final HashMap<Integer, Bitmap> wires = new HashMap<>();
    private final HashMap<String, Bitmap> portraits = new HashMap<>();
    private final HashMap<Integer, String> names = new HashMap<>();

    public UiAssets(Context ctx) {
        this.ctx = ctx;
        try (InputStream in = ctx.getAssets().open("ui/unitnames.txt");
             BufferedReader r = new BufferedReader(new InputStreamReader(in, "UTF-8"))) {
            String line;
            while ((line = r.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;
                int sp = line.indexOf(' ');
                if (sp <= 0) continue;
                try {
                    names.put(Integer.parseInt(line.substring(0, sp)), line.substring(sp + 1));
                } catch (NumberFormatException ignored) {
                }
            }
        } catch (Exception ignored) {
        }
    }

    /** Official English unit name from rez/stat_txt.tbl, or null. */
    public String name(int unitId) {
        return names.get(unitId);
    }

    /**
     * Wireframe portrait bitmap, lazily loaded and cached, or null.
     *
     * The portrait is deliberately team-agnostic: wirefram.grp paints itself
     * from its own palette ramp (Terran 192/193+208..211, Zerg 216..219) and
     * never touches the team-colour slots 8..15, so there is no tinted variant
     * to choose between. See tools/pipeline_ui.py.
     */
    public Bitmap wire(int unitId) {
        Bitmap b = wires.get(unitId);
        if (b != null) return b;
        if (wires.containsKey(unitId)) return null;   // known missing
        for (String ext : new String[]{".webp", ".png"}) {
            try (InputStream in = ctx.getAssets().open("ui/wire/wire_" + unitId + ext)) {
                BitmapFactory.Options o = new BitmapFactory.Options();
                o.inPreferredConfig = Bitmap.Config.ARGB_8888;
                b = BitmapFactory.decodeStream(in, null, o);
                break;
            } catch (Exception ignored) {
            }
        }
        wires.put(unitId, b);   // cache misses too, so we try each id once
        return b;
    }

    /**
     * v2.12 batch E: real talking-head portrait, decoded from the Smacker
     * files in portrait\* by tools/pipeline_portraits.py (first frame only --
     * the plan parks full animation in P3).
     *
     * v2.13: the roster grew from the six Brood War units to every unit the
     * game has a type for -- arr/portdata.tbl is the game's own portrait
     * table and its classic entries (tmarine, PZealot, ...) all resolve in
     * StarDat. Campaign-cast dirs (pArtanis, tSam, UFlag9..12) stay excluded.
     * Returns null when the key has none, so callers fall back to the wireframe.
     */
    public Bitmap portrait(String typeKey) {
        if (typeKey == null) return null;
        Bitmap b = portraits.get(typeKey);
        if (b != null) return b;
        if (portraits.containsKey(typeKey)) return null;   // known missing
        // Try both extensions, like wire(): tools/slim_assets.py rewrites every
        // png under assets/ to lossless webp, so hard-coding ".png" here would
        // silently break the portraits the next time the tree is slimmed.
        for (String ext : new String[]{".webp", ".png"}) {
            try (InputStream in = ctx.getAssets().open("ui/portrait/portrait_" + typeKey + ext)) {
                BitmapFactory.Options o = new BitmapFactory.Options();
                o.inPreferredConfig = Bitmap.Config.ARGB_8888;
                b = BitmapFactory.decodeStream(in, null, o);
                break;
            } catch (Exception ignored) {
            }
        }
        portraits.put(typeKey, b);   // cache misses too
        return b;
    }
}
