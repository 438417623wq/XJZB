package com.xjzb.rts;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;
import android.view.MotionEvent;
import android.view.SurfaceHolder;
import android.view.SurfaceView;

import com.xjzb.rts.core.Game;
import com.xjzb.rts.core.Mission;
import com.xjzb.rts.core.SpriteBank;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Renders the world and handles touch input.
 *
 * Touch model:
 *   tap own unit            -> select
 *   tap ground with select. -> move (or harvest/build marker)
 *   tap enemy with select.  -> attack
 *   slide one finger        -> drag the camera (v2.6 #C1)
 *   hold still 250ms + drag -> box select (v2.6 #C3)
 *   drag with two fingers   -> pan camera
 *   pinch                   -> zoom
 *   minimap tap/drag        -> move camera
 *   command buttons         -> train / build / stop
 */
public class GameView extends SurfaceView implements Runnable, SurfaceHolder.Callback {

    private Game game;
    private final SpriteBank bank;
    private final MapData map;
    private volatile boolean running;
    private Thread thread;

    // v2.44: FILTER_BITMAP on the sprite paint. The terrain chunks have always
    // drawn through chunkPaint's FILTER_BITMAP_FLAG, but every unit, building
    // and effect went through this paint without it -- so at any zoom below or
    // above 1.0 the sprites were point-sampled and crawled with jaggies, which
    // reads as "the units look rough" next to the smooth terrain. Bilinear
    // filtering costs nothing measurable and only affects drawBitmap calls;
    // the ovals, bars and hairlines this paint also draws are untouched.
    private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG
            | Paint.FILTER_BITMAP_FLAG);
    /**
     * v2.42 fix (defect B, "black bar while panning").
     *
     * These three are the RENDERER's camera and are written by the render thread
     * alone. The touch thread never writes them; it publishes its intent into
     * the in* mirrors below and render() adopts that once, at the top of the
     * frame.
     *
     * Why: render() converts a coordinate hundreds of times per frame (once per
     * chunk dst, per entity, per HUD widget) by reading these fields directly.
     * When the touch thread wrote them concurrently, a single frame became a
     * MOSAIC of strips drawn at different cameras -- the chunk dsts stopped
     * tiling and bare canvas showed through between them. That gap IS the black
     * bar: the clear colour is rgb(6,8,12), which reads as black on a phone and
     * turns bright green under the render diagnostic.
     *
     * The touch path deliberately still READS camX/camY/zoom (not its own in*
     * mirrors) wherever it hit-tests, so a tap lands where the player sees it on
     * the last drawn frame rather than where the finger has since dragged to.
     */
    private volatile float camX, camY, zoom = 1.3f;
    /**
     * Camera intent published by the touch thread (and by the construction /
     * restart / settings paths, which run on the UI thread). render() adopts it
     * once per frame, which is what makes a frame internally consistent.
     */
    private volatile float inCamX, inCamY, inZoom = 1.3f;
    /** True while in* holds a value render() has not adopted yet. */
    private volatile boolean camDirty;

    /** The camera the touch thread should compute its next delta from. */
    private float tCamX() { return camDirty ? inCamX : camX; }
    private float tCamY() { return camDirty ? inCamY : camY; }
    private float tZoom() { return camDirty ? inZoom : zoom; }

    /**
     * Publish a camera move from the touch side (absolute, in world px).
     *
     * The value is clamped here, exactly as render() clamps the camera it
     * adopts. That matters: the touch side computes its next delta from
     * tCamX(), so an unclamped publish would let a drag that overshoots the map
     * edge pile up invisible overshoot, and the finger would then have to
     * unwind all of it before the view moved back.
     */
    private void tPanTo(float x, float y) {
        ensureHud();
        float halfW = hud.halfW;
        float z = tZoom();
        float halfTop = hud.centerY / z;
        float halfBot = (getHeight() - hud.centerY) / z;
        inCamX = Game.clamp(x, halfW, Math.max(halfW, game.wPx - halfW));
        inCamY = Game.clamp(y, halfTop, Math.max(halfTop, game.hPx - halfBot));
        camDirty = true;
    }

    /** Publish a relative camera move from the touch side. */
    private void tPanBy(float dx, float dy) {
        tPanTo(tCamX() + dx, tCamY() + dy);
    }

    /** Publish a camera jump from the touch side. */
    private void tCenterOn(float x, float y) {
        tPanTo(x, y);
    }

    /** Publish a zoom change from the touch side. */
    private void tZoomTo(float z) {
        inZoom = z;
        camDirty = true;
    }

    /**
     * Adopt a new zoom preset from the UI side. Both copies are written so the
     * renderer and the touch path agree immediately; a pending pan in inCamX/Y
     * is deliberately left alone, since it is still a legal camera position and
     * render() will adopt and re-clamp it on the next frame.
     */
    private void setZoomNow(float z) {
        zoom = z;
        inZoom = z;
    }

    /**
     * Set the camera outright from the UI/constructor side (fresh match, restart,
     * zoom preset). Both the renderer's fields and the intent mirrors are
     * written, and camDirty is cleared, so the two can never disagree about
     * where the camera starts.
     */
    private void setCameraNow(float x, float y, float z) {
        camX = inCamX = x;
        camY = inCamY = y;
        zoom = inZoom = z;
        camDirty = false;
    }
    // v2.18 batch B: the zoom preset. Default/floor/ceiling all scale with
    // Settings.zoomLevel, so the "small units must stay readable" floor (1.0)
    // can never be zoomed away. ZOOM_MAX stays 2.0 at the standard preset.
    private float zoomMin() { return Settings.zoomMin(settings.zoomLevel); }
    private float zoomMax() { return Settings.zoomMax(settings.zoomLevel); }


    // ---- feedback / hud state (only ever touched on the game thread)
    private String toast;                    // red banner text, console top
    private float toastT;
    private float alertFlash;                // minimap under-attack pulse 0..1
    /** v2.22 batch C: medic-heal voice throttle (seconds until next allowed). */
    private float healSndT;
    /** World point of the last under-attack alert; minimap jump target. */
    private float alertX = -1, alertY = -1;
    private final List<float[]> flashes = new ArrayList<>();   // x,y,life
    private boolean paused;
    private float volume = 1f;   // mirror of Settings.volume; see applySettings()
    private Bitmap fogBmp;                   // 1px/tile, bilinear-upscaled
    private int[] fogPix;
    /** v2.42 batch B: chunk keys this frame draws; the map LRU never evicts these. */
    private final java.util.HashSet<String> keepAlive = new java.util.HashSet<>();
    /** v2.42 batch B: render-diagnostic log throttle. */
    private int diagFrame;
    /** v2.42: caps the per-frame miss log so a long slide cannot flood logcat. */
    private int diagMissLog;
    // v2.42: the on-screen diagnostic readout. logcat is useless for a bug you
    // have to SEE: the bar vanishes the moment the fling ends, so the panel
    // latches the worst frame and keeps showing it after the motion stops --
    // the numbers stay on screen long enough to be photographed.
    /** Misses in the frame currently being drawn. */
    private int diagMissNow;
    /** Largest miss count seen since the readout was last cleared. */
    private int diagMissPeak;
    /** Chunk keys of the frame that produced diagMissPeak. */
    private String diagPeakKeys = "";
    /** Camera/zoom of the frame that produced diagMissPeak. */
    private String diagPeakCam = "";
    /** Frames drawn since the peak, so the panel can say how stale it is. */
    private int diagPeakAge;
    /** Frames since the last frame that missed anything; resets the peak. */
    private int diagCalmFrames;
    /** Rolling tail of miss frames, newest last, shown in the on-screen panel. */
    private final java.util.ArrayDeque<String> diagLog = new java.util.ArrayDeque<>();

    // ---- v2.43 perf instrumentation ------------------------------------
    //
    // The stutter complaint ("很强的顿挫感") has two very different causes and
    // they need different fixes: a steady O(N^2) tax in Game.update, and a
    // one-frame spike when the AI publishes a wave (dozens of A* runs in a
    // single tick). Guessing between them wastes a build cycle each time, so
    // update and render are timed SEPARATELY and the numbers go both to the
    // on-screen diagnostic panel and to logcat every two seconds.
    //
    // Samples live in fixed-size ring buffers (no allocation per frame): the
    // average/max/p95 readout is derived from them once per log interval.
    private static final int PERF_N = 120;
    private final float[] perfUpd = new float[PERF_N];
    private final float[] perfRen = new float[PERF_N];
    private final float[] perfFrm = new float[PERF_N];
    private int perfHead;
    private int perfCount;
    /** Seconds until the next [perf] summary line. */
    private float perfLogT = 2f;
    /** Last computed summary, kept for the on-screen panel. */
    private volatile String perfLine = "";
    private volatile String perfLine2 = "";
    /** Copy for the sort in perfSummary(); reused so the summary is alloc-free. */
    private final float[] perfTmp = new float[PERF_N];

    // ---- v2.43 P1: scratch rects for the render hot path ----------------
    //
    // Every visible sprite per frame used to allocate two Rects (src + dst):
    // with a full screen of units, corpses, animations, storms, swarms and
    // effects that is a few hundred short-lived objects per frame, all of them
    // exactly the shape the GC collects for free and the frame budget pays for.
    //
    // These four are reused instead. The rule that keeps them safe: a scratch
    // Rect is only valid until the next draw call that also wants one, so a
    // site may hold one across a drawBitmap (which does not touch them) but
    // never across a call that draws something else. Sites that genuinely need
    // two live rects at once (src + dst in one drawBitmap) use different
    // scratch fields -- hence more than one.
    //
    // Render-thread only, like everything else in render().
    private final Rect tmpSrc = new Rect();
    private final Rect tmpDst = new Rect();
    private final Rect tmpDst2 = new Rect();

    // ---- v2.43 P2: viewport culling --------------------------------------
    //
    // The world loops (ents, corpses, minerals, shots, anims, effects) walked
    // every object on the map and computed sx()/sy() for each one, then threw
    // the result away if it landed off-screen. A 2048x2048 map shows roughly
    // 1670x770 world px at the default zoom, so most of a busy map was being
    // transformed and clipped for nothing.
    //
    // The gate below throws those away before any draw call.
    //
    // It takes the object's ACTUAL extents rather than a fixed margin, because
    // the extents in this game span two orders of magnitude: a marine cell is
    // 128 px while an explosion cell (plasma, bang_l, nukehit) is up to 256 px
    // and animations draw at up to 1.4x scale, so a single magic radius is
    // either too small (clipped explosions, which reads as puffs vanishing at
    // the screen edge) or so large that it culls nothing.
    //
    // Where the sprite is already in hand (minerals, corpses, anims) the extents
    // come from the cell itself. Live entities use MAX_CELL instead: resolving
    // their sprite would mean a bank.get() per entity per frame, and that
    // lookup builds a "#e" cache key String for every enemy on the map -- the
    // exact per-frame allocation this release is removing. MAX_CELL is a hair
    // conservative for small units, which costs a little culling and can never
    // clip anything.
    //
    // The vertical extents are asymmetric on purpose: drawEnt and drawSingle
    // both anchor a sprite at -0.65h / +0.35h, so most of a sprite sits ABOVE
    // its world position. A cull that assumed symmetry would drop tall sprites
    // whose base is just off the bottom edge.
    //
    // Scans and nukes are deliberately NOT culled: they are at most a couple of
    // objects, and their radius is 384 world px (over 900 screen px at max
    // zoom), so a gate wide enough for them would cull nothing anyway.
    //
    // Culling is a pure draw-time decision: it reads the camera and the
    // object's position, never writes anything, so it cannot affect the
    // lockstep simulation.
    /** Surface size of the frame being drawn, set once at the top of render(). */
    private int frameW, frameH;

    /**
     * Widest sprite cell in sprites/manifest.txt (plasma, 256x256). Nothing
     * drawn at a world position is wider than this, so it is a safe bound for
     * anything whose sprite has not been resolved yet.
     */
    private static final float MAX_CELL = 256f;

    // ---- v2.43 P2: fog bitmap throttle ------------------------------------
    //
    // updateFogBitmap() rebuilt the 1px/tile fog bitmap and re-uploaded the
    // whole texture every frame -- 4096 pixels on divide, 36864 on
    // newgettysburg -- even though the fog array only changes when a unit
    // moves or a scanner sweep lands. Two gates replace that:
    //   * HOK draws no fog at all, so the path is skipped outright (the
    //     bitmap is not even built, and neither the world nor the minimap
    //     blits it -- in HOK the old bitmap was all-transparent, so skipping
    //     the blit is what drawing it already did, minus the blend).
    //   * SC keeps the bitmap but rebuilds it at most 10x/s. The overlay is a
    //     soft haze that fades over hundreds of milliseconds, so a 100 ms step
    //     is invisible, and the minimap shares the same bitmap so both stay
    //     consistent with each other.
    private static final float FOG_REBUILD_INTERVAL = 0.1f;
    /** game.time of the last rebuild; negative forces one on the first frame. */
    private float fogBuiltAt = -1f;

    private final Paint fogPaint = new Paint(Paint.FILTER_BITMAP_FLAG);
    private final Paint brightPaint = new Paint(Paint.FILTER_BITMAP_FLAG);
    /**
     * v2.42 batch B: terrain chunks draw through their own paint with bilinear
     * filtering. The shared `p` has no filter flag, so every chunk upscale was
     * nearest-neighbour -- the rasterizer family behind the hairline seams the
     * 1px bleed papered over (v2.21). Bilinear makes the seam family impossible
     * regardless of how the camera lands on the pixel grid.
     */
    private final Paint chunkPaint = new Paint(Paint.FILTER_BITMAP_FLAG);
    private final android.graphics.DashPathEffect dash =
            new android.graphics.DashPathEffect(new float[]{8, 6}, 0);

    // control groups 1..3 — the groups themselves live in Game (save/load and
    // JVM tests need them); only the press timestamps stay view-side
    private final List<Long> groupDownAt = new ArrayList<>();

    // edge scrolling (batch-2 #9)
    private boolean touching;
    private boolean multiTouch;
    private float touchX, touchY;
    private long touchDownAt;

    // input state
    private float downX, downY, lastX, lastY, last2X, last2Y;
    private float pinchStart;
    private boolean boxing, panning;
    private float boxX0, boxY0, boxX1, boxY1;
    private long lastTapTime;
    private float lastTapX, lastTapY;
    /**
     * v2.6 #C: the press can still turn into a box select (it has neither
     * travelled past the slop nor been pre-empted by the HUD). Cleared the
     * moment the gesture becomes a camera drag.
     */
    private boolean longPressReady;
    /** True once the press has travelled past the slop and is panning. */
    private boolean dragging;
    /**
     * Slop for "is this a tap or a drag", in px.
     *
     * v2.7 batch 7.2: this used to be a hardcoded 8dp whose comment admitted it
     * wanted retuning on real hardware. It now reads the persisted
     * Settings.dragSlopDp, so the player can retune it without a rebuild.
     */
    private float dragSlopPx() {
        return dp(settings.dragSlopDp);
    }
    private static final float PING_LIFE = 0.45f;
    /** Expanding ring drawn at the press point when the box select arms. */
    private float pingX, pingY, pingT;

    // ui
    private Rect minimapRect = new Rect();
    /** v2.19 batch C: the one generation point for the console geometry. */
    private final HudLayout hud = new HudLayout();
    private boolean hudComputed;
    /**
     * Where the selection panel was actually drawn last frame; empty when
     * nothing is selected. inHud() consults this so the unselected strip stays
     * tappable as map instead of becoming a see-through dead zone (v2.5 #4).
     */
    /** The drawn selection-info surface. Empty when nothing is selected -- the
     *  control-group block hit-tests through hud.groups since v2.42. */
    private final RectF infoPanelRect = new RectF();
    private final List<Btn> buttons = new java.util.concurrent.CopyOnWriteArrayList<>();
    private volatile String buildKey = null;      // pending building placement
    /** v2.19 batch 5: non-null while this view is a replay, not a match. */
    private final String replayJson;
    /** True while a replay is playing back; game input is blocked. */
    private boolean replayPlaying;
    private final int uiScale;
    private final UiAssets ui;                    // wireframe portraits + stat_txt names
    /** v2.7 batch 7.1: original ScorePd chrome for the end-of-game panel. */
    private final ScoreAssets score;
    /** Title art, reused as the briefing backdrop (v2.7 batch 8). */
    private final Bitmap titleBmp;
    /** v2.7 batch 7.2: persisted player settings (slop, hold, volume, edge). */
    private final Settings settings;

    private android.media.SoundPool sounds;
    private final HashMap<String, Integer> soundIds = new HashMap<>();
    /** Names already reported by play(), so the warning is not spammed per frame. */
    private final java.util.HashSet<String> missingSounds = new java.util.HashSet<>();
    private long lastWhatSound;

    private void initSounds() {
        android.media.AudioAttributes attrs = new android.media.AudioAttributes.Builder()
                .setUsage(android.media.AudioAttributes.USAGE_GAME)
                .setContentType(android.media.AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .build();
        sounds = new android.media.SoundPool.Builder().setMaxStreams(8)
                .setAudioAttributes(attrs).build();
        int loaded = 0;
        for (String n : SOUND_NAMES) {
            try {
                soundIds.put(n, sounds.load(getContext().getAssets().openFd("sounds/" + n + ".wav"), 1));
                loaded++;
            } catch (Exception ex) {
                // v2.12 batch E: this used to be a silent catch, which made a
                // missing asset indistinguishable from a working one -- the race
                // or the menu simply went mute with no evidence anywhere. Every
                // name in SOUND_NAMES must also exist in pipeline_sounds.py's
                // WANT table, so a miss here means those two lists have drifted.
                android.util.Log.w("XJZB", "sound asset missing: sounds/" + n + ".wav");
            }
        }
        android.util.Log.i("XJZB", "sounds loaded " + loaded + "/" + SOUND_NAMES.length);
    }

    // ------------------------------------------------------------------ music
    // Looping BGM from assets/music/ (first track alphabetically). This repack's
    // MPQs carry no music tracks -- see tools/probe_music4.py, every >=300KB
    // block is a tileset VR4, a Smacker video or a voice WAV -- so the folder is
    // empty by default and the player silently no-ops. Dropping any .ogg/.wav
    // into assets/music/ turns the toggle on without further code.
    private android.media.MediaPlayer bgm;
    private boolean bgmOn = true;
    private String bgmTrack = "(无)";

    private void startBgm() {
        if (!bgmOn) return;
        try {
            String[] list = getContext().getAssets().list("music");
            if (list == null || list.length == 0) {
                bgmTrack = "(无曲目)";
                return;
            }
            java.util.Arrays.sort(list);
            if (bgm == null) {
                bgm = new android.media.MediaPlayer();
                bgm.setAudioAttributes(new android.media.AudioAttributes.Builder()
                        .setUsage(android.media.AudioAttributes.USAGE_GAME)
                        .setContentType(android.media.AudioAttributes.CONTENT_TYPE_MUSIC)
                        .build());
                android.content.res.AssetFileDescriptor fd =
                        getContext().getAssets().openFd("music/" + list[0]);
                bgm.setDataSource(fd.getFileDescriptor(), fd.getStartOffset(), fd.getLength());
                fd.close();
                bgm.setLooping(true);
                bgm.prepare();
                bgmTrack = list[0];
            }
            if (!bgm.isPlaying()) bgm.start();
        } catch (Exception ignored) {
            bgmTrack = "(不可用)";
        }
    }

    private void stopBgm() {
        if (bgm != null && bgm.isPlaying()) bgm.pause();
    }

    private void applyBgmVolume() {
        if (bgm != null) bgm.setVolume(volume, volume);
    }

    /** Releases the BGM player; called when the view is torn down. */
    public void releaseBgm() {
        if (bgm != null) {
            try {
                bgm.release();
            } catch (Exception ignored) {
            }
            bgm = null;
        }
    }

    /** Every voice line tools/pipeline_sounds.py writes. */
    private static final String[] SOUND_NAMES = {
            "build", "explo_sm", "explo_md", "explo_lg", "error", "click",
            "scv_ready", "scv_what", "scv_ack", "scv_die",
            "marine_ready", "marine_what", "marine_ack", "marine_die",
            "firebat_ready", "firebat_what", "firebat_ack", "firebat_die",
            "vulture_ready", "vulture_what", "vulture_ack",
            "tank_ready", "tank_what", "tank_ack", "tank_die",
            "zergling_ready", "zergling_what", "zergling_ack", "zergling_die",
            "hydra_ready", "hydra_what", "hydra_ack", "hydra_die",
            "muta_ready", "muta_what", "muta_ack", "muta_die",
            "drone_ready", "zerg_error",
            // v2.10 protoss. Extracted by tools/pipeline_sounds.py; the names
            // must match its WANT table exactly or initSounds silently loads
            // nothing and the race is mute. Dark archon has no death line --
            // the retail listfile only ships rdy/wht/pss for it.
            "probe_ready", "probe_what", "probe_ack", "probe_die",
            "zealot_ready", "zealot_what", "zealot_ack", "zealot_die",
            "dragoon_ready", "dragoon_what", "dragoon_ack", "dragoon_die",
            "templar_ready", "templar_what", "templar_ack", "templar_die",
            "dtemplar_ready", "dtemplar_what", "dtemplar_ack", "dtemplar_die",
            "archon_ready", "archon_what", "archon_ack", "archon_die",
            "darchon_ready", "darchon_what", "darchon_ack",
            "scout_ready", "scout_what", "scout_ack", "scout_die",
            "corsair_ready", "corsair_what", "corsair_ack", "corsair_die",
            "carrier_ready", "carrier_what", "carrier_ack", "carrier_die",
            "shuttle_ready", "shuttle_what", "shuttle_ack", "shuttle_die",
            "arbiter_ready", "arbiter_what", "arbiter_ack", "arbiter_die",
            "reaver_ready", "reaver_what", "reaver_ack", "reaver_die",
            "observer_ready", "observer_what", "observer_ack", "observer_die",
            "protoss_error",
            // v2.12 batch E: the front-end "glue" interface sounds, extracted
            // from arr\sfxdata.tbl's glue group by tools/pipeline_sounds.py.
            // ui_click is the 15 KB glue\mousedown2; the panel whooshes are
            // glue\swishin / glue\swishout, and the end-of-game panel is
            // glue\scorefill / glue\scorefillend. The names here must match
            // that WANT table or initSounds silently loads nothing.
            //
            // ui_countdown and ui_hover are extracted but deliberately have no
            // call site: retail plays glue\countdown.wav in the 3-2-1 before a
            // networked match, and glue\mouseover.wav needs a pointer to hover
            // with. This port has neither, and wiring them to something
            // invented would be worse than leaving them unused.
            "ui_click", "ui_hover", "ui_swishin", "ui_swishout",
            "ui_countdown", "ui_scorefill", "ui_scoreend",
            // v2.22 batch C: the four units whose lines sat extracted-but-
            // unpacked since the v2.9 sweep. medic_heal rides the heal beam,
            // lurker_burrow the burrow/unburrow morph.
            "medic_ready", "medic_what", "medic_ack", "medic_die", "medic_heal",
            "valkyrie_ready", "valkyrie_what", "valkyrie_ack", "valkyrie_die",
            "lurker_ready", "lurker_what", "lurker_ack", "lurker_die",
            "lurker_burrow",
            "devourer_ready", "devourer_what", "devourer_ack", "devourer_die",
    };

    private void play(String name, float vol) {
        Integer id = soundIds.get(name);
        if (sounds != null && id != null) {
            sounds.play(id, vol * volume, vol * volume, 1, 0, 1f);
        } else if (missingSounds.add(name)) {
            // once per name, so a mistyped play() call site is visible in logcat
            // instead of silently doing nothing (v2.12 batch E).
            android.util.Log.w("XJZB", "play() for unknown sound: " + name);
        }
    }

    /** Voice-line prefix per unit type (matches the extracted sound names). */
    private static String voicePrefix(String typeKey) {
        switch (typeKey) {
            case "scv": return "scv";
            case "marine": return "marine";
            case "firebat": return "firebat";
            case "vulture": return "vulture";
            case "tank":
            case "stank": return "tank";
            case "zergling": return "zergling";
            case "hydra": return "hydra";
            case "muta": return "muta";
            case "drone": return "drone";
            // v2.10 protoss. Prefixes match the WANT names in
            // tools/pipeline_sounds.py. Reaver's line is filed under the
            // original's unit name (TRILOBYTE), and observer's under Witness;
            // both are mapped to the gameplay key here rather than renaming the
            // extracted files, so the pipeline stays a faithful copy of the
            // retail asset names.
            case "probe": return "probe";
            case "zealot": return "zealot";
            case "dragoon": return "dragoon";
            case "templar": return "templar";
            case "dtemplar": return "dtemplar";
            case "archon": return "archon";
            case "darchon": return "darchon";
            case "scout": return "scout";
            case "corsair": return "corsair";
            case "carrier": return "carrier";
            case "shuttle": return "shuttle";
            case "arbiter": return "arbiter";
            case "reaver": return "reaver";
            case "observer": return "observer";
            // v2.22 batch C: the four units that were extracted but unpacked.
            // The burrowed lurker speaks with the mobile form's voice.
            case "medic": return "medic";
            case "valkyrie": return "valkyrie";
            case "lurker":
            case "lurker_bur": return "lurker";
            case "devourer": return "devourer";
            default: return null;
        }
    }

    private void playWhat(Game.Ent e) {
        long now = System.currentTimeMillis();
        if (now - lastWhatSound < 350) return;
        lastWhatSound = now;
        String p = voicePrefix(e.type.key);
        if (p != null) play(p + "_what", 0.8f);
    }

    private void playAck(Game.Ent e) {
        String p = voicePrefix(e.type.key);
        if (p != null) play(p + "_ack", 0.8f);
    }

    private void playDie(String typeKey) {
        String p = voicePrefix(typeKey);
        if (p != null) play(p + "_die", 0.8f);
    }

    private void playReady(String key) {
        String p = voicePrefix(key);
        if (p != null) play(p + "_ready", 0.9f);
    }

    private static class Btn {
        RectF r;
        String action;   // "move","attack","stop","build:cc","train:marine",...
        String label;
        Bitmap icon;
    }

    public GameView(Context ctx, String mapId, int difficulty) {
        this(ctx, mapId, difficulty, null, "terran");
    }

    /** v2.7 batch 8: campaign constructor. `missionJson` may be null. */
    public GameView(Context ctx, String mapId, int difficulty, String missionJson) {
        this(ctx, mapId, difficulty, missionJson, "terran");
    }

    /**
     * v2.8: race-aware constructor. The race has to reach Game before it builds
     * the opening base, so it is a constructor argument rather than a field set
     * afterwards.
     */
    public GameView(Context ctx, String mapId, int difficulty, String missionJson,
                    String race) {
        this(ctx, mapId, difficulty, missionJson, race, null);
    }

    /** v2.19 batch 5: replay playback. `replayJson` null/empty means a live match. */
    public GameView(Context ctx, String mapId, int difficulty, String missionJson,
                    String race, String replayJson) {
        super(ctx);
        getHolder().addCallback(this);
        setFocusable(true);
        // v2.20 batch 5: a replay re-simulates the exact match it was recorded
        // from, so the header's map/race/difficulty win over whatever the
        // launcher passed. A deterministic re-run needs all three to match.
        if (replayJson != null && !replayJson.isEmpty()) {
            String hm = replayHeaderValue(replayJson, "map");
            String hr = replayHeaderValue(replayJson, "race");
            String hd = replayHeaderValue(replayJson, "difficulty");
            if (hm != null && !hm.isEmpty()) mapId = hm;
            if (hr != null && !hr.isEmpty()) race = hr;
            if (hd != null) {
                try { difficulty = Integer.parseInt(hd); } catch (Exception ignored) { }
            }
        }
        bank = new SpriteBank(ctx, readAsset(ctx, "sprites/manifest.txt"));
        map = MapData.load(ctx, mapId);
        ui = new UiAssets(ctx);
        score = new ScoreAssets(ctx);
        settings = new Settings(ctx);
        titleBmp = loadBitmap(ctx, "ui/title.webp", "ui/title.png");
        game = new Game(map.w, map.h, map.walk, map.elev, map.starts, map.units, race);
        // v2.29: hand the mission engine the map's meta.txt so an economy
        // mission can rebuild the resource rows setMission clears.
        game.mapMeta = map.metaText;
        game.difficulty = difficulty;
        camX = map.starts.size() > 0 ? map.starts.get(0)[0] + 64 : 512;
        camY = map.starts.size() > 0 ? map.starts.get(0)[1] + 64 : 512;
        // v2.42 fix (defect B): publish the start camera into the intent mirrors
        // too, so the first render adopts exactly this and not a stale one.
        inCamX = camX;
        inCamY = camY;
        uiScale = getResources().getDisplayMetrics().density > 1.5f ? 2 : 1;
        initSounds();
        applySettings();
        Mission m = missionJson == null ? null : Mission.parse(missionJson);
        this.missionJson = missionJson;
        if (m != null) {
            game.setMission(m);
            mission = m;
            briefing = new ArrayList<>(m.briefing);
            briefingOpen = !briefing.isEmpty();
        }
        // v2.37: a LAN match binds the socket session to this Game. The session
        // was installed by the lobby (a Socket cannot ride an Intent), so the
        // match only has to attach it and let the loop drive it. The lockstep
        // player index comes from the lobby, and the map/race/seed come from the
        // handshake both peers already agreed on.
        com.xjzb.rts.net.NetSession.Config ncfg = com.xjzb.rts.net.NetSession.config();
        if (ncfg != null && com.xjzb.rts.net.NetSession.link() != null) {
            net = new com.xjzb.rts.core.LockstepPeer(game, ncfg.localPlayer,
                    ncfg.players, com.xjzb.rts.net.NetSession.link());
            com.xjzb.rts.net.NetSession.bind(net);
            toast = ncfg.host ? "联机对战(你是房主)" : "联机对战";
            toastT = 3.0f;
        }
        // v2.19 batch 5: every match records its orders so it can be replayed.
        this.replayJson = replayJson;
        game.mapId = mapId;
        game.recording = replayJson == null || replayJson.isEmpty();
        if (!game.recording) {
            game.loadReplay(replayJson);
            replayPlaying = true;
            toast = "回放中(输入已禁用)";
            toastT = 3.0f;
        }
    }

    /**
     * v2.20 batch 5: one value out of a replay header ("map X race Y ...").
     * Kept tiny and tolerant -- a header line this build does not know simply
     * yields null and the launcher's argument stands.
     */
    private static String replayHeaderValue(String json, String key) {
        if (json == null) return null;
        for (String line : json.split("\\n")) {
            String[] tok = line.trim().split(" ");
            for (int i = 0; i + 1 < tok.length; i++) {
                if (key.equals(tok[i])) return tok[i + 1];
            }
        }
        return null;
    }

    /** First of the candidate asset paths that decodes, or null. */
    private static Bitmap loadBitmap(Context ctx, String... paths) {
        for (String path : paths) {
            try (InputStream in = ctx.getAssets().open(path)) {
                BitmapFactory.Options o = new BitmapFactory.Options();
                o.inPreferredConfig = Bitmap.Config.ARGB_8888;
                Bitmap b = BitmapFactory.decodeStream(in, null, o);
                if (b != null) return b;
            } catch (Exception ignored) {
            }
        }
        return null;
    }

    /**
     * v2.20 batch 5: read a replay the player saved from a match. The main
     * menu names them replay_<mapId>.txt in the app's files dir; the name it
     * hands over already carries the "replay_" prefix.
     */
    public static String readLocalReplay(Context ctx, String name) {
        try (java.io.BufferedReader r = new java.io.BufferedReader(
                new java.io.InputStreamReader(new java.io.FileInputStream(
                        new java.io.File(ctx.getFilesDir(), name)), "UTF-8"))) {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = r.readLine()) != null) sb.append(line).append('\n');
            return sb.toString();
        } catch (Exception e) {
            return null;
        }
    }

    public static String readAsset(Context ctx, String path) {
        try (InputStream in = ctx.getAssets().open(path);
             BufferedReader r = new BufferedReader(new InputStreamReader(in, "UTF-8"))) {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = r.readLine()) != null) sb.append(line).append('\n');
            return sb.toString();
        } catch (Exception e) {
            return "";
        }
    }

    /** Static map data loaded from assets/maps/<id>/ */
    public static class MapData {
        public String id;
        public int w, h;
        public boolean[] walk;
        /**
         * v2.23 batch C: per-minitile ground level (0 low / 1 mid / 2 high),
         * loaded from maps/<id>/elev.bin.gz next to the walk map. Null when the
         * map ships none, which turns the elevation miss rule into a no-op.
         */
        public byte[] elev;
        public List<int[]> starts = new ArrayList<>();
        public List<Object[]> units = new ArrayList<>();
        /**
         * v2.29: the map's raw meta.txt. A mission with "economy": true has
         * Game re-parse this for its resource rows, so the level gets the
         * map's real mineral layout rather than a hand-copied coordinate list
         * that drifts from the asset the moment the map is rebuilt.
         */
        public String metaText = "";
        /**
         * v2.42 batch B: the chunk keys the current frame draws. The LRU
         * eviction consults this before removing the eldest entry, so the
         * prefetch ring can never push a visible chunk out of a full cache
         * (a 24-cap device carries visible+ring above the cap during a pan).
         * Swapped once per frame by the render thread; read by decode threads.
         */
        public volatile java.util.Set<String> keepAlive;
        public java.util.LinkedHashMap<String, Bitmap> chunks =
                new java.util.LinkedHashMap<String, Bitmap>(16, 0.75f, true) {
            protected boolean removeEldestEntry(Map.Entry<String, Bitmap> eldest) {
                if (size() <= chunkCap) return false;
                java.util.Set<String> keep = keepAlive;
                return keep == null || !keep.contains(eldest.getKey());
            }
        };
        public Bitmap minimap;

        // ---- v2.17 terrain-chunk async pipeline
        /**
         * The old code decoded a chunk synchronously on the render thread on
         * first sight (10-30 ms, a dropped frame while the camera is being
         * dragged) and, when BitmapFactory returned null (it swallows OOM),
         * render simply skipped the tile and left a 512x512 black hole. Both
         * failure modes are gone now: a miss returns null immediately, the
         * renderer draws the magnified minimap as a placeholder, and the real
         * chunk is decoded on a background thread and dropped into the cache
         * when it is ready.
         */
        public int chunkCap = 24;
        private final Object chunkLock = new Object();
        private final java.util.HashSet<String> pending = new java.util.HashSet<>();
        private java.util.concurrent.ExecutorService decodePool;
        private Context ctx;

        /** Lazily create the daemon decode pool (daemon so it never pins the VM). */
        private void ensurePool() {
            if (decodePool != null) return;
            // v2.23 batch C #2: three decode threads, not two. Two concurrent
            // chunk decodes queued up on a fast fling and the third visible
            // tile stayed a placeholder; three keeps a fling's worth of work
            // from serialising. The cache cap (chunkCap) is unchanged, so the
            // memory budget is the same.
            decodePool = java.util.concurrent.Executors.newFixedThreadPool(3, r -> {
                Thread t = new Thread(r, "xjzb-chunk");
                t.setDaemon(true);
                return t;
            });
        }

        static MapData load(Context ctx, String id) {
            MapData m = new MapData();
            m.id = id;
            String meta = readAsset(ctx, "maps/" + id + "/meta.txt");
            m.metaText = meta == null ? "" : meta;
            for (String line : meta.split("\n")) {
                line = line.trim();
                if (line.startsWith("w=")) m.w = Integer.parseInt(line.substring(2));
                else if (line.startsWith("h=")) m.h = Integer.parseInt(line.substring(2));
                else if (line.startsWith("start=")) {
                    String[] p = line.substring(6).split(",");
                    m.starts.add(new int[]{Integer.parseInt(p[0]), Integer.parseInt(p[1])});
                } else if (line.startsWith("unit=")) {
                    String[] p = line.substring(5).split(",");
                    int u = Integer.parseInt(p[0]);
                    float x = Float.parseFloat(p[1]), y = Float.parseFloat(p[2]);
                    int variant = p.length > 5 ? Integer.parseInt(p[5]) : 0;
                    m.units.add(new Object[]{u, x, y, variant});
                }
            }
            m.walk = loadWalk(ctx, id, m.w * 4 * m.h * 4);
            if (m.walk == null) {
                // Silent all-walkable fallback: if the asset pipeline ever
                // renames the compressed walk map again, units would path
                // straight through cliffs with no visible error. Say so.
                android.util.Log.w("XJZB", "no walk map for map '" + id
                        + "'; falling back to fully walkable");
                m.walk = new boolean[m.w * 4 * m.h * 4];
                java.util.Arrays.fill(m.walk, true);
            }
            m.elev = loadElev(ctx, id, m.w * 4 * m.h * 4);
            m.minimap = decodeAsset(ctx, "maps/" + id + "/minimap");
            // v2.17: size the terrain-chunk cache from the device heap class.
            // 256 MB class phones hold 48 chunks (~12 MB as RGB_565); smaller
            // devices stay at the old 24 so the cache cannot crowd the heap.
            int memClass = 0;
            try {
                android.app.ActivityManager am = (android.app.ActivityManager)
                        ctx.getSystemService(Context.ACTIVITY_SERVICE);
                if (am != null) memClass = am.getMemoryClass();
            } catch (Exception ignored) {
            }
            m.chunkCap = memClass >= 256 ? 48 : 24;
            m.ctx = ctx.getApplicationContext();
            return m;
        }

        /**
         * Walkability, gzipped in the source tree (a 256 KB raw bitmap
         * collapses to ~10 KB). tools/slim_assets.py names the compressed form
         * "walk.bin.gz" and deletes the original.
         *
         * In the APK it arrives as a plain "walk.bin": AGP's asset merge
         * transparently gunzips any .gz asset and strips the extension, which
         * was confirmed by round-tripping a test file. So the fallback below
         * is the path that actually feeds the shipped game, and "walk.bin.gz"
         * only matters for an unslimmed/raw asset tree. Both names are tried
         * so neither layout can silently degrade to the all-walkable default.
         */
        static boolean[] loadWalk(Context ctx, String id, int expect) {
            byte[] raw = null;
            for (String name : new String[]{"walk.bin.gz", "walk.gz"}) {
                raw = readAssetBytes(ctx, "maps/" + id + "/" + name);
                if (raw != null) break;
            }
            if (raw != null) {
                try (java.util.zip.GZIPInputStream gz =
                             new java.util.zip.GZIPInputStream(new java.io.ByteArrayInputStream(raw))) {
                    byte[] out = new byte[expect];
                    int off = 0, n;
                    while (off < out.length && (n = gz.read(out, off, out.length - off)) > 0)
                        off += n;
                    if (off == out.length) {
                        boolean[] w = new boolean[out.length];
                        for (int i = 0; i < out.length; i++) w[i] = out[i] != 0;
                        return w;
                    }
                } catch (Exception ignored) {
                }
            }
            raw = readAssetBytes(ctx, "maps/" + id + "/walk.bin");
            if (raw == null) return null;
            boolean[] w = new boolean[Math.min(expect, raw.length)];
            for (int i = 0; i < w.length; i++) w[i] = raw[i] != 0;
            return w;
        }

        /**
         * v2.23 batch C: the ground-level bitmap, gzipped like the walk map.
         * Same two-name dance as loadWalk (the source tree carries
         * elev.bin.gz, the APK carries the gunzipped elev.bin), and a missing
         * asset returns null rather than an all-low default -- the Game
         * treats null as "no elevation data", which is the honest answer.
         */
        static byte[] loadElev(Context ctx, String id, int expect) {
            byte[] raw = null;
            for (String name : new String[]{"elev.bin.gz", "elev.gz"}) {
                raw = readAssetBytes(ctx, "maps/" + id + "/" + name);
                if (raw != null) break;
            }
            if (raw != null) {
                try (java.util.zip.GZIPInputStream gz =
                             new java.util.zip.GZIPInputStream(new java.io.ByteArrayInputStream(raw))) {
                    byte[] out = new byte[expect];
                    int off = 0, n;
                    while (off < out.length && (n = gz.read(out, off, out.length - off)) > 0)
                        off += n;
                    if (off == out.length) return out;
                } catch (Exception ignored) {
                }
            }
            raw = readAssetBytes(ctx, "maps/" + id + "/elev.bin");
            if (raw == null) return null;
            byte[] out = new byte[Math.min(expect, raw.length)];
            System.arraycopy(raw, 0, out, 0, out.length);
            return out;
        }

        /** Reads an asset fully, or null. */
        static byte[] readAssetBytes(Context ctx, String path) {
            try (InputStream in = ctx.getAssets().open(path)) {
                java.io.ByteArrayOutputStream bo = new java.io.ByteArrayOutputStream();
                byte[] buf = new byte[8192];
                int n;
                while ((n = in.read(buf)) > 0) bo.write(buf, 0, n);
                return bo.toByteArray();
            } catch (Exception e) {
                return null;
            }
        }

        /**
         * Decode an image asset, preferring the slimmed .webp shipped in the APK
         * and falling back to the .png the pipelines write.
         */
        static Bitmap decodeAsset(Context ctx, String pathNoExt) {
            for (String ext : new String[]{".webp", ".png"}) {
                try (InputStream in = ctx.getAssets().open(pathNoExt + ext)) {
                    return BitmapFactory.decodeStream(in);
                } catch (Exception ignored) {
                }
            }
            return null;
        }

        /**
         * v2.17: decode a terrain chunk to RGB_565. Terrain is opaque (verified
         * against every shipped chunk: none carries real alpha), so halving the
         * bytes-per-pixel lets a 48-chunk cache fit in ~12 MB. Returns null on
         * failure, which the caller must treat as "show the placeholder", never
         * as "draw nothing".
         */
        private Bitmap decodeChunkNow(int cx, int cy) {
            String key = cx + "_" + cy;
            for (String ext : new String[]{".webp", ".png"}) {
                try (InputStream in = ctx.getAssets().open("maps/" + id + "/c_" + key + ext)) {
                    BitmapFactory.Options o = new BitmapFactory.Options();
                    o.inPreferredConfig = Bitmap.Config.RGB_565;
                    Bitmap b = BitmapFactory.decodeStream(in, null, o);
                    if (b != null) return b;
                } catch (Exception ignored) {
                }
            }
            return null;
        }

        /**
         * Render-thread lookup. Never decodes: a miss schedules a background
         * decode and returns null so the caller can draw its placeholder. The
         * decode result is inserted under the lock, and `pending` guarantees a
         * chunk is only ever queued once.
         */
        Bitmap chunk(int cx, int cy) {
            String key = cx + "_" + cy;
            synchronized (chunkLock) {
                Bitmap b = chunks.get(key);
                if (b != null) return b;
                if (pending.contains(key)) return null;
                pending.add(key);
            }
            ensurePool();
            decodePool.execute(() -> {
                Bitmap b = null;
                try {
                    b = decodeChunkNow(cx, cy);
                } catch (Throwable ignored) {
                }
                synchronized (chunkLock) {
                    pending.remove(key);
                    if (b != null) chunks.put(key, b);
                }
            });
            return null;
        }

        /**
         * Background pre-fetch for the ring of chunks just outside the viewport,
         * so a camera drag finds them already resident. Fire-and-forget.
         */
        void prefetch(int cx, int cy) {
            if (cx < 0 || cy < 0 || cx * 512 >= w * 32 || cy * 512 >= h * 32) return;
            String key = cx + "_" + cy;
            synchronized (chunkLock) {
                if (chunks.containsKey(key) || pending.contains(key)) return;
                pending.add(key);
            }
            ensurePool();
            decodePool.execute(() -> {
                Bitmap b = null;
                try {
                    b = decodeChunkNow(cx, cy);
                } catch (Throwable ignored) {
                }
                synchronized (chunkLock) {
                    pending.remove(key);
                    if (b != null) chunks.put(key, b);
                }
            });
        }
    }

    // ------------------------------------------------------------- game loop
    @Override
    public void run() {
        long last = System.nanoTime();
        while (running) {
            long frameStart = System.nanoTime();
            long now = frameStart;
            float dt = (now - last) / 1e9f;
            last = now;
            if (dt > 0.05f) dt = 0.05f;
            long updNs = 0, renNs = 0;
            if (!paused) {
                if (net != null) {
                    // v2.37: a networked match runs the three phases the desktop
                    // harness proved out: take whatever the socket delivered,
                    // publish this turn's report, then step (which no-ops until
                    // every peer has reported). Same shape as tools/TcpLockstep.
                    net.receiveFrame();
                    net.sendFrame();
                    net.stepFrame(dt);
                    // v2.37: if the opponent is gone, end the match instead of
                    // freezing on a turn that will never complete. The timeout
                    // logic was asserted from v2.34 on but nothing called it,
                    // so a departed peer still hung the game on a real device.
                    int gone = net.checkForfeit(com.xjzb.rts.core.Lockstep.STALL_LIMIT);
                    if (gone >= 0 && game.status.isEmpty()) {
                        // The result lives on the Game, not the view: the same
                        // field the score panel and the mission bookkeeping read.
                        game.status = gone == net.player ? "lose" : "win";
                        toast = gone == net.player ? "你已掉线,判负" : "对方已掉线,你获胜";
                        toastT = 4.0f;
                    }
                } else {
                    game.update(dt);
                }
                for (Object[] ev : game.events) {
                    String kind = (String) ev[0];
                    if (kind.equals("dead")) {
                        int tiles = (Integer) ev[1];
                        play(tiles >= 4 ? "explo_lg" : tiles >= 3 ? "explo_md" : "explo_sm", 1f);
                        if (ev.length > 2 && ev[2] != null) playDie((String) ev[2]);
                    } else if (kind.equals("trained")) {
                        playReady((String) ev[1]);
                    } else if (kind.equals("built")) {
                        play("build", 1f);
                        if (ev.length > 2)
                            flashes.add(new float[]{(Float) ev[1], (Float) ev[2], 0.45f});
                    } else if (kind.equals("error")) {
                        toast = (String) ev[1];
                        toastT = 2.0f;
                    } else if (kind.equals("mission_msg")) {
                        missionMsgs.add((String) ev[1]);
                        missionMsgT.add(4.5f);
                        if (missionMsgs.size() > 4) {
                            missionMsgs.remove(0);
                            missionMsgT.remove(0);
                        }
                    } else if (kind.equals("alert")) {
                        alertFlash = 1f;
                        if (ev.length > 2) {
                            alertX = (Float) ev[1];
                            alertY = (Float) ev[2];
                        }
                        play("alert", 1f);
                    } else if (kind.equals("heal")) {
                        // v2.22 batch C: the medic's working voice. Several
                        // medics channel at once, so one line per half second
                        // is the whole budget -- the beam art already carries
                        // the per-medic rhythm.
                        if (healSndT <= 0) {
                            play("medic_heal", 0.7f);
                            healSndT = 0.5f;
                        }
                    } else if (kind.equals("burrow")) {
                        // v2.22 batch C: lurker burrow/unburrow.
                        play("lurker_burrow", 0.9f);
                    }
                }
                game.events.clear();
                edgeScroll(dt);
            }
            updNs = System.nanoTime() - frameStart;
            // v2.7 batch 8.2: unlock the next mission the first frame the
            // result appears, so returning to the menu shows it available.
            if (mission != null && !game.status.isEmpty() && !campaignRecorded) {
                campaignRecorded = true;
                if (game.status.equals("win")) recordCampaignWin();
            }
            // v2.12 batch E: the glue score-screen stings. Retail loops
            // glue\scorefill while the score bars fill and stamps
            // glue\scorefillend at the end; our panel appears fully drawn, so
            // one sting per result is the honest mapping. resultShown is the
            // once-only guard, and it fires for skirmish too (no mission).
            if (!game.status.isEmpty() && !resultShown) {
                resultShown = true;
                play(game.status.equals("win") ? "ui_scorefill" : "ui_scoreend", 1f);
            }
            holdStillCheck();
            if (pingT > 0) pingT = Math.max(0f, pingT - dt);
            if (healSndT > 0) healSndT = Math.max(0f, healSndT - dt);
            if (toastT > 0) toastT -= dt;
            for (int i = missionMsgT.size() - 1; i >= 0; i--) {
                missionMsgT.set(i, missionMsgT.get(i) - dt);
                if (missionMsgT.get(i) <= 0) {
                    missionMsgT.remove(i);
                    missionMsgs.remove(i);
                }
            }
            if (alertFlash > 0) alertFlash = Math.max(0, alertFlash - dt * 0.8f);
            for (int i = flashes.size() - 1; i >= 0; i--) {
                float[] f = flashes.get(i);
                f[2] -= dt;
                if (f[2] <= 0) flashes.remove(i);
            }
            // per-map chunk loading happens in render via map.chunk(ctx,...)
            long renStart = System.nanoTime();
            Canvas c = null;
            try {
                c = getHolder().lockCanvas();
                if (c != null) render(c);
            } catch (Exception ignored) {
            } finally {
                if (c != null) {
                    try {
                        getHolder().unlockCanvasAndPost(c);
                    } catch (Exception ignored) {
                    }
                }
            }
            renNs = System.nanoTime() - renStart;
            perfSample(dt, updNs, renNs);
            // v2.43 P1: aim the frame at 16 ms instead of adding a flat 14 ms of
            // sleep on top of the work. The old form made the frame length
            // (work + 14), so a 5 ms frame still ran at ~52 fps; this one sleeps
            // only the remainder of the budget, and skips the sleep entirely
            // once the frame has already overrun it.
            long workMs = (System.nanoTime() - frameStart) / 1000000L;
            long sleepMs = 16L - workMs;
            if (sleepMs > 0) {
                try {
                    Thread.sleep(sleepMs);
                } catch (InterruptedException e) {
                    break;
                }
            }
        }
    }

    /**
     * v2.43: record one frame's timings and, twice a second, publish a summary.
     *
     * updNs covers everything the frame does before rendering (game.update or
     * the three network phases, event drain, edge scroll, timers); renNs covers
     * lockCanvas + render + unlock. Keeping them apart is the whole point: an
     * update-bound stutter and a render-bound one want opposite fixes.
     */
    private void perfSample(float dt, long updNs, long renNs) {
        float upd = updNs / 1e6f;
        float ren = renNs / 1e6f;
        float frm = dt * 1000f;
        perfUpd[perfHead] = upd;
        perfRen[perfHead] = ren;
        perfFrm[perfHead] = frm;
        perfHead = (perfHead + 1) % PERF_N;
        if (perfCount < PERF_N) perfCount++;
        perfLogT -= dt;
        if (perfLogT > 0) return;
        perfLogT = 2f;
        int n = game.ents.size();
        String a = "upd avg=" + f1(perfAvg(perfUpd)) + " max=" + f1(perfMax(perfUpd))
                + " p95=" + f1(perfP95(perfUpd))
                + "  ren avg=" + f1(perfAvg(perfRen)) + " max=" + f1(perfMax(perfRen))
                + " p95=" + f1(perfP95(perfRen));
        String b = "frame avg=" + f1(perfAvg(perfFrm)) + " max=" + f1(perfMax(perfFrm))
                + "  fps=" + (perfAvg(perfFrm) > 0.01f ? (int) (1000f / perfAvg(perfFrm)) : 0)
                + "  N=" + n + " s=" + game.shots.size() + " a=" + game.anims.size()
                + " c=" + game.corpses.size();
        perfLine = a;
        perfLine2 = b;
        android.util.Log.i("XJZB", "[perf] " + a + "  " + b);
    }

    /** One-decimal format without the String.format allocation. */
    private static String f1(float v) {
        int x = (int) (v * 10f + 0.5f);
        return (x / 10) + "." + (x % 10);
    }

    private float perfAvg(float[] a) {
        if (perfCount == 0) return 0;
        float s = 0;
        for (int i = 0; i < perfCount; i++) s += a[i];
        return s / perfCount;
    }

    private float perfMax(float[] a) {
        float m = 0;
        for (int i = 0; i < perfCount; i++) if (a[i] > m) m = a[i];
        return m;
    }

    /** p95 over the ring, using a scratch copy so the ring stays intact. */
    private float perfP95(float[] a) {
        if (perfCount == 0) return 0;
        System.arraycopy(a, 0, perfTmp, 0, perfCount);
        java.util.Arrays.sort(perfTmp, 0, perfCount);
        int i = (int) (perfCount * 0.95f);
        if (i >= perfCount) i = perfCount - 1;
        return perfTmp[i];
    }

    // ---------------------------------------------------------------- render
    private float sx(float wx) {
        return (wx - camX) * zoom + getWidth() / 2f;
    }

    private float sy(float wy) {
        return (wy - camY) * zoom + gameCenterY();
    }

    private float wx(float sx) {
        return (sx - getWidth() / 2f) / zoom + camX;
    }

    private float wy(float sy) {
        return (sy - gameCenterY()) / zoom + camY;
    }

    /**
     * v2.17: the vertical anchor of the world-to-screen mapping. It used to be
     * the screen centre H/2, but the camera clamp measures half the PLAYFIELD
     * ((H - top bar - console) / 2), which is smaller -- so the two disagreed by
     * (console - top bar)/2 (about 55dp on a phone). Pushing the camera to the
     * top of the map then left a permanent black band under the top bar, and the
     * bottom 55dp of the map could never be scrolled into view. Anchoring on the
     * playfield centre makes the existing clamp exact: sy(0) lands on the top
     * bar and sy(hPx) on the console, with no asymmetric clamp needed.
     */
    private float gameCenterY() {
        ensureHud();
        return hud.centerY;
    }

    private void render(Canvas c) {
        int W = getWidth(), H = getHeight();
        // v2.43 P2: publish the surface size for offScreen(). Both are stable
        // for the whole frame, and the culling gates below run on this thread.
        frameW = W;
        frameH = H;
        // v2.42 fix (defect B): adopt the camera the touch thread published, ONCE
        // per frame. Everything below -- the chunk loop, every entity, every HUD
        // widget, the fog rect -- then reads one value that cannot change under
        // it, so the frame is internally consistent and neighbouring chunk dsts
        // tile. Without this, a pan that landed mid-frame left bare canvas
        // showing between strips: the "black bar while panning".
        if (camDirty) {
            camX = inCamX;
            camY = inCamY;
            zoom = inZoom;
            camDirty = false;
        }
        // v2.42 diagnostic: the clear colour is rgb(6,8,12) -- itself nearly
        // black, so a screenshot cannot tell "uncovered pixel / dst gap" apart
        // from "legitimately dark terrain". Under the render-diagnostic toggle
        // the clear colour becomes a loud green that no tileset contains, which
        // makes the read unambiguous: any pixel that is still BLACK with this
        // on is covered by real geometry (a bitmap or a shape), and any band
        // that turns GREEN is bare canvas -- a gap in the chunk dst coverage.
        c.drawColor(settings.renderDiag ? Color.rgb(0, 255, 0) : Color.rgb(6, 8, 12));
        // Defensive reset: this single Paint is shared by sprites, terrain,
        // shapes and text, and several draw helpers legitimately lower its
        // alpha or switch it to STROKE. Starting every frame from a known
        // state keeps a missed restore from silently washing out a whole
        // layer (the v2.3 "everything is see-through" regression).
        p.setAlpha(255);
        p.setStyle(Paint.Style.FILL);
        // v2.41: no console height any more; the battlefield is the whole
        // screen and the layout recompute below anchors the top chips itself.
        // v2.19 batch C: recompute the layout once per frame; the camera clamp
        // and every draw/hit-test below read the same rects.
        recomputeHud(W, H);

        // camera clamp -- v2.41: the playfield IS the screen. hud.centerY is
        // H/2 (HudLayout no longer reserves a console band), so the clamp
        // keeps terrain under every pixel, widgets included.
        float halfW = hud.halfW;
        float anchorY = hud.centerY;
        float halfTop = anchorY / zoom;
        float halfBot = (H - anchorY) / zoom;
        camX = Game.clamp(camX, halfW, Math.max(halfW, game.wPx - halfW));
        camY = Game.clamp(camY, halfTop, Math.max(halfTop, game.hPx - halfBot));

        // terrain chunks -- v2.21 #1: the loop spans the FULL screen's world
        // range (wx(0)..wx(W), wy(0)..wy(H)), not the playfield: the clamp now
        // guarantees terrain under the top bar and the console band, so the
        // chunk rows behind them must actually be drawn.
        int cs = 512;
        int cx0 = Math.max(0, (int) (wx(0) / cs));
        int cx1 = Math.min((game.wPx - 1) / cs, (int) (wx(W) / cs));
        int cy0 = Math.max(0, (int) (wy(0) / cs));
        int cy1 = Math.min((game.hPx - 1) / cs, (int) (wy(H) / cs));
        // v2.17: chunks outside the viewport are pre-fetched in the background
        // so a fast drag does not have to wait for a decode.
        // v2.23 batch C #2: the ring widened from 1 to 2. At the default zoom a
        // screen is ~2x2 chunks, so one ring covered only the immediate
        // neighbours; two rings cover where a quick fling actually lands, which
        // is what turned a miss into a visible placeholder.
        int px0 = Math.max(0, cx0 - 2), px1 = Math.min((game.wPx - 1) / cs, cx1 + 2);
        int py0 = Math.max(0, cy0 - 2), py1 = Math.min((game.hPx - 1) / cs, cy1 + 2);
        // v2.42 batch B: the keys the visible loop draws this frame. The chunk
        // LRU consults this set before evicting, so the prefetch ring can no
        // longer push a chunk the renderer is about to show out of a full cache
        // and straight back onto the decode path (the mid-pan flicker family).
        java.util.Set<String> keepAlive = this.keepAlive;
        keepAlive.clear();
        int diagMiss = 0;
        StringBuilder diagMissKeys = settings.renderDiag ? new StringBuilder() : null;
        for (int cy = py0; cy <= py1; cy++)
            for (int cx = px0; cx <= px1; cx++) {
                boolean visible = cx >= cx0 && cx <= cx1 && cy >= cy0 && cy <= cy1;
                if (!visible) {
                    map.prefetch(cx, cy);
                    continue;
                }
                keepAlive.add(cx + "_" + cy);
                map.keepAlive = keepAlive;
                Bitmap b = map.chunk(cx, cy);
                // v2.42 batch B: floor, not truncation. (int) rounds toward
                // zero, which for negative screen coords rounds the dst edge
                // the OTHER way and can open a 1px gap on the top/left map
                // edge; floor keeps every edge on the same side of the grid.
                int dx0 = (int) Math.floor(sx(cx * cs));
                int dy0 = (int) Math.floor(sy(cy * cs));
                int dx1 = (int) Math.floor(sx(Math.min(cx * cs + cs, game.wPx)));
                int dy1 = (int) Math.floor(sy(Math.min(cy * cs + cs, game.hPx)));
                // v2.42 batch B: the bleed is UNCONDITIONAL now. The old code
                // skipped it on the map's last row/column, which left a 1px
                // clear-colour line along the bottom edge when the camera sat
                // on the south clamp, and nothing covered the beyond-map
                // sliver on screens wider than the map. The overdraw past the
                // map edge just stretches the edge tile by 4px -- invisible.
                dx1 += CHUNK_BLEED;
                dy1 += CHUNK_BLEED;
                // v2.43 P1: scratch rect (see tmpDst). The chunk loop is the
                // hottest allocator in render() -- one Rect per visible chunk
                // per frame, plus one more for every placeholder.
                Rect dst = tmpDst;
                dst.set(dx0, dy0, dx1, dy1);
                if (b != null) {
                    c.drawBitmap(b, null, dst, chunkPaint);
                } else {
                    diagMiss++;
                    if (diagMissKeys != null && diagMissKeys.length() < 160)
                        diagMissKeys.append(' ').append(cx).append('_').append(cy);
                    if (map.minimap != null) {
                        // v2.17: never skip a whole 512x512 tile. A chunk that
                        // is still decoding (or failed) shows its own patch of
                        // the minimap, magnified -- low-res, but never a black
                        // hole. v2.24: brightened so dark water/shadow do not
                        // read as black blocks. v2.42: PLACEHOLDER_BRIGHT lifts
                        // the floor further and the veil drops to 96 so a
                        // loading tile reads as veiled terrain, never as a hole
                        // (the "black bar while panning" family, one head of it).
                        int mw = map.minimap.getWidth(), mh = map.minimap.getHeight();
                        int msx0 = (int) ((float) (cx * cs) / game.wPx * mw);
                        int msy0 = (int) ((float) (cy * cs) / game.hPx * mh);
                        int msx1 = (int) ((float) Math.min(cx * cs + cs, game.wPx) / game.wPx * mw);
                        int msy1 = (int) ((float) Math.min(cy * cs + cs, game.hPx) / game.hPx * mh);
                        if (msx1 > msx0 && msy1 > msy0) {
                            brightPaint.setColorFilter(new android.graphics.ColorMatrixColorFilter(
                                    PLACEHOLDER_BRIGHT));
                            // v2.43 P1: src needs its own scratch -- `dst` above
                            // is still live for this same drawBitmap.
                            Rect msrc = tmpSrc;
                            msrc.set(msx0, msy0, msx1, msy1);
                            c.drawBitmap(map.minimap, msrc, dst, brightPaint);
                            brightPaint.setColorFilter(null);
                            int keep = p.getAlpha();
                            p.setAlpha(96);
                            p.setColor(Color.rgb(0, 0, 0));
                            c.drawRect(dst, p);
                            p.setAlpha(keep);
                        }
                    }
                }
                if (settings.renderDiag) {
                    // v2.42 batch B diagnostic: 1px frame per visible chunk,
                    // colour = (row+col) parity, so a screenshot of a black bar
                    // directly answers "inside a chunk (bitmap), between chunks
                    // (dst gap) or over everything (overlay)".
                    p.setStyle(Paint.Style.STROKE);
                    p.setStrokeWidth(1);
                    p.setColor(((cx + cy) & 1) == 0 ? Color.rgb(0, 255, 255)
                            : Color.rgb(255, 200, 0));
                    c.drawRect(dx0, dy0, dx1, dy1, p);
                    p.setStyle(Paint.Style.FILL);
                    if (b == null) {
                        // v2.42 fix: the Settings javadoc promised a magenta
                        // flash and the code never drew one, so the instrument
                        // could not tell a still-decoding chunk from a black
                        // bar that lives somewhere else entirely. Tint the
                        // whole placeholder: a magenta patch in the screenshot
                        // IS an undecoded chunk, and its absence while a black
                        // bar is on screen rules the decode path out.
                        p.setColor(Color.argb(110, 255, 0, 255));
                        c.drawRect(dx0, dy0, dx1, dy1, p);
                    }
                    // v2.42: the 0.5 Hz line can miss a fling that lasts a few
                    // frames, which is exactly the event under investigation.
                    // Log every frame that shows a miss (throttled to a burst
                    // so a long slide cannot flood the buffer): the bar and its
                    // chunk keys then land in the same logcat window.
                    if (b == null && diagMissLog < 400) {
                        diagMissLog++;
                        String line = "[diag-miss] f=" + diagMissLog
                                + " chunk=" + cx + "_" + cy
                                + " cam=(" + Math.round(camX) + "," + Math.round(camY) + ")"
                                + " zoom=" + String.format("%.3f", zoom);
                        android.util.Log.i("XJZB", line);
                        // v2.42: same line into the on-screen readout -- a phone
                        // is not attached to a logcat, and the user must be able
                        // to read the evidence straight off the screen.
                        if (diagLog.size() >= 60) diagLog.pollFirst();
                        diagLog.addLast(line);
                    }
                }
            }
        if (settings.renderDiag && (diagFrame++ % 30) == 0) {
            android.util.Log.i("XJZB", "[diag] map=" + (game.mapId == null ? "?" : game.mapId)
                    + " visible=" + ((cx1 - cx0 + 1) * (cy1 - cy0 + 1))
                    + " miss=" + diagMiss + " missKeys=" + (diagMissKeys == null ? "-" : diagMissKeys.toString().trim())
                    + " zoom=" + String.format("%.3f", zoom)
                    + " fog=" + settings.fogStyle
                    + " cam=(" + Math.round(camX) + "," + Math.round(camY) + ")");
        }
        if (settings.renderDiag) {
            // Latch the worst frame. A fling is a handful of frames long and the
            // bar disappears as soon as it ends, so "current frame" numbers are
            // gone before anyone can read them; the peak is what gets kept.
            diagMissNow = diagMiss;
            if (diagMiss > diagMissPeak) {
                diagMissPeak = diagMiss;
                diagPeakKeys = diagMissKeys == null ? "" : diagMissKeys.toString().trim();
                diagPeakCam = "(" + Math.round(camX) + "," + Math.round(camY) + ")";
                diagPeakAge = 0;
            } else if (diagMiss > 0) {
                diagPeakAge = 0;
            } else {
                diagPeakAge++;
            }
            // A few calm seconds means the interesting moment is over; drop the
            // stale peak so the next fling reports its own, not the old one.
            if (diagMiss == 0) {
                if (++diagCalmFrames > 90) {
                    diagMissPeak = 0;
                    diagPeakKeys = "";
                    diagPeakCam = "";
                }
            } else {
                diagCalmFrames = 0;
            }
        }

        // fog: a 1px/tile bitmap upscaled with bilinear filtering, so the
        // unexplored->explored edge is a smooth gradient instead of hard
        // per-tile rectangles (batch-2 #7)
        //
        // v2.43 P2: rebuilding this every frame meant a w*h loop plus a full
        // texture upload per frame (4096 px on divide, 36864 on newgettysburg)
        // for data that only changes when a unit moves. Two gates replace it:
        // HOK draws no fog at all, so it skips the bitmap entirely; SC rebuilds
        // at most 10x/s, which is invisible on an overlay that fades over
        // hundreds of milliseconds. The minimap blits this same bitmap, so
        // gating here keeps both views consistent with each other.
        boolean fogOn = settings.fogStyle != Settings.FOG_HOK;
        // The `game.time < fogBuiltAt` arm matters on a restart: game.time goes
        // back to 0 while fogBuiltAt still holds the old match's clock, and a
        // plain `elapsed >= interval` test would then never fire again.
        if (fogOn && (fogBuiltAt < 0f || game.time < fogBuiltAt
                || game.time - fogBuiltAt >= FOG_REBUILD_INTERVAL)) {
            updateFogBitmap();
            fogBuiltAt = game.time;
        }
        if (fogOn && fogBmp != null) {
            // v2.43 P1: scratch rect (not live across any other draw here).
            Rect fogDst = tmpDst2;
            fogDst.set((int) sx(0), (int) sy(0), (int) sx(game.wPx), (int) sy(game.hPx));
            c.drawBitmap(fogBmp, null, fogDst, fogPaint);
        }

        // minerals
        // v2.43 P2: the gate lives here, not inside drawSingle(), because the
        // build-placement ghost draws through drawSingle too and must never be
        // culled -- it follows the finger, which can sit outside the view.
        for (Game.Mineral m : game.minerals) {
            String key = m.variant >= 3 ? "geyser" : (m.variant == 0 ? "mineral" : m.variant == 1 ? "mineral2" : "mineral3");
            SpriteBank.Sprite s = bank.get(key, false);
            if (s == null) continue;
            if (offScreen(m.x, m.y, s, 1f)) continue;
            drawSingle(c, s, m.x, m.y, 0, 1f);
        }

        // buildings first, then units
        for (Game.Ent e : game.ents)
            if (e.alive() && e.isBuilding() && !offScreenEnt(e)) drawEnt(c, e);

        // corpses sit under the living units and above the ground
        for (Game.Corpse cp : game.corpses) {
            SpriteBank.Sprite s = bank.get(cp.key, cp.team == 1);
            if (s == null) continue;
            if (offScreen(cp.x, cp.y, s, 1f)) continue;
            float a = cp.t < Game.Corpse.HOLD ? 1f
                    : Math.max(0f, 1f - (cp.t - Game.Corpse.HOLD) / Game.Corpse.FADE);
            // v2.43 P1: scratch src/dst pair.
            Rect src = bank.frameRect(s, cp.frame, tmpSrc);
            float w = s.fw * zoom, h = s.fh * zoom;
            float x = sx(cp.x), y = sy(cp.y);
            Rect dst = tmpDst;
            dst.set((int) (x - w / 2), (int) (y - h * 0.65f),
                    (int) (x + w / 2), (int) (y + h * 0.35f));
            p.setAlpha((int) (255 * a));
            c.drawBitmap(s.sheet, src, dst, p);
            p.setAlpha(255);
        }

        for (Game.Ent e : game.ents)
            if (e.alive() && !e.isBuilding() && !offScreenEnt(e)) drawEnt(c, e);

        // shots: a tracer for bullets, a bright shell for missiles (the smoke
        // puffs behind them are spawned by the core)
        for (Game.Shot s : game.shots) {
            float t = s.prog();
            float ix = s.x + (s.tx - s.x) * t, iy = s.y + (s.ty - s.y) * t;
            // A shell is a few px wide; 8 * zoom covers the widest case.
            if (offScreen(ix, iy, 8 * zoom, 8 * zoom, 8 * zoom)) continue;
            if (s.missile) {
                p.setColor(Color.argb(190, 255, 190, 110));
                c.drawCircle(sx(ix), sy(iy), 3.6f * zoom, p);
                p.setColor(Color.argb(120, 255, 240, 190));
                c.drawCircle(sx(ix), sy(iy), 1.8f * zoom, p);
            } else {
                p.setColor(Color.rgb(255, 230, 140));
                c.drawCircle(sx(ix), sy(iy), 2.5f * zoom, p);
            }
        }

        // sprite-sheet effects (explosions, death sequences)
        for (Game.Anim a : game.anims) {
            SpriteBank.Sprite s = bank.get(a.key, a.team == 1);
            if (s == null) continue;
            if (offScreen(a.x, a.y, s, a.scale)) continue;
            // v2.43 P1: scratch src/dst pair.
            Rect src = bank.frameRect(s, a.frame(), tmpSrc);
            float w = s.fw * zoom * a.scale, h = s.fh * zoom * a.scale;
            float x = sx(a.x), y = sy(a.y);
            Rect dst = tmpDst;
            dst.set((int) (x - w / 2), (int) (y - h * 0.65f),
                    (int) (x + w / 2), (int) (y + h * 0.35f));
            c.drawBitmap(s.sheet, src, dst, p);
        }

        // v2.25: the scanner sweep. A bright square with a sweeping highlight,
        // drawn over the terrain for the sweep's 8 seconds so the player can
        // see exactly what the comsat is revealing (and the fog lift that
        // follows it is permanent until the fog layer dims it back).
        for (Game.Scan sc : game.scans) {
            float r = Game.SCAN_RADIUS * zoom;
            float x = sx(sc.x), y = sy(sc.y);
            float k = Math.min(1f, sc.t / Game.SCAN_DURATION);
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.argb((int) (40 * k), 120, 220, 255));
            c.drawRect(x - r, y - r, x + r, y + r, p);
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(2 * uiScale);
            p.setColor(Color.argb((int) (220 * k), 120, 220, 255));
            c.drawRect(x - r, y - r, x + r, y + r, p);
            // a scan line sweeping top-to-bottom inside the square
            float sweepY = y - r + (2 * r) * ((game.time * 1.6f) % 1f);
            p.setColor(Color.argb((int) (200 * k), 180, 240, 255));
            c.drawLine(x - r, sweepY, x + r, sweepY, p);
            p.setStrokeWidth(1);
            p.setStyle(Paint.Style.FILL);
        }

        // v2.25: the nuclear countdown, visible to BOTH players -- the whole
        // point of the warning is that the defender can see it coming and has
        // ten seconds to kill the spotter. A red ring closes on the target and
        // a beam falls from the top of the screen as impact nears.
        for (Game.Nuke n : game.nukes) {
            float x = sx(n.x), y = sy(n.y);
            float frac = Math.min(1f, n.t / Game.NUKE_DELAY);
            float r = Game.NUKE_RADIUS * zoom;
            // the blast circle, flashing faster as impact approaches
            float pulse = 0.5f + 0.5f * (float) Math.sin(n.t * (6f + 12f * frac));
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(3 * uiScale);
            p.setColor(Color.argb((int) (140 + 100 * pulse), 255, 60, 50));
            c.drawCircle(x, y, r, p);
            // the closing ring: from the blast radius down to the centre
            p.setStrokeWidth(2 * uiScale);
            p.setColor(Color.argb(230, 255, 120, 90));
            c.drawCircle(x, y, r * (1f - frac), p);
            // crosshair
            p.setColor(Color.argb(220, 255, 90, 70));
            c.drawLine(x - 14 * uiScale, y, x + 14 * uiScale, y, p);
            c.drawLine(x, y - 14 * uiScale, x, y + 14 * uiScale, p);
            p.setStrokeWidth(1);
            p.setStyle(Paint.Style.FILL);
            // the falling beam, drawn from above the screen down to the target
            SpriteBank.Sprite beam = bank.get("nukebeam", false);
            if (beam != null) {
                float bw = beam.fw * zoom * 1.2f;
                float top = sy(0) - 200 * zoom;
                // v2.43 P1: scratch src/dst pair.
                Rect dst = tmpDst;
                dst.set((int) (x - bw / 2), (int) top,
                        (int) (x + bw / 2), (int) (y + bw * 0.3f));
                p.setAlpha((int) (150 + 105 * frac));
                c.drawBitmap(beam.sheet, bank.frameRect(beam, beam.frames - 1, tmpSrc), dst, p);
                p.setAlpha(255);
            }
            // the target marker on the ground
            SpriteBank.Sprite targ = bank.get("nuketarg", false);
            if (targ != null) {
                float tw = targ.fw * zoom * 1.5f;
                Rect tsrc = bank.frameRect(targ, targ.frames - 1, tmpSrc);
                Rect tdst = tmpDst2;
                tdst.set((int) (x - tw / 2), (int) (y - tw / 2),
                        (int) (x + tw / 2), (int) (y + tw / 2));
                c.drawBitmap(targ.sheet, tsrc, tdst, p);
            }
            // and the countdown text, so "how long" is never a guess
            float left = Math.max(0f, Game.NUKE_DELAY - n.t);
            p.setTextAlign(Paint.Align.CENTER);
            p.setTextSize(14 * uiScale);
            drawOutlined(c, "核弹 " + String.format("%.1f", left) + "s", x,
                    y - r - 8 * uiScale, Color.rgb(255, 130, 100));
            p.setTextAlign(Paint.Align.LEFT);
        }

        // v2.10: psionic storms. The field outlives the cast, so it is drawn
        // from the sheet directly rather than through a one-shot Anim -- the
        // 14-frame sheet is looped for the storm's whole 3 seconds and faded
        // out over the last half second so the edge of the field is readable.
        for (Game.Storm st : game.storms) {
            SpriteBank.Sprite s = bank.get("psistorm", st.team == 1);
            if (s == null) continue;
            int nf = Math.max(1, s.frames);
            int fr = ((int) (st.t * 14f)) % nf;
            // v2.43 P1: scratch src/dst pair.
            Rect src = bank.frameRect(s, fr, tmpSrc);
            float w = s.fw * zoom * 1.1f, h = s.fh * zoom * 1.1f;
            float x = sx(st.x), y = sy(st.y);
            float left = Game.STORM_DURATION - st.t;
            if (left < 0.5f) p.setAlpha((int) (255 * Math.max(0f, left / 0.5f)));
            Rect dst = tmpDst;
            dst.set((int) (x - w / 2), (int) (y - h * 0.65f),
                    (int) (x + w / 2), (int) (y + h * 0.35f));
            c.drawBitmap(s.sheet, src, dst, p);
            p.setAlpha(255);
        }

        // v2.11 batch B: dark swarm. Same "field outlives the cast" shape as the
        // storm above, but the swarm is a smoke bank -- it fades in over the
        // first half second and out over the last, and the alpha never reaches
        // full so the units underneath stay legible (that is the whole point of
        // the spell).
        for (Game.Dswarm ds : game.dswarms) {
            SpriteBank.Sprite s = bank.get("dswarm", ds.team == 1);
            if (s == null) continue;
            int nf = Math.max(1, s.frames);
            int fr = ((int) (ds.t * 10f)) % nf;
            // v2.43 P1: scratch src/dst pair.
            Rect src = bank.frameRect(s, fr, tmpSrc);
            float w = s.fw * zoom * 0.85f, h = s.fh * zoom * 0.85f;
            float x = sx(ds.x), y = sy(ds.y);
            float left = Game.DSWARM_DURATION - ds.t;
            float a = Math.min(1f, ds.t / 0.5f) * Math.min(1f, left / 0.5f);
            p.setAlpha((int) (185 * Math.max(0f, a)));
            Rect dst = tmpDst;
            dst.set((int) (x - w / 2), (int) (y - h * 0.65f),
                    (int) (x + w / 2), (int) (y + h * 0.35f));
            c.drawBitmap(s.sheet, src, dst, p);
            p.setAlpha(255);
        }

        // v2.11 batch B: ensnare. The goo sheet ships in three sizes; pick the
        // one closest to the field's radius so the splat neither floats inside
        // nor spills past the area it actually covers.
        for (Game.Ensnare en : game.ensnares) {
            String gk = Game.ENSNARE_RADIUS <= 48f ? "ensgoo_s"
                    : Game.ENSNARE_RADIUS <= 80f ? "ensgoo_m" : "ensgoo_l";
            SpriteBank.Sprite s = bank.get(gk, en.team == 1);
            if (s == null) continue;
            int nf = Math.max(1, s.frames);
            int fr = ((int) (en.t * 8f)) % nf;
            // v2.43 P1: scratch src/dst pair.
            Rect src = bank.frameRect(s, fr, tmpSrc);
            float w = s.fw * zoom * 1.4f, h = s.fh * zoom * 1.4f;
            float x = sx(en.x), y = sy(en.y);
            float left = Game.ENSNARE_DURATION - en.t;
            if (left < 0.5f) p.setAlpha((int) (255 * Math.max(0f, left / 0.5f)));
            Rect dst = tmpDst;
            dst.set((int) (x - w / 2), (int) (y - h * 0.65f),
                    (int) (x + w / 2), (int) (y + h * 0.35f));
            c.drawBitmap(s.sheet, src, dst, p);
            p.setAlpha(255);
        }
        for (float[] fx : game.effects) {
            // Radius peaks at (1.4 - 0) * 22 * zoom, so 31 * zoom is a bound.
            if (offScreen(fx[0], fx[1], 31 * zoom, 31 * zoom, 31 * zoom)) continue;
            float a = fx[2] / 0.7f;
            p.setColor(fx[3] == 1 ? Color.argb((int) (200 * a), 255, 120, 50)
                    : Color.argb((int) (180 * a), 255, 200, 90));
            float x = sx(fx[0]), y = sy(fx[1]);
            c.drawCircle(x, y, (1.4f - fx[2]) * 22 * zoom, p);
        }

        // selection ring & health
        // v2.43 P2: this loop used to transform and then draw over EVERY living
        // entity on the map, including the ones the viewport cull had just
        // thrown away in the world pass -- which is where the win is, since the
        // bar stack is up to six drawRect calls per entity.
        for (Game.Ent e : game.ents) {
            if (!e.alive()) continue;
            if (offScreenEnt(e)) continue;
            float x = sx(e.x), y = sy(e.y);
            float r = Math.max(e.type.radius, e.type.tiles * 14) * zoom;
            if (e.selected && e.team == 0) {
                p.setStyle(Paint.Style.STROKE);
                p.setStrokeWidth(2f * zoom);
                p.setColor(Color.rgb(80, 255, 120));
                c.drawCircle(x, y, r + 4 * zoom, p);
                p.setStyle(Paint.Style.FILL);
            }
            // v2.17: the settings toggle draws the bar even at full health,
            // for players who want to see the whole army at a glance. Same rule
            // for both teams.
            if (e.hp < e.type.hp || settings.alwaysShowHp) {
                // v2.17: floor the bar to a readable size on a phone. At 0.7
                // zoom a 4*zoom-px bar was ~3 px tall and an r*1.9 bar could be
                // ~10 px wide, which is why nobody could tell who was dying.
                float bh = Math.max(4 * zoom, dp(3));
                float bw = Math.max(r * 1.9f, dp(16));
                p.setColor(Color.BLACK);
                c.drawRect(x - bw / 2, y - r - 9 * zoom, x + bw / 2,
                        y - r - 9 * zoom + bh, p);
                float f = e.hp / (float) e.type.hp;
                p.setColor(e.team == 0 ? Color.rgb(90, 230, 110) : Color.rgb(240, 80, 70));
                c.drawRect(x - bw / 2, y - r - 9 * zoom, x - bw / 2 + bw * f,
                        y - r - 9 * zoom + bh, p);
            }
            // v2.10: the shield bar rides above the health bar, in the same
            // cyan the protoss energy effects use. It is drawn whenever the
            // shield is not full -- including at full hp -- because a protoss
            // unit that is unhurt but shield-stripped is the common state right
            // after a fight, and that is exactly the moment the bar matters.
            if (e.type.shield > 0 && e.shield < e.type.shield) {
                float bh = Math.max(4 * zoom, dp(3));
                float bw = Math.max(r * 1.9f, dp(16));
                p.setColor(Color.BLACK);
                c.drawRect(x - bw / 2, y - r - 14 * zoom, x + bw / 2,
                        y - r - 14 * zoom + bh, p);
                float f = e.shield / (float) e.type.shield;
                p.setColor(Color.rgb(90, 200, 255));
                c.drawRect(x - bw / 2, y - r - 14 * zoom, x - bw / 2 + bw * f,
                        y - r - 14 * zoom + bh, p);
            }
            // v2.22 batch A: the caster's energy pool, above the shield row.
            // Hidden while full -- a fresh caster sits at 50/200 and its bar is
            // the whole point of watching whether the next storm is affordable.
            if (e.maxEnergy > 0 && e.energy < e.maxEnergy - 0.5f) {
                float bh = Math.max(4 * zoom, dp(3));
                float bw = Math.max(r * 1.9f, dp(16));
                p.setColor(Color.BLACK);
                c.drawRect(x - bw / 2, y - r - 19 * zoom, x + bw / 2,
                        y - r - 19 * zoom + bh, p);
                float f = e.energy / e.maxEnergy;
                p.setColor(Color.rgb(70, 140, 255));
                c.drawRect(x - bw / 2, y - r - 19 * zoom, x - bw / 2 + bw * f,
                        y - r - 19 * zoom + bh, p);
            }
        }

        // build placement ghost: per-tile blueprint grid plus the sprite tint
        // (batch-1 #3)
        if (buildKey != null) {
            Game.Type t = Game.TYPES.get(buildKey);
            int tiles = Math.max(1, t.tiles);
            int tx0 = (int) (lastXToWorld / 32) - tiles / 2;
            int ty0 = (int) (lastYToWorld / 32) - tiles / 2;
            boolean afford = game.mineralsPlayer >= t.cost && game.gasPlayer >= t.gasCost;
            boolean place = game.canPlace(buildKey, lastXToWorld, lastYToWorld) && afford;
            for (int ty = ty0; ty < ty0 + tiles; ty++)
                for (int tx = tx0; tx < tx0 + tiles; tx++) {
                    boolean walk = true;
                    for (int my = 0; my < 4 && walk; my++)
                        for (int mx = 0; mx < 4; mx++)
                            if (!game.passMini(tx * 4 + mx, ty * 4 + my)) {
                                walk = false;
                                break;
                            }
                    boolean ok = walk && place;
                    p.setColor(ok ? Color.argb(120, 90, 255, 120)
                            : Color.argb(120, 255, 80, 80));
                    float x0 = sx(tx * 32), y0 = sy(ty * 32);
                    c.drawRect(x0 + 1, y0 + 1, sx(tx * 32 + 32) - 1, sy(ty * 32 + 32) - 1, p);
                }
            SpriteBank.Sprite s = bank.get(buildKey, false);
            if (s != null) {
                p.setAlpha(place ? 150 : 110);
                drawSingle(c, s, lastXToWorld, lastYToWorld, 0, 1f);
                p.setAlpha(255);
            }
            if (!afford) {
                p.setTextAlign(Paint.Align.CENTER);
                p.setTextSize(12 * uiScale);
                p.setColor(Color.rgb(255, 130, 120));
                c.drawText(game.buildError(buildKey, lastXToWorld, lastYToWorld),
                        lastXToWorld, sy(lastYToWorld) - tiles * 16 * zoom - 8 * uiScale, p);
                p.setTextAlign(Paint.Align.LEFT);
            }
        }

        // order-acknowledgement markers (batch-1 #1)
        for (Game.Marker mk : game.markers) {
            float x = sx(mk.x), y = sy(mk.y);
            float k = Math.min(1f, mk.t / mk.dur);
            p.setStyle(Paint.Style.STROKE);
            if (mk.kind == 0) {
                p.setStrokeWidth(2.5f * zoom);
                p.setColor(Color.argb((int) (220 * (1 - k)), 90, 255, 130));
                c.drawCircle(x, y, (5 + 20 * k) * zoom, p);
            } else {
                p.setStrokeWidth(3 * zoom);
                p.setColor(Color.argb((int) (230 * (1 - k)), 255, 70, 60));
                float r = 8 * zoom;
                c.drawLine(x - r, y - r, x + r, y + r, p);
                c.drawLine(x - r, y + r, x + r, y - r, p);
            }
            p.setStyle(Paint.Style.FILL);
        }

        // building-completion flash (batch-1 #3)
        for (float[] f : flashes) {
            float k = 1f - f[2] / 0.45f;
            p.setColor(Color.argb((int) (170 * (1 - k)), 255, 255, 255));
            c.drawCircle(sx(f[0]), sy(f[1]), (12 + 26 * k) * zoom, p);
        }

        // rally point: yellow flag + dashed line, only for selected buildings
        // (batch-1 #5)
        for (Game.Ent e : game.ents) {
            if (!e.alive() || e.team != 0 || e.rallyX < 0 || !e.selected) continue;
            float x0 = sx(e.x), y0 = sy(e.y), x1 = sx(e.rallyX), y1 = sy(e.rallyY);
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(2 * zoom);
            p.setPathEffect(dash);
            p.setColor(Color.argb(190, 255, 210, 90));
            c.drawLine(x0, y0, x1, y1, p);
            p.setPathEffect(null);
            p.setStyle(Paint.Style.FILL);
            // flag
            float fy = y1 - 16 * zoom;
            p.setColor(Color.rgb(60, 50, 30));
            c.drawLine(x1, fy, x1, y1, p);
            p.setColor(Color.rgb(255, 200, 60));
            c.drawCircle(x1, fy, 4.5f * zoom, p);
            p.setStyle(Paint.Style.STROKE);
            p.setColor(Color.argb(200, 255, 220, 110));
            c.drawCircle(x1, fy, 7.5f * zoom, p);
            p.setStyle(Paint.Style.FILL);
        }

        // v2.22 batch B: selected detectors show their reveal radius, the same
        // teaching aid the rally line is -- without it "why did my turret stop
        // shooting the dark templar" has no visible answer.
        for (Game.Ent e : game.ents) {
            if (!e.alive() || e.team != 0 || !e.type.detector || !e.selected) continue;
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(1.5f * zoom);
            p.setColor(Color.argb(80, 110, 190, 255));
            c.drawCircle(sx(e.x), sy(e.y), Game.CLOAK_RADIUS * zoom, p);
            p.setStyle(Paint.Style.FILL);
        }

        // selection box
        if (boxing) {
            p.setColor(Color.argb(60, 120, 220, 255));
            c.drawRect(Math.min(boxX0, boxX1), Math.min(boxY0, boxY1),
                    Math.max(boxX0, boxX1), Math.max(boxY0, boxY1), p);
            p.setStyle(Paint.Style.STROKE);
            p.setColor(Color.argb(220, 120, 220, 255));
            c.drawRect(Math.min(boxX0, boxX1), Math.min(boxY0, boxY1),
                    Math.max(boxX0, boxX1), Math.max(boxY0, boxY1), p);
            p.setStyle(Paint.Style.FILL);
        }

        // v2.6 #C3: expanding ring at the press point the moment the box select
        // arms, so the 250ms hold is not a silent mode change.
        if (pingT > 0) {
            float k = 1f - pingT / PING_LIFE;
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(2 * uiScale);
            p.setColor(Color.argb((int) (200 * (1 - k)), 130, 225, 255));
            c.drawCircle(pingX, pingY, (10 + 34 * k) * uiScale, p);
            p.setStrokeWidth(1);
            p.setStyle(Paint.Style.FILL);
        }

        drawHud(c, W, H);
    }

    private float lastXToWorld, lastYToWorld;

    /**
     * Rebuild the 1px-per-tile fog bitmap. Unexplored is opaque black, explored
     * is 70% black (terrain still reads through), visible is fully clear.
     */
    private void updateFogBitmap() {
        int w = game.wTiles, h = game.hTiles;
        if (fogBmp == null || fogBmp.getWidth() != w || fogBmp.getHeight() != h) {
            fogBmp = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
            fogPix = new int[w * h];
        }
        // v2.18 batch A: HOK style draws NO fog at all -- the terrain is always
        // fully visible and the "vision" is enforced by the enemy draw gate
        // instead (see enemyVisible). SC style keeps the two-tone overlay, with
        // the explored dim eased from 70% to 50% so it reads as haze, not a hole.
        boolean hok = settings.fogStyle == Settings.FOG_HOK;
        for (int i = 0; i < w * h; i++) {
            if (hok) { fogPix[i] = 0; continue; }
            int f = game.fog[i];
            fogPix[i] = f == 2 ? 0 : (f == 0 ? 0xFF000000 : 0x80000000);
        }
        fogBmp.setPixels(fogPix, 0, w, 0, 0, w, h);
    }

    /** SC-ish outlined text: dark edge, bright fill. */
    private void drawOutlined(Canvas c, String s, float x, float y, int color) {
        p.setColor(Color.argb(200, 0, 0, 0));
        c.drawText(s, x + 1.5f, y + 1.5f, p);
        c.drawText(s, x - 1.5f, y + 1.5f, p);
        c.drawText(s, x + 1.5f, y - 1.5f, p);
        c.drawText(s, x - 1.5f, y - 1.5f, p);
        p.setColor(color);
        c.drawText(s, x, y, p);
    }

    /**
     * Trim `s` with a trailing ellipsis so it fits `maxW` at the current text
     * size (v2.5 #3: queue entries are narrow and the Chinese name must not
     * spill over the neighbouring slot).
     */
    private String ellipsize(String s, float maxW, float size) {
        if (s == null || s.isEmpty()) return "";
        float prev = p.getTextSize();
        p.setTextSize(size);
        if (p.measureText(s) <= maxW) {
            p.setTextSize(prev);
            return s;
        }
        String cut = s;
        while (cut.length() > 1 && p.measureText(cut + "…") > maxW)
            cut = cut.substring(0, cut.length() - 1);
        p.setTextSize(prev);
        return cut + "…";
    }

    private void drawSingle(Canvas c, SpriteBank.Sprite s, float wx, float wy,
                            int frame, float scale) {
        // v2.43 P1: scratch src/dst pair (src and dst are both live for the
        // drawBitmap below, so they cannot share one Rect).
        Rect src = bank.frameRect(s, frame, tmpSrc);
        float w = s.fw * zoom * scale, h = s.fh * zoom * scale;
        Rect dst = tmpDst;
        dst.set((int) (sx(wx) - w / 2), (int) (sy(wy) - h * 0.65f),
                (int) (sx(wx) + w / 2), (int) (sy(wy) + h * 0.35f));
        c.drawBitmap(s.sheet, src, dst, p);
    }

    /**
     * v2.18 batch A: should an enemy entity be drawn? Two models share this
     * one gate so the main view and the minimap can never disagree.
     *   cloak -- v2.22 batch B runs FIRST: a cloaked enemy is drawn only
     *          while a friendly detector reveals it, and this holds in BOTH
     *          fog styles. Terrain being globally visible in the HOK mode is
     *          about the ground, not about the units standing on it.
     *   HOK -- v2.21 #4: ALWAYS visible otherwise.
     *   SC  -- the classic model: anything on explored ground (fog!=0) shows,
     *          so a remembered position keeps drawing until the tile decays.
     * Own-team entities never call this.
     */
    private boolean enemyVisible(Game.Ent e) {
        if (!game.enemyRevealed(e)) return false;
        if (settings.fogStyle == Settings.FOG_HOK) return true;
        int tf = game.fog[(int) (e.y / 32) * game.wTiles + (int) (e.x / 32)];
        return tf != 0;
    }

    /**
     * v2.43 P2: is this world position outside the drawable view, given how
     * far the thing drawn there actually extends? The caller passes world
     * coordinates and this does the transform, so a culled object never pays
     * for sx()/sy() twice.
     *
     * Extents are screen-space and asymmetric: `above` is how far the drawing
     * reaches above the anchor and `below` how far under it, because both
     * drawEnt and drawSingle anchor a sprite at -0.65h / +0.35h. A symmetric
     * test would drop tall sprites whose base sits just off the bottom edge.
     *
     * frameW/frameH are the surface size captured at the top of render(), so
     * this is only valid on the render thread inside a frame.
     */
    private boolean offScreen(float wx, float wy, float halfW, float above, float below) {
        float x = sx(wx), y = sy(wy);
        return x + halfW < 0 || x - halfW > frameW
                || y + below < 0 || y - above > frameH;
    }

    /**
     * The same gate for something drawn from a sprite sheet at `scale`.
     *
     * The extents come from the sheet cell rather than a fixed radius because
     * cells span two orders of magnitude here: a marine cell is 128 px while an
     * explosion cell (plasma, bang_l, nukehit) is up to 256 px, and animations
     * draw at up to 1.4x. A single magic number is either too small -- which
     * shows up as puffs vanishing when the camera pans past the screen edge --
     * or so large it culls nothing at all.
     */
    private boolean offScreen(float wx, float wy, SpriteBank.Sprite s, float scale) {
        if (s == null) {
            // No sheet resolved yet. Fall back to the widest cell we ship, so
            // the object is still kept while its sprite is missing.
            float half = MAX_CELL * zoom * 0.5f * scale;
            return offScreen(wx, wy, half, half * 1.3f, half * 0.7f);
        }
        float w = s.fw * zoom * scale, h = s.fh * zoom * scale;
        return offScreen(wx, wy, w / 2f, h * 0.65f, h * 0.35f);
    }

    /**
     * The gate for a live entity, which draws more than its sprite: the
     * health / shield / energy stack rides up to (r + 19 * zoom + bar height)
     * above the anchor, and the selection ring reaches r + 4 * zoom sideways.
     * Both are folded in so a bar whose unit is just off-screen is not clipped
     * off mid-bar.
     *
     * Uses MAX_CELL rather than the entity's own cell on purpose -- see the
     * note on the cull block above.
     */
    private boolean offScreenEnt(Game.Ent e) {
        float r = Math.max(e.type.radius, e.type.tiles * 14) * zoom;
        float half = MAX_CELL * zoom * 0.5f;
        float above = Math.max(half * 1.3f, r + 24 * zoom);
        float halfW = Math.max(half, r + 6 * zoom);
        return offScreen(e.x, e.y, halfW, above, half * 0.7f);
    }
    private void drawEnt(Canvas c, Game.Ent e) {
        // v2.18 batch A: HOK hides any enemy outside friendly vision; SC only
        // hides one standing on an unexplored tile.
        // v2.23: a unit riding in a transport or sitting in a bunker is off
        // the field, so it is not drawn at its old position -- the carrier or
        // the bunker stands for it.
        if (e.cargoOf != null || e.garrisoned) return;
        if (e.team == 1 && !enemyVisible(e)) return;

        SpriteBank.Sprite s = bank.get(e.type.key, e.team == 1);
        float x = sx(e.x), y = sy(e.y);
        float r = Math.max(e.type.radius, e.type.tiles * 14) * zoom;

        // Ground shadow so units don't look like they are floating (batch-5 #17).
        // Buildings are excluded: `r` scales with tile footprint, so the oval
        // came out wider than the sprite itself and read as a pool of black.
        // NOTE: Paint.setColor() also sets the paint's alpha, and this same
        // Paint draws the sprite below -- leaving it at 90 modulated the
        // bitmap down to ~35% opacity, which is the v2.3 transparency
        // regression. Always restore alpha to 255 after the shadow.
        if (!e.isBuilding()) {
            if (!e.type.flying) {
                p.setColor(Color.argb(90, 0, 0, 0));
                c.drawOval(x - r * 0.8f, y - r * 0.26f, x + r * 0.8f, y + r * 0.26f, p);
            } else {
                p.setColor(Color.argb(45, 0, 0, 0));
                c.drawOval(x - r * 0.55f, y + r * 0.5f, x + r * 0.55f, y + r * 0.72f, p);
            }
            p.setAlpha(255);
            p.setStyle(Paint.Style.FILL);
        }

        if (s != null) {
            // v2.43 P1: scratch rects. `src` and `dst` are both live for the
            // drawBitmap at the end of this block, so src uses tmpSrc and dst
            // uses tmpDst.
            Rect src;
            if (s.kind == SpriteBank.KIND_UNIT) {
                int row = 0;
                if (e.flashTime > 0 && s.attackRow >= 0) row = s.attackRow;
                else if (e.moving) row = ((int) (e.animTime / 0.16f)) % Math.max(1, s.walkRows);
                src = tmpSrc;
                src.set(e.dir * s.fw, row * s.fh, (e.dir + 1) * s.fw, (row + 1) * s.fh);
            } else {
                // buildings and the siege tank: pose 0 (siege tank keeps its own
                // 6-frame sheet, which the manifest now describes correctly)
                src = bank.frameRect(s, 0, tmpSrc);
            }
            float w = s.fw * zoom, h = s.fh * zoom;
            Rect dst = tmpDst;
            dst.set((int) (x - w / 2), (int) (y - h * 0.65f),
                    (int) (x + w / 2), (int) (y + h * 0.35f));
            // v2.22 batch B: a cloaked unit renders as a translucent shimmer.
            // Own units always (the owner can see their own ghosts), enemies
            // only once a detector has revealed them -- the undetected ones
            // never reach this line (the enemyVisible gate above).
            boolean shimmer = e.cloakActive && !e.constructing;
            if (e.constructing) {
                // under construction: draw at 40% alpha
                p.setAlpha(130);
                c.drawBitmap(s.sheet, src, dst, p);
                p.setAlpha(255);
                drawConstruction(c, e, x, y, r);
            } else {
                if (shimmer) p.setAlpha(150);
                c.drawBitmap(s.sheet, src, dst, p);
                if (shimmer) p.setAlpha(255);
                // v2.26: a burrowed unit shows only a faint mound -- the
                // original's dirt clump. The sheet still draws (translucent)
                // so the owner can see and un-burrow it, while the enemy only
                // gets it once a detector is in range (the gate above).
                if (e.burrowed && e.team == 0) {
                    p.setAlpha(90);
                    c.drawOval(x - r * 0.9f, y - r * 0.3f, x + r * 0.9f, y + r * 0.3f, p);
                    p.setAlpha(255);
                }
            }
        }
    }

    /**
     * Under-construction feedback (batch-1 #3): a yellow progress bar over the
     * site and welding sparks where the SCV is working.
     */
    private void drawConstruction(Canvas c, Game.Ent e, float x, float y, float r) {
        float frac = Math.max(0f, Math.min(1f, e.buildProgress));
        float bw = Math.max(18 * zoom, r * 1.6f);
        float by = y - r - 13 * zoom;
        p.setColor(Color.BLACK);
        c.drawRect(x - bw / 2 - 1, by - 1, x + bw / 2 + 1, by + 5 * zoom + 1, p);
        p.setColor(Color.argb(255, 250, 200, 60));
        c.drawRect(x - bw / 2, by, x - bw / 2 + bw * frac, by + 5 * zoom, p);

        // welding sparks: a few jittering bright dots on the site edge
        long t = (long) (game.time * 20);
        for (int i = 0; i < 3; i++) {
            float ang = (t * 0.7f + i * 2.1f) % 6.283f;
            float dx = (float) Math.cos(ang) * r * 0.95f;
            float dy = (float) Math.sin(ang) * r * 0.35f - r * 0.2f;
            float j = ((t + i * 7) % 13) / 13f - 0.5f;
            p.setColor(i % 2 == 0 ? Color.argb(230, 255, 230, 150)
                    : Color.argb(230, 255, 170, 70));
            c.drawCircle(x + dx + j * 3 * zoom, y + dy + j * 2 * zoom,
                    (1.2f + (i % 2)) * zoom, p);
        }
    }

    // ================================================================ console
    // SC-style console HUD. The original glue\Console\*.pcx chrome is not in
    // this repack, so the metal panel is drawn in code; the wireframe
    // portraits, command icons and stat_txt unit names are the real assets.
    private static final int PANEL_DARK = Color.rgb(24, 28, 40);
    private static final int PANEL_MID = Color.rgb(46, 54, 76);
    private static final int PANEL_LITE = Color.rgb(88, 100, 128);
    private static final int PANEL_EDGE = Color.rgb(130, 145, 175);
    private static final int SLOT_DARK = Color.rgb(14, 18, 30);
    private static final int SLOT_EDGE = Color.rgb(70, 82, 108);

    // v2.23 batch A removed the scrims; v2.41 removed the bands themselves.
    // The rule for the whole in-match screen is: the HUD is six independent
    // opaque chips floating on a full-screen map. No band, no hairline rule,
    // no full-width layer of any kind outside the modal menus.

    // v2.23 batch B: the command card 1px separator lines and the opaque chip
    // colours of the name strip / formation chips.
    private static final int CARD_SEP = Color.rgb(56, 66, 90);
    private static final int CHIP_DARK = Color.rgb(12, 16, 26);

    // v2.23 batch C #1: the minimap brightening matrix, shared by the minimap
    // itself and by the chunk placeholder so a still-decoding tile reads the
    // same as the minimap patch it is magnified from (never as a black block).
    private static final android.graphics.ColorMatrix MINIMAP_BRIGHT =
            new android.graphics.ColorMatrix(new float[]{
                    1.45f, 0, 0, 0, 14,
                    0, 1.45f, 0, 0, 14,
                    0, 0, 1.45f, 0, 14,
                    0, 0, 0, 1, 0});

    /**
     * v2.42 batch B: the still-decoding placeholder gets its own, brighter
     * matrix. MINIMAP_BRIGHT lifted a black minimap pixel to rgb(14,14,14) and
     * the 50% veil pulled it back to ~7 -- a "loading" tile that still read as
     * a black block mid-pan, which is exactly the dark flash the player kept
     * reporting. Scale 1.45 + offset 34 keeps the dimmest patch pixel at ~34
     * before the (now lighter) veil, so a loading tile reads as veiled terrain,
     * never as a hole.
     */
    private static final android.graphics.ColorMatrix PLACEHOLDER_BRIGHT =
            new android.graphics.ColorMatrix(new float[]{
                    1.45f, 0, 0, 0, 34,
                    0, 1.45f, 0, 0, 34,
                    0, 0, 1.45f, 0, 34,
                    0, 0, 0, 1, 0});

    /**
     * v2.42 batch B: how many screen pixels a chunk's right/bottom edge
     * overdraws into its neighbour. 1px covered the truncation seam; a real
     * device rasterizer showed wider hairline gaps while panning (the v2.21
     * note), so the bleed now covers that family with margin to spare. The
     * overdraw lands under the neighbour's own draw, so it is invisible.
     */
    private static final int CHUNK_BLEED = 4;

    // ---- v2.19 batch C: the console metrics moved into HudLayout, which is
    // ---- the single generation point for the widget rects and the playfield
    // ---- envelope. These aliases keep the renderer and the hit-tests reading
    // ---- the same numbers they always did. (v2.41: the console-fraction cap
    // ---- retired with the band model.)
    private static final int CARD_COLS = HudLayout.CARD_COLS;
    private static final int CARD_ROWS = HudLayout.CARD_ROWS;
    private static final float CARD_GAP_DP = HudLayout.CARD_GAP_DP;
    private static final float CARD_PAD_DP = HudLayout.CARD_PAD_DP;
    private static final float CELL_DP = HudLayout.CELL_DP;
    private static final float CELL_MIN_DP = HudLayout.CELL_MIN_DP;

    /**
     * v2.42: the widest the selection card is allowed to get, in dp before the
     * layout's S/M/L multiplier. A multi-select used to claim the whole middle
     * strip, so five SCVs drew a 1310px hp bar inside a 1540px slab -- more
     * console than battlefield. 165dp holds the portrait, a three-character
     * Chinese name, an "xN" and the full hp readout, so the card is now the
     * same width whether one SCV is selected or fifty. The only thing that may
     * exceed it is a genuinely mixed group, whose per-type filter row needs one
     * cell per kind (see drawBottomWidgets).
     */
    private static final float INFO_CAP_DP = 165f;

    private float dp(float v) {
        return v * uiScale;
    }

    /**
     * v2.23 batch C #3: how many px of the window the system is holding back.
     * On a healthy immersive fullscreen this is 0/0; a non-zero inset is the
     * fingerprint of a ROM that insets the window for a notch or the gesture
     * bar, which reads on screen as a black band along an edge. Printed in the
     * settings sheet so a real-device report can be triaged at a glance.
     */
    private int insetLeftPx() {
        if (android.os.Build.VERSION.SDK_INT < 28) return 0;
        android.view.WindowInsets wi = getRootWindowInsets();
        return wi == null ? 0 : wi.getSystemWindowInsetLeft();
    }

    private int insetRightPx() {
        if (android.os.Build.VERSION.SDK_INT < 28) return 0;
        android.view.WindowInsets wi = getRootWindowInsets();
        return wi == null ? 0 : wi.getSystemWindowInsetRight();
    }

    // ==================================================== v2.19 step 3: editor
    /**
     * Enter the layout editor from the pause menu. The current arrangement (a
     * saved custom layout, else the active preset) seeds the editable spec so
     * the player starts from what they already see. The game is paused and the
     * editor is modal.
     */
    private void startLayoutEdit() {
        float[] src = customSpec();
        if (src == null) {
            // seed from the preset currently in force
            ensureHud();
            src = new float[HudLayout.SPEC_LEN];
            seedSpecFromRects(src);
        }
        System.arraycopy(src, 0, editSpec, 0, HudLayout.SPEC_LEN);
        layoutEdit = true;
        editDrag = -1;
        editSel = -1;
        menuOpen = false;
        paused = true;
        layoutRev++;
        play("ui_swishin", 0.9f);
    }

    /** Normalise the current hud rects into an editable spec (preset -> spec). */
    private void seedSpecFromRects(float[] out) {
        int W = Math.max(1, getWidth()), H = Math.max(1, getHeight());
        out[0] = hud.minimapSlot.centerX() / W;
        out[1] = hud.minimapSlot.centerY() / H;
        out[2] = sizeIdxFor(hud.minimapSlot.width() / (HudLayout.MINIMAP_DP * uiScale));
        out[3] = hud.card.centerX() / W;
        out[4] = hud.card.centerY() / H;
        out[5] = sizeIdxFor(hud.card.width()
                / (HudLayout.CARD_COLS * HudLayout.CARD_CELL_DP * uiScale
                   + (HudLayout.CARD_COLS - 1) * HudLayout.CARD_GAP_DP * uiScale));
        out[6] = hud.middle.centerX() / W;
        out[7] = hud.middle.centerY() / H;
        out[8] = sizeIdxFor(hud.middle.width() / (HudLayout.INFO_W_DP * uiScale));
        // v2.41: the clock/res chips are panels 3/4 of the spec now
        out[9] = hud.clock.centerX() / W;
        out[10] = hud.clock.centerY() / H;
        out[11] = sizeIdxFor(hud.clock.height() / (HudLayout.CHIP_H_DP * uiScale));
        out[12] = hud.res.centerX() / W;
        out[13] = hud.res.centerY() / H;
        out[14] = sizeIdxFor(hud.res.height() / (HudLayout.CHIP_H_DP * uiScale));
        // v2.42: the control-group block is panel 5
        out[15] = hud.groups.centerX() / W;
        out[16] = hud.groups.centerY() / H;
        out[17] = sizeIdxFor(hud.groups.width()
                / (HudLayout.groupsW(uiScale)));
    }

    private static int sizeIdxFor(float ratio) {
        // nearest of S(0.8) / M(1.0) / L(1.25)
        float best = 1f, bi = 1;
        float[] sc = HudLayout.SIZE_SCALE;
        for (int i = 0; i < 3; i++) {
            float d = Math.abs(ratio - sc[i]);
            if (d < best) { best = d; bi = i; }
        }
        return (int) bi;
    }

    /**
     * Save the edited layout: reject an overlap (the plan's rule), otherwise
     * persist the normalised spec and switch the view to it.
     */
    private void saveLayoutEdit() {
        if (panelsOverlap(editSpec)) {
            toast = "面板重叠,请先分开";
            toastT = 2.0f;
            play("error", 0.9f);
            return;
        }
        settings.layoutNorm = formatSpec(editSpec);
        settings.layoutCustom = true;
        settings.hudPreset = Settings.HUD_CUSTOM;
        commitSettings();
        layoutEdit = false;
        editDrag = -1;
        layoutRev++;
        menuOpen = true;
        paused = true;
        toast = "布局已保存";
        toastT = 1.8f;
        play("build", 1.0f);
    }

    /** Discard the edit and return to the pause menu. */
    private void cancelLayoutEdit() {
        layoutEdit = false;
        editDrag = -1;
        layoutRev++;
        menuOpen = true;
        paused = true;
        play("ui_swishout", 0.9f);
    }

    private static String formatSpec(float[] v) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < HudLayout.SPEC_LEN; i++) {
            if (i > 0) sb.append(',');
            sb.append(String.format(java.util.Locale.US, "%.4f", v[i]));
        }
        return sb.toString();
    }

    /**
     * Parse the persisted spec; null when malformed (falls back to preset).
     * v2.41: a legacy 9-float save (minimap/card/info only) migrates by
     * appending the clock/res anchors from the current default layout.
     * v2.42: a legacy 15-float save migrates by appending the group block's
     * default bottom-strip anchor, so an old custom layout keeps working.
     */
    private float[] parseSpec(String s) {
        if (s == null || s.isEmpty()) return null;
        String[] p = s.split(",");
        if (p.length < 9) return null;
        float[] v = new float[HudLayout.SPEC_LEN];
        try {
            for (int i = 0; i < 9 && i < p.length; i++) v[i] = Float.parseFloat(p[i]);
            if (p.length >= HudLayout.SPEC_LEN) {
                for (int i = 9; i < HudLayout.SPEC_LEN; i++) v[i] = Float.parseFloat(p[i]);
            } else {
                // legacy save: default chip anchors, normalised to this screen
                int W = Math.max(1, getWidth()), H = Math.max(1, getHeight());
                float chipH = HudLayout.CHIP_H_DP * uiScale;
                float clockW = HudLayout.CLOCK_W_DP * uiScale;
                float resW = HudLayout.RES_W_DP * uiScale;
                float chipTop = (topBarH() - chipH) / 2f;
                float pauseS = topBarH() - 10 * uiScale;
                v[9] = (W / 2f) / W;
                v[10] = (chipTop + chipH / 2f) / H;
                v[11] = 1;
                v[12] = (6 * uiScale + pauseS + 10 * uiScale + resW / 2f) / W;
                v[13] = (chipTop + chipH / 2f) / H;
                v[14] = 1;
                if (p.length >= 15) {
                    for (int i = 9; i < 15 && i < p.length; i++) v[i] = Float.parseFloat(p[i]);
                }
                // v2.42: the group block lands where the default preset puts
                // it, computed from the same HudLayout so migration can never
                // disagree with the draw.
                HudLayout t = new HudLayout();
                t.compute(W, H, topBarH(), uiScale, zoom, HudLayout.PRESET_DEFAULT, null);
                v[15] = t.groups.centerX() / W;
                v[16] = t.groups.centerY() / H;
                v[17] = 1;
            }
        } catch (Exception e) {
            return null;
        }
        return v;
    }

    /**
     * Overlap test on the live rects: the plan refuses a save when two panels
     * overlap. Computed from the same HudLayout that will draw them, so the
     * check and the result can never disagree.
     */
    private boolean panelsOverlap(float[] spec) {
        int W = getWidth(), H = getHeight();
        if (W <= 0 || H <= 0) return false;
        HudLayout t = new HudLayout();
        t.compute(W, H, topBarH(), uiScale, zoom,
                HudLayout.PRESET_CUSTOM, spec);
        for (int i = 0; i < HudLayout.PANEL_COUNT; i++)
            for (int j = i + 1; j < HudLayout.PANEL_COUNT; j++)
                if (RectF.intersects(t.panel(i), t.panel(j))) return true;
        return false;
    }

    /** Panels and the Save/Cancel/Size controls for the layout editor. */
    private void drawLayoutEditor(Canvas c, int W, int H) {
        p.setColor(Color.argb(70, 4, 6, 12));
        c.drawRect(0, 0, W, H, p);
        // v2.41: five editable panels -- the clock and resource chips joined
        // v2.42: six -- the control-group block joined
        String[] names = {"小地图", "命令卡", "信息面板", "时间", "资源", "编队"};
        for (int i = 0; i < HudLayout.PANEL_COUNT; i++) {
            RectF r = hud.panel(i);
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(2 * uiScale);
            p.setColor(i == editDrag ? Color.rgb(120, 255, 160)
                    : (i == editSel ? Color.rgb(180, 230, 255) : Color.rgb(255, 210, 110)));
            c.drawRect(r, p);
            p.setStyle(Paint.Style.FILL);
            p.setTextSize(12 * uiScale);
            p.setTextAlign(Paint.Align.CENTER);
            p.setColor(Color.rgb(235, 245, 255));
            c.drawText(names[i] + " " + "SML".charAt(HudLayout.sizeIdx(editSpec[i * 3 + 2]))
                            + (i == editSel ? " \u25c0" : ""),
                    r.centerX(), r.top - 6 * uiScale, p);
            p.setTextAlign(Paint.Align.LEFT);
            // NOTE: the panel itself is NOT registered as a Btn. Panels are
            // hit-tested directly from editSpec in handleLayoutEditTouch, and a
            // Btn here would shadow the S/M/L and Save/Cancel controls that sit
            // on top of a panel (handleButton returns on the first rect that
            // contains the point, and the panels are registered first).
        }
        // size cycles + save/cancel
        float bw = Math.min(150 * uiScale, W * 0.20f);
        float bh = 34 * uiScale;
        float y = H - bh - 10 * uiScale;
        String[][] acts = {
                {"面板大小 S", "ledit:size0"}, {"面板大小 M", "ledit:size1"},
                {"面板大小 L", "ledit:size2"},
        };
        float x = 10 * uiScale;
        for (String[] a : acts) {
            RectF r = new RectF(x, y, x + bw, y + bh);
            bevelPanel(c, r);
            p.setTextAlign(Paint.Align.CENTER);
            p.setTextSize(12 * uiScale);
            p.setColor(Color.rgb(225, 238, 255));
            c.drawText(a[0], r.centerX(), r.centerY() + 4 * uiScale, p);
            p.setTextAlign(Paint.Align.LEFT);
            Btn b = new Btn();
            b.r = r; b.action = a[1]; b.label = a[0];
            buttons.add(b);
            x += bw + 8 * uiScale;
        }
        float bx = W - 10 * uiScale;
        String[][] right = {{"取 消", "ledit:cancel"}, {"保 存", "ledit:save"}};
        for (int i = right.length - 1; i >= 0; i--) {
            RectF r = new RectF(bx - bw, y, bx, y + bh);
            bevelPanel(c, r);
            p.setTextAlign(Paint.Align.CENTER);
            p.setTextSize(13 * uiScale);
            p.setColor(i == 1 ? Color.rgb(120, 255, 160) : Color.rgb(225, 238, 255));
            c.drawText(right[i][0], r.centerX(), r.centerY() + 4 * uiScale, p);
            p.setTextAlign(Paint.Align.LEFT);
            Btn b = new Btn();
            b.r = r; b.action = right[i][1]; b.label = right[i][0];
            buttons.add(b);
            bx -= bw + 8 * uiScale;
        }
        p.setTextAlign(Paint.Align.CENTER);
        p.setTextSize(13 * uiScale);
        drawOutlined(c, "拖动面板调整位置(自动吸附屏幕边)", W / 2f, 24 * uiScale,
                Color.rgb(255, 210, 110));
        p.setTextAlign(Paint.Align.LEFT);
    }

    /** Drag a panel, tap the size buttons, or save/cancel. */
    private void handleLayoutEditTouch(MotionEvent ev) {
        int act = ev.getActionMasked();
        if (act == MotionEvent.ACTION_DOWN) {
            // The S/M/L and Save/Cancel controls sit ON the panels they belong
            // to, so the drag hit-test has to lose to them: otherwise every tap
            // on a control started a drag, ACTION_UP swallowed it, and the
            // editor's own buttons were unreachable.
            for (Btn b : buttons) {
                if (b.action != null && b.action.startsWith("ledit:")
                        && !b.action.startsWith("ledit:panel")
                        && b.r.contains(ev.getX(), ev.getY())) {
                    editDrag = -1;
                    return;
                }
            }
            editDrag = -1;
            // topmost panel wins if they touch
            for (int i = HudLayout.PANEL_COUNT - 1; i >= 0; i--) {
                if (hud.panel(i).contains(ev.getX(), ev.getY())) {
                    editDrag = i;
                    editSel = i;
                    break;
                }
            }
            editDownX = ev.getX();
            editDownY = ev.getY();
            System.arraycopy(editSpec, 0, editStart, 0, HudLayout.SPEC_LEN);
            return;
        }
        if (act == MotionEvent.ACTION_MOVE && editDrag >= 0) {
            int W = Math.max(1, getWidth()), H = Math.max(1, getHeight());
            int b = editDrag * 3;
            editSpec[b] = Game.clamp(editStart[b] + (ev.getX() - editDownX) / W, 0f, 1f);
            editSpec[b + 1] = Game.clamp(editStart[b + 1] + (ev.getY() - editDownY) / H, 0f, 1f);
            layoutRev++;
            return;
        }
        if (act == MotionEvent.ACTION_UP) {
            if (editDrag >= 0) { editDrag = -1; return; }
            if (handleButton(ev.getX(), ev.getY())) return;
        }
    }

    /** Layout-editor button actions. */
    private void handleLayoutEditAction(String action) {
        if (action.equals("ledit:save")) { saveLayoutEdit(); return; }
        if (action.equals("ledit:cancel")) { cancelLayoutEdit(); return; }
        if (action.startsWith("ledit:size")) {
            int sz = action.charAt(action.length() - 1) - '0';
            // apply to whichever panel the last tap selected, else all five
            int[] targets = editSel >= 0 ? new int[]{editSel}
                    : new int[]{0, 1, 2, 3, 4};
            for (int t : targets) editSpec[t * 3 + 2] = sz;
            layoutRev++;
            play("click", 0.8f);
        }
    }

    private float topBarH() {
        return dp(40);
    }

    /**
     * Command-cell edge in px.
     *
     * On a short screen (a 720p phone at density 2 is only 360dp tall) three
     * 50dp rows would eat a third of the viewport, so the cell is squeezed
     * down to CELL_MIN_DP. That floor is deliberate: shrinking further would
     * make the buttons untappable, which is worse than a cramped card.
     */
    private float cardCell() {
        // v2.19 batch C: geometry now lives in HudLayout (single source).
        return HudLayout.cardCell(getHeight(), uiScale);
    }

    private boolean menuOpen;
    /** v2.7 batch 7.2: the settings sheet is modal over the pause menu. */
    private boolean settingsOpen;
    /** True while the settings volume slider is being dragged. */
    private boolean volumeDragging;
    /** v2.7 7.4: two-finger tap on the minimap issues a move order. */
    private long twoFingerAt;
    private float twoFingerX, twoFingerY;
    private boolean twoFingerArmed;

    // ---- v2.7 batch 8: mission state
    private Mission mission;
    /**
     * v2.37: non-null while this match is a LAN match. The game loop drives the
     * three lockstep phases through it instead of calling game.update directly.
     */
    private com.xjzb.rts.core.LockstepPeer net;
    /**
     * v2.29: the mission JSON this view was launched with, kept so the pause
     * menu's restart can re-parse and re-install the level. Restart used to
     * rebuild a bare Game and silently lose the mission.
     */
    private final String missionJson;
    /** Briefing lines shown one at a time before the mission starts. */
    private List<String> briefing = new ArrayList<>();
    private int briefingLine;
    private boolean briefingOpen;
    /** Scrolling mission messages (event `message` actions). */
    private final List<String> missionMsgs = new ArrayList<>();
    private final List<Float> missionMsgT = new ArrayList<>();
    /** Objectives completed at the moment the result was decided. */
    private boolean resultShown;
    /** Set once the campaign unlock for this run has been persisted. */
    private boolean campaignRecorded;

    private void drawHud(Canvas c, int W, int H) {
        buttons.clear();
        drawTopChips(c, W, topBarH());
        drawBottomWidgets(c, W, H);
        drawToast(c, W, H);
        if (menuOpen) {
            drawPauseMenu(c, W, H);
            if (settingsOpen) {
                // The sheet is modal: drop the pause menu's buttons so a tap
                // that misses a settings control cannot reach restart/quit.
                buttons.clear();
                drawSettings(c, W, H);
            }
        }
        drawMissionHud(c, W, H);
        if (briefingOpen) drawBriefing(c, W, H);
        if (layoutEdit) drawLayoutEditor(c, W, H);
        if (replayPlaying) drawReplayBanner(c, W, H);
        drawWinLose(c, W, H);
        // v2.42: last, so nothing draws over the readout.
        if (settings.renderDiag) drawDiagPanel(c, W, H);
    }

    /**
     * v2.42: the on-screen half of the black-bar instrument.
     *
     * logcat is the wrong place for this bug. The bar only exists DURING a
     * fling and is gone the moment the finger stops, so by the time anyone
     * reads a log the evidence is stale -- and a phone in the field has no
     * adb attached at all. So the readout lives on the screen and LATCHES the
     * worst frame: peak miss count, the chunk keys that were missing, the
     * camera and zoom that produced them. A fling, then a screenshot, and the
     * numbers are still there.
     *
     * Reading it:
     *   peak > 0  -> the black bar IS undecoded chunks (decode path).
     *   peak == 0 -> nothing was missing, so the bar is NOT a decode miss:
     *                look at the green (bare canvas = dst gap) or at an
     *                overlay drawn on top.
     */
    private void drawDiagPanel(Canvas c, int W, int H) {
        // Never over a modal sheet. The readout sits top-left, right where the
        // settings sheet puts its first rows -- and the diagnostic must stay
        // switchable OFF, which is the one thing the user has to be able to do.
        // The latched peak survives in the fields, so it is still there when
        // the sheet closes.
        if (menuOpen || briefingOpen || layoutEdit) return;
        p.setTextAlign(Paint.Align.LEFT);
        p.setTextSize(10 * uiScale);
        float pad = 5 * uiScale;
        float lh = 12 * uiScale;
        String[] lines = new String[]{
                "渲染诊断(黑条排查)",
                "map=" + (game.mapId == null ? "?" : game.mapId)
                        + "  zoom=" + String.format("%.2f", zoom),
                "cam=(" + Math.round(camX) + "," + Math.round(camY) + ")"
                        + "  fog=" + settings.fogStyle,
                "miss 本帧=" + diagMissNow + "  峰值=" + diagMissPeak
                        + "  峰值后=" + diagPeakAge + "帧",
                "峰值 cam=" + (diagPeakCam.isEmpty() ? "-" : diagPeakCam),
                "峰值 chunks=" + (diagPeakKeys.isEmpty() ? "-" : diagPeakKeys),
                "峰值 miss=" + diagMissPeak,
                // v2.43: the stutter numbers ride along in the same readout, so
                // a phone with no adb can still report what the frame budget is
                // being spent on. Same panel, same toggle -- no new setting.
                perfLine.isEmpty() ? "性能 (等采样…)" : perfLine,
                perfLine2.isEmpty() ? "" : perfLine2,
        };
        float wMax = 0;
        for (String s : lines) wMax = Math.max(wMax, p.measureText(s));
        for (String s : diagLog) wMax = Math.max(wMax, p.measureText(s));
        float bw = Math.min(W - 2 * pad, wMax + 2 * pad);
        float bh = pad * 2 + lh * lines.length;
        float x = pad, y = topBarH() + pad;
        p.setStyle(Paint.Style.FILL);
        p.setColor(Color.argb(200, 0, 0, 0));
        c.drawRect(x, y, x + bw, y + bh, p);
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(1);
        p.setColor(diagMissPeak > 0 ? Color.rgb(255, 80, 80) : Color.rgb(0, 255, 0));
        c.drawRect(x, y, x + bw, y + bh, p);
        p.setStyle(Paint.Style.FILL);
        float ty = y + pad + 10 * uiScale;
        for (int i = 0; i < lines.length; i++) {
            p.setColor(i == 0 ? Color.rgb(255, 220, 120)
                    : (i >= 3 && i <= 6 && diagMissPeak > 0) ? Color.rgb(255, 150, 150)
                    : Color.rgb(220, 235, 255));
            c.drawText(lines[i], x + pad, ty, p);
            ty += lh;
        }
        // The raw miss lines, newest last -- the same text logcat would show.
        // Show the TAIL of the buffer, not the head: the most recent misses are
        // the ones from the fling just performed.
        p.setTextSize(9 * uiScale);
        p.setColor(Color.rgb(160, 220, 255));
        int total = diagLog.size();
        int skip = Math.max(0, total - 8);
        int idx = 0;
        for (String s : diagLog) {
            if (idx++ < skip) continue;
            c.drawText(s, x + pad, ty, p);
            ty += 10 * uiScale;
        }
        p.setTextSize(10 * uiScale);
    }

    /** v2.19 batch 5: a small always-on badge so the player knows it is a replay. */
    private void drawReplayBanner(Canvas c, int W, int H) {
        String s = game.replayFinished() ? "回放结束" : "回 放 中";
        p.setTextSize(13 * uiScale);
        float tw = p.measureText(s) + 24 * uiScale;
        float bh = 24 * uiScale;
        float x = W / 2f - tw / 2f, y = hud.clock.bottom + 6 * uiScale;
        p.setColor(Color.argb(190, 20, 10, 10));
        c.drawRect(x, y, x + tw, y + bh, p);
        p.setStyle(Paint.Style.STROKE);
        p.setColor(Color.rgb(255, 180, 80));
        c.drawRect(x, y, x + tw, y + bh, p);
        p.setStyle(Paint.Style.FILL);
        p.setTextAlign(Paint.Align.CENTER);
        c.drawText(s, W / 2f, y + bh * 0.7f, p);
        p.setTextAlign(Paint.Align.LEFT);
    }

    /**
     * Red error banner at the top of the console (batch-1 #2): tells the player
     * WHY the last order failed instead of just beeping. Fades over 2 s.
     */
    private void drawToast(Canvas c, int W, int H) {
        if (toast == null || toastT <= 0) return;
        p.setTextSize(13 * uiScale);
        float tw = p.measureText(toast);
        float padX = 14 * uiScale, bh = 22 * uiScale;
        // v2.41: anchor above the bottom widgets (the taller of card/minimap),
        // not above a console band -- there is no band any more.
        float botTop = Math.min(hud.minimapSlot.top, hud.card.top);
        if (botTop >= H) botTop = H;
        float y = botTop - bh - 6 * uiScale;
        float a = Math.min(1f, toastT / 0.6f);
        // v2.23 batch A #5: the toast is a permanent-ish part of the match
        // picture, so it is an OPAQUE deep chip, not a semi-see-through banner.
        // The chip fades in/out as a whole (alpha on the whole chip), never a
        // half-transparent fill sitting over the map at full strength.
        RectF chip = new RectF(W / 2f - tw / 2 - padX, y,
                W / 2f + tw / 2 + padX, y + bh);
        int keep = p.getAlpha();
        p.setAlpha((int) (255 * a));
        p.setColor(CHIP_DARK);
        c.drawRect(chip, p);
        p.setStyle(Paint.Style.STROKE);
        p.setColor(Color.rgb(200, 60, 50));
        c.drawRect(chip.left + 0.5f, chip.top + 0.5f, chip.right - 0.5f,
                chip.bottom - 0.5f, p);
        p.setStyle(Paint.Style.FILL);
        p.setAlpha(keep);
        p.setTextAlign(Paint.Align.CENTER);
        drawOutlined(c, toast, W / 2f, y + bh * 0.72f,
                Color.argb((int) (255 * a), 255, 120, 110));
        p.setTextAlign(Paint.Align.LEFT);
    }

    /**
     * v2.7 batch 7.2: pull the persisted settings into the live fields. Volume
     * used to be a view field that nothing saved; now Settings owns it and this
     * is the single place it is copied in, so the pause menu, the touch code
     * and the BGM player cannot drift apart.
     */
    private void applySettings() {
        volume = settings.volume;
        applyBgmVolume();
        // v2.18 batch B: adopting the preset resets the live zoom to its default.
        // Called at construction and whenever the zoom preset changes.
        // v2.42 fix (defect B): write both copies, or the next adopted snapshot
        // would immediately undo the preset.
        setZoomNow(Settings.zoomDefault(settings.zoomLevel));
    }

    /** Persist + apply in one step, used by every settings control. */
    private void commitSettings() {
        settings.volume = volume;
        settings.save();
        applyBgmVolume();
    }

    /**
     * Settings sheet (v2.7 batch 7.2). Opened from the pause menu, it is the
     * home for the knobs that used to be hardcoded or missing:
     *   - drag sensitivity + box-select hold  (the v2.6 "retune me" debt)
     *   - a continuous volume slider          (the v2.4 "5 steps only" debt)
     *   - an edge-scroll toggle               (accidental panning complaints)
     */
    private void drawSettings(Canvas c, int W, int H) {
        p.setColor(Color.argb(200, 4, 6, 12));
        c.drawRect(0, 0, W, H, p);
        float bw = Math.min(560 * uiScale, W * 0.90f);
        float x0 = W / 2f - bw / 2f;

        float titleH = 34 * uiScale;
        float backH = 40 * uiScale;
        float rowGap = 8 * uiScale;
        float bodyTop = H * 0.10f + titleH;
        float bodyBottom = H - 16 * uiScale - backH - rowGap;

        // v2.18: the sheet is a two-column grid now. Seven controls in one
        // column did not fit a 720p phone (rowPitch 90px left a 50px control),
        // so it is four rows: three paired rows plus a full-width volume row.
        // v2.19: five rows now (the layout preset joined the sheet).
        // v2.42: six rows -- the render diagnostic toggle joined, so the black
        // bar report comes with an on-device instrument instead of screenshots
        // that cannot say which layer they are looking at.
        int rows = 6;
        float rowPitch = (bodyBottom - bodyTop) / rows;
        float colGap = 16 * uiScale;
        float colW = (bw - colGap) / 2f;
        float labelH = 18 * uiScale;
        float ctrlH = Math.min(38 * uiScale, rowPitch - labelH - 6 * uiScale);
        ctrlH = Math.max(24 * uiScale, ctrlH);

        p.setTextAlign(Paint.Align.CENTER);
        p.setTextSize(20 * uiScale);
        drawOutlined(c, "设 置", W / 2f, H * 0.10f + 20 * uiScale, Color.rgb(255, 210, 110));
        // v2.23 batch C #3: a device self-check for the black-edge report, on
        // the title line so it never fights the layout row. 满屏 means the
        // window owns the whole screen; a non-zero inset means the ROM is
        // holding back a notch/nav strip -- the number says how many px, so a
        // screenshot tells cutout from chunk from seam.
        int insL = insetLeftPx(), insR = insetRightPx();
        p.setTextSize(11 * uiScale);
        p.setColor(insL + insR == 0 ? Color.rgb(150, 220, 160)
                : Color.rgb(255, 190, 120));
        c.drawText(insL + insR == 0 ? "屏幕: 满屏"
                        : ("屏幕: 被系统内缩 " + (insL + insR) + "px"),
                W / 2f, H * 0.10f + 36 * uiScale, p);
        p.setTextAlign(Paint.Align.LEFT);

        float rightX = x0 + colW + colGap;
        float y = bodyTop;

        // ---- row 0: drag sensitivity | zoom preset
        segmented(c, x0, y, colW, labelH, ctrlH, "拖动灵敏度",
                Settings.sensitivityName(settings.sensitivity()), "set:sens", "灵敏度",
                new String[]{Settings.sensitivityName(0), Settings.sensitivityName(1),
                        Settings.sensitivityName(2)}, settings.sensitivity(), 3);
        segmented(c, rightX, y, colW, labelH, ctrlH, "画面缩放",
                Settings.zoomName(settings.zoomLevel), "set:zoom", "画面缩放",
                new String[]{Settings.zoomName(0), Settings.zoomName(1),
                        Settings.zoomName(2)}, settings.zoomLevel, 3);
        y += rowPitch;

        // ---- row 1: box-select hold | vision mode
        segmented(c, x0, y, colW, labelH, ctrlH, "框选长按",
                Settings.holdName(settings.holdLevel()), "set:hold", "长按",
                new String[]{Settings.holdName(0), Settings.holdName(1),
                        Settings.holdName(2)}, settings.holdLevel(), 3);
        segmented(c, rightX, y, colW, labelH, ctrlH, "视野模式",
                Settings.fogStyleName(settings.fogStyle), "set:fog", "视野模式",
                new String[]{Settings.fogStyleName(0), Settings.fogStyleName(1)},
                settings.fogStyle, 2);
        y += rowPitch;

        // ---- row 2: full-width continuous volume
        settingsRow(c, x0, y, bw, "音量", Math.round(volume * 100) + "%");
        RectF track = new RectF(x0, y + labelH, x0 + bw, y + labelH + ctrlH);
        bevelSlot(c, track);
        float fillR = track.left + 4 * uiScale
                + (track.width() - 8 * uiScale) * volume;
        p.setColor(Color.rgb(90, 200, 255));
        c.drawRect(track.left + 4 * uiScale, track.centerY() - 3 * uiScale,
                fillR, track.centerY() + 3 * uiScale, p);
        RectF knob = new RectF(fillR - 9 * uiScale, track.top + 3 * uiScale,
                fillR + 9 * uiScale, track.bottom - 3 * uiScale);
        p.setColor(Color.rgb(225, 238, 255));
        c.drawRect(knob, p);
        Btn vol = new Btn();
        vol.r = track;
        vol.action = "set:vol";
        vol.label = "音量";
        buttons.add(vol);
        y += rowPitch;

        // ---- row 3: edge scroll | always-show-hp
        toggle(c, x0, y, colW, labelH, ctrlH, "边缘卷动", settings.edgeScroll, "set:edge");
        toggle(c, rightX, y, colW, labelH, ctrlH, "始终显示血条",
                settings.alwaysShowHp, "set:hp");
        y += rowPitch;

        // ---- v2.19 batch C: console layout preset
        // v2.20 step 3: 自定义 joins the row once the editor has saved a spec.
        // Without one it is still listed but marked "未保存", and tapping it is
        // a no-op, so the player is told what to do instead of landing on a
        // preset that silently looks like 默认.
        boolean hasCustom = settings.layoutCustom && customSpec() != null;
        String customName = hasCustom ? Settings.layoutName(Settings.HUD_CUSTOM) : "未保存";
        segmented(c, x0, y, bw, labelH, ctrlH, "界面布局",
                hasCustom || settings.hudPreset != Settings.HUD_CUSTOM
                        ? Settings.layoutName(settings.hudPreset) : "未保存",
                "set:layout", "界面布局",
                new String[]{Settings.layoutName(0), Settings.layoutName(1),
                        Settings.layoutName(2), customName},
                settings.hudPreset, 4);
        y += rowPitch;

        // ---- v2.42 batch B: render diagnostic (the black-bar instrument)
        toggle(c, x0, y, bw, labelH, ctrlH, "渲染诊断(黑条排查)",
                settings.renderDiag, "set:diag");

        RectF back = new RectF(W / 2f - 120 * uiScale, H - 16 * uiScale - backH,
                W / 2f + 120 * uiScale, H - 16 * uiScale);
        bevelPanel(c, back);
        p.setTextAlign(Paint.Align.CENTER);
        p.setTextSize(14 * uiScale);
        p.setColor(Color.rgb(225, 238, 255));
        c.drawText("返 回", back.centerX(), back.centerY() + 5 * uiScale, p);
        p.setTextAlign(Paint.Align.LEFT);
        Btn bb = new Btn();
        bb.r = back;
        bb.action = "set:back";
        bb.label = "返回";
        buttons.add(bb);
    }

    /**
     * v2.18: one settings cell rendered as a labelled segmented control. `names`
     * has `count` entries; the selected one is highlighted and each cell becomes
     * a button whose action is actionPrefix + index (e.g. "set:zoom" + "2").
     */
    private void segmented(Canvas c, float x, float y, float w, float labelH,
                           float ctrlH, String label, String value, String actionPrefix,
                           String btnLabel, String[] names, int selected, int count) {
        settingsRow(c, x, y, w, label, value);
        float gap = 6 * uiScale;
        float cw = (w - (count - 1) * gap) / count;
        for (int i = 0; i < count; i++) {
            RectF r = new RectF(x + i * (cw + gap), y + labelH,
                    x + i * (cw + gap) + cw, y + labelH + ctrlH);
            bevelSlot(c, r);
            boolean on = selected == i;
            p.setTextAlign(Paint.Align.CENTER);
            p.setTextSize(13 * uiScale);
            p.setColor(on ? Color.rgb(120, 255, 160) : Color.rgb(160, 180, 205));
            c.drawText(names[i], r.centerX(), r.centerY() + 5 * uiScale, p);
            p.setTextAlign(Paint.Align.LEFT);
            Btn b = new Btn();
            b.r = r;
            b.action = actionPrefix + i;
            b.label = btnLabel;
            buttons.add(b);
        }
    }

    /** v2.18: one settings cell rendered as an on/off toggle. */
    private void toggle(Canvas c, float x, float y, float w, float labelH,
                        float ctrlH, String label, boolean on, String action) {
        settingsRow(c, x, y, w, label, on ? "开" : "关");
        RectF r = new RectF(x, y + labelH, x + w, y + labelH + ctrlH);
        bevelPanel(c, r);
        p.setTextAlign(Paint.Align.CENTER);
        p.setTextSize(13 * uiScale);
        p.setColor(on ? Color.rgb(120, 255, 160) : Color.rgb(180, 150, 150));
        c.drawText(on ? "开  启" : "关  闭", r.centerX(), r.centerY() + 5 * uiScale, p);
        p.setTextAlign(Paint.Align.LEFT);
        Btn b = new Btn();
        b.r = r;
        b.action = action;
        b.label = label;
        buttons.add(b);
    }
    private void setVolumeFromX(float x, RectF track) {
        float t = (x - (track.left + 4 * uiScale))
                / Math.max(1f, track.width() - 8 * uiScale);
        volume = Game.clamp(t, 0f, 1f);
        applyBgmVolume();
    }

    /** One settings row: label on the left, current value on the right. */
    private void settingsRow(Canvas c, float x0, float y, float bw,
                             String label, String value) {
        p.setTextAlign(Paint.Align.LEFT);
        p.setTextSize(14 * uiScale);
        p.setColor(Color.rgb(210, 226, 246));
        c.drawText(label, x0, y + 14 * uiScale, p);
        p.setTextAlign(Paint.Align.RIGHT);
        p.setColor(Color.rgb(255, 224, 140));
        c.drawText(value, x0 + bw, y + 14 * uiScale, p);
        p.setTextAlign(Paint.Align.LEFT);
    }

    /**
     * v2.7 batch 8: mission objective list under the top chips, plus any active
     * event messages. Objectives tick as they resolve so the player can see
     * progress without opening a menu.
     */
    private void drawMissionHud(Canvas c, int W, int H) {
        // v2.41: anchor below the top chips (pause is the tallest), not below
        // a top-bar band.
        float y = Math.max(hud.pause.bottom, hud.res.bottom) + 12 * uiScale;
        if (mission != null) {
            p.setTextSize(12 * uiScale);
            p.setTextAlign(Paint.Align.LEFT);
            for (Mission.Objective o : mission.objectives) {
                String mark = o.failed ? "✗" : o.done ? "✓" : "•";
                int col = o.failed ? Color.rgb(255, 110, 100)
                        : o.done ? Color.rgb(120, 255, 150)
                        : Color.rgb(215, 228, 248);
                String label = (o.optional ? "[可选] " : "") + mark + " " + o.desc;
                if (o.kind.equals("survive") && !o.done) {
                    int left = Math.max(0, (int) (o.time - mission.elapsed()));
                    label += "  " + (left / 60) + ":" + String.format("%02d", left % 60);
                }
                drawOutlined(c, label, 10 * uiScale, y, col);
                y += 16 * uiScale;
            }
        }
        // mission messages stack above the bottom widgets
        float my = Math.min(hud.minimapSlot.top, hud.card.top) - 14 * uiScale;
        p.setTextAlign(Paint.Align.CENTER);
        p.setTextSize(13 * uiScale);
        for (int i = missionMsgs.size() - 1; i >= 0; i--) {
            float a = Math.min(1f, missionMsgT.get(i) / 0.8f);
            drawOutlined(c, missionMsgs.get(i), W / 2f, my,
                    Color.argb((int) (255 * a), 255, 226, 150));
            my -= 18 * uiScale;
        }
        p.setTextAlign(Paint.Align.LEFT);
    }

    /**
     * v2.7 batch 8: pre-mission briefing. Uses the original title art as the
     * backdrop, shows one line at a time and advances on tap -- the original
     * campaign's subtitle cadence, minus voice-over (this repack has none).
     */
    private void drawBriefing(Canvas c, int W, int H) {
        p.setColor(Color.argb(225, 4, 6, 12));
        c.drawRect(0, 0, W, H, p);
        // The title art is 640x480 (4:3). Cap its height to the band above the
        // heading or it runs straight through the briefing text on a 16:9
        // phone (measured: 576px of art over a heading at 0.42*H).
        float nameY = H * 0.62f;
        float artTop = H * 0.08f;
        float artMaxH = nameY - artTop - 20 * uiScale;
        if (titleBmp != null && artMaxH > 0) {
            float tw = Math.min(W * 0.5f, 640 * uiScale);
            float th = tw * titleBmp.getHeight() / (float) titleBmp.getWidth();
            if (th > artMaxH) {
                th = artMaxH;
                tw = th * titleBmp.getWidth() / (float) titleBmp.getHeight();
            }
            float tx = W / 2f - tw / 2f;
            p.setAlpha(200);
            c.drawBitmap(titleBmp, null, new RectF(tx, artTop, tx + tw, artTop + th), p);
            p.setAlpha(255);
        }
        String name = mission != null && !mission.name.isEmpty() ? mission.name : "任务简报";
        p.setTextAlign(Paint.Align.CENTER);
        p.setTextSize(22 * uiScale);
        drawOutlined(c, name, W / 2f, nameY, Color.rgb(255, 210, 110));

        int shown = Math.min(briefingLine, briefing.size() - 1);
        if (shown >= 0 && !briefing.isEmpty()) {
            // shrink a long line until it fits the viewport instead of running
            // off both edges
            String line = briefing.get(shown);
            float size = 15 * uiScale;
            p.setTextSize(size);
            float maxW = W * 0.9f;
            while (size > 9 * uiScale && p.measureText(line) > maxW) {
                size -= uiScale;
                p.setTextSize(size);
            }
            drawOutlined(c, line, W / 2f, H * 0.78f, Color.rgb(220, 232, 250));
        }
        p.setTextSize(12 * uiScale);
        p.setColor(Color.rgb(150, 170, 200));
        c.drawText("点击继续  " + Math.min(briefingLine + 1, briefing.size())
                + "/" + briefing.size(), W / 2f, H * 0.92f, p);
        p.setTextAlign(Paint.Align.LEFT);
    }

    private void drawPauseMenu(Canvas c, int W, int H) {
        p.setColor(Color.argb(175, 4, 6, 12));
        c.drawRect(0, 0, W, H, p);
        float bw = Math.min(260 * uiScale, W * 0.7f);
        float bh = 42 * uiScale;
        float y = H * 0.22f;
        p.setTextAlign(Paint.Align.CENTER);
        p.setTextSize(19 * uiScale);
        drawOutlined(c, "菜 单", W / 2f, y - 14 * uiScale, Color.rgb(255, 210, 110));
        p.setTextAlign(Paint.Align.LEFT);

        // 2-column grid keeps the menu short enough for small screens now that
        // save / load / music toggles joined it
        String[][] items = {
                {"继 续", "menu:resume"}, {"重 新 开 始", "menu:restart"},
                {"存 档", "menu:save"}, {"读 档", "menu:load"},
                {"音乐:" + (bgmOn ? "开" : "关"), "menu:bgm"},
                {"设 置", "menu:settings"},
                {"布 局 编 辑", "menu:layoutedit"},
                {"保 存 回 放", "menu:savereplay"},
                {"观 看 回 放", "menu:playreplay"},
                {"返 回 主 菜 单", "menu:quit"},
        };
        float cw = bw / 2f - 5 * uiScale;
        for (int i = 0; i < items.length; i++) {
            float x = W / 2f - bw / 2 + (i % 2) * (cw + 10 * uiScale);
            RectF r = new RectF(x, y, x + cw, y + bh);
            bevelPanel(c, r);
            p.setTextAlign(Paint.Align.CENTER);
            p.setTextSize(14 * uiScale);
            p.setColor(Color.rgb(225, 238, 255));
            c.drawText(items[i][0], r.centerX(), y + bh * 0.68f, p);
            p.setTextAlign(Paint.Align.LEFT);
            Btn b = new Btn();
            b.r = r;
            b.action = items[i][1];
            b.label = items[i][0];
            buttons.add(b);
            if (i % 2 == 1) y += bh + 10 * uiScale;
        }
        // volume row
        RectF vr = new RectF(W / 2f - bw / 2, y, W / 2f + bw / 2, y + bh);
        bevelPanel(c, vr);
        p.setTextAlign(Paint.Align.CENTER);
        p.setTextSize(14 * uiScale);
        p.setColor(Color.rgb(225, 238, 255));
        c.drawText("音量 " + Math.round(volume * 100) + "%"
                + (bgmTrack.startsWith("(") ? "" : "  ♪" + bgmTrack), W / 2f, y + bh * 0.66f, p);
        p.setTextAlign(Paint.Align.LEFT);
        float bs = bh * 0.62f;
        RectF minus = new RectF(vr.left + 8 * uiScale, y + (bh - bs) / 2,
                vr.left + 8 * uiScale + bs, y + (bh - bs) / 2 + bs);
        RectF plus = new RectF(vr.right - 8 * uiScale - bs, y + (bh - bs) / 2,
                vr.right - 8 * uiScale, y + (bh - bs) / 2 + bs);
        for (int i = 0; i < 2; i++) {
            RectF r = i == 0 ? minus : plus;
            bevelSlot(c, r);
            p.setColor(Color.rgb(200, 225, 250));
            p.setTextSize(16 * uiScale);
            p.setTextAlign(Paint.Align.CENTER);
            c.drawText(i == 0 ? "−" : "+", r.centerX(), r.centerY() + 5 * uiScale, p);
            p.setTextAlign(Paint.Align.LEFT);
            Btn b = new Btn();
            b.r = r;
            b.action = i == 0 ? "menu:vol-" : "menu:vol+";
            b.label = "音量";
            buttons.add(b);
        }
    }

    /**
     * v2.41: the top of the screen is four INDEPENDENT opaque chips floating
     * on the full-screen map -- pause, resources, clock, team tally. There is
     * no band and no hairline rule any more: the gaps between the chips are
     * live battlefield (inHud only claims the chip rects).
     */
    private void drawTopChips(Canvas c, int W, float topH) {
        // pause/menu chip, top-left (batch-4 #13), rect from the layout
        RectF pr = new RectF(hud.pause);
        bevelPanel(c, pr);
        p.setColor(Color.rgb(220, 232, 250));
        float bs = pr.width();
        float bw = bs * 0.16f;
        c.drawRect(pr.left + bs * 0.28f, pr.top + bs * 0.24f,
                pr.left + bs * 0.28f + bw, pr.bottom - bs * 0.24f, p);
        c.drawRect(pr.right - bs * 0.28f - bw, pr.top + bs * 0.24f,
                pr.right - bs * 0.28f, pr.bottom - bs * 0.24f, p);
        Btn pb = new Btn();
        pb.r = pr;
        pb.action = "menu:toggle";
        pb.label = "菜单";
        buttons.add(pb);

        // resource chip: the three readouts on one line, shrunk until they fit
        boolean capped = game.supplyUsed >= game.supplyCap && game.supplyCap > 0;
        bevelPanel(c, hud.res);
        String sMin = "晶体 " + game.mineralsPlayer;
        String sGas = "瓦斯 " + game.gasPlayer;
        String sSup = "人口 " + game.supplyUsed + "/" + game.supplyCap;
        float resMax = hud.res.width() - 12 * uiScale;
        float size = 13 * uiScale;
        p.setTextSize(size);
        while (size > 9 * uiScale
                && p.measureText(sMin) + p.measureText(sGas) + p.measureText(sSup)
                   + 16 * uiScale > resMax) {
            size -= 0.5f * uiScale;
            p.setTextSize(size);
        }
        float ty = hud.res.centerY() - (p.ascent() + p.descent()) / 2f;
        float x = hud.res.left + 6 * uiScale;
        drawRes(c, sMin, x, ty, Color.rgb(140, 220, 255));
        x += p.measureText(sMin) + 8 * uiScale;
        drawRes(c, sGas, x, ty, Color.rgb(150, 255, 150));
        x += p.measureText(sGas) + 8 * uiScale;
        drawRes(c, sSup, x, ty,
                capped ? Color.rgb(255, 110, 90) : Color.rgb(220, 230, 250));
        if (capped) {   // the whole chip warns, not just the number
            p.setStyle(Paint.Style.STROKE);
            p.setColor(Color.rgb(255, 110, 90));
            c.drawRect(hud.res.left + 0.5f, hud.res.top + 0.5f,
                    hud.res.right - 0.5f, hud.res.bottom - 0.5f, p);
            p.setStyle(Paint.Style.FILL);
        }

        // clock chip
        bevelPanel(c, hud.clock);
        int t = (int) game.time;
        drawChipText(c, String.format("%02d:%02d", t / 60, t % 60), hud.clock,
                14 * uiScale, Color.rgb(230, 236, 248));

        // team-tally chip: hidden when a custom layout parks the clock over it
        if (!hud.tally.isEmpty() && !RectF.intersects(hud.clock, hud.tally)) {
            bevelPanel(c, hud.tally);
            drawChipText(c, "我方 " + countTeam(0) + "  敌方 " + countTeam(1),
                    hud.tally, 13 * uiScale, Color.rgb(220, 230, 250));
        }
        p.setTextAlign(Paint.Align.LEFT);
    }

    /** Draw a string centred in a chip, shrinking until it fits (v2.41). */
    private void drawChipText(Canvas c, String s, RectF r, float size, int color) {
        p.setTextSize(size);
        float maxW = r.width() - 8 * uiScale;
        while (size > 8 * uiScale && p.measureText(s) > maxW) {
            size -= 0.5f * uiScale;
            p.setTextSize(size);
        }
        p.setTextAlign(Paint.Align.CENTER);
        drawOutlined(c, s, r.centerX(),
                r.centerY() - (p.ascent() + p.descent()) / 2f, color);
    }

    private void drawRes(Canvas c, String s, float x, float y, int color) {
        // v2.6 #B: the top bar lost its opaque backing, so a single bottom-right
        // shadow is no longer enough over bright terrain -- full 1px outline.
        p.setColor(Color.BLACK);
        c.drawText(s, x - 1, y - 1, p);
        c.drawText(s, x + 1, y - 1, p);
        c.drawText(s, x - 1, y + 1, p);
        c.drawText(s, x + 1, y + 1, p);
        p.setColor(color);
        c.drawText(s, x, y, p);
    }

    /** Embossed panel bevel: lite top/left, dark bottom/right. */
    private void bevelPanel(Canvas c, RectF r) {
        p.setColor(PANEL_MID);
        c.drawRect(r, p);
        p.setColor(PANEL_LITE);
        c.drawRect(r.left, r.top, r.right, r.top + 2 * uiScale, p);
        c.drawRect(r.left, r.top, r.left + 2 * uiScale, r.bottom, p);
        p.setColor(PANEL_DARK);
        c.drawRect(r.left, r.bottom - 2 * uiScale, r.right, r.bottom, p);
        c.drawRect(r.right - 2 * uiScale, r.top, r.right, r.bottom, p);
        p.setColor(PANEL_EDGE);
        p.setStyle(Paint.Style.STROKE);
        c.drawRect(r.left + 0.5f, r.top + 0.5f, r.right - 0.5f, r.bottom - 0.5f, p);
        p.setStyle(Paint.Style.FILL);
    }

    /** Recessed slot for the minimap frame and command-card cells. */
    private void bevelSlot(Canvas c, RectF r) {
        p.setColor(SLOT_DARK);
        c.drawRect(r, p);
        p.setColor(PANEL_DARK);
        c.drawRect(r.left, r.top, r.right, r.top + 2 * uiScale, p);
        c.drawRect(r.left, r.top, r.left + 2 * uiScale, r.bottom, p);
        p.setColor(PANEL_LITE);
        c.drawRect(r.left, r.bottom - 1.5f * uiScale, r.right, r.bottom, p);
        c.drawRect(r.right - 1.5f * uiScale, r.top, r.right, r.bottom, p);
        p.setColor(SLOT_EDGE);
        p.setStyle(Paint.Style.STROKE);
        c.drawRect(r.left + 0.5f, r.top + 0.5f, r.right - 0.5f, r.bottom - 0.5f, p);
        p.setStyle(Paint.Style.FILL);
    }

    private void drawBottomWidgets(Canvas c, int W, int H) {
        // v2.41: no console band. The minimap, the info widget and the command
        // card are three independent opaque chips floating on the map; between
        // them and around them the battlefield shows and takes taps. A custom
        // arrangement may have lifted any of them off the bottom edge.
        // v2.19 batch C: every rect comes from the layout, computed this frame.
        bevelSlot(c, hud.minimapSlot);
        drawMinimap(c);

        // ---- v2.42 batch C: the control groups are their own widget. They
        // draw at hud.groups in EVERY selection state -- the panel no longer
        // carries a private copy of the grid, so "编队" is one UI with one
        // place to look at and one hit-test, wherever the selection is.
        drawFormationOnly(c, hud.groups);

        // ---- middle: selection portrait + hp, or nothing at all (v2.5 #4).
        // With an empty selection the old panel was a full-width opaque slab
        // showing a logo over the playfield -- pure dead space the player
        // could see through but not tap. Now it collapses to nothing and the
        // strip is handed back to the map (see inHud()/infoPanelRect()).
        List<Game.Ent> sel = game.selected();
        float infoL = hud.middle.left;
        float infoR = hud.middle.right - queueStripW(sel);
        if (sel.isEmpty()) {
            infoPanelRect.setEmpty();
        } else {
            // v2.42 batch C: bottom-anchored and content-tall. The layout rect
            // is the upper bound; the drawn surface is what the content needs
            // (INFO_H_DP) and hugs the bottom edge like the rest of the strip.
            float panelH = Math.min(hud.middle.height(),
                    HudLayout.INFO_H_DP * uiScale * hud.infoScale);
            // v2.21 #3: the content cap scales with the custom layout's S/M/L
            // (infoScale), so an L panel is filled by L-sized content instead of
            // M content with a dead ring around it.
            // v2.42: the card hugs its content in EVERY selection state. A
            // multi-select used to take the whole middle strip, which stretched
            // the hp bar across most of the screen -- five SCVs read as a single
            // 1300px green line inside a 1540px slab. The width is now what the
            // card actually needs and the strip it does not use goes back to the
            // map, which is also what makes the frame stop looking oversized.
            float k = uiScale * hud.infoScale;
            boolean multi = sel.size() > 1
                    && !sel.get(0).isBuilding();
            // v2.42: the cap grew 150->165dp so a three-character Chinese name
            // plus its "xN" never runs past the panel edge.
            float cap = INFO_CAP_DP * k;
            if (multi) {
                // room for the per-type filter row: one cell per distinct unit
                // kind, up to the six the card draws. A mixed group is the one
                // case that legitimately needs more than the single-select cap.
                float cellS = Math.max(18 * k, Math.min(30 * k, panelH - 48 * k));
                int kinds = kindsOf(sel);
                cap = Math.max(cap, 20 * k + kinds * cellS
                        + Math.max(0, kinds - 1) * 5 * k);
            }
            float wantW = Math.min(infoR - infoL, cap);
            wantW = Math.max(wantW, 90 * k);
            float panelTop = hud.middle.bottom - panelH;
            RectF infoPanel = new RectF(infoL, panelTop,
                    Math.min(infoL + wantW, infoR), hud.middle.bottom);
            infoPanelRect.set(infoPanel);
            // v2.21 #3: opaque. The translucent panel read as "a big transparent
            // area" over bright terrain; the info surface is a console panel and
            // now renders like one (the minimap slot's own chrome).
            bevelPanel(c, infoPanel);
            drawSelInfo(c, sel, infoPanel);
        }

        // ---- command card
        drawCmdCard(c, W, H, sel);
    }

    /**
     * v2.19 batch C: recompute the console layout for the current viewport. The
     * render thread calls this once per frame from render(); the touch path calls
     * it through ensureHud() before any hit-test, so the two can never use rects
     * from different frames.
     */
    // v2.19 batch C: memo key for ensureHud(). sy()/wy() call gameCenterY() very
    // often (once per entity per pass), so the layout must not be regenerated on
    // every call -- only when the viewport, preset or zoom moves.
    private int hudCacheW = -1, hudCacheH = -1, hudCachePreset = -1, hudCacheRev = -1;
    private float hudCacheZoom = -1;

    // ---- v2.19 batch C step 3: the layout editor
    /** Bumped whenever the saved custom layout changes, to invalidate ensureHud. */
    private int layoutRev;
    /** True while the pause-menu layout editor is up. */
    private boolean layoutEdit;
    /** The spec being edited: cx, cy, size per panel (see HudLayout.P_*). */
    private final float[] editSpec = new float[HudLayout.SPEC_LEN];
    /** Which panel the current drag holds, or -1. */
    private int editDrag = -1;
    /**
     * The panel the size buttons act on. Kept separate from editDrag: a drag
     * ends on ACTION_UP, but the player still expects S/M/L to hit the panel
     * they just touched. -1 means "no panel picked yet", and the size buttons
     * then apply to all five.
     */
    private int editSel = -1;
    private float editDownX, editDownY;
    private final float[] editStart = new float[HudLayout.SPEC_LEN];

    private void recomputeHud(int W, int H) {
        // v2.19 step 3: a custom layout overrides the preset; the editor works on
        // a live spec so the panels follow the finger before the save.
        // v2.20 step 3: the saved custom layout is now one of the presets
        // (Settings.HUD_CUSTOM) rather than an implicit override, so the player
        // can switch back to 默认/左右互换/紧凑 without losing it.
        float[] spec = layoutEdit ? editSpec : customSpec();
        int preset = activePreset();
        hud.compute(W, H, topBarH(), uiScale, zoom, preset, spec);
        minimapRect.set((int) hud.minimap.left, (int) hud.minimap.top,
                (int) hud.minimap.right, (int) hud.minimap.bottom);
        hudComputed = true;
        hudCacheW = W; hudCacheH = H; hudCacheZoom = zoom;
        hudCachePreset = preset; hudCacheRev = layoutRev;
    }

    /**
     * The preset actually in force this frame: the editor forces custom, and a
     * 自定义 selection with no saved spec (or a malformed one) degrades to the
     * default rather than drawing nothing.
     */
    private int activePreset() {
        if (layoutEdit) return HudLayout.PRESET_CUSTOM;
        if (settings.hudPreset == Settings.HUD_CUSTOM) {
            return customSpec() != null ? HudLayout.PRESET_CUSTOM : HudLayout.PRESET_DEFAULT;
        }
        return settings.hudPreset;
    }

    /** The saved custom spec, or null when the player has not made one. */
    private float[] customSpec() {
        if (!settings.layoutCustom) return null;
        return parseSpec(settings.layoutNorm);
    }

    /** Make sure the layout rects are current; a no-op when nothing moved. */
    private void ensureHud() {
        int W = getWidth(), H = getHeight();
        if (W <= 0 || H <= 0) return;
        if (hudComputed && W == hudCacheW && H == hudCacheH && zoom == hudCacheZoom
                && hudCachePreset == activePreset()
                && hudCacheRev == layoutRev) return;
        recomputeHud(W, H);
    }

    private void drawFormationOnly(Canvas c, RectF strip) {
        // v2.42 batch C: the control-group block draws at its OWN widget rect
        // (hud.groups), in every selection state. Ten chips, two rows of five
        // (a single row of ten is too narrow to tap on a 720p phone). The chip
        // edge derives from the placed rect, so a custom layout's S/M/L scales
        // the chips with the block instead of leaving a dead ring around them.
        float gap = 4 * uiScale;
        float cellS = Math.max(14 * uiScale,
                (strip.width() - 8 * uiScale - 4 * gap) / 5f);
        float gx0 = strip.left + 4 * uiScale;
        // v2.23 batch A #4: every formation slot is an independent OPAQUE chip
        // (bevelPanel), so nothing semi-see-through sits over the map. The
        // chips live inside hud.groups, whose gaps fall through to the map.
        float rowH = cellS + gap;
        float top = strip.centerY() - (2 * cellS + gap) / 2f;
        for (int g = 0; g < 10; g++) {
            int col = g % 5, row = g / 5;
            float x = gx0 + col * (cellS + gap);
            float y = top + row * rowH;
            RectF r = new RectF(x, y, x + cellS, y + cellS);
            bevelPanel(c, r);
            boolean set = g < game.groups.size() && !game.groups.get(g).isEmpty();
            p.setColor(set ? Color.rgb(120, 255, 160) : Color.rgb(200, 220, 245));
            p.setTextSize(cellS * 0.34f);
            p.setTextAlign(Paint.Align.CENTER);
            c.drawText(String.valueOf(g + 1), r.centerX(), r.centerY() + cellS * 0.12f, p);
            p.setTextAlign(Paint.Align.LEFT);
            Btn b = new Btn();
            b.r = r;
            b.action = "group:" + g;
            b.label = "编队" + (g + 1);
            buttons.add(b);
        }
    }

    /**
     * v2.42: how many distinct unit kinds a selection holds, capped at the six
     * filter cells drawSelInfo can draw. The card's width is sized from this so
     * a mixed group gets exactly the row it needs -- no more (the old
     * full-strip panel) and no less (clipped cells).
     */
    private static int kindsOf(List<Game.Ent> sel) {
        java.util.HashSet<String> seen = new java.util.HashSet<>();
        for (Game.Ent e : sel) {
            seen.add(e.type.key);
            if (seen.size() >= 6) return 6;
        }
        return seen.size();
    }

    /**
     * Width reserved for the production-queue strip: non-zero exactly when
     * drawQueueColumn will actually draw, so the info panel and the strip
     * never fight for the same pixels.
     */
    private float queueStripW(List<Game.Ent> sel) {
        if (sel.isEmpty()) return 0;
        Game.Ent b = sel.get(0);
        if (!b.isBuilding() || b.buildProgress < 1f || b.queue.isEmpty()) return 0;
        // v2.21 #2: mirror drawCmdCard's cell size (derived from hud.card) so
        // the reserved strip matches the drawn queue icons at every S/M/L.
        float gap = dp(HudLayout.CARD_GAP_DP);
        float cs = hud.card.width() > 0
                ? (hud.card.width() - (HudLayout.CARD_COLS - 1) * gap) / HudLayout.CARD_COLS
                : cardCell();
        return cs * 0.62f + 7 * uiScale;
    }

    private void drawMinimap(Canvas c) {
        p.setColor(Color.BLACK);
        c.drawRect(minimapRect, p);
        if (map.minimap != null) {
            // brightened so the terrain actually reads (batch-2 #8)
            brightPaint.setColorFilter(new android.graphics.ColorMatrixColorFilter(
                    MINIMAP_BRIGHT));
            c.drawBitmap(map.minimap, null, minimapRect, brightPaint);
            brightPaint.setColorFilter(null);
        }
        // fog as a semi-transparent overlay (reuses the world fog bitmap)
        // v2.43 P2: gated on the fog style, not just on the bitmap existing.
        // The world blit skips HOK outright, so the bitmap keeps whatever the
        // last SC frame left in it -- drawing it here would show a stale haze
        // over the minimap after switching to HOK.
        if (fogBmp != null && settings.fogStyle != Settings.FOG_HOK) {
            p.setAlpha(150);
            c.drawBitmap(fogBmp, null, minimapRect, fogPaint);
            p.setAlpha(255);
        }
        // resource dots so expansions are findable at a glance
        for (Game.Mineral m : game.minerals) {
            float mx = minimapRect.left + m.x / game.wPx * minimapRect.width();
            float my = minimapRect.top + m.y / game.hPx * minimapRect.height();
            p.setColor(m.variant >= 3 ? Color.rgb(90, 235, 120) : Color.rgb(120, 225, 255));
            c.drawRect(mx - 1.5f * uiScale, my - 1.5f * uiScale,
                    mx + 1.5f * uiScale, my + 1.5f * uiScale, p);
        }
        for (Game.Ent e : game.ents) {
            if (!e.alive()) continue;
            if (e.team == 1 && !enemyVisible(e)) continue;
            float mx = minimapRect.left + e.x / game.wPx * minimapRect.width();
            float my = minimapRect.top + e.y / game.hPx * minimapRect.height();
            p.setColor(e.team == 0 ? Color.rgb(90, 200, 255)
                    : (e.isBuilding() ? Color.rgb(255, 80, 60) : Color.rgb(255, 160, 60)));
            c.drawRect(mx - 1.5f * uiScale, my - 1.5f * uiScale,
                    mx + 1.5f * uiScale, my + 1.5f * uiScale, p);
        }
        p.setStyle(Paint.Style.STROKE);
        p.setColor(Color.rgb(60, 255, 60));
        // v2.21 #1: the viewport rectangle mirrors what the camera actually
        // shows (the full screen, terrain included), not just the playfield,
        // and is clipped to the minimap so an off-map camera cannot smear the
        // green frame over the console.
        float vl = wx(0) / game.wPx, vr = wx(getWidth()) / game.wPx;
        float vt = wy(0) / game.hPx, vb = wy(getHeight()) / game.hPx;
        c.drawRect(minimapRect.left + Math.max(0f, vl) * minimapRect.width(),
                minimapRect.top + Math.max(0f, vt) * minimapRect.height(),
                minimapRect.left + Math.min(1f, vr) * minimapRect.width(),
                minimapRect.top + Math.min(1f, vb) * minimapRect.height(), p);
        // under-attack pulse (batch-4 #16)
        if (alertFlash > 0) {
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(3 * uiScale);
            p.setColor(Color.argb((int) (255 * alertFlash), 255, 60, 50));
            c.drawRect(minimapRect, p);
            p.setStrokeWidth(1);
        }
        // v2.25: live scanner sweeps (cyan squares) and nuclear countdowns
        // (red squares). Both are drawn on the minimap because they are the
        // two things a player needs to find without moving the camera -- the
        // sweep to know what got revealed, the nuke to know where it is aimed.
        for (Game.Scan sc : game.scans) {
            float sr = Game.SCAN_RADIUS / game.wPx * minimapRect.width();
            float mx = minimapRect.left + sc.x / game.wPx * minimapRect.width();
            float my = minimapRect.top + sc.y / game.hPx * minimapRect.height();
            p.setStyle(Paint.Style.STROKE);
            p.setColor(Color.rgb(120, 220, 255));
            c.drawRect(mx - sr, my - sr, mx + sr, my + sr, p);
            p.setStyle(Paint.Style.FILL);
        }
        for (Game.Nuke n : game.nukes) {
            float nr = Game.NUKE_RADIUS / game.wPx * minimapRect.width();
            float mx = minimapRect.left + n.x / game.wPx * minimapRect.width();
            float my = minimapRect.top + n.y / game.hPx * minimapRect.height();
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(2 * uiScale);
            p.setColor(Color.rgb(255, 70, 50));
            c.drawRect(mx - nr, my - nr, mx + nr, my + nr, p);
            p.setStrokeWidth(1);
            p.setStyle(Paint.Style.FILL);
        }
        p.setStyle(Paint.Style.FILL);
    }

    private void drawSelInfo(Canvas c, List<Game.Ent> sel, RectF panel) {
        Game.Ent first = sel.get(0);
        // v2.21 #3: content scale. Presets keep uiScale (infoScale == 1); the
        // custom layout's S/M/L grows text, bars and cells with the panel, so
        // the size buttons change what is drawn, not just the box around it.
        float k = uiScale * hud.infoScale;
        float px = panel.left + 10 * k;

        // v2.42 batch C: the slim card. The control groups left the panel (they
        // draw at hud.groups now), so the whole height serves the readout:
        // portrait left; name, hp and one status line to its right. The English
        // subtitle is gone -- it duplicated the Chinese name beside it.
        boolean multiType = sel.size() > 1;
        java.util.LinkedHashMap<String, Integer> tally = new java.util.LinkedHashMap<>();
        if (multiType) for (Game.Ent e : sel) tally.merge(e.type.key, 1, Integer::sum);

        // portrait: v2.12 batch E prefers the real Smacker talking-head still
        // for the six units that have one (medic, lurker, devourer, valkyrie,
        // corsair, dark archon); everything else keeps the GRP wireframe.
        // v2.42 batch C: the name is measured FIRST and the portrait yields
        // width to it -- a 640dp-wide budget phone cannot fit both at full
        // size, and the name is the one thing that must never clip.
        Bitmap wire = ui.portrait(first.type.key);
        boolean isPortrait = wire != null;
        if (wire == null) wire = ui.wire(first.type.unitId);
        p.setTextAlign(Paint.Align.LEFT);
        p.setTextSize(15 * k);
        String nameTxt = first.type.name + (sel.size() > 1 ? " x" + sel.size() : "");
        float nameW = p.measureText(nameTxt);
        float ws = panel.height() - 20 * k;
        float availW = panel.width() - 20 * k - nameW - 24 * k;
        if (availW < ws) ws = Math.max(36 * k, availW);
        if (wire != null) {
            RectF wr = new RectF(px, panel.top + (panel.height() - ws) / 2f,
                    px + ws, panel.top + (panel.height() + ws) / 2f);
            bevelSlot(c, wr);
            float pad = 4 * k;
            RectF inner = new RectF(wr.left + pad, wr.top + pad,
                    wr.right - pad, wr.bottom - pad);
            if (isPortrait) {
                // 60x56 stills are not square: letterbox instead of stretching
                float s = Math.min(inner.width() / wire.getWidth(),
                        inner.height() / wire.getHeight());
                float dw = wire.getWidth() * s, dh = wire.getHeight() * s;
                float cl = inner.centerX() - dw / 2f, ct = inner.centerY() - dh / 2f;
                inner = new RectF(cl, ct, cl + dw, ct + dh);
            }
            c.drawBitmap(wire, null, inner, p);
        }
        float tx = px + ws + 12 * k;
        float ty = panel.top + 22 * k;

        p.setColor(first.team == 1 ? Color.rgb(255, 170, 150) : Color.rgb(255, 220, 130));
        c.drawText(nameTxt, tx, ty, p);

        // HP bar: green > 2/3, yellow > 1/3, red below (SC convention)
        float frac = Math.max(0f, Math.min(1f, first.hp / (float) first.type.hp));
        int hc = frac > 2f / 3f ? Color.rgb(80, 230, 80)
                : frac > 1f / 3f ? Color.rgb(240, 220, 60) : Color.rgb(250, 70, 50);
        float barY = ty + 10 * k;
        float barW = panel.right - 10 * k - tx;
        // v2.10: protoss shields are drawn as a second, cyan segment stacked on
        // the health bar. Only protoss types have a shield at all, so the
        // terran and zerg console is pixel-identical to v2.9.
        if (first.type.shield > 0) {
            float sf = Math.max(0f, Math.min(1f,
                    first.shield / (float) first.type.shield));
            p.setColor(Color.BLACK);
            c.drawRect(tx, barY, tx + barW, barY + 5 * k, p);
            p.setColor(Color.rgb(90, 200, 255));
            c.drawRect(tx, barY, tx + barW * sf, barY + 5 * k, p);
            p.setStyle(Paint.Style.STROKE);
            p.setColor(PANEL_LITE);
            c.drawRect(tx, barY, tx + barW, barY + 5 * k, p);
            p.setStyle(Paint.Style.FILL);
            barY += 6 * k;
        }
        p.setColor(Color.BLACK);
        c.drawRect(tx, barY, tx + barW, barY + 9 * k, p);
        p.setColor(hc);
        c.drawRect(tx, barY, tx + barW * frac, barY + 9 * k, p);
        p.setStyle(Paint.Style.STROKE);
        p.setColor(PANEL_LITE);
        c.drawRect(tx, barY, tx + barW, barY + 9 * k, p);
        p.setStyle(Paint.Style.FILL);
        p.setTextSize(11 * k);
        // v2.17: the HP number sits right-aligned INSIDE the bar, so it can
        // never spill off the panel edge.
        String hpTxt = first.hp + "/" + first.type.hp;
        p.setTextAlign(Paint.Align.RIGHT);
        p.setColor(Color.argb(190, 0, 0, 0));
        c.drawText(hpTxt, tx + barW - 3 * k + 1, barY + 8 * k + 1, p);
        p.setColor(Color.WHITE);
        c.drawText(hpTxt, tx + barW - 3 * k, barY + 8 * k, p);
        p.setTextAlign(Paint.Align.LEFT);

        if (multiType) {
            // v2.42 batch C: per-type filter cells, ONE compact row along the
            // panel's bottom (they used to share a band with the group grid --
            // that grid moved to hud.groups, so the row is all that is left).
            float cellS = Math.max(18 * k,
                    Math.min(30 * k, panel.height() - 48 * k));
            float cy2 = panel.bottom - cellS - 6 * k;
            float cx = px;
            int drawn = 0;
            for (java.util.Map.Entry<String, Integer> t : tally.entrySet()) {
                if (drawn >= 6) break;
                RectF cr = new RectF(cx, cy2, cx + cellS, cy2 + cellS);
                bevelSlot(c, cr);
                Bitmap tWire = ui.wire(Game.TYPES.get(t.getKey()).unitId);
                if (tWire != null) c.drawBitmap(tWire, null,
                        new RectF(cr.left + 2 * k, cr.top + 2 * k,
                                cr.right - 2 * k, cr.bottom - 2 * k), p);
                p.setColor(Color.rgb(190, 205, 230));
                p.setTextSize(9 * k);
                c.drawText("x" + t.getValue(), cr.right - 2 * k,
                        cr.bottom - 2 * k, p);
                Btn b = new Btn();
                b.r = cr;
                b.action = "pick:" + t.getKey();
                b.label = Game.TYPES.get(t.getKey()).name;
                buttons.add(b);
                cx += cellS + 5 * k;
                drawn++;
            }
            return;
        }

        // status line: production / harvest / combat stats
        float ly = barY + 20 * k;
        p.setColor(Color.rgb(160, 200, 230));
        p.setTextSize(11 * k);
        String status = null;
        if (first.isBuilding() && !first.queue.isEmpty()) {
            Game.Type t = Game.TYPES.get(first.queue.get(0));
            if (t != null) {
                int pct = (int) (first.queueProgress / t.buildTime * 100);
                status = "生产 " + t.name + "  " + pct + "%";
            }
        } else if (first.isBuilding() && first.constructing) {
            status = "建造中 " + (int) (first.buildProgress * 100) + "%";
        } else if (first.carrying > 0) {
            status = (first.haulingGas ? "运送瓦斯 " : "运送晶体 ") + first.carrying;
        } else if (!first.isBuilding() && first.type.dmg > 0) {
            status = "攻击 " + first.type.dmg + "   射程 " + first.type.range;
        }
        if (status != null && tx + p.measureText(status) < panel.right - 6 * k)
            c.drawText(status, tx, ly, p);

        // v2.22 batch A: the caster's pool, its own line under the status.
        // Drawn only when the whole string still fits inside the slim card.
        if (first.maxEnergy > 0) {
            float ey = ly + 15 * k;
            String energy = "能量 " + (int) first.energy + "/" + (int) first.maxEnergy;
            if (ey < panel.bottom - 4 * k
                    && tx + p.measureText(energy) < panel.right - 6 * k) {
                p.setColor(Color.rgb(120, 175, 255));
                c.drawText(energy, tx, ey, p);
            }
        }
    }

    // (the empty-selection "星 际 争 霸" logo was removed in v2.5 #4 -- with no
    // selection the console strip now collapses to the formation slots only)

    /** 3x3 command card, real cmdicons art in recessed slots. */
    private void drawCmdCard(Canvas c, int W, int H, List<Game.Ent> sel) {
        // NOTE: do NOT clear `buttons` here. drawHud() already clears once per
        // frame, and drawFormationOnly() registers the 1/2/3 group slots before
        // this runs -- clearing again silently dropped them, so with nothing
        // selected the formation slots were impossible to tap (v2.5 #4).
        float gap = dp(CARD_GAP_DP);
        int cols = CARD_COLS, rows = CARD_ROWS;
        // v2.21 #2: the cell edge derives from the layout's card rect itself.
        // It used to come from cardCell() -- a screen-height formula -- so in
        // the custom layout's S/M/L the outer backing grew while every cell,
        // icon and tap target inside stayed at the M size (the "bigger frame,
        // same icons" the tester hit). For the three presets the rect was
        // BUILT from cardCell(), so this reproduces the old value exactly.
        float cs = hud.card.width() > 0
                ? (hud.card.width() - (cols - 1) * gap) / cols
                : cardCell();
        float gridW = cols * cs + (cols - 1) * gap;
        float gridH = rows * cs + (rows - 1) * gap;
        float gx = hud.card.left;
        float gy = hud.card.top;
        // v2.19: hud.card already applies the off-screen clamp.
        // v2.23 batch B: the old half-cell translucent backing is gone. With a
        // selection the nine cells sit on ONE opaque metal panel (bevelPanel)
        // whose margin is just 2dp; with no selection NOTHING is drawn here at
        // all -- that empty 3x3 was the "frame inside a frame" the player saw.
        // Only the cells that actually hold an action are drawn (drawGridCell),
        // so the card is exactly as big as the orders it carries.
        float cardPad = dp(2f);

        Game.Ent first = sel.isEmpty() ? null : sel.get(0);
        java.util.LinkedHashSet<String[]> acts = new java.util.LinkedHashSet<>();
        if (first != null) {
            // v2.8: "all workers" rather than "all SCVs" -- a drone base shows
            // the same build/repair submenu shape.
            boolean allWorkers = true;
            for (Game.Ent e : sel) if (!Game.isWorker(e)) allWorkers = false;
            boolean zerg = "zerg".equals(game.race);
            boolean protoss = "protoss".equals(game.race);
            // The worker card no longer fits in 3x3 once repair is added, so the
            // structures live on a second page behind 建造 -- the same
            // submenu shape the original uses. cardPage self-validates: if the
            // selection stops being all-worker we fall back to page 0.
            // v2.10: protoss has twelve placeable buildings against terran's
            // eight, so it needs a third page; the two build pages split along
            // the same basic/advanced line the original uses (economy and the
            // gateway opening on page 1, the tech buildings behind it).
            boolean buildPage = allWorkers && cardPage == 1;
            // Page 2 exists for every race: terran's eleven placeable
            // buildings no longer fit behind a single "更多", and protoss and
            // zerg both needed it already.
            boolean buildPage2 = allWorkers && cardPage == 2;
            // v2.11: zerg's page 2 carries seven tech buildings and still needs
            // both a "更多" and a "返回" cell, so the last two spill onto a
            // page 3. Terran and protoss never reach it.
            boolean buildPage3 = zerg && allWorkers && cardPage == 3;
            if (!first.isBuilding()) {
                if (buildPage3) {
                    // v2.11: the three cells that did not fit on page 2.
                    acts.add(new String[]{"build:greatspire", "大飞龙塔"});
                    acts.add(new String[]{"build:ucereb", "雷兽洞穴"});
                    acts.add(new String[]{"build:cerebrate", "脑虫"});
                    acts.add(new String[]{"page:2", "返回"});
                } else if (buildPage2) {
                    if (zerg) {
                        // v2.11: the advanced half of the zerg tree. Every row
                        // here hangs off lair or hive, which is why page 1
                        // carries the pool -> lair -> hive chain instead.
                        acts.add(new String[]{"build:spire", "飞龙塔"});
                        acts.add(new String[]{"build:hydraden", "刺蛇巢"});
                        acts.add(new String[]{"build:evolcham", "进化腔"});
                        acts.add(new String[]{"build:spore", "孢子殖地"});
                        acts.add(new String[]{"build:mutapit", "污染者巢穴"});
                        acts.add(new String[]{"build:nest", "皇后巢"});
                        acts.add(new String[]{"build:nydus", "虫道"});
                        acts.add(new String[]{"page:3", "更多"});
                        acts.add(new String[]{"page:1", "返回"});
                    } else if (protoss) {
                        acts.add(new String[]{"build:citadel", "圣殿"});
                        acts.add(new String[]{"build:archives", "档案馆"});
                        acts.add(new String[]{"build:robotic", "机器人"});
                        acts.add(new String[]{"build:stargate", "星门"});
                        acts.add(new String[]{"build:beacon", "航标"});
                        acts.add(new String[]{"page:1", "返回"});
                    } else {
                        // v2.11 batch C: the air and science half of the terran
                        // tree. starport gates valkyrie and battlecruiser,
                        // armory sells the weapon/armor upgrades (moved off the
                        // engineering bay) and gates the valkyrie, sciencefac
                        // gates the battlecruiser.
                        acts.add(new String[]{"build:starport", "星港"});
                        acts.add(new String[]{"build:armory", "军械库"});
                        acts.add(new String[]{"build:sciencefac", "科学设施"});
                        // v2.23 batch B: the bunker rides the advanced page --
                        // page 1 already carries all nine of its cells, and the
                        // bunker is a defensive tech building in any case.
                        acts.add(new String[]{"build:bunker", "地堡"});
                        acts.add(new String[]{"page:1", "返回"});
                    }
                } else if (buildPage) {
                    if (zerg) {
                        // v2.8's five zerg cells plus the two new tech-chain
                        // links v2.11 adds. sunken is a static defense like the
                        // terran turret, extractor the gas building; creep is
                        // the plan's creep-colony art, kept as a cheap forward
                        // outpost even though this game has no creep field.
                        // Seven cells, not eight: the page also has to carry
                        // both "更多" and "返回", or a drone that opened the
                        // build menu could never get back to its action card.
                        acts.add(new String[]{"build:hatchery", "孵化场"});
                        acts.add(new String[]{"build:lair", "兽穴"});
                        acts.add(new String[]{"build:hive", "虫巢"});
                        acts.add(new String[]{"build:pool", "孵化池"});
                        acts.add(new String[]{"build:extractor", "萃取场"});
                        acts.add(new String[]{"build:creep", "菌毯殖地"});
                        acts.add(new String[]{"build:sunken", "地刺"});
                        acts.add(new String[]{"page:2", "更多"});
                        acts.add(new String[]{"page:0", "返回"});
                    } else if (protoss) {
                        acts.add(new String[]{"build:nexus", "枢纽"});
                        acts.add(new String[]{"build:pylon", "水晶塔"});
                        acts.add(new String[]{"build:assim", "吸收站"});
                        acts.add(new String[]{"build:gateway", "传送门"});
                        acts.add(new String[]{"build:forge", "锻造厂"});
                        acts.add(new String[]{"build:photon", "光子炮"});
                        acts.add(new String[]{"build:gencore", "机械核心"});
                        acts.add(new String[]{"page:2", "更多"});
                        acts.add(new String[]{"page:0", "返回"});
                    } else {
                        // v2.11 batch C: the three tech buildings moved to
                        // page 2, so the eighth cell here becomes "更多"
                        // instead of the old dead-end "返回".
                        acts.add(new String[]{"build:cc", "基地"});
                        acts.add(new String[]{"build:depot", "补给"});
                        acts.add(new String[]{"build:barracks", "兵营"});
                        acts.add(new String[]{"build:refinery", "炼油"});
                        acts.add(new String[]{"build:factory", "重工"});
                        acts.add(new String[]{"build:turret", "炮塔"});
                        acts.add(new String[]{"build:academy", "学院"});
                        acts.add(new String[]{"build:engbay", "工程湾"});
                        acts.add(new String[]{"page:2", "更多"});
                    }
                } else {
                    acts.add(new String[]{"attack", "攻击"});
                    // attack-move: core has supported it since batch 1
                    // (orderMove(..., true)); no verified icon exists in
                    // cmdicons, so this cell renders its label as text.
                    acts.add(new String[]{"amove", "攻击移动"});
                    acts.add(new String[]{"stop", "停止"});
                    acts.add(new String[]{"patrol", "巡逻"});
                    // v2.14: hold position. The order existed in the core since
                    // the batch-1 round; the cell finally ships with it.
                    acts.add(new String[]{"hold", "驻守"});
                    if (allWorkers) {
                        // Only the terran worker repairs; a drone has no
                        // equivalent, so the cell would be a dead button.
                        if (!zerg) acts.add(new String[]{"repair", "修理"});
                        acts.add(new String[]{"page:1", "建造"});
                    }
                    // v2.7 9.1: stimpack on infantry that can use it
                    if (first.type.key.equals("marine") || first.type.key.equals("firebat"))
                        acts.add(new String[]{"stim", "兴奋剂"});
                    if (first.type.key.equals("tank"))
                        acts.add(new String[]{"siege", "架塔"});
                    else if (first.type.key.equals("stank"))
                        acts.add(new String[]{"unsiege", "解除"});
                    // v2.11: the lurker borrows the tank's morph cell -- it is
                    // the same operation, so it gets the same two labels.
                    if (first.type.key.equals("lurker"))
                        acts.add(new String[]{"burrow", "钻地"});
                    else if (first.type.key.equals("lurker_bur"))
                        acts.add(new String[]{"unburrow", "出土"});
                    // v2.10: the templar's psionic storm. Only the templar has
                    // it, so the cell would be dead weight on every other unit.
                    if (first.type.key.equals("templar"))
                        acts.add(new String[]{"storm", "灵能风暴"});
                    // v2.11 batch B: the defiler's two fields. Both are cast at
                    // a point on the map, exactly like the storm, so they reuse
                    // its targeting mode rather than inventing a new one.
                    if (first.type.key.equals("defiler")) {
                        acts.add(new String[]{"dswarm", "黑暗蜂群"});
                        acts.add(new String[]{"ensnare", "诱捕"});
                    }
                    // v2.11 batch C: the medic heals a unit, the vulture drops
                    // a mine where it stands. Different targets (a unit vs the
                    // ground under it), so they get separate modes.
                    if (first.type.key.equals("medic"))
                        acts.add(new String[]{"heal", "治疗"});
                    if (first.type.key.equals("vulture"))
                        acts.add(new String[]{"mine", "埋雷"});
                    // v2.14: the science spells. None of them has a verified
                    // cmdicons frame (the icon hunt rendered 238-390 and the
                    // candidates stayed ambiguous), so every cell renders its
                    // Chinese label as text -- the same honest fallback the
                    // attack-move cell has used since batch 6.
                    if (first.type.key.equals("vessel")) {
                        acts.add(new String[]{"emp", "电磁脉冲"});
                        acts.add(new String[]{"irradiate", "辐射"});
                    }
                    if (first.type.key.equals("battlecruiser"))
                        acts.add(new String[]{"yamato", "大和炮"});
                    if (first.type.key.equals("ghost")) {
                        acts.add(new String[]{"lockdown", "锁定"});
                        // v2.22 batch B: the personal cloak toggle, label
                        // reflecting the state the tap will switch TO.
                        acts.add(new String[]{"cloak", first.cloakOn ? "显形" : "隐形"});
                    }
                    if (first.type.key.equals("wraith"))
                        acts.add(new String[]{"cloak", first.cloakOn ? "显形" : "隐形"});
                    if (first.type.key.equals("corsair"))
                        acts.add(new String[]{"dweb", "干扰网"});
                    // v2.23 batch A: the transport card. "load" arms a
                    // friendly-unit pick, "unload" arms a ground pick -- the
                    // same two targeting shapes repair and storm already use.
                    if (first.type.cargoCap > 0) {
                        acts.add(new String[]{"load", "装载"});
                        acts.add(new String[]{"unload", "卸载"});
                    }
                    // v2.23 batch B: the bunker card. garrison sweeps nearby
                    // infantry in, release spills them out beside the bunker.
                    if (first.type.bunkerCap > 0) {
                        acts.add(new String[]{"garrison", "驻守"});
                        acts.add(new String[]{"release", "放出"});
                    }
                    // v2.25: the comsat's scanner sweep -- a ground pick, the
                    // same targeting shape storm and the nuke use.
                    if (first.type.key.equals("comsat")) {
                        acts.add(new String[]{"scan", "扫描"});
                    }
                    // v2.25: the ghost's nuclear strike. Offered whenever a silo
                    // is armed, so the player sees the button the moment the
                    // missile is ready rather than only after selecting the
                    // silo first.
                    if (first.type.key.equals("ghost")) {
                        acts.add(new String[]{"nuke", "核弹打击"});
                    }
                    // v2.26: the two templars merge into an archon. The cell
                    // appears whenever the player has two of the same type
                    // selected and standing together, which is exactly when
                    // the original shows it.
                    if (Game.mergeResult(first.type.key) != null
                            && sel.size() == 2
                            && game.mergeError(sel, null) == null) {
                        acts.add(new String[]{"merge", "合体"});
                    }
                    // v2.26: any zerg ground unit can burrow. The label tracks
                    // the state the tap switches TO, like the cloak cell.
                    if (Game.canBurrow(first)) {
                        acts.add(new String[]{"burrow", first.burrowed ? "出土" : "钻地"});
                    }
                }
            } else if (first.team == 0 && first.buildProgress >= 1f
                    && first.type.trains.length > 0) {
                for (String tKey : first.type.trains)
                    acts.add(new String[]{"train:" + tKey, Game.TYPES.get(tKey).name});
                acts.add(new String[]{"rally", "集结"});
            } else if (first.team == 0 && first.buildProgress >= 1f
                    && upgradeLine(first.type.key) != null) {
                // v2.28: the three research buildings each own ONE class line,
                // which is the plan's "e-bay/factory/armory 各管一线": the
                // engineering bay sells infantry, the factory vehicles and the
                // armoury ships. Before this one building sold two army-wide
                // upgrades, so a single research buffed marines and
                // battlecruisers alike. Each cell carries its own line's level
                // so the player can see which line they are buying.
                String cls = upgradeLine(first.type.key);
                String cn = upgradeLineName(cls);
                acts.add(new String[]{"upgrade:w:" + cls,
                        cn + "武器 " + game.weaponFor(cls) + "/3"});
                acts.add(new String[]{"upgrade:a:" + cls,
                        cn + "防御 " + game.armorFor(cls) + "/3"});
                // v2.27: the population ceiling is a research, not a constant.
                // The cell names the next tier so the player can see what the
                // money buys before spending it.
                acts.add(new String[]{"upgrade:pop",
                        game.capTier >= Game.SUPPLY_TIERS.length - 1
                                ? "人口 " + Game.SUPPLY_CAP + "(满)"
                                : "人口 → " + Game.SUPPLY_TIERS[game.capTier + 1]});
            } else if (first.team == 0 && first.constructing) {
                // v2.17: an unfinished building selected on its own gets one
                // cell that explains how to resume it, since a worker pulled off
                // the site now freezes progress until it is sent back.
                acts.add(new String[]{"hint:resume", "派工人点击续建"});
            }
        }

        // v2.25: a completed building offers the add-ons it owns, so the player
        // never has to hunt for where the control tower lives. This sits AFTER
        // the branch above (not inside it) because the academy and the science
        // facility train nothing -- they would otherwise never reach a trains
        // branch and their comsat/nuke-silo cells would be unreachable. The
        // add-on cell only appears when the pad is actually free, so a full
        // parent shows nothing extra.
        if (first != null && first.team == 0 && first.buildProgress >= 1f
                && !first.constructing) {
            for (String ak : new String[]{"comsat", "controlt",
                    "machineshop", "physicslab", "nukesilo"}) {
                Game.Type at = Game.TYPES.get(ak);
                if (at != null && first.type.key.equals(at.addonFor)
                        && game.addonError(first, ak) == null)
                    acts.add(new String[]{"addon:" + ak, "建造" + at.name});
            }
        }

        java.util.Iterator<String[]> it = acts.iterator();
        for (int i = 0; i < cols * rows; i++) {
            float x = gx + (i % cols) * (cs + gap);
            float y = gy + (i / cols) * (cs + gap);
            RectF r = new RectF(x, y, x + cs, y + cs);
            String[] a = it.hasNext() ? it.next() : null;
            // v2.23 batch B: an unused cell draws NOTHING -- not even an empty
            // recessed slot. The nine blank wells under a mostly-empty card
            // were the "frame inside a frame"; now the panel is exactly as big
            // as the orders it carries.
            if (a == null) continue;
            // One opaque metal panel behind the whole grid (drawn once, on the
            // first live cell), so the gaps between cells are panel, not a
            // translucent halo.
            if (i == 0) {
                float pad = dp(2f);
                bevelPanel(c, new RectF(gx - pad, gy - pad,
                        gx + gridW + pad, gy + gridH + pad));
            }
            // The cell itself is a flat well with 1px separators only: the old
            // per-cell bevel (slot depth + highlight + outline, three lines
            // each) stacked on the outer frame is the "box in a box".
            drawGridCell(c, r, i);

            // affordability gate (batch-4 #14): grey the button out and badge
            // the price so a failed tap is explained on sight
            boolean afford = true;
            String costText = null;
            // v2.17: a pure hint cell is not a real order, so it must not be
            // affordability-gated (its action has no type key to look up).
            if (a[0].startsWith("hint:")) {
                p.setColor(Color.rgb(200, 225, 250));
                p.setTextSize(11 * uiScale);
                p.setTextAlign(Paint.Align.CENTER);
                c.drawText(a[1], r.centerX(), r.centerY() + 4 * uiScale, p);
                p.setTextAlign(Paint.Align.LEFT);
                continue;
            }
            // v2.27: the population research shows its price like the other
            // two armoury upgrades (which are free-form, so they show none).
            if (a[0].equals("upgrade:pop")) {
                int tier = game.capTier + 1;
                afford = tier < Game.SUPPLY_TIERS.length;
                costText = afford ? String.valueOf(Game.popUpgradeCost(tier)) : null;
            }
            if ((a[0].startsWith("train:") || a[0].startsWith("build:"))) {
                String k = a[0].substring(a[0].indexOf(':') + 1);
                Game.Type t = Game.TYPES.get(k);
                afford = game.mineralsPlayer >= t.cost && game.gasPlayer >= t.gasCost
                        && (t.supply <= 0 || game.supplyUsed + t.supply <= game.supplyCap);
                costText = t.gasCost > 0 ? t.cost + "+" + t.gasCost
                        : (t.cost > 0 ? String.valueOf(t.cost) : null);
            }
            // v2.22 batch A: spell cells gate on the caster's pool and show the
            // energy price where the mineral badge sits, in the pool's blue.
            // The personal-cloak cell is its own toggle (cloakAction below).
            boolean energyCell = Game.spellEnergyCost(a[0]) >= 0;
            Game.Ent caster0 = sel.isEmpty() ? null : sel.get(0);
            if (energyCell) {
                float ec = Game.spellEnergyCost(a[0]);
                afford = caster0 != null && game.spellGate(caster0, a[0]) == null;
                costText = String.valueOf((int) ec);
            } else if (a[0].equals("cloak")) {
                afford = caster0 != null && game.cloakError(caster0) == null;
            }
            Bitmap ic = iconFor(a[0]);
            // Chinese label strip along the cell bottom (v2.5 #3): the name sits
            // on its own bar so the player never has to decode an icon alone.
            // v2.10: the price badge is drawn separately, over the icon.
            // v2.23 batch B: the strip is a hair thinner (12->10dp, 10->9) so
            // the icon regains a little height, and it is opaque now.
            float barH = (cs >= 46 * uiScale) ? 10 * uiScale : 9 * uiScale;
            float iconBottom = r.bottom - barH;
            if (ic != null) {
                // v2.23 batch B: icon padding 4dp -> 2dp, ~15% larger icon.
                float pad = 2 * uiScale;
                if (!afford) p.setAlpha(90);
                c.drawBitmap(ic, null, new RectF(r.left + pad, r.top + pad,
                        r.right - pad, iconBottom - pad * 0.5f), p);
                p.setAlpha(255);
            } else {
                p.setColor(afford ? Color.rgb(200, 225, 250) : Color.rgb(110, 125, 145));
                p.setTextSize(12 * uiScale);
                p.setTextAlign(Paint.Align.CENTER);
                // no icon: the label owns the whole cell, so the price has to
                // ride along with it -- a corner badge would land on the text.
                String fallback = costText != null ? a[1] + " " + costText : a[1];
                c.drawText(fallback, r.centerX(), (r.top + iconBottom) / 2f + 4 * uiScale, p);
                p.setTextAlign(Paint.Align.LEFT);
            }

            // v2.10: the price moved out of the name strip and onto the icon's
            // top-right corner. The strip is only ~96px wide on a 100px cell,
            // and a seven-character "300+200" left a three-character name about
            // one glyph before the ellipsis -- the protoss build page shipped
            // reading "水...", "传...", "机...". The strip now belongs to the
            // name alone, so every name renders whole; the price keeps its own
            // badge, drawn over the icon art where there is room for it.
            if (costText != null && ic != null) {
                p.setTextSize(8.5f * uiScale);
                p.setTextAlign(Paint.Align.RIGHT);
                float cw = p.measureText(costText);
                float bpad = 2.5f * uiScale;
                RectF badge = new RectF(r.right - bpad - cw - 4f * uiScale, r.top + bpad,
                        r.right - bpad, r.top + bpad + 12f * uiScale);
                // v2.23 batch B: opaque badge (was 190/255 see-through).
                p.setColor(Color.rgb(10, 14, 24));
                c.drawRect(badge, p);
                p.setColor(afford ? Color.rgb(140, 220, 255) : Color.rgb(255, 110, 90));
                c.drawText(costText, badge.right - 2f * uiScale,
                        badge.centerY() + 3f * uiScale, p);
                p.setTextAlign(Paint.Align.LEFT);
            }

            // name strip: the whole bar, now that the price has left it
            RectF bar = new RectF(r.left + 1 * uiScale, r.bottom - barH,
                    r.right - 1 * uiScale, r.bottom - 1 * uiScale);
            // v2.23 batch B: opaque deep chip, not a 200/255 see-through bar.
            p.setColor(CHIP_DARK);
            c.drawRect(bar, p);
            float nameX = bar.left + 3f * uiScale;
            float barBase = bar.centerY() + 3.2f * uiScale;
            float nameMaxW = bar.width() - 6f * uiScale;
            p.setTextSize(9.5f * uiScale);
            p.setTextAlign(Paint.Align.LEFT);
            p.setColor(afford ? Color.rgb(215, 232, 250) : Color.rgb(150, 160, 175));
            c.drawText(ellipsize(a[1], Math.max(0f, nameMaxW), 9.5f * uiScale),
                    nameX, barBase, p);
            p.setTextAlign(Paint.Align.LEFT);

            Btn b = new Btn();
            b.r = r;
            b.action = a[0] + (afford ? "" : ":locked");
            b.label = a[1];
            buttons.add(b);
        }
        drawQueueColumn(c, first, gx, gy, cs, gap);
    }

    /**
     * v2.23 batch B: one command-card cell. A flat well (SLOT_DARK) with a
     * single 1px separator on the right and bottom edges of every non-last
     * column/row. No per-cell bevel, no outline -- the depth and the frame come
     * from the single bevelPanel behind the grid, which is what stops the nine
     * cells reading as "boxes inside a box".
     */
    private void drawGridCell(Canvas c, RectF r, int i) {
        int col = i % CARD_COLS, row = i / CARD_COLS;
        p.setColor(SLOT_DARK);
        c.drawRect(r, p);
        p.setColor(CARD_SEP);
        if (col < CARD_COLS - 1) c.drawRect(r.right - 1, r.top, r.right, r.bottom, p);
        if (row < CARD_ROWS - 1) c.drawRect(r.left, r.bottom - 1, r.right, r.bottom, p);
    }

    /**
     * Production queue, drawn as a vertical strip of small icons to the left of
     * the command card (batch-1 #4). Tapping an entry cancels it and refunds.
     */
    private void drawQueueColumn(Canvas c, Game.Ent building, float gx, float gy,
                                 float cs, float gap) {
        if (building == null || !building.isBuilding()
                || building.buildProgress < 1f || building.queue.isEmpty()) return;
        float qs = cs * 0.62f;
        float qx = gx - qs - 7 * uiScale;
        for (int i = 0; i < building.queue.size(); i++) {
            String key = building.queue.get(i);
            RectF r = new RectF(qx, gy + i * (qs + 4 * uiScale),
                    qx + qs, gy + i * (qs + 4 * uiScale) + qs);
            bevelSlot(c, r);
            Game.Type qt = Game.TYPES.get(key);
            String qName = (qt != null) ? qt.name : key;
            // name strip (v2.5 #3): tiny entries are unreadable as icons alone
            float qBarH = 9.5f * uiScale;
            float qIconBottom = r.bottom - qBarH;
            Bitmap ic = iconFor("train:" + key);
            if (ic == null) ic = iconFor("build:" + key);
            if (ic != null) {
                float pad = 2.5f * uiScale;
                c.drawBitmap(ic, null, new RectF(r.left + pad, r.top + pad,
                        r.right - pad, qIconBottom - pad * 0.5f), p);
            } else {
                p.setColor(Color.rgb(200, 225, 250));
                p.setTextSize(9 * uiScale);
                p.setTextAlign(Paint.Align.CENTER);
                c.drawText("?", r.centerX(), (r.top + qIconBottom) / 2f + 3 * uiScale, p);
                p.setTextAlign(Paint.Align.LEFT);
            }
            RectF qBar = new RectF(r.left + 1 * uiScale, r.bottom - qBarH,
                    r.right - 1 * uiScale, r.bottom - 1 * uiScale);
            // v2.23 batch A: opaque, like every other persistent HUD chip.
            p.setColor(CHIP_DARK);
            c.drawRect(qBar, p);
            p.setColor(Color.rgb(215, 232, 250));
            p.setTextSize(8 * uiScale);
            p.setTextAlign(Paint.Align.CENTER);
            c.drawText(ellipsize(qName, qBar.width() - 3 * uiScale, 8 * uiScale),
                    qBar.centerX(), qBar.centerY() + 2.8f * uiScale, p);
            p.setTextAlign(Paint.Align.LEFT);
            if (i == 0) {
                // progress wedge on the in-progress entry
                Game.Type t = Game.TYPES.get(key);
                float frac = Math.min(1f, building.queueProgress / t.buildTime);
                p.setStyle(Paint.Style.STROKE);
                p.setStrokeWidth(2 * uiScale);
                p.setColor(Color.rgb(90, 255, 130));
                c.drawLine(r.left, r.bottom, r.left + r.width() * frac, r.bottom, p);
                p.setStrokeWidth(1);
                p.setStyle(Paint.Style.FILL);
            }
            Btn b = new Btn();
            b.r = r;
            b.action = "cancel:" + i;
            b.label = "取消";
            buttons.add(b);
        }
    }

    /**
     * End-of-game panel (v2.7 batch 7.1). Uses the original glue\ScorePd
     * chrome when it decoded, and falls back to the code-drawn panel when the
     * asset set was stripped. Either way the scoreboard is filled from
     * Game.kills/losses/mineralsMined/gasMined, so a result is explained by
     * numbers instead of a bare win/lose word.
     */
    private void drawWinLose(Canvas c, int W, int H) {
        if (game.status.isEmpty()) return;
        boolean win = game.status.equals("win");
        p.setColor(Color.argb(190, 4, 6, 12));
        c.drawRect(0, 0, W, H, p);

        // the source panel is a fixed 640x480; scale it to fit the viewport
        float panelW = Math.min(W * 0.86f, 640 * uiScale * 0.9f);
        float panelH = panelW * 480f / 640f;
        if (panelH > H * 0.86f) {
            panelH = H * 0.86f;
            panelW = panelH * 640f / 480f;
        }
        float px = W / 2f - panelW / 2f, py = H / 2f - panelH / 2f;
        RectF panel = new RectF(px, py, px + panelW, py + panelH);

        if (score.ready()) {
            p.setAlpha(255);
            c.drawBitmap(score.pmain, null, panel, p);
            if (score.pinset != null) {
                RectF ins = new RectF(px + panelW * 0.05f, py + panelH * 0.03f,
                        px + panelW * 0.95f, py + panelH * 0.03f + panelH * 0.075f);
                c.drawBitmap(score.pinset, null, ins, p);
            }
        } else {
            bevelPanel(c, panel);
        }

        float cx = panel.centerX();
        float sx = panelW / 640f;      // one design unit -> px
        float sy = panelH / 480f;

        p.setTextAlign(Paint.Align.CENTER);
        p.setTextSize(30 * sx);
        drawOutlined(c, win ? "胜  利" : "任 务 失 败", cx, py + panelH * 0.095f,
                win ? Color.rgb(150, 255, 170) : Color.rgb(255, 120, 110));

        // scoreboard rows: label left, value right, boxed like the original
        String[][] rows = {
                {"击杀敌方单位", String.valueOf(game.kills)},
                {"损失己方单位", String.valueOf(game.losses)},
                {"采集晶体矿", String.valueOf(game.mineralsMined)},
                {"采集高能瓦斯", String.valueOf(game.gasMined)},
                {"作战时间", String.format("%d:%02d", (int) game.time / 60, (int) game.time % 60)},
        };
        float rowH = panelH * 0.085f;
        float firstY = py + panelH * 0.30f;
        for (int i = 0; i < rows.length; i++) {
            RectF box = new RectF(px + panelW * 0.14f, firstY + i * rowH,
                    px + panelW * 0.86f, firstY + i * rowH + rowH * 0.78f);
            if (score.scorebox != null) {
                c.drawBitmap(score.scorebox, null, box, p);
            } else {
                p.setColor(Color.argb(170, 14, 20, 32));
                c.drawRect(box, p);
                p.setStyle(Paint.Style.STROKE);
                p.setColor(PANEL_EDGE);
                c.drawRect(box, p);
                p.setStyle(Paint.Style.FILL);
            }
            p.setTextSize(14 * sx);
            p.setTextAlign(Paint.Align.LEFT);
            p.setColor(Color.rgb(210, 226, 246));
            c.drawText(rows[i][0], box.left + 14 * sx, box.centerY() + 5 * sy, p);
            p.setTextAlign(Paint.Align.RIGHT);
            p.setColor(Color.rgb(255, 224, 140));
            c.drawText(rows[i][1], box.right - 14 * sx, box.centerY() + 5 * sy, p);
        }
        // v2.7 batch 8.3: mission objectives + grade ride on the score panel
        if (mission != null) {
            int done = 0, total = 0;
            for (Mission.Objective o : mission.objectives) {
                total++;
                if (o.done) done++;
            }
            p.setTextAlign(Paint.Align.CENTER);
            p.setTextSize(13 * sx);
            drawOutlined(c, "目标 " + done + "/" + total + "   评价 "
                    + mission.grade(game.losses), cx, py + panelH * 0.885f,
                    Color.rgb(255, 224, 140));
        }
        p.setTextAlign(Paint.Align.CENTER);
        p.setTextSize(13 * sx);
        p.setColor(Color.rgb(200, 215, 240));
        c.drawText("点击任意处返回主菜单", cx, py + panelH * 0.95f, p);
        p.setTextAlign(Paint.Align.LEFT);
    }
    private float halfW() {
        ensureHud();
        return hud.halfW;
    }

    private float halfH() {
        ensureHud();
        return hud.halfH;
    }

    /**
     * v2.28: which upgrade class a research building sells. The engineering bay
     * is the infantry shop, the factory the vehicle shop and the armoury the
     * ship shop -- the plan's "e-bay/factory/armory 各管一线". A building with
     * no line (everything else) returns null and shows no research cells.
     */
    private static String upgradeLine(String buildingKey) {
        switch (buildingKey) {
            case "engbay": return "infantry";
            case "factory": return "vehicle";
            case "armory": return "ship";
            default: return null;
        }
    }

    private static String upgradeLineName(String cls) {
        switch (cls) {
            case "infantry": return "步兵";
            case "vehicle": return "载具";
            case "ship": return "空军";
            default: return "";
        }
    }

    private Bitmap iconFor(String action) {
        switch (action) {
            case "attack": return bank.icon("ic_attack");
            case "stop": return bank.icon("ic_stop");
            case "move": return bank.icon("ic_move");
            case "siege": return bank.icon("ic_siege");
            case "unsiege": return bank.icon("ic_unsiege");
            case "patrol": return bank.icon("ic_patrol");
            case "repair": return bank.icon("ic_repair");
            // the build submenu's "back" is a cancel/back glyph; the "建造"
            // opener has no verified submenu icon, so it renders as text
            case "page:0": return bank.icon("ic_cancel");
            case "rally": return bank.icon("ic_move");
            case "build:cc": return bank.icon("ic_cc");
            case "build:depot": return bank.icon("ic_depot");
            case "build:barracks": return bank.icon("ic_barracks");
            case "build:refinery": return bank.icon("ic_refinery");
            case "build:factory": return bank.icon("ic_factory");
            case "build:turret": return bank.icon("ic_turret");
            case "train:scv": return bank.icon("ic_scv");
            case "train:marine": return bank.icon("ic_marine");
            case "train:firebat": return bank.icon("ic_firebat");
            case "train:vulture": return bank.icon("ic_vulture");
            case "train:tank": return bank.icon("ic_tank");
            case "build:academy": return bank.icon("ic_academy");
            // v2.8: cmdicons #122 is the engineering bay; #123 is the armory.
            // v2.7 borrowed the armory icon here, so the bay looked wrong.
            case "build:engbay": return bank.icon("ic_engbay");
            // v2.8: the units the art gate cleared (unitId 1 = Ghost,
            // 8 = Wraith) and the new Starport that builds the wraith.
            case "build:starport": return bank.icon("ic_starport");
            case "train:ghost": return bank.icon("ic_ghost");
            case "train:wraith": return bank.icon("ic_wraith");
            // v2.25: the add-on builds, the scanner sweep and the nuclear
            // strike. ic_scan/ic_nukestrike are the repack's own ability
            // buttons (unitnames.txt ids 316/257); the five add-on cells use
            // their units.dat building icons.
            case "addon:comsat": return bank.icon("ic_comsat");
            case "addon:controlt": return bank.icon("ic_controlt");
            case "addon:machineshop": return bank.icon("ic_machineshop");
            case "addon:physicslab": return bank.icon("ic_physicslab");
            case "addon:nukesilo": return bank.icon("ic_nukesilo");
            case "scan": return bank.icon("ic_scan");
            case "nuke": return bank.icon("ic_nukestrike");
            // v2.26: merge has no dedicated button in the pack, so it borrows
            // the archon's own unit icon (units.dat 68 / 63) -- which is what
            // the original's merge button shows anyway. Burrow uses the
            // zerg's own burrow art (units.dat 118 "Zerg Burrow").
            case "merge": return bank.icon("ic_archon");
            // The pack has no verified burrow button frame -- the ability
            // block's indices are not the units.dat ids, and guessing one
            // would ship the wrong art. Like the other unproven buttons it
            // renders as a text cell (see the fallback in drawCmdCard).
            case "burrow": return null;
            // v2.8: zerg cells. Every one of these is a cmdicons frame whose
            // number is the units.dat id, the same rule the terran rows use.
            case "build:hatchery": return bank.icon("ic_hatchery");
            case "build:pool": return bank.icon("ic_pool");
            case "build:extractor": return bank.icon("ic_extractor");
            case "build:spire": return bank.icon("ic_spire");
            case "build:sunken": return bank.icon("ic_sunken");
            case "train:drone": return bank.icon("ic_drone");
            case "train:over": return bank.icon("ic_overlord");
            case "train:zergling": return bank.icon("ic_zergling");
            case "train:hydra": return bank.icon("ic_hydra");
            case "train:muta": return bank.icon("ic_mutalisk");
            // v2.10: protoss cells. Same units.dat-id rule as the other two
            // races -- every icon below came out of cmdicons with the id the
            // plan's table lists, so nothing here is guessed.
            case "build:nexus": return bank.icon("ic_nexus");
            case "build:pylon": return bank.icon("ic_pylon");
            case "build:assim": return bank.icon("ic_assim");
            case "build:gateway": return bank.icon("ic_gateway");
            case "build:forge": return bank.icon("ic_forge");
            case "build:photon": return bank.icon("ic_photon");
            case "build:gencore": return bank.icon("ic_gencore");
            case "build:citadel": return bank.icon("ic_citadel");
            case "build:archives": return bank.icon("ic_archives");
            case "build:robotic": return bank.icon("ic_robotic");
            case "build:stargate": return bank.icon("ic_stargate");
            // the fleet beacon is units.dat 169; the extracted file kept the
            // art's own name
            case "build:beacon": return bank.icon("ic_fleetbeacon");
            case "train:probe": return bank.icon("ic_probe");
            case "train:zealot": return bank.icon("ic_zealot");
            case "train:dragoon": return bank.icon("ic_dragoon");
            case "train:templar": return bank.icon("ic_templar");
            case "train:dtemplar": return bank.icon("ic_dtemplar");
            case "train:archon": return bank.icon("ic_archon");
            case "train:darchon": return bank.icon("ic_darchon");
            case "train:shuttle": return bank.icon("ic_shuttle");
            case "train:scout": return bank.icon("ic_scout");
            case "train:corsair": return bank.icon("ic_corsair");
            case "train:arbiter": return bank.icon("ic_arbiter");
            case "train:carrier": return bank.icon("ic_carrier");
            case "train:reaver": return bank.icon("ic_reaver");
            case "train:observer": return bank.icon("ic_observer");
            // v2.11 batch B/C: zerg completion and the terran Brood War units.
            // Same units.dat-id rule as everything above; the only substitution
            // is the lurker egg, whose #97 icon is a literal "BLANK" bitmap in
            // this repack, so it borrows the zerg egg at #36.
            case "build:creep": return bank.icon("ic_creep");
            case "build:spore": return bank.icon("ic_spore");
            case "build:evolcham": return bank.icon("ic_evolcham");
            case "build:hydraden": return bank.icon("ic_hydraden");
            case "build:mutapit": return bank.icon("ic_mutapit");
            case "build:nest": return bank.icon("ic_nest");
            case "build:nydus": return bank.icon("ic_nydus");
            case "build:ucereb": return bank.icon("ic_ultracavern");
            case "build:cerebrate": return bank.icon("ic_cerebrate");
            case "build:greatspire": return bank.icon("ic_greatspire");
            case "build:lair": return bank.icon("ic_lair");
            case "build:hive": return bank.icon("ic_hive");
            case "train:ultra": return bank.icon("ic_ultra");
            case "train:guardian": return bank.icon("ic_guardian");
            case "train:devourer": return bank.icon("ic_devourer");
            case "train:queen": return bank.icon("ic_queen");
            case "train:defiler": return bank.icon("ic_defiler");
            case "train:lurker": return bank.icon("ic_lurker");
            case "train:broodling": return bank.icon("ic_broodling");
            case "build:armory": return bank.icon("ic_armory");
            case "build:sciencefac": return bank.icon("ic_sciencefac");
            case "train:medic": return bank.icon("ic_medic");
            case "train:valkyrie": return bank.icon("ic_valkyrie");
            case "train:battlecruiser": return bank.icon("ic_battlecruiser");
            case "heal": return bank.icon("ic_medic");
            case "dswarm": return bank.icon("ic_defiler");
            case "ensnare": return bank.icon("ic_defiler");
            case "mine": return bank.icon("ic_spider");
            case "stim":
                // v2.14: ic_hold went home to the hold cell. cmdicons has no
                // verified stimpack frame, so stim renders its label as text
                // like attack-move and the five spell cells do.
                return null;
            case "hold":
                // the ring-with-slash frame verified against the grid in v2.5
                return bank.icon("ic_hold");
            case "upgrade:w": return bank.icon("ic_armory");
            case "upgrade:a": return bank.icon("ic_bunker");
            // v2.23: the new transport / bunker / goliath cells. ic_dropship
            // and ic_goliath were already in the shipped icon set; the load
            // and unload cells have no verified cmdicons frame, so they keep
            // the Chinese-label fallback the spell cells use.
            case "build:bunker": return bank.icon("ic_bunker");
            case "train:goliath": return bank.icon("ic_goliath");
            case "train:dropship": return bank.icon("ic_dropship");
            case "garrison": return bank.icon("ic_bunker");
            default: return null;
        }
    }

    private void addBtn(float x, float y, float s, String action, String label) {
        Btn b = new Btn();
        b.r = new RectF(x, y, x + s, y + s);
        b.action = action;
        b.label = label;
        buttons.add(b);
    }

    private int countTeam(int team) {
        int n = 0;
        for (Game.Ent e : game.ents)
            if (e.alive() && e.team == team && !e.isBuilding()) n++;
        return n;
    }

    // ----------------------------------------------------------------- input
    @Override
    public boolean onTouchEvent(MotionEvent ev) {
        int act = ev.getActionMasked();
        int pointers = ev.getPointerCount();
        // v2.19 batch C: every hit-test below reads the layout rects, so make
        // sure they match the current viewport before the first one runs.
        ensureHud();

        // v2.7 batch 8: the briefing is modal -- tap to advance each line
        if (briefingOpen) {
            if (act == MotionEvent.ACTION_UP) {
                briefingLine++;
                if (briefingLine >= briefing.size()) briefingOpen = false;
            }
            return true;
        }
        // the win/lose overlay is modal: any tap returns to the map menu
        if (!game.status.isEmpty()) {
            if (act == MotionEvent.ACTION_UP) {
                android.content.Context ctx = getContext();
                ctx.startActivity(new android.content.Intent(ctx, MainActivity.class)
                        .addFlags(android.content.Intent.FLAG_ACTIVITY_CLEAR_TOP));
            }
            return true;
        }
        // v2.19 step 3: the layout editor is modal over the pause menu.
        if (layoutEdit) {
            handleLayoutEditTouch(ev);
            return true;
        }
        // the pause menu is modal too: only its own buttons respond
        if (menuOpen) {
            if (settingsOpen) {
                // v2.7 7.2: the volume slider needs move events, so the sheet
                // tracks the drag itself instead of only firing on ACTION_UP.
                if (act == MotionEvent.ACTION_DOWN) {
                    volumeDragging = false;
                    for (Btn b : buttons) {
                        if ("set:vol".equals(b.action) && b.r.contains(ev.getX(), ev.getY())) {
                            volumeDragging = true;
                            setVolumeFromX(ev.getX(), b.r);
                            break;
                        }
                    }
                    if (volumeDragging) return true;
                }
                if (act == MotionEvent.ACTION_MOVE && volumeDragging) {
                    for (Btn b : buttons)
                        if ("set:vol".equals(b.action)) {
                            setVolumeFromX(ev.getX(), b.r);
                            break;
                        }
                    return true;
                }
                if (act == MotionEvent.ACTION_UP) {
                    if (volumeDragging) {
                        volumeDragging = false;
                        commitSettings();
                        return true;
                    }
                    handleButton(ev.getX(), ev.getY());
                }
                return true;
            }
            if (act == MotionEvent.ACTION_UP) handleButton(ev.getX(), ev.getY());
            return true;
        }

        switch (act) {
            case MotionEvent.ACTION_DOWN:
                downX = lastX = ev.getX();
                downY = lastY = ev.getY();
                touching = true;
                touchX = downX;
                touchY = downY;
                touchDownAt = System.currentTimeMillis();
                boxing = false;
                panning = false;
                dragging = false;
                longPressReady = false;
                lastXToWorld = wx(downX);
                lastYToWorld = wy(downY);
                // a hold on a control-group slot is what assigns it, so stamp
                // the press time here and let ACTION_UP decide recall vs assign
                for (Btn b : buttons)
                    if (b.action.startsWith("group:") && b.r.contains(downX, downY)) {
                        int gi = Integer.parseInt(b.action.substring(6));
                        while (groupDownAt.size() <= gi) groupDownAt.add(0L);
                        groupDownAt.set(gi, System.currentTimeMillis());
                    }
                if (inMinimap(downX, downY)) {
                    // v2.7 7.4: tapping the pulsing alert box jumps to the
                    // attacked unit and selects it; elsewhere the minimap still
                    // pans the camera as before.
                    if (alertFlash > 0 && alertX >= 0 && inAlertBox(downX, downY)) {
                        jumpToAlert();
                        break;
                    }
                    panning = true;
                    centerOnMinimap(downX, downY);
                } else if (!inHud(downX, downY)) {
                    // v2.6 #C: a press on the battlefield is a candidate for
                    // either a tap, a camera drag or (if it stays put) a box
                    // select. Presses that start on the HUD -- command cells,
                    // formation slots, the info strip -- only ever tap.
                    longPressReady = true;
                }
                break;

            case MotionEvent.ACTION_POINTER_DOWN:
                if (pointers == 2) {
                    multiTouch = true;
                    // v2.7 7.4: remember when the second finger landed so a
                    // quick two-finger tap on the minimap can be told apart
                    // from a pinch. One finger stays reserved for the camera.
                    twoFingerArmed = true;
                    twoFingerAt = System.currentTimeMillis();
                    twoFingerX = (ev.getX(0) + ev.getX(1)) / 2f;
                    twoFingerY = (ev.getY(0) + ev.getY(1)) / 2f;
                    boxing = false;
                    dragging = false;
                    longPressReady = false;
                    pinchStart = pinchDist(ev);
                    last2X = (ev.getX(0) + ev.getX(1)) / 2f;
                    last2Y = (ev.getY(0) + ev.getY(1)) / 2f;
                }
                break;

            case MotionEvent.ACTION_MOVE:
                lastXToWorld = wx(ev.getX());
                lastYToWorld = wy(ev.getY());
                touchX = ev.getX();
                touchY = ev.getY();
                if (pointers >= 2) {
                    float cx = (ev.getX(0) + ev.getX(1)) / 2f;
                    float cy = (ev.getY(0) + ev.getY(1)) / 2f;
                    // v2.42 fix (defect B): publish, never write the renderer's
                    // camera. See the field comment at the top of the class.
                    tPanBy(-(cx - last2X) / tZoom(), -(cy - last2Y) / tZoom());
                    last2X = cx;
                    last2Y = cy;
                    float d = pinchDist(ev);
                    if (pinchStart > 0 && d > 0) {
                        tZoomTo(Game.clamp(tZoom() * d / pinchStart, zoomMin(), zoomMax()));
                        pinchStart = d;
                    }
                } else if (panning) {
                    centerOnMinimap(ev.getX(), ev.getY());
                } else if (!inHud(ev.getX(), ev.getY())) {
                    // v2.41: the move guard is widget-based, not a band. A drag
                    // or box select keeps running across the old console strip;
                    // it only pauses while the finger sits on a widget rect.
                    if (!boxing && !dragging && longPressReady) {
                        float slop = dragSlopPx();
                        float dist = (float) Math.hypot(ev.getX() - downX, ev.getY() - downY);
                        if (dist > slop) {
                            // v2.6 #C1: a one-finger slide is a camera drag, not
                            // a box select. The slop the gesture ate while it was
                            // still ambiguous is folded in on this first step so the
                            // camera does not lag behind the finger by 8dp.
                            longPressReady = false;
                            dragging = true;
                            tPanBy(-(ev.getX() - downX) / tZoom(),
                                    -(ev.getY() - downY) / tZoom());
                        } else if (System.currentTimeMillis() - touchDownAt >= settings.boxHoldMs) {
                            // v2.6 #C3: held still for 250ms -> box select.
                            longPressReady = false;
                            boxing = true;
                            boxX0 = downX;
                            boxY0 = downY;
                            boxX1 = ev.getX();
                            boxY1 = ev.getY();
                            pingX = downX;
                            pingY = downY;
                            pingT = PING_LIFE;
                        }
                    }
                    if (boxing) {
                        boxX1 = ev.getX();
                        boxY1 = ev.getY();
                    } else if (dragging) {
                        tPanBy(-(ev.getX() - lastX) / tZoom(),
                                -(ev.getY() - lastY) / tZoom());
                    }
                }
                lastX = ev.getX();
                lastY = ev.getY();
                break;

            case MotionEvent.ACTION_UP:
                touching = false;
                multiTouch = false;
                longPressReady = false;
                if (buildKey != null && !inHud(ev.getX(), ev.getY())) {
                    String key = buildKey;
                    final float bx = wx(ev.getX()), by = wy(ev.getY());
                    Game.Type tt = Game.TYPES.get(key);
                    String why = game.buildError(key, bx, by);
                    if (why != null) {
                        // invalid placement: red X + reason, keep placement mode
                        game.addMarker(bx, by, false);
                        toast = why;
                        toastT = 2.0f;
                        play("error", 0.9f);
                    } else {
                        final String k2 = key;
                        buildKey = null;
                        final List<Game.Ent> scvs = pickScv();
                        if (scvs != null) {
                            final Game.Ent scv = scvs.get(0);
                            play("build", 0.9f);
                            game.post(() -> {
                                game.recordOrder("build",
                                        java.util.Collections.singletonList(scv),
                                        k2 + " " + bx + " " + by);
                                game.tryBuild(scv, k2, bx, by);
                            });
                        }
                    }
                    break;
                }
                // v2.6 #C1: a camera drag must not also press whatever button it
                // happens to end on. Taps still reach the buttons untouched.
                if (!dragging && handleButton(ev.getX(), ev.getY())) break;
                if (panning) {
                    panning = false;
                    break;
                }
                if (boxing) {
                    doBoxSelect();
                    boxing = false;
                } else if (!dragging
                        && Math.hypot(ev.getX() - downX, ev.getY() - downY) <= dragSlopPx()) {
                    // v2.6 #C2: a short, still press is a tap. `dragging` is
                    // checked explicitly so a camera drag that happens to end
                    // back near its origin does not fire a stray tap.
                    long now = System.currentTimeMillis();
                    doTap(ev.getX(), ev.getY(),
                            now - lastTapTime < 320 && Math.hypot(ev.getX() - lastTapX,
                                    ev.getY() - lastTapY) < 40);
                    lastTapTime = now;
                    lastTapX = ev.getX();
                    lastTapY = ev.getY();
                }
                dragging = false;
                break;

            case MotionEvent.ACTION_POINTER_UP:
                // v2.7 7.4: a still, quick two-finger tap on the minimap is a
                // move order for the current selection; anything slower or
                // farther is a pinch/pan and is left alone.
                if (twoFingerArmed && pointers == 2
                        && System.currentTimeMillis() - twoFingerAt < 300) {
                    float cx = (ev.getX(0) + ev.getX(1)) / 2f;
                    float cy = (ev.getY(0) + ev.getY(1)) / 2f;
                    if (Math.hypot(cx - twoFingerX, cy - twoFingerY) < 24
                            && inMinimap(cx, cy)) {
                        minimapMoveOrder(cx, cy);
                    }
                }
                twoFingerArmed = false;
                break;

            case MotionEvent.ACTION_CANCEL:
                touching = false;
                multiTouch = false;
                boxing = false;
                panning = false;
                dragging = false;
                longPressReady = false;
                twoFingerArmed = false;
                break;
        }
        return true;
    }

    /** v2.8: the selection's workers, SCV or drone alike. */
    private List<Game.Ent> pickScv() {
        List<Game.Ent> scvs = new ArrayList<>();
        for (Game.Ent e : game.selected())
            if (Game.isWorker(e)) scvs.add(e);
        return scvs;
    }

    /**
     * v2.6 #C3 fallback channel. A finger that never moves still fires MOVE
     * events on most devices, but not all -- so the hold-to-box-select timer is
     * also serviced once per frame on the game thread. Same predicate as the
     * MOVE branch: still inside the slop, still a candidate, past the hold time.
     */
    private void holdStillCheck() {
        if (paused || !touching || !longPressReady || boxing || dragging || panning
                || multiTouch) return;
        if (!game.status.isEmpty()) return;
        if (System.currentTimeMillis() - touchDownAt < settings.boxHoldMs) return;
        float slop = dragSlopPx();
        if (Math.hypot(touchX - downX, touchY - downY) > slop) return;
        longPressReady = false;
        boxing = true;
        boxX0 = downX;
        boxY0 = downY;
        boxX1 = touchX;
        boxY1 = touchY;
        pingX = downX;
        pingY = downY;
        pingT = PING_LIFE;
    }

    private boolean inHud(float x, float y) {
        // v2.41: no band test any more. The HUD is a set of independent
        // widget rects; a point in any of them is HUD, and EVERYTHING else --
        // the gaps between chips, the old console band, the old top bar --
        // falls through to the map. infoPanelRect comes from the last draw
        // (one frame stale at worst, as before).
        ensureHud();
        if (hud.minimapSlot.contains(x, y)) return true;
        if (hud.card.contains(x, y)) return true;
        if (hud.pause.contains(x, y)) return true;
        if (hud.clock.contains(x, y)) return true;
        if (hud.res.contains(x, y)) return true;
        if (!hud.tally.isEmpty() && hud.tally.contains(x, y)) return true;
        if (!infoPanelRect.isEmpty() && infoPanelRect.contains(x, y)) return true;
        // v2.42 batch C: the group block is its own widget and hit-tests as one
        return !hud.groups.isEmpty() && hud.groups.contains(x, y);
    }

    private boolean inMinimap(float x, float y) {
        return minimapRect.contains((int) x, (int) y);
    }

    /** Is (x,y) inside the minimap marker drawn for the last alert? */
    private boolean inAlertBox(float x, float y) {
        float mx = minimapRect.left + alertX / game.wPx * minimapRect.width();
        float my = minimapRect.top + alertY / game.hPx * minimapRect.height();
        float r = 14 * uiScale;
        return Math.abs(x - mx) < r && Math.abs(y - my) < r;
    }

    /** Centre the camera on the last alert and select whatever is there. */
    private void jumpToAlert() {
        // v2.42 fix (defect B): publish, never write the renderer's camera.
        tCenterOn(alertX, alertY);
        for (Game.Ent e : game.ents) e.selected = false;
        Game.Ent best = null;
        float bd = 120 * 120;
        for (Game.Ent e : game.ents) {
            if (!e.alive() || e.team != 0) continue;
            float dx = e.x - alertX, dy = e.y - alertY;
            float d2 = dx * dx + dy * dy;
            if (d2 < bd) {
                bd = d2;
                best = e;
            }
        }
        if (best != null) best.selected = true;
        alertFlash = 0;
        play("click", 0.8f);
    }

    /**
     * v2.7 7.4: minimap move order. The tap point is the world position, so the
     * order is just the ordinary orderMove with the current selection -- no new
     * order type, which keeps the core unchanged.
     */
    private void minimapMoveOrder(float mx, float my) {
        List<Game.Ent> sel = game.selected();
        if (sel.isEmpty()) {
            centerOnMinimap(mx, my);
            return;
        }
        float wx = (mx - minimapRect.left) / minimapRect.width() * game.wPx;
        float wy = (my - minimapRect.top) / minimapRect.height() * game.hPx;
        final float fx = wx, fy = wy;
        final List<Game.Ent> s2 = new ArrayList<>(sel);
        game.post(() -> {
            game.recordOrder("move", s2, fx + " " + fy);
            game.orderMove(s2, fx, fy, false);
        });
        play("click", 0.9f);
    }

    private void centerOnMinimap(float x, float y) {
        // v2.42 fix (defect B): publish, never write the renderer's camera.
        tCenterOn((x - minimapRect.left) / minimapRect.width() * game.wPx,
                (y - minimapRect.top) / minimapRect.height() * game.hPx);
    }

    private boolean handleButton(float x, float y) {
        // v2.20 step 3: the layout editor is modal and draws its own controls on
        // top of the console. The console's card/formation buttons are still in
        // the list (drawHud registers them before the editor draws), and a
        // rect-based first-match walk would let a card slot sitting under the
        // editor's Save/Cancel bar steal the tap. Route the editor's actions
        // first so its own controls always win.
        if (layoutEdit) {
            for (Btn b : buttons) {
                if (b.action != null && b.action.startsWith("ledit:")
                        && b.r.contains(x, y)) {
                    handleLayoutEditAction(b.action);
                    return true;
                }
            }
            return true;    // modal: nothing else is reachable while editing
        }
        for (Btn b : buttons) {
            if (b.r.contains(x, y)) {
                // v2.7 7.2: the settings sheet's own controls are legal while
                // the pause menu is up; everything else stays blocked.
                boolean settingsBtn = b.action.startsWith("set:");
                if (menuOpen && !settingsBtn && !b.action.startsWith("menu:")) continue;
                // v2.12 fix: the settings sheet's own two case-only cells
                // ("set:back", "set:edge") live in handleMenu but are NOT
                // "menu:"-prefixed, so routing on the prefix alone left both
                // dead and trapped the player inside the settings overlay.
                // v2.42 fix: "set:diag" was missing from this list, so the
                // render-diagnostic toggle drew, hit-tested, matched its own
                // button -- and then fell through every branch below to
                // "return false". A tap did nothing and the flag stayed false,
                // which is exactly what the on-device report said. Every
                // settings cell must appear here (or in its own branch below);
                // GameDesktop's "ui sweep" now asserts that, cell by cell.
                if (b.action.startsWith("menu:")
                        || "set:back".equals(b.action) || "set:edge".equals(b.action)
                        || "set:hp".equals(b.action) || "set:diag".equals(b.action)
                        || b.action.startsWith("set:fog")
                        || b.action.startsWith("set:zoom")
                        || b.action.startsWith("set:layout")) {
                    handleMenu(b.action);
                    return true;
                }
                // v2.19 step 3: the layout editor's own controls
                if (b.action.startsWith("ledit:")) {
                    handleLayoutEditAction(b.action);
                    return true;
                }
                if (b.action.startsWith("cancel:")) {
                    final int idx = Integer.parseInt(b.action.substring(7));
                    List<Game.Ent> sel = game.selected();
                    if (!sel.isEmpty()) {
                        final Game.Ent b0 = sel.get(0);
                        play("click", 0.9f);
                        game.post(() -> game.cancelQueue(b0, idx));
                    }
                    return true;
                }
                if (b.action.startsWith("pick:")) {
                    String key = b.action.substring(5);
                    for (Game.Ent e : game.ents)
                        e.selected = e.team == 0 && e.alive() && e.type.key.equals(key);
                    play("click", 0.8f);
                    return true;
                }
                if (b.action.startsWith("set:sens")) {
                    settings.setSensitivity(Integer.parseInt(b.action.substring(8)));
                    settings.save();
                    play("click", 0.8f);
                    return true;
                }
                if (b.action.startsWith("set:hold")) {
                    settings.setHoldLevel(Integer.parseInt(b.action.substring(8)));
                    settings.save();
                    play("click", 0.8f);
                    return true;
                }
                if ("set:vol".equals(b.action)) {
                    setVolumeFromX(x, b.r);
                    commitSettings();
                    play("click", 0.8f);
                    return true;
                }
                if (b.action.startsWith("group:")) {
                    handleGroup(Integer.parseInt(b.action.substring(6)));
                    return true;
                }
                if (b.action.endsWith(":locked")) {
                    // explained by the toast + red badge; no silent failure
                    String tKey = b.action.replace(":locked", "")
                            .substring(b.action.indexOf(':') + 1);
                    String why = b.action.startsWith("train")
                            ? game.trainError(tKey)
                            : game.buildError(tKey, lastXToWorld, lastYToWorld);
                    toast = why != null ? why : "资源不足";
                    toastT = 2.0f;
                    play("error", 0.9f);
                    return true;
                }
                if (b.action.startsWith("build:")) {
                    buildKey = b.action.substring(6);
                } else if (b.action.startsWith("train:")) {
                    List<Game.Ent> sel = game.selected();
                    if (!sel.isEmpty()) {
                        final Game.Ent b0 = sel.get(0);
                        final String tKey = b.action.substring(6);
                        String why = game.trainError(tKey);
                        if (why != null) {
                            toast = why;
                            toastT = 2.0f;
                            play("error", 0.9f);
                        } else {
                            play("click", 0.9f);
                            game.post(() -> {
                                game.recordOrder("train",
                                        java.util.Collections.singletonList(b0), tKey);
                                game.tryTrain(b0, tKey);
                            });
                        }
                    }
                } else if (b.action.equals("siege") || b.action.equals("unsiege")
                        || b.action.equals("burrow") || b.action.equals("unburrow")) {
                    // v2.11: burrowing is the tank's morph wearing a different
                    // label, so all four cells land in the same call.
                    List<Game.Ent> sel = game.selected();
                    for (Game.Ent e : sel) {
                        final Game.Ent t = e;
                        game.post(() -> game.toggleSiege(t));
                    }
                    play("click", 0.8f);
                } else if (b.action.equals("stop")) {
                    final List<Game.Ent> s2 = new ArrayList<>(game.selected());
                    game.post(() -> {
                        for (Game.Ent e : s2) {
                            e.target = null;
                            e.moving = false;
                            e.path = Game.Ent.EMPTY_PATH;
                            e.aiTimer = 0;
                            // v2.44 pathing fix: Stop must also drop anything
                            // waiting in the path budget queue. Without this the
                            // request survived, drainPathQueue served it a few
                            // ticks later and set moving back to true -- so the
                            // unit visibly walked off to the destination the
                            // player had just cancelled. orderHold has always
                            // done this; Stop was the one order that did not.
                            game.cancelQueuedPath(e);
                        }
                    });
                } else if (b.action.equals("stim")) {
                    List<Game.Ent> sel = game.selected();
                    boolean any = false;
                    for (Game.Ent e : sel) {
                        if (game.stim(e)) any = true;
                    }
                    if (any) {
                        play("click", 0.9f);
                    } else {
                        toast = "无法使用兴奋剂";
                        toastT = 1.6f;
                        play("error", 0.9f);
                    }
                } else if (b.action.startsWith("upgrade:w")
                        || b.action.startsWith("upgrade:a")
                        || b.action.equals("upgrade:pop")) {
                    // v2.28: the research cells carry their class in the action
                    // ("upgrade:w:infantry"), so the same handler serves all
                    // three buildings. v2.27: the population ceiling rides
                    // along on the same card.
                    String why;
                    if (b.action.startsWith("upgrade:w:")) {
                        why = game.buyWeaponUpgrade(b.action.substring(10));
                    } else if (b.action.startsWith("upgrade:a:")) {
                        why = game.buyArmorUpgrade(b.action.substring(10));
                    } else if (b.action.equals("upgrade:pop")) {
                        why = game.raiseSupplyCap();
                    } else {
                        why = "未知升级";
                    }
                    if (why != null) {
                        toast = why;
                        toastT = 2.0f;
                        play("error", 0.9f);
                    } else {
                        if (b.action.equals("upgrade:pop")) {
                            toast = "人口上限 " + Game.SUPPLY_TIERS[game.capTier];
                            toastT = 1.8f;
                        }
                        play("build", 0.9f);
                    }
                } else if (b.action.equals("rally")) {
                    buildKey = null;
                    // next tap on ground sets rally — reuse placement state
                    rallyMode = true;
                    clearTargetingModes();
                } else if (b.action.equals("storm")) {
                    // v2.10: arm storm targeting. The card reports a bad caster
                    // (a non-templar can never see this cell) but the real check
                    // runs again on the ground tap.
                    Game.Ent c = game.selected().isEmpty() ? null : game.selected().get(0);
                    String why = game.stormError(c);
                    if (why != null) {
                        toast = why;
                        toastT = 2.0f;
                        play("error", 0.9f);
                    } else {
                        buildKey = null;
                        clearTargetingModes();
                        stormMode = true;
                        play("click", 0.9f);
                    }
                } else if (b.action.equals("dswarm") || b.action.equals("ensnare")) {
                    // v2.11 batch B: the defiler's two fields, armed exactly the
                    // way the storm is.
                    final boolean swarm = b.action.equals("dswarm");
                    Game.Ent c = game.selected().isEmpty() ? null : game.selected().get(0);
                    String why = swarm ? game.dswarmError(c) : game.ensnareError(c);
                    if (why != null) {
                        toast = why;
                        toastT = 2.0f;
                        play("error", 0.9f);
                    } else {
                        buildKey = null;
                        clearTargetingModes();
                        dswarmMode = swarm;
                        ensnareMode = !swarm;
                        mineMode = false;
                        play("click", 0.9f);
                    }
                } else if (b.action.equals("heal")) {
                    // v2.11 batch C: arm heal targeting. A medic with nothing
                    // to do can still arm it; the pick is validated on the tap.
                    buildKey = null;
                    clearTargetingModes();
                    healMode = true;
                    play("click", 0.9f);
                } else if (b.action.equals("mine")) {
                    // v2.11 batch C: the vulture needs no target, so unlike the
                    // other modes this one can fire straight away and only arms
                    // itself as a fallback for the off-cooldown case.
                    List<Game.Ent> sel = game.selected();
                    boolean any = false;
                    for (Game.Ent e : sel) {
                        if (game.mineError(e) == null) any = true;
                    }
                    if (!any) {
                        toast = "无法布雷";
                        toastT = 2.0f;
                        play("error", 0.9f);
                    } else {
                        buildKey = null;
                        clearTargetingModes();
                        mineMode = true;
                        play("click", 0.9f);
                    }
                } else if (b.action.equals("cloak")) {
                    // v2.22 batch B: the personal cloak toggle -- an immediate
                    // order, recorded like siege so replays replay it.
                    Game.Ent c = game.selected().isEmpty() ? null : game.selected().get(0);
                    String why = game.cloakError(c);
                    if (why != null) {
                        toast = why;
                        toastT = 2.0f;
                        play("error", 0.9f);
                    } else {
                        final Game.Ent c2 = c;
                        final boolean on = !c2.cloakOn;
                        game.post(() -> {
                            game.recordOrder("cloak",
                                    java.util.Collections.singletonList(c2), "");
                            game.toggleCloak(c2);
                        });
                        toast = on ? "已隐形" : "已显形";
                        toastT = 1.2f;
                        play("click", 0.9f);
                    }
                } else if (b.action.equals("merge")) {
                    // v2.26: the templar merge. Immediate -- the two units are
                    // already named by the selection, so there is nothing to
                    // aim. Both are consumed and the archon appears between
                    // them (see Game.orderMerge).
                    List<Game.Ent> sel = new ArrayList<>(game.selected());
                    String why = game.mergeError(sel, null);
                    if (why != null) {
                        toast = why;
                        toastT = 2.0f;
                        play("error", 0.9f);
                    } else {
                        final List<Game.Ent> pair = new ArrayList<>(sel);
                        game.post(() -> {
                            game.recordOrder("merge", pair, "");
                            game.orderMerge(pair, null);
                        });
                        play("click", 0.9f);
                    }
                } else if (b.action.equals("burrow")) {
                    // v2.26: the burrow toggle -- an immediate order recorded
                    // like siege/cloak so a replay replays it.
                    final List<Game.Ent> sel = new ArrayList<>(game.selected());
                    boolean any = false;
                    for (Game.Ent e : sel) if (game.burrowError(e) == null) any = true;
                    if (!any) {
                        toast = "无法钻地";
                        toastT = 2.0f;
                        play("error", 0.9f);
                    } else {
                        game.post(() -> {
                            for (Game.Ent e : sel) {
                                if (game.burrowError(e) != null) continue;
                                game.recordOrder("burrow",
                                        java.util.Collections.singletonList(e), "");
                                game.toggleBurrow(e);
                            }
                        });
                        play("click", 0.9f);
                    }
                } else if (b.action.equals("load")) {
                    // v2.23 batch A: arm a friendly-unit pick. The tap names
                    // the unit to take aboard; the transport walks to it and
                    // collects it on arrival (see Game.updateLoading).
                    buildKey = null;
                    clearTargetingModes();
                    loadMode = true;
                    play("click", 0.9f);
                } else if (b.action.equals("unload")) {
                    // v2.23 batch A: arm a ground pick. The tap is the drop
                    // point; every selected transport empties its hold there.
                    buildKey = null;
                    clearTargetingModes();
                    unloadMode = true;
                    play("click", 0.9f);
                } else if (b.action.equals("garrison")) {
                    // v2.23 batch B: sweep nearby infantry into the bunker.
                    // Immediate, like hold -- there is nothing to aim.
                    List<Game.Ent> sel = game.selected();
                    if (!sel.isEmpty()) {
                        final Game.Ent bunker = sel.get(0);
                        game.post(() -> game.orderGarrisonNear(bunker));
                        play("click", 0.9f);
                    }
                } else if (b.action.equals("release")) {
                    // v2.23 batch B: spill the garrison out beside the bunker.
                    List<Game.Ent> sel = game.selected();
                    if (!sel.isEmpty()) {
                        final Game.Ent bunker = sel.get(0);
                        game.post(() -> game.ungarrisonAll(bunker));
                        play("click", 0.9f);
                    }
                } else if (b.action.equals("scan")) {
                    // v2.25: arm the scanner sweep. Ground pick, like storm --
                    // the tap is the centre of the square the comsat reveals.
                    Game.Ent c = game.selected().isEmpty() ? null : game.selected().get(0);
                    String why = game.scanError(c);
                    if (why != null) {
                        toast = why;
                        toastT = 2.0f;
                        play("error", 0.9f);
                    } else {
                        buildKey = null;
                        clearTargetingModes();
                        scanMode = true;
                        play("click", 0.9f);
                    }
                } else if (b.action.equals("nuke")) {
                    // v2.25: arm the nuclear strike. Ground pick; the ghost is
                    // rooted for the countdown once the aim lands.
                    Game.Ent c = game.selected().isEmpty() ? null : game.selected().get(0);
                    String why = game.nukeError(c);
                    if (why != null) {
                        toast = why;
                        toastT = 2.0f;
                        play("error", 0.9f);
                    } else {
                        buildKey = null;
                        clearTargetingModes();
                        nukeMode = true;
                        play("click", 0.9f);
                    }
                } else if (b.action.startsWith("addon:")) {
                    // v2.25: attach an add-on to the selected building. It is
                    // placed for the player (the pad is fixed by geometry), so
                    // this is an immediate order rather than a placement mode.
                    final String key = b.action.substring(6);
                    List<Game.Ent> sel = game.selected();
                    if (!sel.isEmpty()) {
                        final Game.Ent parent = sel.get(0);
                        String why = game.addonError(parent, key);
                        if (why != null) {
                            toast = why;
                            toastT = 2.0f;
                            play("error", 0.9f);
                        } else {
                            game.post(() -> {
                                game.recordOrder("addon",
                                        java.util.Collections.singletonList(parent), key);
                                game.buildAddon(parent, key);
                            });
                            play("build", 0.9f);
                        }
                    }
                } else if (b.action.equals("hold")) {
                    // v2.14: hold is an immediate order like stop -- nothing to
                    // arm, no follow-up tap. Units keep auto-acquiring inside
                    // weapon range and walk home afterwards.
                    List<Game.Ent> sel = game.selected();
                    if (!sel.isEmpty()) {
                        for (Game.Ent e : sel) playAck(e);
                        final List<Game.Ent> s2 = new ArrayList<>(sel);
                        game.post(() -> game.orderHold(s2));
                        play("click", 0.9f);
                    }
                } else if (b.action.equals("emp") || b.action.equals("dweb")) {
                    // v2.14: the two ground-targeted fields arm exactly like
                    // the storm -- caster validated now, aim validated on tap.
                    final boolean pulse = b.action.equals("emp");
                    Game.Ent c = game.selected().isEmpty() ? null : game.selected().get(0);
                    String why = pulse ? game.empError(c) : game.dwebError(c);
                    if (why != null) {
                        toast = why;
                        toastT = 2.0f;
                        play("error", 0.9f);
                    } else {
                        buildKey = null;
                        clearTargetingModes();
                        if (pulse) empMode = true;
                        else dwebMode = true;
                        play("click", 0.9f);
                    }
                } else if (b.action.equals("irradiate")
                        || b.action.equals("yamato") || b.action.equals("lockdown")) {
                    // v2.14: the three unit-targeted spells arm like heal, but
                    // the tap names a HOSTILE unit, so the pick gate (unlike
                    // repair/heal) must not filter by team. The null-target
                    // error here is caster-side only; the real target check
                    // runs on the tap.
                    final String kind = b.action;
                    Game.Ent c = game.selected().isEmpty() ? null : game.selected().get(0);
                    String why = kind.equals("irradiate") ? game.irradiateError(c, null)
                            : kind.equals("yamato") ? game.yamatoError(c, null)
                            : game.lockdownError(c, null);
                    if (why != null) {
                        toast = why;
                        toastT = 2.0f;
                        play("error", 0.9f);
                    } else {
                        buildKey = null;
                        clearTargetingModes();
                        if (kind.equals("irradiate")) irradiateMode = true;
                        else if (kind.equals("yamato")) yamatoMode = true;
                        else lockdownMode = true;
                        play("click", 0.9f);
                    }
                } else if (b.action.startsWith("page:")) {
                    // v2.12 batch E: the command-card pages are the same
                    // swish panel metaphor as the console menu.
                    int to = Integer.parseInt(b.action.substring(5));
                    play(to == 0 ? "ui_swishout" : "ui_swishin", 0.8f);
                    cardPage = to;
                } else if (b.action.equals("patrol")) {
                    buildKey = null;
                    clearTargetingModes();
                    patrolMode = true;
                    play("click", 0.8f);
                } else if (b.action.equals("amove")) {
                    buildKey = null;
                    clearTargetingModes();
                    amoveMode = true;
                    play("click", 0.8f);
                } else if (b.action.equals("repair")) {
                    buildKey = null;
                    clearTargetingModes();
                    repairMode = true;
                    play("click", 0.8f);
                }
                return true;
            }
        }
        return false;
    }

    private void handleMenu(String action) {
        switch (action) {
            case "menu:toggle":
                menuOpen = !menuOpen;
                paused = menuOpen;
                if (menuOpen) startBgm();
                // v2.12 batch E: the glue panel whooshes mark the console
                // menu opening and closing; everything inside it is ui_click.
                play(menuOpen ? "ui_swishin" : "ui_swishout", 0.9f);
                break;
            case "menu:resume":
                menuOpen = false;
                paused = false;
                play("ui_swishout", 0.9f);
                break;
            case "menu:restart":
                restart();
                menuOpen = false;
                paused = false;
                play("ui_click", 0.9f);
                break;
            case "menu:quit":
                play("ui_swishout", 0.9f);
                android.content.Context ctx = getContext();
                ctx.startActivity(new android.content.Intent(ctx, MainActivity.class)
                        .addFlags(android.content.Intent.FLAG_ACTIVITY_CLEAR_TOP));
                break;
            case "menu:vol-":
                volume = Math.max(0f, volume - 0.1f);
                commitSettings();
                play("ui_click", 0.9f);
                break;
            case "menu:vol+":
                volume = Math.min(1f, volume + 0.1f);
                commitSettings();
                play("ui_click", 0.9f);
                break;
            case "menu:bgm":
                bgmOn = !bgmOn;
                if (bgmOn) startBgm();
                else stopBgm();
                play("ui_click", 0.9f);
                break;
            case "menu:settings":
                settingsOpen = true;
                play("ui_swishin", 0.9f);
                break;
            case "menu:layoutedit":
                startLayoutEdit();
                break;
            case "menu:savereplay":
                saveReplay();
                break;
            case "menu:playreplay":
                playReplay();
                break;
            case "set:back":
                settingsOpen = false;
                play("ui_swishout", 0.9f);
                break;
            case "set:edge":
                settings.edgeScroll = !settings.edgeScroll;
                commitSettings();
                play("ui_click", 0.9f);
                break;
            case "set:hp":
                settings.alwaysShowHp = !settings.alwaysShowHp;
                commitSettings();
                play("ui_click", 0.9f);
                break;
            case "set:diag":
                // v2.42 batch B: the render diagnostic. Takes effect the next
                // frame (the chunk loop reads the flag directly); no restart.
                settings.renderDiag = !settings.renderDiag;
                diagFrame = 0;
                diagMissLog = 0;
                // Each toggle starts a clean measurement: stale peaks from a
                // previous fling would otherwise be mistaken for the new one.
                diagMissPeak = 0;
                diagPeakKeys = "";
                diagPeakCam = "";
                diagPeakAge = 0;
                diagCalmFrames = 0;
                diagLog.clear();
                // v2.43: the perf ring restarts too, so the first summary after
                // switching the readout on describes only frames since then.
                perfHead = 0;
                perfCount = 0;
                perfLogT = 0.2f;
                perfLine = "";
                perfLine2 = "";
                commitSettings();
                play("ui_click", 0.9f);
                break;
            case "set:fog0":
            case "set:fog1":
                // v2.18 batch A: instant switch -- the fog bitmap is rebuilt
                // every frame and the enemy gate reads the field directly, so
                // no restart is needed. Fog grid state is untouched.
                settings.fogStyle = action.equals("set:fog1") ? Settings.FOG_HOK
                        : Settings.FOG_SC;
                commitSettings();
                play("ui_click", 0.9f);
                break;
            case "set:layout0":
            case "set:layout1":
            case "set:layout2":
            case "set:layout3":
                // v2.19 batch C: the layout is recomputed every frame, so a
                // preset change is live immediately; the camera re-clamps to
                // the new envelope on the next frame.
                // v2.20 step 3: 自定义 needs a saved spec first; a tap without
                // one explains how to make it rather than switching silently.
                if (action.equals("set:layout3")
                        && !(settings.layoutCustom && customSpec() != null)) {
                    toast = "先在暂停菜单用“布局编辑”保存一套布局";
                    toastT = 2.4f;
                    play("error", 0.7f);
                    break;
                }
                settings.hudPreset = action.charAt(action.length() - 1) - (char) 48;
                commitSettings();
                ensureHud();
                play("ui_click", 0.9f);
                break;
            case "set:zoom0":
            case "set:zoom1":
            case "set:zoom2":
                // v2.18 batch B: adopting a preset resets the live zoom to that
                // preset default (see applySettings) and clamps the pinch range.
                settings.zoomLevel = action.charAt(action.length() - 1) - (char) 48;
                commitSettings();
                applySettings();
                play("ui_click", 0.9f);
                break;
            case "menu:save":
                saveGame();
                break;
            case "menu:load":
                loadGame();
                break;
        }
    }

    /**
     * v2.7 batch 8.2: unlock the next mission. Written from the view because
     * the result is decided on the game thread but the progress store is an
     * Android SharedPreferences, which MainActivity reads back on resume.
     */
    private void recordCampaignWin() {
        if (mission == null || mission.id.isEmpty()) return;
        try {
            android.content.SharedPreferences sp = getContext()
                    .getSharedPreferences("xjzb_campaign", Context.MODE_PRIVATE);
            int idx = Integer.parseInt(mission.id.substring(1));
            if (idx > sp.getInt("progress", 0)) {
                sp.edit().putInt("progress", idx).apply();
            }
        } catch (Exception ignored) {
        }
    }

    private java.io.File saveFile() {
        return new java.io.File(getContext().getFilesDir(), "save_" + map.id + ".txt");
    }

    /** v2.19 batch 5: where a match's replay is written. */
    private java.io.File replayFile() {
        return new java.io.File(getContext().getFilesDir(), "replay_" + map.id + ".txt");
    }

    /** Write the recorded replay of the current match to app storage. */
    private void saveReplay() {
        try (java.io.Writer w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(replayFile()), "UTF-8")) {
            w.write(game.serializeReplay());
            toast = "已保存回放(" + game.replayLog.size() + " 条指令)";
            toastT = 1.8f;
            play("build", 1.0f);
        } catch (Exception ex) {
            toast = "回放保存失败:" + ex.getMessage();
            toastT = 1.8f;
            play("error", 0.7f);
        }
    }

    /** Restart the map and re-simulate the saved replay, with input disabled. */
    private void playReplay() {
        java.io.File f = replayFile();
        if (!f.exists()) {
            toast = "没有 " + map.id + " 的回放";
            toastT = 1.8f;
            play("error", 0.7f);
            return;
        }
        try (java.io.BufferedReader r = new java.io.BufferedReader(
                new java.io.InputStreamReader(new java.io.FileInputStream(f), "UTF-8"))) {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = r.readLine()) != null) sb.append(line).append('\n');
            Game fresh = new Game(map.w, map.h, map.walk, map.elev, map.starts,
                    map.units, game.race);
            fresh.mapMeta = map.metaText;
            fresh.difficulty = game.difficulty;
            if (!fresh.loadReplay(sb.toString())) {
                toast = "回放格式错误";
                toastT = 1.8f;
                play("error", 0.7f);
                return;
            }
            game = fresh;
            replayPlaying = true;
            for (Game.Ent e : game.ents) e.selected = false;
            buildKey = null;
            clearTargetingModes();
            menuOpen = false;
            paused = false;
            toast = "回放中(输入已禁用)";
            toastT = 2.0f;
            play("build", 1.0f);
        } catch (Exception ex) {
            toast = "回放失败:" + ex.getMessage();
            toastT = 1.8f;
            play("error", 0.7f);
        }
    }

    private void saveGame() {
        try (java.io.Writer w = new java.io.OutputStreamWriter(
                new java.io.FileOutputStream(saveFile()), "UTF-8")) {
            w.write(game.serialize());
            toast = "已存档(" + map.id + ")";
        } catch (Exception ex) {
            toast = "存档失败:" + ex.getMessage();
        }
        toastT = 1.8f;
        play("click", 0.9f);
    }

    private void loadGame() {
        java.io.File f = saveFile();
        if (!f.exists()) {
            toast = "没有 " + map.id + " 的存档";
            toastT = 1.8f;
            play("error", 0.7f);
            return;
        }
        try (java.io.BufferedReader r = new java.io.BufferedReader(
                new java.io.InputStreamReader(new java.io.FileInputStream(f), "UTF-8"))) {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = r.readLine()) != null) sb.append(line).append('\n');
            Game fresh = new Game(map.w, map.h, map.walk, map.elev, map.starts,
                    map.units, game.race);
            fresh.mapMeta = map.metaText;
            fresh.difficulty = game.difficulty;
            if (!fresh.deserialize(sb.toString())) {
                toast = "存档已损坏";
                toastT = 1.8f;
                play("error", 0.7f);
                return;
            }
            game = fresh;
            for (Game.Ent e : game.ents) e.selected = false;
            buildKey = null;
            clearTargetingModes();
            menuOpen = false;
            paused = false;
            toast = "已读档";
            toastT = 1.6f;
            play("build", 1f);
        } catch (Exception ex) {
            toast = "读档失败:" + ex.getMessage();
            toastT = 1.8f;
            play("error", 0.7f);
        }
    }

    /** Control groups: tap recalls, a long hold assigns the current selection. */
    private void handleGroup(int g) {
        long held = System.currentTimeMillis() - groupDownAt.get(g);
        // the assign/recall decision lives in the core so it can be regression
        // tested on the JVM; the view maps hold duration and renders the message
        int res = game.groupTap(g, held > 450);
        if (res == Game.GROUP_ASSIGNED) {
            List<Game.Ent> grp = game.groups.get(g);
            toast = "编队 " + (g + 1) + " 已指派 " + grp.size() + " 个单位";
            toastT = 1.6f;
            play("click", 0.9f);
        } else if (res == Game.GROUP_EMPTY) {
            toast = "编队 " + (g + 1) + " 为空(长按指派)";
            toastT = 1.6f;
            play("error", 0.7f);
        } else {
            play("click", 0.9f);
        }
    }

    /** Rebuild the simulation in place for the pause menu's restart option. */
    private void restart() {
        // v2.37: a networked match cannot be rebuilt from one side. The peer
        // holds the old Game and the opponent holds its own state, so a restart
        // here would desync the match rather than restart it.
        if (net != null) {
            toast = "联机对战不能重新开始";
            toastT = 1.8f;
            menuOpen = false;
            return;
        }
        Game fresh = new Game(map.w, map.h, map.walk, map.elev, map.starts,
                map.units, game.race);
        // v2.29: restarting a campaign level must restart the LEVEL, not drop
        // into a bare skirmish on the same map. The old code threw the mission
        // away here, so "重新开始" on m01 gave a symmetric skirmish board with
        // none of the mission's units or objectives -- and the level could then
        // never be won.
        fresh.mapMeta = map.metaText;
        fresh.difficulty = game.difficulty;
        if (mission != null) {
            mission = Mission.parse(missionJson);
            if (mission != null) {
                fresh.setMission(mission);
                briefing = new ArrayList<>(mission.briefing);
                briefingOpen = false;
            }
        }
        game = fresh;          // reference swap; one event may still see the old
        buildKey = null;
        rallyMode = false;
        cardPage = 0;
        clearTargetingModes();
        menuOpen = false;
        paused = false;
        // v2.12 batch E: a fresh run must be able to play the result sting again
        resultShown = false;
        toast = null;
        toastT = 0;
        flashes.clear();
        game.groups.clear();
        // v2.42 fix (defect B): a restart must move BOTH copies of the camera;
        // writing only the renderer's would be undone by the next adopted
        // snapshot, and the fresh match would open where the old one ended.
        setCameraNow(map.starts.size() > 0 ? map.starts.get(0)[0] + 64 : 512,
                map.starts.size() > 0 ? map.starts.get(0)[1] + 64 : 512, zoom);
        play("build", 1f);
    }

    private volatile boolean rallyMode;

    /**
     * Command-card page for the SCV (v2.5 batch-6): 0 = orders (attack/stop/
     * patrol/repair + 建造), 1 = the six structures. Reset whenever the
     * selection changes so the card never strands the player on a submenu.
     */
    private int cardPage;
    /** Set while the next ground tap should issue a patrol instead of a move. */
    private volatile boolean patrolMode;
    /** Set while the next tap should pick a repair target. */
    private volatile boolean repairMode;
    /** Set while the next ground tap is an attack-move destination. */
    private volatile boolean amoveMode;
    /**
     * v2.10: set while the next ground tap is a psionic storm target. Mirrors
     * the other one-shot targeting modes so the cast always costs exactly one
     * tap and then clears itself.
     */
    private volatile boolean stormMode;
    /**
     * v2.11 batch C: set while the next tap picks a unit for the medic to heal.
     * Like repairMode it wants a unit, not a patch of ground.
     */
    private volatile boolean healMode;
    /** v2.11 batch B: set while the next ground tap is a dark swarm target. */
    private volatile boolean dswarmMode;
    /** v2.11 batch B: set while the next ground tap is an ensnare target. */
    private volatile boolean ensnareMode;
    /**
     * v2.11 batch C: set while the next ground tap tells a vulture to drop its
     * spider mine. The mine lands where the vulture stands, so the tap only
     * decides which vulture acts.
     */
    private volatile boolean mineMode;

    // ---- v2.14 batch 1: the five science-spell targeting modes. emp/dweb are
    // ground-targeted fields (storm-shaped); irradiate/yamato/lockdown name a
    // hostile unit (repair/heal-shaped, minus the friendly-only gate).
    private volatile boolean empMode;
    private volatile boolean dwebMode;
    private volatile boolean irradiateMode;
    private volatile boolean yamatoMode;
    private volatile boolean lockdownMode;

    // ---- v2.23 batch A/B: the transport and bunker picks. load names a
    // friendly unit (heal-shaped), unload names a patch of ground
    // (storm-shaped); garrison/release are immediate and need no mode.
    private volatile boolean loadMode;
    private volatile boolean unloadMode;

    // ---- v2.25: the comsat's scanner sweep and the ghost's nuclear strike.
    // Both are ground picks (storm-shaped): the tap is the centre of the
    // square the comsat reveals, or the aim point of the missile.
    private volatile boolean scanMode;
    private volatile boolean nukeMode;

    /** Disarms every pending targeting mode (v2.14: one call per site instead
     * of a growing wall of per-field resets). */
    private void clearTargetingModes() {
        amoveMode = false;
        patrolMode = false;
        repairMode = false;
        stormMode = false;
        healMode = false;
        dswarmMode = false;
        ensnareMode = false;
        mineMode = false;
        empMode = false;
        dwebMode = false;
        irradiateMode = false;
        yamatoMode = false;
        lockdownMode = false;
        loadMode = false;
        unloadMode = false;
        scanMode = false;
        nukeMode = false;
    }

    /**
     * Screen-edge scrolling (batch-2 #9): while a finger rests in the outer
     * band (or is dragging a selection box) the camera creeps that way, which
     * is how you reach across a large map one-handed.
     */
    private void edgeScroll(float dt) {
        ensureHud();                   // v2.19: inHud() reads the layout rects
        if (briefingOpen) return;      // v2.7: no camera creep during the briefing
        if (!touching || multiTouch || paused || !game.status.isEmpty()) return;
        if (!settings.edgeScroll) return;   // v2.7 7.2: player can turn it off
        // v2.19: in the compact preset the minimap floats over the playfield,
        // so the inHud() edge test alone would let edge-scroll creep the camera
        // under a finger that is resting on it. inMinimap covers all presets.
        if (inHud(touchX, touchY) || inMinimap(touchX, touchY)) return;
        int W = getWidth(), H = getHeight();
        float band = 46 * uiScale;
        float speed = 460 * dt;
        float dx = 0, dy = 0;
        if (touchX < band) dx = -speed * (1f - touchX / band);
        else if (touchX > W - band) dx = speed * (1f - (W - touchX) / band);
        // v2.41: full-screen edge scroll -- no top-bar/console limits any more.
        // The inHud() guard above already keeps a finger resting on a widget
        // from creeping the camera.
        if (touchY < band) dy = -speed;
        else if (touchY > H - band) dy = speed;
        // v2.42 fix (defect B): publish like every other camera move, so a pan
        // the player is also dragging cannot be silently overwritten when
        // render() adopts its snapshot at the top of the frame.
        tPanBy(dx, dy);
    }

    private void doBoxSelect() {
        float x0 = Math.min(boxX0, boxX1), x1 = Math.max(boxX0, boxX1);
        float y0 = Math.min(boxY0, boxY1), y1 = Math.max(boxY0, boxY1);
        for (Game.Ent e : game.ents) e.selected = false;
        boolean any = false;
        for (Game.Ent e : game.ents) {
            if (e.team != 0 || !e.alive()) continue;
            float ux = sx(e.x), uy = sy(e.y);
            if (ux >= x0 && ux <= x1 && uy >= y0 && uy <= y1) {
                if (!any && e.isBuilding()) continue;   // prefer units in mixed boxes
                e.selected = true;
                any = true;
            }
        }
        if (!any) {
            for (Game.Ent e : game.ents) {
                if (e.team != 0 || !e.alive() || !e.isBuilding()) continue;
                float ux = sx(e.x), uy = sy(e.y);
                if (ux >= x0 && ux <= x1 && uy >= y0 && uy <= y1) {
                    e.selected = true;
                    any = true;
                    break;
                }
            }
        }
        // v2.6 #C3: the old fallback nudged the camera when the box caught
        // nothing. With a slide now meaning drag the camera, that leftover made
        // a deliberate empty-box deselect jerk the view, so it is gone.
        if (any) {
            play("click", 0.7f);        // box select used to be silent (batch-1 #6)
        }
        rallyMode = false;
        cardPage = 0;
        clearTargetingModes();
    }

    private void doTap(float px, float py, boolean doubleTap) {
        if (replayPlaying) return;   // v2.19 batch 5: replay input is disabled
        if (rallyMode) {
            List<Game.Ent> sel = game.selected();
            for (Game.Ent e : sel) {
                e.rallyX = wx(px);
                e.rallyY = wy(py);
            }
            rallyMode = false;
            return;
        }
        float wx = wx(px), wy = wy(py);
        Game.Ent hit = unitAt(wx, wy);
        List<Game.Ent> sel = game.selected();

        if (buildKey != null) return;

        // repair mode (v2.5 batch-6): the next tap picks a friendly damaged
        // unit/building; an illegal pick explains itself instead of failing mute
        if (repairMode) {
            if (hit != null && hit.team == 0 && !sel.isEmpty()) {
                String why = game.repairError(hit);
                if (why != null) {
                    toast = why;
                    toastT = 2.0f;
                    play("error", 0.9f);
                    repairMode = false;
                    return;
                }
                for (Game.Ent e : sel) playAck(e);
                final Game.Ent target = hit;
                final List<Game.Ent> s2 = new ArrayList<>(sel);
                game.post(() -> game.orderRepair(s2, target));
            }
            repairMode = false;
            return;
        }
        // attack-move mode (v2.5 batch-6): the next ground tap advances while
        // engaging anything encountered on the way
        if (amoveMode) {
            if (!sel.isEmpty()) {
                for (Game.Ent e : sel) playAck(e);
                final float fx = wx, fy = wy;
                final List<Game.Ent> s2 = new ArrayList<>(sel);
                game.post(() -> {
                    game.recordOrder("move", s2, fx + " " + fy + " 1");
                    game.orderMove(s2, fx, fy, true);
                });
            }
            amoveMode = false;
            return;
        }
        // patrol mode (v2.5 batch-6): the next ground tap is the far endpoint
        if (patrolMode) {
            if (!sel.isEmpty()) {
                for (Game.Ent e : sel) playAck(e);
                final float fx = wx, fy = wy;
                final List<Game.Ent> s2 = new ArrayList<>(sel);
                game.post(() -> game.orderPatrol(s2, fx, fy));
            }
            patrolMode = false;
            return;
        }
        // psionic storm (v2.10): the next ground tap is the centre of the
        // field. Every selected templar that is off cooldown casts, so a group
        // of them lays down overlapping storms the way the original does.
        if (stormMode) {
            final float fx = wx, fy = wy;
            final List<Game.Ent> s2 = new ArrayList<>(sel);
            boolean any = false;
            for (Game.Ent e : sel) {
                if (game.stormError(e) == null) any = true;
            }
            if (any) {
                for (Game.Ent e : sel) playAck(e);
                game.post(() -> {
                    for (Game.Ent e : s2) game.castStorm(e, fx, fy);
                });
            } else {
                Game.Ent c = sel.isEmpty() ? null : sel.get(0);
                toast = c == null ? "没有施法者" : game.stormError(c);
                toastT = 2.0f;
                play("error", 0.9f);
            }
            stormMode = false;
            return;
        }
        // v2.25: the scanner sweep. The tap is the centre of the square the
        // comsat reveals; every selected comsat that can afford it sweeps, so
        // a group lays overlapping squares like a group of templars does.
        if (scanMode) {
            final float fx = wx, fy = wy;
            final List<Game.Ent> s2 = new ArrayList<>(sel);
            boolean any = false;
            for (Game.Ent e : sel) if (game.scanError(e) == null) any = true;
            if (any) {
                for (Game.Ent e : sel) playAck(e);
                game.post(() -> {
                    for (Game.Ent e : s2) game.castScan(e, fx, fy);
                });
            } else {
                Game.Ent c = sel.isEmpty() ? null : sel.get(0);
                toast = c == null ? "没有雷达站" : game.scanError(c);
                toastT = 2.0f;
                play("error", 0.9f);
            }
            scanMode = false;
            return;
        }
        // v2.25: the nuclear strike. The tap is the aim point; the ghost is
        // rooted for the countdown once it lands.
        if (nukeMode) {
            final float fx = wx, fy = wy;
            final List<Game.Ent> s2 = new ArrayList<>(sel);
            boolean any = false;
            for (Game.Ent e : sel) if (game.nukeError(e) == null) any = true;
            if (any) {
                for (Game.Ent e : sel) playAck(e);
                game.post(() -> {
                    for (Game.Ent e : s2) game.callNuke(e, fx, fy);
                });
                toast = "核弹已发射";
                toastT = 2.0f;
            } else {
                Game.Ent c = sel.isEmpty() ? null : sel.get(0);
                toast = c == null ? "没有幽灵" : game.nukeError(c);
                toastT = 2.0f;
                play("error", 0.9f);
            }
            nukeMode = false;
            return;
        }
        // v2.14: EMP and disruption web are ground-targeted fields and behave
        // exactly like the storm above. EMP strips shields (both teams), the
        // web silences ranged fire (both teams) -- the caster-side error is
        // the same either way, so the aim decides whether it was worth it.
        if (empMode || dwebMode) {
            final boolean pulse = empMode;
            final float fx = wx, fy = wy;
            final List<Game.Ent> s2 = new ArrayList<>(sel);
            boolean any = false;
            for (Game.Ent e : sel) {
                if (pulse ? game.empError(e) == null : game.dwebError(e) == null) any = true;
            }
            if (any) {
                for (Game.Ent e : sel) playAck(e);
                game.post(() -> {
                    for (Game.Ent e : s2) {
                        if (pulse) game.castEmp(e, fx, fy);
                        else game.castDweb(e, fx, fy);
                    }
                });
            } else {
                Game.Ent c = sel.isEmpty() ? null : sel.get(0);
                String why = c == null ? "没有施法者"
                        : (pulse ? game.empError(c) : game.dwebError(c));
                toast = why;
                toastT = 2.0f;
                play("error", 0.9f);
            }
            empMode = false;
            dwebMode = false;
            return;
        }
        // v2.14: irradiate / yamato / lockdown name a hostile unit. Unlike
        // repair and heal there is no team gate on the pick -- the spell's own
        // rule (biological / any target / mechanical) explains a bad pick.
        if (irradiateMode || yamatoMode || lockdownMode) {
            final int kind = irradiateMode ? 0 : (yamatoMode ? 1 : 2);
            if (hit != null && !sel.isEmpty()) {
                String why = kind == 0 ? game.irradiateError(sel.get(0), hit)
                        : kind == 1 ? game.yamatoError(sel.get(0), hit)
                        : game.lockdownError(sel.get(0), hit);
                if (why != null) {
                    toast = why;
                    toastT = 2.0f;
                    play("error", 0.9f);
                } else {
                    for (Game.Ent e : sel) playAck(e);
                    final Game.Ent target = hit;
                    final List<Game.Ent> s2 = new ArrayList<>(sel);
                    game.post(() -> {
                        for (Game.Ent e : s2) {
                            if (kind == 0) game.castIrradiate(e, target);
                            else if (kind == 1) game.castYamato(e, target);
                            else game.castLockdown(e, target);
                        }
                    });
                }
            }
            irradiateMode = false;
            yamatoMode = false;
            lockdownMode = false;
            return;
        }
        // v2.23 batch A: transport load. The tap names a friendly unit; every
        // selected transport that can take it walks over and collects it.
        if (loadMode) {
            if (hit != null && hit.team == 0 && !sel.isEmpty()) {
                boolean any = false;
                for (Game.Ent c : sel) {
                    if (game.loadError(c, hit) == null) any = true;
                }
                if (!any) {
                    toast = game.loadError(sel.get(0), hit);
                    toastT = 2.0f;
                    play("error", 0.9f);
                    loadMode = false;
                    return;
                }
                for (Game.Ent e : sel) playAck(e);
                final Game.Ent target = hit;
                final List<Game.Ent> s2 = new ArrayList<>(sel);
                game.post(() -> {
                    for (Game.Ent c : s2) {
                        if (game.loadError(c, target) != null) continue;
                        game.recordOrder("load", java.util.Collections.singletonList(c),
                                String.valueOf(game.ents.indexOf(target)));
                        // remember the unit and walk to it; updateLoading
                        // boards it once the transport is close enough
                        game.orderLoad(java.util.Collections.singletonList(c), target);
                        game.orderMove(java.util.Collections.singletonList(c),
                                target.x, target.y, false);
                    }
                });
            }
            loadMode = false;
            return;
        }
        // v2.23 batch A: transport unload. The tap is the drop point; every
        // selected transport empties its hold there, spreading the units out.
        if (unloadMode) {
            final float fx = wx, fy = wy;
            final List<Game.Ent> s2 = new ArrayList<>(sel);
            boolean any = false;
            for (Game.Ent c : s2) {
                if (c.type.cargoCap > 0 && !c.cargo.isEmpty()) any = true;
            }
            if (any) {
                for (Game.Ent e : s2) playAck(e);
                game.post(() -> {
                    for (Game.Ent c : s2) {
                        if (c.cargo.isEmpty()) continue;
                        game.recordOrder("unload", java.util.Collections.singletonList(c),
                                fx + " " + fy);
                        game.unloadAll(c, fx, fy);
                    }
                });
            } else {
                toast = "无处卸载";
                toastT = 2.0f;
                play("error", 0.9f);
            }
            unloadMode = false;
            return;
        }
        // v2.11 batch C: medic heal. Same shape as repair -- the tap names a
        // friendly unit -- but the medic's own rules live in Game.healError.
        if (healMode) {
            if (hit != null && hit.team == 0 && !sel.isEmpty()) {
                String why = game.healError(hit);
                if (why != null) {
                    toast = why;
                    toastT = 2.0f;
                    play("error", 0.9f);
                    healMode = false;
                    return;
                }
                for (Game.Ent e : sel) playAck(e);
                final Game.Ent target = hit;
                final List<Game.Ent> s2 = new ArrayList<>(sel);
                game.post(() -> game.orderHeal(s2, target));
            }
            healMode = false;
            return;
        }
        // v2.11 batch B: dark swarm and ensnare are both ground-targeted
        // fields, so they behave exactly like the storm above.
        if (dswarmMode || ensnareMode) {
            final boolean swarm = dswarmMode;
            final float fx = wx, fy = wy;
            final List<Game.Ent> s2 = new ArrayList<>(sel);
            boolean any = false;
            for (Game.Ent e : sel) {
                if (swarm ? game.dswarmError(e) == null : game.ensnareError(e) == null) any = true;
            }
            if (any) {
                for (Game.Ent e : sel) playAck(e);
                game.post(() -> {
                    for (Game.Ent e : s2) {
                        if (swarm) game.castDswarm(e, fx, fy);
                        else game.castEnsnare(e, fx, fy);
                    }
                });
            } else {
                Game.Ent c = sel.isEmpty() ? null : sel.get(0);
                String why = c == null ? "没有施法者"
                        : (swarm ? game.dswarmError(c) : game.ensnareError(c));
                toast = why;
                toastT = 2.0f;
                play("error", 0.9f);
            }
            dswarmMode = false;
            ensnareMode = false;
            return;
        }
        // v2.11 batch C: spider mine. The tap only says "now"; the mine lands
        // at the vulture's own feet, so it never needs a world position.
        if (mineMode) {
            final List<Game.Ent> s2 = new ArrayList<>(sel);
            boolean any = false;
            for (Game.Ent e : sel) {
                if (game.mineError(e) == null) any = true;
            }
            if (any) {
                for (Game.Ent e : sel) playAck(e);
                game.post(() -> {
                    for (Game.Ent e : s2) game.placeMine(e);
                });
            } else {
                toast = "无法布雷";
                toastT = 2.0f;
                play("error", 0.9f);
            }
            mineMode = false;
            return;
        }

        // v2.17: a worker tapping its own unfinished building resumes the build
        // instead of selecting the site. This must run BEFORE the friendly
        // select branch below, otherwise the tap would just select the building
        // and there would be no way to restart construction.
        if (hit != null && hit.isBuilding() && hit.team == 0 && hit.constructing
                && !sel.isEmpty()) {
            boolean allWorkers = true;
            for (Game.Ent e : sel) if (!Game.isWorker(e)) allWorkers = false;
            if (allWorkers) {
                for (Game.Ent e : sel) playAck(e);
                final Game.Ent target = hit;
                final List<Game.Ent> s2 = new ArrayList<>(sel);
                game.post(() -> {
                    game.recordOrder("resume", s2, String.valueOf(game.ents.indexOf(target)));
                    game.orderResumeBuild(s2, target);
                });
                return;
            }
        }

        // v2.44 gas fix: workers tapping a finished gas building gather from
        // its geyser. The refinery sits ON the geyser, so before this the tap
        // always landed in the friendly-select branch below and there was no
        // way to (re)staff a refinery by hand; combined with the missing
        // auto-staff in Game this is why the match never produced gas.
        if (hit != null && hit.isBuilding() && hit.team == 0 && hit.geyser != null
                && !sel.isEmpty()) {
            boolean allWorkers = true;
            for (Game.Ent e : sel) if (!Game.isWorker(e)) allWorkers = false;
            if (allWorkers) {
                final Game.Mineral gm = hit.geyser;
                if (game.gasHarvestable(gm)) {
                    for (Game.Ent e : sel) playAck(e);
                    final List<Game.Ent> s2 = new ArrayList<>(sel);
                    game.post(() -> {
                        game.recordOrder("harvest", s2,
                                String.valueOf(game.minerals.indexOf(gm)));
                        game.orderHarvest(s2, gm);
                    });
                    return;
                }
                // still raising: fall through and select the site as usual
            }
        }

        if (hit != null && hit.team == 0) {
            playWhat(hit);
            if (doubleTap && !hit.isBuilding()) {
                // select all of same type on screen
                for (Game.Ent e : game.ents) e.selected = false;
                for (Game.Ent e : game.ents)
                    if (e.team == 0 && e.alive() && e.type == hit.type
                            && Math.abs(e.x - camX) < halfW() && Math.abs(e.y - camY) < halfH())
                        e.selected = true;
            } else {
                for (Game.Ent e : game.ents) e.selected = false;
                hit.selected = true;
            }
            // a fresh selection resets the SCV submenu and any pending mode
            cardPage = 0;
            clearTargetingModes();
            playWhat(hit);
            return;
        }
        if (hit != null && hit.team == 1) {
            if (!sel.isEmpty()) {
                for (Game.Ent e : sel) playAck(e);
                final Game.Ent target = hit;
                final List<Game.Ent> s2 = new ArrayList<>(sel);
                game.post(() -> {
                    game.recordOrder("attack", s2, String.valueOf(game.ents.indexOf(target)));
                    game.orderAttack(s2, target);
                });
            }
            return;
        }
        // ground
        if (!sel.isEmpty()) {
            Game.Ent first = sel.get(0);
            // harvest: worker tapped on a mineral (SCV or drone)
            Game.Mineral m = mineralAt(wx, wy);
            boolean allWorkers = !sel.isEmpty();
            for (Game.Ent e : sel) if (!Game.isWorker(e)) allWorkers = false;
            if (allWorkers && m != null) {
                for (Game.Ent e : sel) playAck(e);
                final Game.Mineral mm = m;
                final List<Game.Ent> s2 = new ArrayList<>(sel);
                game.post(() -> {
                    game.recordOrder("harvest", s2, String.valueOf(game.minerals.indexOf(mm)));
                    game.orderHarvest(s2, mm);
                });
                return;
            }
            for (Game.Ent e : sel) playAck(e);
            final float fx = wx, fy = wy;
            final List<Game.Ent> s2 = new ArrayList<>(sel);
            game.post(() -> {
                game.recordOrder("move", s2, fx + " " + fy);
                game.orderMove(s2, fx, fy, false);
            });
        } else {
            for (Game.Ent e : game.ents) e.selected = false;
        }
    }

    private Game.Ent unitAt(float wx, float wy) {
        // v2.17 two-stage pick. The old single pass used a world-pixel radius
        // (max(radius, tiles*14) + 6) that at 0.7 zoom is only ~10 screen px for
        // an SCV or marine -- smaller than a fingertip, so a tap that missed a
        // small unit fell through to the ground branch and scattered the whole
        // selection. Stage 1 keeps that precise radius (so a tight clump picks
        // the unit actually under the finger); stage 2, only if stage 1 found
        // nothing, retries with a screen-space floor converted back to world
        // units, taking the nearest centre. The floor is 20dp of screen at the
        // current zoom: 20/zoom world px, which grows as the view zooms out.
        Game.Ent precise = pickNearest(wx, wy, false);
        if (precise != null) return precise;
        return pickNearest(wx, wy, true);
    }

    /** Nearest selectable entity within its hit radius; useFloor applies the
     * v2.17 screen-space pick floor on top of the nominal world radius. */
    private Game.Ent pickNearest(float wx, float wy, boolean useFloor) {
        Game.Ent best = null;
        float bd = Float.MAX_VALUE;
        float floor = useFloor ? dp(20) / zoom : 0f;
        for (Game.Ent e : game.ents) {
            if (!e.alive()) continue;
            // v2.23: a loaded or garrisoned unit is not on the field.
            if (e.cargoOf != null || e.garrisoned) continue;
            if (e.team == 1) {
                // v2.17/v2.18: an enemy is selectable exactly when it is drawn,
                // so the two can never disagree ("visible but not clickable").
                // HOK: only inside current vision (fog==2). SC: anywhere on
                // explored ground (fog!=0), matching the classic render gate.
                if (!enemyVisible(e)) continue;
            }
            // buildings are rectangular: use the footprint half-extent so a
            // corner tap registers (a 4x4 CC is 64 world px to the edge, vs the
            // 56 a circle approximation gave). Non-buildings keep the circle.
            float dx = Math.abs(e.x - wx), dy = Math.abs(e.y - wy);
            float r;
            if (e.isBuilding()) {
                r = e.type.tiles * 16f + 6f;
                if (useFloor) r = Math.max(r, floor);
                if (dx > r || dy > r) continue;
                float d2 = dx * dx + dy * dy;
                if (d2 < bd) { bd = d2; best = e; }
            } else {
                r = Math.max(e.type.radius, e.type.tiles * 14) + 6;
                if (useFloor) r = Math.max(r, floor);
                float ddx = e.x - wx, ddy = e.y - wy;
                float d2 = ddx * ddx + ddy * ddy;
                if (d2 < r * r && d2 < bd) { bd = d2; best = e; }
            }
        }
        return best;
    }

    private Game.Mineral mineralAt(float wx, float wy) {
        for (Game.Mineral m : game.minerals) {
            float dx = m.x - wx, dy = m.y - wy;
            if (dx * dx + dy * dy < 34 * 34) return m;
        }
        return null;
    }

    private float pinchDist(MotionEvent e) {
        if (e.getPointerCount() < 2) return 0;
        float dx = e.getX(0) - e.getX(1), dy = e.getY(0) - e.getY(1);
        return (float) Math.sqrt(dx * dx + dy * dy);
    }

    // ------------------------------------------------------ surface callbacks
    @Override
    public void surfaceCreated(SurfaceHolder holder) {
        running = true;
        thread = new Thread(this);
        thread.start();
        startBgm();
    }

    @Override
    public void surfaceChanged(SurfaceHolder holder, int f, int w, int h) {
    }

    @Override
    public void surfaceDestroyed(SurfaceHolder holder) {
        running = false;
        try {
            if (thread != null) thread.join(600);
        } catch (InterruptedException ignored) {
        }
        stopBgm();
        releaseBgm();
    }
}
