import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import com.xjzb.rts.core.Game;

/**
 * Desktop verification harness: runs the same com.xjzb.rts.core.Game simulation
 * and renders frames to PNG for visual inspection before building the APK.
 *
 * manifest.txt row: key,kind,walkCount,hasAttack,frames,cols
 */
public class GameDesktop {

    static String ASSETS = "F:/KF/XJZB/AndroidPort/app/app/src/main/assets";
    static String OUT = "F:/KF/XJZB/AndroidPort/tools/out/";
    static {
        // Shipped assets are lossless WEBP (tools/slim_assets.py); the
        // TwelveMonkeys plugin on the classpath teaches ImageIO to read them.
        javax.imageio.ImageIO.scanForPlugins();
    }
    static com.xjzb.rts.core.Game game;
    /** v2.29: the loaded map's meta.txt, handed to a mission's economy restore. */
    static String mapMetaText = "";
    static Map<String, BufferedImage> sheets = new HashMap<>();
    static Map<String, int[]> manifest = new HashMap<>();  // key -> {kind, walk, atk, frames, cols}
    static Map<String, BufferedImage> chunkCache = new HashMap<>();
    static String mapId = "bloodbath";
    static int mapW, mapH;
    static boolean[] walk;
    /** v2.23 batch C: per-minitile ground level, or null when the map has none. */
    static byte[] elev;
    static List<int[]> starts = new ArrayList<>();
    static List<Object[]> units = new ArrayList<>();
    static int viewW = 480, viewH = 420;
    /** v2.43 section 2: `bench` mode -- baseline only, no assertions, no PNGs. */
    static boolean benchMode;
    /** v2.43 section 2: bench times the renderer without paying ImageIO.write. */
    static boolean benchNoWrite;
    /** v2.43 section 2: the bench's scratch frame, allocated once. */
    static BufferedImage benchImg;

    public static void main(String[] args) throws Exception {
        // v2.43 section 2: `bench [map]` runs the frame-time baseline and
        // nothing else. Any other first argument stays the map id, so every
        // existing invocation is unchanged.
        if (args.length > 0 && "bench".equals(args[0])) {
            benchMode = true;
            mapId = args.length > 1 ? args[1] : "divide";
        } else if (args.length > 0) {
            mapId = args[0];
        }
        readManifest();
        readMap();
        if (benchMode) {
            bench();
            return;
        }
        game = new com.xjzb.rts.core.Game(mapW, mapH, walk, starts, units);

        for (int i = 0; i < 8 * 30; i++) game.update(1f / 30f);
        render("frame_idle.png");

        List<com.xjzb.rts.core.Game.Ent> scvs = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : game.ents)
            if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);
        if (!scvs.isEmpty()) game.orderMove(scvs, game.wPx / 2f, game.hPx / 2f, false);
        for (int i = 0; i < 6 * 30; i++) game.update(1f / 30f);
        render("frame_move.png");

        // combat + death animation capture: kill a marine and a zergling and
        // render mid-explosion so the new effect sheets are actually exercised.
        com.xjzb.rts.core.Game.Ent m1 = game.spawn("marine", 0, 300, 320, true);
        com.xjzb.rts.core.Game.Ent z1 = game.spawn("zergling", 1, 320, 300, true);
        com.xjzb.rts.core.Game.Ent z2 = game.spawn("zergling", 1, 350, 300, true);
        com.xjzb.rts.core.Game.Ent h1 = game.spawn("hydra", 1, 380, 320, true);
        for (int i = 0; i < 2 * 30; i++) game.update(1f / 30f);
        camX = 330;
        camY = 310;
        render("frame_combat.png");

        // force kills and capture the explosion frames
        z1.hp = 0;
        z2.hp = 0;
        m1.hp = 0;
        h1.hp = 0;
        for (int i = 0; i < 8; i++) game.update(1f / 30f);
        render("frame_explosion.png");
        System.out.println("anims alive after kills: " + game.anims.size());

        // long-run simulation + AI sanity
        for (int i = 0; i < 60 * 30; i++) game.update(1f / 30f);
        for (int i = 0; i < 180 * 30; i++) game.update(1f / 30f);
        int pc = 0, ec = 0, pb = 0, eb = 0;
        for (com.xjzb.rts.core.Game.Ent e : game.ents) {
            if (!e.alive()) continue;
            if (e.team == 0) { if (e.isBuilding()) pb++; else pc++; }
            else { if (e.isBuilding()) eb++; else ec++; }
        }
        System.out.println("after 180s: player units=" + pc + " bldg=" + pb
                + " | enemy units=" + ec + " bldg=" + eb
                + " | minerals=" + game.mineralsPlayer + " status=" + game.status);
        System.out.println("supply=" + game.supplyUsed + "/" + game.supplyCap);

        // siege tank: exercise the morph that used to NPE
        com.xjzb.rts.core.Game.Ent tank = game.spawn("tank", 0, 300, 300, true);
        boolean ok = game.toggleSiege(tank);
        System.out.println("siege morph -> " + ok + " key=" + tank.type.key);
        render("frame_siege.png");

        // ---- batch-1: order markers, construction feedback, combat fx
        // The long run above is undefended, so the AI attack wave that the
        // repaired walk map finally lets path to the player base wipes the
        // starting SCVs (measured: alive through t=150, dead by t=170, all 13
        // attackers standing on walkable ground). The assertions below need a
        // worker, so respawn one rather than silently indexing an empty list.
        List<com.xjzb.rts.core.Game.Ent> scvs2 = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : game.ents)
            if (e.team == 0 && e.alive() && e.type.key.equals("scv")) scvs2.add(e);
        if (scvs2.isEmpty()) {
            com.xjzb.rts.core.Game.Ent fresh = game.spawn("scv", 0, starts.get(0)[0], starts.get(0)[1], true);
            if (fresh != null) scvs2.add(fresh);
            System.out.println("NOTE: no SCV survived the undefended 180s AI push; respawned one for the build test");
        }
        game.orderMove(scvs2, 400, 380, false);
        for (int i = 0; i < 3; i++) game.update(1f / 30f);
        camX = 400;
        camY = 380;
        render("frame_markers.png");
        System.out.println("markers after move order: " + game.markers.size());

        com.xjzb.rts.core.Game.Ent scvB = scvs2.get(0);
        game.tryBuild(scvB, "barracks", 430, 300);
        for (int i = 0; i < 20; i++) game.update(1f / 30f);
        camX = 430;
        camY = 300;
        render("frame_construction.png");

        com.xjzb.rts.core.Game.Ent m2 = game.spawn("marine", 0, 330, 300, true);
        com.xjzb.rts.core.Game.Ent z3 = game.spawn("zergling", 1, 342, 300, true);
        m2.cd = 0;
        for (int i = 0; i < 4; i++) game.update(1f / 30f);
        camX = 336;
        camY = 300;
        render("frame_fx.png");

        renderDirs("frame_dirs.png");
        renderSheet("bang_m", "frame_bang.png");
        renderSheet("death_marine", "frame_death_marine.png");
        renderSheet("stank", "frame_stank.png");
        renderSheet("flsh_s", "frame_flsh_s.png");
        renderSheet("smoke", "frame_smoke.png");
        renderSheet("hit", "frame_hit.png");

        // ---- v2.5 batch-6: patrol loop + SCV repair
        // NOTE: spawn on walkable ground -- the map centre of bloodbath is
        // inside a wall, and a unit boxed in can never demonstrate a patrol.
        // v2.44: skip tiles a BUILDING covers too (passMini is terrain-only),
        // and build a FRESH game: the 180s AI run above ends in 'lose' on an
        // undefended base, and update() is a no-op once status is set, so the
        // patrol marine never took a single step and the assertion reported an
        // engine freeze that does not exist (protossFrame needed the same).
        readMapById(mapId);
        com.xjzb.rts.core.Game.Ent pat = null;
        outer:
        for (int ty = 4; ty < game.hTiles - 4; ty++) {
            for (int tx = 4; tx < game.wTiles - 4; tx++) {
                float wx = tx * 32f + 16, wy = ty * 32f + 16;
                if (!game.passMini((int) (wx / 8), (int) (wy / 8))) continue;
                if (!game.passMini((int) ((wx + 150) / 8), (int) (wy / 8))) continue;
                if (!spotClear(wx, wy) || !spotClear(wx + 150, wy)) continue;
                pat = game.spawn("marine", 0, wx, wy, true);
                if (pat != null) break outer;
            }
        }
        if (pat != null) {
            List<com.xjzb.rts.core.Game.Ent> patSel = new ArrayList<>();
            patSel.add(pat);
            float startX = pat.x, startY = pat.y;
            game.orderPatrol(patSel, startX + 150, startY);
            System.out.println("patrol ordered -> patrolling=" + pat.patrolling
                    + " A=(" + (int) pat.patrolAX + "," + (int) pat.patrolAY + ")"
                    + " B=(" + (int) pat.patrolBX + "," + (int) pat.patrolBY + ")");
            float minX = pat.x, maxX = pat.x;
            int reversals = 0;
            float prevDir = 0;
            for (int i = 0; i < 60 * 20; i++) {
                game.update(1f / 30f);
                float dir = Math.signum(pat.goalX - pat.x);
                if (prevDir != 0 && dir != 0 && dir != prevDir) reversals++;
                prevDir = dir;
                minX = Math.min(minX, pat.x);
                maxX = Math.max(maxX, pat.x);
            }
            System.out.println("patrol after 20s -> still=" + pat.patrolling
                    + " xRange=" + (int) minX + ".." + (int) maxX
                    + " reversals=" + reversals
                    + " PASS=" + (pat.patrolling && reversals >= 3));
        }

        // repair: damage a building, send an SCV, confirm hp climbs + minerals fall
        com.xjzb.rts.core.Game.Ent ccB = null;
        for (com.xjzb.rts.core.Game.Ent e : game.ents)
            if (e.team == 0 && e.isBuilding() && e.type.key.equals("cc")) { ccB = e; break; }
        if (ccB == null) {
            ccB = game.spawn("cc", 0, 260, 360, true);
        }
        ccB.hp = Math.max(1, ccB.type.hp / 3);
        List<com.xjzb.rts.core.Game.Ent> rScv = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : game.ents)
            if (e.team == 0 && e.type.key.equals("scv")) { rScv.add(e); break; }
        if (!rScv.isEmpty() && game.orderRepair(rScv, ccB)) {
            int hp0 = ccB.hp, min0 = game.mineralsPlayer;
            for (int i = 0; i < 60 * 6; i++) game.update(1f / 30f);
            System.out.println("repair 6s -> hp " + hp0 + "->" + ccB.hp
                    + "/" + ccB.type.hp + "  minerals " + min0 + "->" + game.mineralsPlayer
                    + "  healed=" + (ccB.hp > hp0) + "  paid=" + (game.mineralsPlayer < min0));
        } else {
            System.out.println("repair: no SCV or order refused (err="
                    + game.repairError(ccB) + ")");
        }
        // ---- control groups: the 450 ms long-press decision now lives in the
        // core, so both branches are testable without a touch screen
        // Top the group up to three workers: this asserts group semantics, and
        // the undefended AI push above leaves an arbitrary number of SCVs
        // alive, which would otherwise decide whether "recall after 1 death"
        // is even a meaningful branch (with a single member the group empties
        // and correctly reports GROUP_EMPTY instead of GROUP_RECALLED).
        System.out.println("[groups]");
        List<com.xjzb.rts.core.Game.Ent> gsel = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : game.ents)
            if (e.team == 0 && e.alive() && e.type.key.equals("scv")) gsel.add(e);
        for (int i = gsel.size(); i < 3; i++) {
            com.xjzb.rts.core.Game.Ent extra =
                    game.spawn("scv", 0, starts.get(0)[0] + 20 * i, starts.get(0)[1] + 20, true);
            if (extra != null) gsel.add(extra);
        }
        for (com.xjzb.rts.core.Game.Ent e : game.ents) e.selected = false;
        for (int i = 0; i < Math.min(3, gsel.size()); i++) gsel.get(i).selected = true;

        int r0 = game.groupTap(0, true);          // long press -> assign
        System.out.println("  assign -> res=" + r0
                + " size=" + game.groups.get(0).size()
                + " PASS=" + (r0 == com.xjzb.rts.core.Game.GROUP_ASSIGNED
                              && game.groups.get(0).size() == Math.min(3, gsel.size())));

        for (com.xjzb.rts.core.Game.Ent e : game.ents) e.selected = false;
        int r1 = game.groupTap(0, false);         // tap -> recall
        int recalled = 0;
        for (com.xjzb.rts.core.Game.Ent e : game.ents) if (e.selected) recalled++;
        System.out.println("  recall -> res=" + r1 + " selected=" + recalled
                + " PASS=" + (r1 == com.xjzb.rts.core.Game.GROUP_RECALLED
                              && recalled == Math.min(3, gsel.size())));

        game.groups.get(0).get(0).hp = 0;         // dead member must be dropped
        for (int i = 0; i < 2; i++) game.update(1f / 30f);
        int r2 = game.groupTap(0, false);
        int alive2 = 0;
        for (com.xjzb.rts.core.Game.Ent e : game.ents) if (e.selected) alive2++;
        System.out.println("  recall after 1 death -> res=" + r2
                + " selected=" + alive2
                + " PASS=" + (r2 == com.xjzb.rts.core.Game.GROUP_RECALLED
                              && alive2 == Math.min(3, gsel.size()) - 1));

        for (com.xjzb.rts.core.Game.Ent e : game.ents) e.selected = false;
        int r3 = game.groupTap(2, false);         // untouched slot
        System.out.println("  empty slot -> res=" + r3 + " PASS="
                + (r3 == com.xjzb.rts.core.Game.GROUP_EMPTY));

        // ---- save / load round-trip
        System.out.println("[saveload]");
        game.mineralsPlayer = 777;
        game.gasPlayer = 33;
        String save = game.serialize();
        int entsBefore = 0;
        for (com.xjzb.rts.core.Game.Ent e : game.ents) if (e.alive()) entsBefore++;
        int fog1 = game.fog[10 * game.wTiles + 10];

        com.xjzb.rts.core.Game restored = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units);
        boolean restoredOk = restored.deserialize(save);
        int entsAfter = 0;
        for (com.xjzb.rts.core.Game.Ent e : restored.ents) if (e.alive()) entsAfter++;
        // walkability must be restored bit-identical (footprints + terrain)
        boolean walkSame = java.util.Arrays.equals(restored.walk, game.walk);
        boolean fogSame = java.util.Arrays.equals(restored.fog, game.fog);
        System.out.println("  deserialize=" + restoredOk
                + " ents " + entsBefore + "->" + entsAfter
                + " minerals=" + restored.mineralsPlayer + "/" + restored.gasPlayer
                + " walkSame=" + walkSame + " fogSame=" + fogSame
                + " time=" + String.format("%.1f", restored.time)
                + " PASS=" + (restoredOk && entsBefore == entsAfter
                              && restored.mineralsPlayer == 777 && restored.gasPlayer == 33
                              && walkSame && fogSame));
        // the restored instance must keep simulating (walk/buildings intact)
        for (int i = 0; i < 30; i++) restored.update(1f / 30f);
        int alive3 = 0;
        for (com.xjzb.rts.core.Game.Ent e : restored.ents) if (e.alive()) alive3++;
        System.out.println("  after 1s sim: alive=" + alive3 + " status='"
                + restored.status + "' PASS=" + (alive3 >= entsAfter - 2));

        // ---- v2.7 batch 8: mission engine regression.
        // Four assertions from the plan: m1 times out into a loss, m2 wipes the
        // enemy into a win, a protect objective fails when its target dies, and
        // a timed wave actually spawns its units at the scripted moment.
        // ---- v2.7 batch 9: combat depth regression (armor, stim, upgrades)
        System.out.println("[combat]");
        combatTests();

        // ---- v2.8: playable zerg + the two gated terran units
        System.out.println("[races]");
        raceTests();

        System.out.println("[missions]");
        missionTest1();
        missionTest2();
        missionTest3();
        missionTest4();
        missionTest5();

        // ---- v2.10 batch A: a protoss frame, so the new sheets (zealot walk
        // rows, dragoon, the psistorm effect drawn straight from its sheet) are
        // exercised by the renderer and not only by the assertions.
        protossFrame();

        // ---- v2.14 batch 1.5: all six spell effects drawn mid-animation, so
        // the new sheets are exercised by the renderer, not only by the
        // manifest assertions.
        spellFrame();

        // ---- v2.13 batch D: the DD2 data layer ships in meta.txt, and river
        // (96x256, the old missing 10th map) must load now that the 128-dim
        // cap is gone.
        mapDataTests();
        memoryTests();

        // ---- v2.14 batch 1: combat depth. Damage types against unit sizes,
        // splash falloff, the hold order, the five caster spells, and the four
        // skirmish-AI behaviours.
        System.out.println("[v214]");
        depthTests();

        System.out.println("[v217]");
        pickTests();
        cameraTests();
        buildTests();

        System.out.println("[v218]");
        fogTests();
        scaleTests();

        System.out.println("[v219]");
        layoutTests();

        System.out.println("[v220]");
        layoutCustomTests();
        replayTests();

        System.out.println("[v221]");
        v221Tests();

        System.out.println("[v222]");
        v222Tests();

        System.out.println("[v223]");
        v223Tests();

        System.out.println("[v224]");
        v224Tests();

        System.out.println("[v225]");
        v225Tests();

        System.out.println("[v226]");
        v226Tests();

        System.out.println("[v227]");
        v227Tests();

        System.out.println("[v228]");
        v228Tests();

        System.out.println("[v229]");
        v229Tests();

        System.out.println("[v230]");
        v230Tests();

        System.out.println("[v231]");
        v231Tests();

        System.out.println("[v232]");
        v232Tests();

        System.out.println("[v233]");
        v233Tests();

        System.out.println("[v234]");
        v234Tests();

        System.out.println("[v236]");
        v236Tests();

        System.out.println("[v237]");
        v237Tests();

        System.out.println("[v238]");
        v238Tests();

        System.out.println("[v239]");
        v239Tests();

        System.out.println("[v240]");
        v240Tests();

        System.out.println("[v241]");
        v241Tests();

        System.out.println("[v242]");
        v242Tests();

        System.out.println("[v243]");
        v243Tests();

        System.out.println("[v244]");
        v244Tests();

        System.out.println("desktop render done");
    }

    // ------------------------------------------------------------------ bench
    //
    // v2.43 section 2: the frame-time baseline the plan's step 0 asks for.
    //
    // The plan wanted "divide, single player, fastest, 100/200/400 units" and a
    // before/after table. The `after` half is measured here on the shipped
    // v2.43 build. The `before` half cannot be measured on this build -- the
    // O(N^2) loops it removed no longer exist -- so it is produced by a
    // separate run against a reverted copy of core/ (see tools/bench_before.ps1)
    // and both halves land in the same table in the handover doc.
    //
    // Two phases per roster size, because the plan names two distinct failure
    // modes and one number would hide the other:
    //   idle        -- every unit standing still. Exercises the per-tick scans:
    //                  separation, building collision, cloak/detector, the
    //                  idle-acquire sweep, fog reveal.
    //   attack-move -- the whole roster ordered to one distant point in a single
    //                  call. This is the shape of the AI wave spike (B class):
    //                  one A* per unit in the issuing tick.
    //
    // Render is timed too, into a reused image with the PNG write skipped, so
    // the number is drawing cost rather than ImageIO cost.

    /** Fixed roster sizes the plan calls out. */
    static final int[] BENCH_SIZES = {100, 200, 400};
    static final int BENCH_WARM = 120;
    static final int BENCH_TICKS = 300;

    static void bench() {
        viewW = 2608;
        viewH = 1200;
        benchNoWrite = true;
        benchImg = new BufferedImage(viewW, viewH, BufferedImage.TYPE_INT_RGB);

        System.out.println("[bench] map=" + mapId + " view=" + viewW + "x" + viewH
                + " warm=" + BENCH_WARM + " ticks=" + BENCH_TICKS);
        System.out.println("[bench] columns are milliseconds per tick");
        System.out.println("  n  phase        upd_avg upd_p95 upd_max ren_avg ren_p95 ren_max"
                + "  ents  auraQ  auraS  acqQ  acqS  gridQ  gridC  pathQ  pathD  hash");
        for (int si = 0; si < BENCH_SIZES.length; si++) {
            int n = BENCH_SIZES[si];
            benchRoster(n, false);
            benchRoster(n, true);
        }
        System.out.println("[bench] done");
    }

    /**
     * One roster size, one phase. `attackMove` selects the phase.
     *
     * The roster is placed on walkable tiles sampled every second tile, so the
     * units stand on ground the pathfinder agrees with -- a roster dropped onto
     * walls would measure the collision-resolution path instead of the scans.
     */
    static void benchRoster(int n, boolean attackMove) {
        com.xjzb.rts.core.Game g = cleanGame("terran");
        List<com.xjzb.rts.core.Game.Ent> sel = new ArrayList<>();
        float sx = 0, sy = 0;
        outer:
        for (int ty = 2; ty < g.hTiles - 2; ty += 2)
            for (int tx = 2; tx < g.wTiles - 2; tx += 2) {
                float wx = tx * 32f + 16, wy = ty * 32f + 16;
                if (!g.passMini((int) (wx / 8), (int) (wy / 8))) continue;
                com.xjzb.rts.core.Game.Ent e = g.spawn("marine", 0, wx, wy, true);
                if (e == null) continue;
                sel.add(e);
                sx += wx;
                sy += wy;
                if (sel.size() >= n) break outer;
            }
        if (sel.isEmpty()) {
            System.out.println("  n=" + n + " FAILED: no walkable ground for a roster");
            return;
        }
        camX = sx / sel.size();
        camY = sy / sel.size();
        // render() draws the harness's `game` field, not this local.
        game = g;

        // Warm both halves: the JIT compiles the update path and the Java2D
        // pipeline lazily, and the very first drawn frame costs ~800ms on its
        // own -- including it would swamp every percentile below.
        for (int i = 0; i < BENCH_WARM; i++) g.update(1f / 30f);
        for (int i = 0; i < BENCH_WARM; i++) {
            try {
                render("bench_frame.png");
            } catch (Exception ex) {
                System.out.println("  warm render failed: " + ex);
                break;
            }
        }

        // The counters are cumulative, so the phase's cost is the delta.
        int aq0 = g.statAuraQueries, as0 = g.statAuraScans;
        int cq0 = g.statAcquireQueries, cs0 = g.statAcquireScans;
        int gq0 = g.statGridQueries, gc0 = g.statGridCandidates;
        int pq0 = g.statPathQueued, pd0 = g.statPathDrains;

        if (attackMove) {
            // One order to the whole roster: the AI-wave spike in miniature.
            g.orderMove(sel, g.wPx - 200, g.hPx - 200, true);
        }

        float[] upd = new float[BENCH_TICKS];
        float[] ren = new float[BENCH_TICKS];
        long hash = 0;
        for (int i = 0; i < BENCH_TICKS; i++) {
            long t0 = System.nanoTime();
            g.update(1f / 30f);
            long t1 = System.nanoTime();
            try {
                render("bench_frame.png");
            } catch (Exception ex) {
                System.out.println("  render failed: " + ex);
                break;
            }
            long t2 = System.nanoTime();
            upd[i] = (t1 - t0) / 1000000f;
            ren[i] = (t2 - t1) / 1000000f;
        }
        hash = g.stateHash();

        int alive = 0;
        for (int i = 0; i < g.ents.size(); i++) if (g.ents.get(i).alive()) alive++;

        System.out.println(String.format(
                "  %3d  %-11s %7s %7s %7s %7s %7s %7s  %4d %6d %6d %5d %5d %6d %6d %6d %6d  %d",
                n, attackMove ? "attack-move" : "idle",
                ms(avg(upd)), ms(p95(upd)), ms(max(upd)),
                ms(avg(ren)), ms(p95(ren)), ms(max(ren)),
                alive,
                g.statAuraQueries - aq0, g.statAuraScans - as0,
                g.statAcquireQueries - cq0, g.statAcquireScans - cs0,
                g.statGridQueries - gq0, g.statGridCandidates - gc0,
                g.statPathQueued - pq0, g.statPathDrains - pd0,
                hash));
    }

    static String ms(float v) {
        return String.format("%.3f", v);
    }

    static float avg(float[] a) {
        float s = 0;
        for (int i = 0; i < a.length; i++) s += a[i];
        return a.length == 0 ? 0 : s / a.length;
    }

    static float max(float[] a) {
        float m = 0;
        for (int i = 0; i < a.length; i++) if (a[i] > m) m = a[i];
        return m;
    }

    /** 95th percentile, nearest-rank, on a sorted copy. */
    static float p95(float[] a) {
        if (a.length == 0) return 0;
        float[] c = new float[a.length];
        System.arraycopy(a, 0, c, 0, a.length);
        java.util.Arrays.sort(c);
        int i = (int) Math.ceil(0.95 * c.length) - 1;
        return c[Math.max(0, Math.min(c.length - 1, i))];
    }

    /**
     * v2.22: the energy pool (batch A) and the cloak layer (batch B).
     * [energy]: spawn at 50, regen per second, price deduction, refusal
     * without spending the cooldown, medic heals free. [cloak]: permanent
     * types are hidden and untargetable until a detector comes, the ghost's
     * toggle costs and drains, the arbiter's aura covers friends, the
     * burrowed lurker hides entirely, and none of it changes friendly fire.
     */
    static void v222Tests() {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- A: spawn levels and regen ------------------------------------
        com.xjzb.rts.core.Game eg = cleanGame("protoss");
        com.xjzb.rts.core.Game.Ent tpl = eg.spawn("templar", 0, 500, 500, true);
        boolean spawnLv = tpl.maxEnergy == 200f && Math.abs(tpl.energy - 50f) < 0.01f;
        com.xjzb.rts.core.Game.Ent m = eg.spawn("marine", 0, 560, 500, true);
        boolean noPool = m.maxEnergy == 0f && m.energy == 0f;
        for (int i = 0; i < 30; i++) eg.update(1 / 30f);   // 1s
        boolean regen = tpl.energy > 50.5f && tpl.energy < 51.5f;
        ok &= spawnLv && noPool && regen;
        sb.append(" spawn=").append(spawnLv).append(" noPool=").append(noPool)
                .append(" regen=").append(regen);

        // ---- A: price paid, refusal leaves the cooldown untouched ---------
        tpl.energy = 100f;
        boolean cast = eg.castStorm(tpl, 500, 500);
        boolean paid = cast && tpl.energy == 25f;
        ok &= paid;
        sb.append(" paid=").append(paid);
        com.xjzb.rts.core.Game.Ent tplB = eg.spawn("templar", 0, 700, 500, true);
        tplB.energy = 50f;
        String poor = eg.stormError(tplB);
        boolean refuse = poor != null && poor.contains("能量")
                && tplB.stormCd == 0f && !eg.castStorm(tplB, 500, 500);
        ok &= refuse;
        sb.append(" refuse=").append(refuse);

        // ---- A: the medic heals without a pool -----------------------------
        com.xjzb.rts.core.Game mh = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent medic = mh.spawn("medic", 0, 500, 500, true);
        com.xjzb.rts.core.Game.Ent hurt = mh.spawn("marine", 0, 520, 500, true);
        hurt.hp = 10;
        List<com.xjzb.rts.core.Game.Ent> one = new ArrayList<>();
        one.add(medic);
        mh.orderHeal(one, hurt);
        for (int i = 0; i < 45; i++) mh.update(1 / 30f);   // 1.5s of channel
        boolean healFree = hurt.hp > 10 && medic.maxEnergy == 0f;
        ok &= healFree;
        sb.append(" healFree=").append(healFree);

        // ---- B: permanent cloak hides and protects -------------------------
        com.xjzb.rts.core.Game ck = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent marine = ck.spawn("marine", 0, 500, 500, true);
        com.xjzb.rts.core.Game.Ent dt = ck.spawn("dtemplar", 1, 540, 500, true);
        ck.update(1 / 30f);   // settle the cloak layer
        boolean hidden = dt.cloakActive && !dt.spotted
                && ck.findEnemyInRange(marine, 400) == null;
        com.xjzb.rts.core.Game.Ent turret = ck.spawn("turret", 0, 560, 560, true);
        ck.update(1 / 30f);
        boolean revealed = dt.spotted && ck.findEnemyInRange(marine, 400) == dt;
        ok &= hidden && revealed;
        sb.append(" hidden=").append(hidden).append(" revealed=").append(revealed);

        // ---- B: the ghost toggle costs 25 and drains out -------------------
        com.xjzb.rts.core.Game gh = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent ghost = gh.spawn("ghost", 0, 500, 500, true);
        fullEnergy(ghost);
        gh.update(1 / 30f);
        boolean tOn = gh.toggleCloak(ghost) && ghost.cloakOn
                && Math.abs(ghost.energy - (Game.ENERGY_MAX - Game.CLOAK_COST)) < 0.01f;
        gh.update(1 / 30f);   // the layer settles on the next tick
        boolean active = ghost.cloakActive;
        boolean tOff = gh.toggleCloak(ghost) && !ghost.cloakOn;
        gh.update(1 / 30f);   // the layer drops on the next tick
        tOff &= !ghost.cloakActive;
        ghost.energy = 10f;
        boolean broke = gh.cloakError(ghost) != null && !gh.toggleCloak(ghost);
        // broke means the toggle was refused at 10 energy -- force the state
        // the way an already-cloaked ghost would be, then let the drain end it
        ghost.cloakOn = true;
        ghost.energy = 1.5f;
        for (int i = 0; i < 60; i++) gh.update(1 / 30f);   // 2s: drain 2 > 1.5
        // the decloak is instant; regen resumes the same tick, so the pool is
        // asserted "still nearly empty" rather than exactly zero
        boolean drained = !ghost.cloakOn && ghost.energy < 1f;
        ok &= tOn && active && tOff && broke && drained;
        sb.append(" toggle=").append(tOn).append("/").append(active)
                .append(" broke=").append(broke).append(" drained=").append(drained);

        // ---- B: the arbiter's aura cloaks friends, not itself --------------
        com.xjzb.rts.core.Game ar = cleanGame("protoss");
        com.xjzb.rts.core.Game.Ent arb = ar.spawn("arbiter", 0, 500, 500, true);
        com.xjzb.rts.core.Game.Ent zealot = ar.spawn("zealot", 0, 560, 560, true);
        com.xjzb.rts.core.Game.Ent far = ar.spawn("zealot", 0, 1500, 1500, true);
        ar.update(1 / 30f);
        boolean aura = !arb.cloakActive && zealot.cloakActive && !far.cloakActive;
        ok &= aura;
        sb.append(" aura=").append(aura);

        // ---- B: the burrowed lurker hides entirely; a detector unpicks it --
        com.xjzb.rts.core.Game lk = cleanGame("zerg");
        float lx = mapW * 16f, ly = mapH * 16f;   // map centre: no friendly detector
        com.xjzb.rts.core.Game.Ent lurk = lk.spawn("lurker", 1, lx, ly, true);
        com.xjzb.rts.core.Game.Ent shooter = lk.spawn("marine", 0, lx + 40, ly + 20, true);
        lk.toggleSiege(lurk);
        lk.update(1 / 30f);
        boolean buried = Game.isBurrowed(lurk) && lurk.cloakActive && !lurk.spotted
                && lk.findEnemyInRange(shooter, 400) == null;
        com.xjzb.rts.core.Game.Ent spore = lk.spawn("spore", 1, 520, 560, true);
        lk.update(1 / 30f);
        // the spore is the LURKER's own side, so it must NOT reveal the marine
        boolean ownSide = shooter.cloakActive == false;
        com.xjzb.rts.core.Game lk2 = cleanGame("zerg");
        com.xjzb.rts.core.Game.Ent lurk2 = lk2.spawn("lurker", 1, lx, ly, true);
        com.xjzb.rts.core.Game.Ent shooter2 = lk2.spawn("marine", 0, lx + 40, ly + 20, true);
        com.xjzb.rts.core.Game.Ent t2 = lk2.spawn("turret", 0, lx + 60, ly + 60, true);
        lk2.toggleSiege(lurk2);
        lk2.update(1 / 30f);
        boolean spotted = lurk2.spotted
                && lk2.findEnemyInRange(shooter2, 400) == lurk2;
        ok &= buried && ownSide && spotted;
        sb.append(" buried=").append(buried).append(" ownSide=").append(ownSide)
                .append(" spotted=").append(spotted);

        System.out.println("  energy pool + cloak/detect" + sb + " PASS=" + ok);
    }


    /**
     * v2.23: batch A (transport cargo), batch B (bunker + goliath dual weapon)
     * and batch C (the high-ground miss).
     *
     * [A] loading takes a unit off the field -- untargetable, invisible to the
     * fog, unpickable -- while it keeps costing its supply, capacity is
     * measured in supply slots (8 marines or 4 tanks, not 8 units), unloading
     * puts it back, the drop spreads a full hold over free ground, and a dead
     * carrier kills everyone aboard. [B] a bunker holds 4 infantry slots and
     * its garrison fires from the bunker own position; losing the bunker loses
     * the garrison; the goliath hits air and ground on two different axes.
     * [C] the elevation bitmap agrees with the shipped elev.bin, an uphill
     * ranged shot lands 50-56% of the time, a downhill shot never misses, and
     * melee ignores elevation entirely.
     */
    static void v223Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ================= batch A: transport cargo ========================

        // ---- load takes the unit off the field ---------------------------
        com.xjzb.rts.core.Game lg = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent shuttle = lg.spawn("shuttle", 0, 600, 600, true);
        // The marine sits 300 px away, outside LOAD_RANGE, so the per-tick
        // auto-load sweep cannot board it before the explicit call -- the
        // sweep is exercised by the spread test below, and mixing the two
        // here would only test updateLoading twice.
        com.xjzb.rts.core.Game.Ent m1 = lg.spawn("marine", 0, 900, 600, true);
        lg.update(1 / 30f);              // settle supplyUsed before sampling
        int supBefore = lg.supplyUsed;
        boolean loaded = lg.loadUnit(shuttle, m1);
        lg.update(1 / 30f);
        boolean offField = m1.cargoOf == shuttle && shuttle.cargo.size() == 1;
        // the marine sits closer to the enemy than the shuttle, so if the
        // off-field gate failed this search would return it
        com.xjzb.rts.core.Game.Ent foe = lg.spawn("zergling", 1, 950, 600, true);
        boolean hidden = true;
        for (int i = 0; i < 5; i++)
            if (lg.findEnemyInRange(foe, 400) == m1) hidden = false;
        boolean supKept = lg.supplyUsed == supBefore;
        ok &= loaded && offField && hidden && supKept;
        sb.append(" load=").append(loaded).append(" offField=").append(offField)
          .append(" untargetable=").append(hidden).append(" supKept=").append(supKept);

        // ---- unload puts it back on the field ----------------------------
        boolean un = lg.unloadAll(shuttle, 900, 600);
        lg.update(1 / 30f);
        boolean back = un && m1.cargoOf == null && shuttle.cargo.isEmpty()
                && m1.alive();
        ok &= back;
        sb.append(" unload=").append(back);

        // ---- capacity is 8 SUPPLY SLOTS, not 8 units ----------------------
        com.xjzb.rts.core.Game cg = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent sh2 = cg.spawn("shuttle", 0, 600, 600, true);
        int marinesIn = 0;
        for (int i = 0; i < 9; i++) {
            com.xjzb.rts.core.Game.Ent mm = cg.spawn("marine", 0, 620 + i * 4, 600, true);
            if (mm != null && cg.loadUnit(sh2, mm)) marinesIn++;
        }
        com.xjzb.rts.core.Game.Ent extra = cg.spawn("marine", 0, 700, 600, true);
        boolean nineRefused = cg.loadError(sh2, extra) != null;
        com.xjzb.rts.core.Game cg2 = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent sh3 = cg2.spawn("shuttle", 0, 600, 600, true);
        int tanksIn = 0;
        for (int i = 0; i < 5; i++) {
            com.xjzb.rts.core.Game.Ent tk = cg2.spawn("tank", 0, 620 + i * 8, 600, true);
            if (tk != null && cg2.loadUnit(sh3, tk)) tanksIn++;
        }
        boolean cap = marinesIn == 8 && nineRefused && tanksIn == 4
                && cg2.cargoUsed(sh3) == 8;
        ok &= cap;
        sb.append(" cap8=").append(cap).append("(m=").append(marinesIn)
          .append(",t=").append(tanksIn).append(")");

        // ---- the load ORDER walks the transport over and collects it ------
        // (the path the command card actually uses: orderLoad sets the
        // target, updateLoading boards it once it is close enough)
        com.xjzb.rts.core.Game og = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent hauler = og.spawn("shuttle", 0, 600, 600, true);
        com.xjzb.rts.core.Game.Ent walker = og.spawn("marine", 0, 760, 600, true);
        boolean ordered = og.orderLoad(
                java.util.Collections.singletonList(hauler), walker);
        og.orderMove(java.util.Collections.singletonList(hauler), walker.x, walker.y, false);
        for (int i = 0; i < 300; i++) og.update(1 / 30f);
        boolean collected = walker.cargoOf == hauler && hauler.cargo.contains(walker)
                && hauler.loadTarget == null;
        ok &= ordered && collected;
        sb.append(" orderLoad=").append(ordered && collected);

        // ---- an idle transport hoovers up nothing on its own -------------
        // The overlord is a transport too; a free sweep would have it eating
        // the player base.
        com.xjzb.rts.core.Game hg = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent idle = hg.spawn("shuttle", 0, 600, 600, true);
        com.xjzb.rts.core.Game.Ent near = hg.spawn("marine", 0, 620, 600, true);
        for (int i = 0; i < 60; i++) hg.update(1 / 30f);
        boolean idleSafe = near.cargoOf == null && idle.cargo.isEmpty();
        ok &= idleSafe;
        sb.append(" idleSafe=").append(idleSafe);

        // ---- a full hold spreads out over free ground ---------------------
        com.xjzb.rts.core.Game ug = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent sh4 = ug.spawn("shuttle", 0, 600, 600, true);
        for (int i = 0; i < 4; i++)
            ug.loadUnit(sh4, ug.spawn("marine", 0, 604 + i * 3, 600, true));
        boolean spread = ug.unloadAll(sh4, 600, 600);
        java.util.HashSet<String> spots = new java.util.HashSet<>();
        for (com.xjzb.rts.core.Game.Ent e : ug.ents)
            if (e.type.key.equals("marine") && e.team == 0 && e.cargoOf == null
                    && Math.abs(e.x - 600) < 500)
                spots.add((int) e.x + "," + (int) e.y);
        boolean spreadOk = spread && spots.size() == 4;
        boolean emptyRefused = !ug.unloadAll(sh4, 600, 600);
        ok &= spreadOk && emptyRefused;
        sb.append(" spread=").append(spreadOk).append(" emptyRefused=")
          .append(emptyRefused);

        // ---- a dead transport kills everyone aboard -----------------------
        com.xjzb.rts.core.Game dg = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent sh5 = dg.spawn("shuttle", 0, 600, 600, true);
        com.xjzb.rts.core.Game.Ent c1 = dg.spawn("marine", 0, 604, 600, true);
        com.xjzb.rts.core.Game.Ent c2 = dg.spawn("marine", 0, 608, 600, true);
        dg.loadUnit(sh5, c1);
        dg.loadUnit(sh5, c2);
        dg.update(1 / 30f);
        sh5.hp = 0;
        dg.update(1 / 30f);
        dg.update(1 / 30f);
        boolean doomed = !c1.alive() && !c2.alive()
                && !dg.ents.contains(c1) && !dg.ents.contains(c2);
        ok &= doomed;
        sb.append(" escort=").append(doomed);

        // ---- save/load round-trips a loaded hold --------------------------
        com.xjzb.rts.core.Game sg = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent sh6 = sg.spawn("shuttle", 0, 600, 600, true);
        com.xjzb.rts.core.Game.Ent s1 = sg.spawn("marine", 0, 604, 600, true);
        sg.loadUnit(sh6, s1);
        sg.update(1 / 30f);
        String blob = sg.serialize();
        com.xjzb.rts.core.Game sg2 = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, elev, starts, units, "terran");
        boolean rt = sg2.deserialize(blob);
        boolean rtOk = false;
        if (rt) {
            com.xjzb.rts.core.Game.Ent car = null, cgo = null;
            for (com.xjzb.rts.core.Game.Ent e : sg2.ents) {
                if (e.type.key.equals("shuttle") && e.team == 0) car = e;
                if (e.type.key.equals("marine") && e.cargoOf != null) cgo = e;
            }
            rtOk = car != null && cgo != null && cgo.cargoOf == car
                    && car.cargo.contains(cgo);
        }
        ok &= rtOk;
        sb.append(" saveRT=").append(rtOk);

        // ---- the island flag round-trips through index.txt ----------------
        java.util.List<String> idx = Files.readAllLines(
                Paths.get(ASSETS + "/maps/index.txt"));
        boolean sawIsland = false, sawNormal = false, flagOk = true;
        for (String line : idx) {
            String[] p = line.split("\\|");
            if (p.length < 6) continue;
            String meta = new String(Files.readAllBytes(
                    Paths.get(ASSETS + "/maps/" + p[0] + "/meta.txt")),
                    java.nio.charset.StandardCharsets.UTF_8);
            boolean metaIsland = meta.contains("island=1");
            boolean metaElev = meta.contains("elev=1");
            if (!metaElev) flagOk = false;
            if ("1".equals(p[5].trim())) {
                sawIsland = true;
                if (!metaIsland) flagOk = false;
            } else {
                sawNormal = true;
                if (metaIsland) flagOk = false;
            }
        }
        boolean islandOk = sawIsland && sawNormal && flagOk;
        ok &= islandOk;
        sb.append(" island=").append(islandOk);

        // ================= batch B: bunker + goliath =======================

        // ---- the goliath carries two weapon axes --------------------------
        com.xjzb.rts.core.Game gg = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent gol = gg.spawn("goliath", 0, 600, 600, true);
        com.xjzb.rts.core.Game.Ent ground = gg.spawn("zergling", 1, 640, 600, true);
        com.xjzb.rts.core.Game.Ent air = gg.spawn("muta", 1, 640, 560, true);
        boolean axes = com.xjzb.rts.core.Game.TYPES.get("goliath").dmg == 12
                && com.xjzb.rts.core.Game.TYPES.get("goliath").dmgAir == 20
                && gg.damageOf(gol, ground) == 12
                && gg.damageOf(gol, air) == 20
                // every other row still uses its single axis
                && gg.damageOf(gg.spawn("marine", 0, 620, 600, true), air) == 6;
        ok &= axes;
        sb.append(" goliathAxes=").append(axes);

        // ---- the bunker holds 4 infantry slots, 2 firebats ---------------
        com.xjzb.rts.core.Game bg = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent bunk = bg.spawn("bunker", 0, 600, 600, true);
        int gIn = 0;
        for (int i = 0; i < 5; i++) {
            com.xjzb.rts.core.Game.Ent mm = bg.spawn("marine", 0, 610 + i * 3, 600, true);
            if (mm != null && bg.garrisonUnit(bunk, mm)) gIn++;
        }
        com.xjzb.rts.core.Game.Ent gExtra = bg.spawn("marine", 0, 660, 600, true);
        boolean gRefused = bg.garrisonError(bunk, gExtra) != null;
        com.xjzb.rts.core.Game bg2 = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent bunk2 = bg2.spawn("bunker", 0, 600, 600, true);
        int fbIn = 0;
        for (int i = 0; i < 3; i++) {
            com.xjzb.rts.core.Game.Ent fb = bg2.spawn("firebat", 0, 610 + i * 3, 600, true);
            if (fb != null && bg2.garrisonUnit(bunk2, fb)) fbIn++;
        }
        boolean gCap = gIn == 4 && gRefused && fbIn == 2
                && bg2.garrisonUsed(bunk2) == 4;
        ok &= gCap;
        sb.append(" bunkerCap=").append(gCap).append("(m=").append(gIn)
          .append(",fb=").append(fbIn).append(")");

        // ---- a garrisoned unit fires from the bunker ----------------------
        com.xjzb.rts.core.Game fg = cleanGame("terran");
        // spawn() snaps a building onto the tile grid, so the victim and the
        // gun are placed RELATIVE to where the bunker actually landed rather
        // than to the requested point.
        com.xjzb.rts.core.Game.Ent bunk3 = fg.spawn("bunker", 0, 600, 600, true);
        // The marine is garrisoned from 300 px away, so its OWN position is
        // far out of range of the victim; only the "range measured from the
        // bunker" rule lets the shot happen at all.
        com.xjzb.rts.core.Game.Ent gun = fg.spawn("marine", 0, bunk3.x - 300,
                bunk3.y, true);
        fg.garrisonUnit(bunk3, gun);
        com.xjzb.rts.core.Game.Ent victim = fg.spawn("zergling", 1, bunk3.x + 80,
                bunk3.y, true);
        int vHp0 = victim.hp;
        boolean ownOut = fg.dist(gun, victim) > gun.type.range;
        boolean bunkIn = fg.dist(bunk3, victim) <= gun.type.range;
        for (int i = 0; i < 90; i++) fg.update(1 / 30f);
        boolean fires = ownOut && bunkIn && (victim.hp < vHp0 || !victim.alive());
        ok &= fires;
        sb.append(" bunkerFires=").append(fires);

        // ---- losing the bunker loses the garrison -------------------------
        com.xjzb.rts.core.Game kg = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent bunk4 = kg.spawn("bunker", 0, 600, 600, true);
        com.xjzb.rts.core.Game.Ent g1 = kg.spawn("marine", 0, 610, 600, true);
        com.xjzb.rts.core.Game.Ent g2 = kg.spawn("marine", 0, 614, 600, true);
        kg.garrisonUnit(bunk4, g1);
        kg.garrisonUnit(bunk4, g2);
        kg.update(1 / 30f);
        bunk4.hp = 0;
        kg.update(1 / 30f);
        kg.update(1 / 30f);
        boolean lost = !g1.alive() && !g2.alive()
                && !kg.ents.contains(g1) && !kg.ents.contains(g2);
        ok &= lost;
        sb.append(" bunkerLoss=").append(lost);

        // ================= batch C: the high-ground miss ===================

        // ---- the elevation bitmap agrees with the shipped elev.bin --------
        com.xjzb.rts.core.Game eg = cleanGame("terran");
        boolean haveElev = elev != null && elev.length == walk.length;
        boolean matches = true;
        if (haveElev) {
            for (int my = 0; my < eg.hMini; my += 7)
                for (int mx = 0; mx < eg.wMini; mx += 7) {
                    int want = elev[my * eg.wMini + mx];
                    int got = eg.elevLevel(mx * 8 + 4, my * 8 + 4);
                    if (want != got) matches = false;
                }
        }
        ok &= haveElev && matches;
        sb.append(" elevFile=").append(haveElev).append("/").append(matches);

        // ---- find an uphill pair on this map ------------------------------
        float[] lowPt = null, upPt = null;
        scan:
        for (int my = 1; my < eg.hMini - 1; my++)
            for (int mx = 1; mx < eg.wMini - 8; mx++) {
                if (!eg.passMini(mx, my) || eg.elevLevel(mx * 8 + 4, my * 8 + 4) != 0)
                    continue;
                for (int k = 1; k <= 8; k++) {
                    int nx = mx + k;
                    if (!eg.passMini(nx, my)) continue;
                    if (eg.elevLevel(nx * 8 + 4, my * 8 + 4) > 0) {
                        lowPt = new float[]{mx * 8 + 4, my * 8 + 4};
                        upPt = new float[]{nx * 8 + 4, my * 8 + 4};
                        break scan;
                    }
                }
            }
        boolean found = lowPt != null && upPt != null;
        ok &= found;
        sb.append(" uphillPair=").append(found);

        if (found) {
            com.xjzb.rts.core.Game.Ent lowGun = eg.spawn("marine", 0, lowPt[0], lowPt[1], true);
            com.xjzb.rts.core.Game.Ent highGun = eg.spawn("marine", 0, upPt[0], upPt[1], true);
            com.xjzb.rts.core.Game.Ent lowTgt = eg.spawn("zergling", 1, lowPt[0], lowPt[1], true);
            com.xjzb.rts.core.Game.Ent highTgt = eg.spawn("zergling", 1, upPt[0], upPt[1], true);
            com.xjzb.rts.core.Game.Ent brawler = eg.spawn("zergling", 0, lowPt[0], lowPt[1], true);

            boolean upPen = eg.elevationPenalty(lowGun, highTgt);
            // The published original figure is 53.125% and it is the MISS
            // chance -- the plan names it the hit rate, but its own acceptance
            // note ("the shells land about half the time, 约一半落空")
            // and the original both describe the miss. So the statistic
            // asserted here is the miss rate, in the plan 50-56% band.
            int misses = 0;
            for (int i = 0; i < 10000; i++) if (!eg.shotHits(lowGun, highTgt)) misses++;
            double rate = misses / 10000.0;
            boolean stat = upPen && rate >= 0.50 && rate <= 0.56;

            // downhill is free: a marine on the plateau at a target below
            boolean downFree = !eg.elevationPenalty(highGun, lowTgt)
                    && eg.shotHits(highGun, lowTgt);
            // same level is free
            boolean sameFree = !eg.elevationPenalty(lowGun, lowTgt);
            // melee never rolls, even uphill
            boolean meleeFree = !eg.elevationPenalty(brawler, highTgt)
                    && eg.shotHits(brawler, highTgt);
            // an all-flat game (no elevation asset) never penalises anything
            com.xjzb.rts.core.Game flat = new com.xjzb.rts.core.Game(
                    mapW, mapH, walk, starts, units, "terran");
            com.xjzb.rts.core.Game.Ent fa = flat.spawn("marine", 0, lowPt[0], lowPt[1], true);
            com.xjzb.rts.core.Game.Ent fb = flat.spawn("zergling", 1, upPt[0], upPt[1], true);
            boolean flatFree = !flat.elevationPenalty(fa, fb);

            ok &= stat && downFree && sameFree && meleeFree && flatFree;
            sb.append(" miss=").append(String.format("%.4f", rate))
              .append(" down=").append(downFree).append(" same=").append(sameFree)
              .append(" melee=").append(meleeFree).append(" flat=").append(flatFree);
        }

        System.out.println("  cargo/bunker/goliath/high-ground" + sb + " PASS=" + ok);
    }

    /** Occurrences of `sub` in `s` (non-overlapping). */
    static int countOf(String s, String sub) {
        int n = 0, i = 0;
        while ((i = s.indexOf(sub, i)) >= 0) { n++; i += sub.length(); }
        return n;
    }

    /**
     * v2.23: the UI pass (three batches, mirrored here so the arithmetic and
     * the source invariants -- not only the picture -- are pinned).
     *
     *   A no half-transparent layer on the always-on match path: both scrims
     *     and the see-through bevel are gone, the formation slots are opaque
     *     chips, the toast is an opaque chip;
     *   B the command card is an opaque panel only when it has orders: an empty
     *     selection draws nothing, a selected one is exactly 3x3 + 2dp, the
     *     icons use 2dp padding and the name strip is opaque;
     *   C the chunk placeholder uses the minimap brightening matrix, the
     *     prefetch ring is 2, the decode pool is 3, and GameActivity no longer
     *     sets FLAG_FULLSCREEN.
     */
    static void v224Tests() throws Exception {
        String root = "F:/KF/XJZB/AndroidPort/";
        String gv = new String(Files.readAllBytes(java.nio.file.Paths.get(
                root + "app/app/src/main/java/com/xjzb/rts/GameView.java")),
                java.nio.charset.StandardCharsets.UTF_8);
        String ga = new String(Files.readAllBytes(java.nio.file.Paths.get(
                root + "app/app/src/main/java/com/xjzb/rts/GameActivity.java")),
                java.nio.charset.StandardCharsets.UTF_8);
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- batch A: no translucent layer on the always-on path ----------
        boolean scrimGone = !gv.contains("TOPBAR_SCRIM") && !gv.contains("CONSOLE_SCRIM")
                && !gv.contains("argb(64, 8, 11, 20)") && !gv.contains("argb(84, 8, 11, 20)");
        // the see-through bevel may still be DEFINED, but nothing may call it
        boolean transUnused = countOf(gv, "bevelPanelTranslucent(c,") == 0;
        // the two HUD chips the player saw as "half transparent" are opaque now
        boolean chipOpaque = gv.contains("CHIP_DARK") && gv.contains("float pad = 2 * uiScale")
                && !gv.contains("argb(200, 12, 16, 26)") && !gv.contains("argb(190, 10, 14, 24)");
        ok &= scrimGone && transUnused && chipOpaque;
        sb.append(" scrimGone=").append(scrimGone).append(" transUnused=").append(transUnused)
          .append(" chipOpaque=").append(chipOpaque);

        // ---- batch B: the command card ------------------------------------
        // the empty card is skipped BEFORE any draw, and the panel is drawn only
        // on the first live cell -- so an empty selection has a zero rect
        int cardStart = gv.indexOf("private void drawCmdCard");
        int cardEnd = gv.indexOf("private void drawGridCell");
        String card = cardStart < 0 || cardEnd < cardStart ? ""
                : gv.substring(cardStart, cardEnd);
        boolean skipBeforePanel = card.indexOf("if (a == null) continue;") >= 0
                && card.indexOf("if (a == null) continue;") < card.indexOf("if (i == 0)")
                && card.indexOf("bevelPanel(c, new RectF(gx - pad") > 0;
        boolean gridCell = gv.contains("drawGridCell");
        // geometry: the panel is exactly 3 cells + 2 gaps + 2 x 2dp
        float dp = 2f;
        float cs = HudLayoutCardCell(720, dp);
        float gap = 4 * dp;
        float gridW = 3 * cs + 2 * gap;
        float panelW = gridW + 2 * (2 * dp);
        boolean panelExact = Math.abs(panelW - (3 * cs + 2 * gap + 2 * (2 * dp))) < 0.01f
                && panelW > gridW;
        boolean cardBacking = gv.contains("float cardPad = dp(2f)")
                && !gv.contains("cardPad = cs * 0.5f");
        ok &= skipBeforePanel && gridCell && panelExact && cardBacking;
        sb.append(" emptyCard0=").append(skipBeforePanel).append(" gridCell=").append(gridCell)
          .append(" panel=").append((int) panelW).append("(3x").append((int) cs)
          .append("+2dp)=").append(panelExact);

        // ---- batch C: loading path + window flags -------------------------
        // v2.42 batch B changed the loading-tile placeholder: the veil dropped
        // from 128 to 96 and the tile is now brightened with PLACEHOLDER_BRIGHT
        // (offset 34) instead of MINIMAP_BRIGHT (offset 14). MINIMAP_BRIGHT is
        // still the minimap's own matrix, so all three must be present.
        boolean placeholder = gv.contains("PLACEHOLDER_BRIGHT") && gv.contains("p.setAlpha(96)")
                && gv.contains("MINIMAP_BRIGHT");
        boolean ring2 = gv.contains("cx0 - 2") && gv.contains("cx1 + 2");
        boolean pool3 = gv.contains("newFixedThreadPool(3");
        boolean noFullscreen = !ga.contains("WindowManager.LayoutParams.FLAG_FULLSCREEN");
        boolean stillImmersive = ga.contains("IMMERSIVE_STICKY")
                && ga.contains("SHORT_EDGES");
        ok &= placeholder && ring2 && pool3 && noFullscreen && stillImmersive;
        sb.append(" placeholder=").append(placeholder).append(" ring2=").append(ring2)
          .append(" pool3=").append(pool3).append(" noFlagFullscreen=").append(noFullscreen)
          .append(" immersive=").append(stillImmersive);

        System.out.println("  ui sweep" + sb + " PASS=" + ok);
    }

    /**
     * v2.25: Terran add-ons, the scanner sweep and the nuclear strike.
     *
     *   add-ons -- a parent builds its pad add-on, the pad is exactly 2x2 at
     *     the parent's side, the add-on is refused without its parent, and it
     *     dies with the parent;
     *   tech -- a starport with no control tower cannot build the dropship,
     *     and can once the tower is attached;
     *   scan -- the comsat's sweep costs 50, reveals fog, and reveals cloaked
     *     units inside its square without any detector;
     *   nuke -- a silo arms, a ghost calls the strike, the ghost is rooted for
     *     the countdown, and the blast is 800 at the centre falling off to
     *     25% at the rim.
     */
    static void v225Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- the six add-on rows exist and carry their parent ---------------
        boolean rows = com.xjzb.rts.core.Game.TYPES.containsKey("comsat")
                && com.xjzb.rts.core.Game.TYPES.containsKey("controlt")
                && com.xjzb.rts.core.Game.TYPES.containsKey("machineshop")
                && com.xjzb.rts.core.Game.TYPES.containsKey("physicslab")
                && com.xjzb.rts.core.Game.TYPES.containsKey("nukesilo");
        boolean parents = "academy".equals(com.xjzb.rts.core.Game.TYPES.get("comsat").addonFor)
                && "starport".equals(com.xjzb.rts.core.Game.TYPES.get("controlt").addonFor)
                && "factory".equals(com.xjzb.rts.core.Game.TYPES.get("machineshop").addonFor)
                && "sciencefac".equals(com.xjzb.rts.core.Game.TYPES.get("physicslab").addonFor)
                && "sciencefac".equals(com.xjzb.rts.core.Game.TYPES.get("nukesilo").addonFor);
        ok &= rows && parents;
        sb.append(" rows=").append(rows).append(" parents=").append(parents);

        // ---- placement: pad geometry and the parent rule --------------------
        com.xjzb.rts.core.Game ag = cleanGame("terran");
        ag.gasPlayer = 5000;              // add-ons cost gas; the starter game has none
        float[] spot = clearGround(ag, 3, 4);
        if (spot == null) { System.out.println("  [v225] no open ground"); return; }
        // The academy owns the cleared square (the scan guarantees its pad is
        // free); the barracks only has to exist to prove the parent rule, so it
        // goes wherever the ordinary scan lands -- a different corner.
        com.xjzb.rts.core.Game.Ent academy =
                ag.spawn("academy", 0, spot[0], spot[1], true);
        float[] spot2 = openGround(ag, 200);
        com.xjzb.rts.core.Game.Ent barracks =
                ag.spawn("barracks", 0, spot2[0], spot2[1], true);
        // the wrong parent is refused, the right one is not
        boolean wrongParent = ag.addonError(barracks, "comsat") != null;
        boolean rightParent = ag.addonError(academy, "comsat") == null;
        com.xjzb.rts.core.Game.Ent comsat = ag.buildAddon(academy, "comsat");
        boolean built = comsat != null && comsat.addonParent == academy;
        // the pad is 2x2 flush against the parent's +x side: 3x3 parent (48 px
        // half) + 2x2 add-on (32 px half) = 80 px from centre to centre
        float[] pad = com.xjzb.rts.core.Game.addonPad(academy, 0);
        boolean padExact = Math.abs(pad[0] - academy.x - 80f) < 0.01f
                && Math.abs(pad[1] - academy.y) < 0.01f
                && Math.abs(comsat.x - pad[0]) < 0.01f
                && Math.abs(comsat.y - pad[1]) < 0.01f;
        // a second add-on on the same pad is refused
        boolean noDouble = ag.addonError(academy, "comsat") != null;
        // and it is gone the moment the parent dies
        academy.hp = 0;
        ag.update(1 / 30f);
        boolean orphan = !comsat.alive();
        ok &= wrongParent && rightParent && built && padExact && noDouble && orphan;
        sb.append(" pad=80").append(padExact).append(" built=").append(built)
          .append(" wrongParent=").append(wrongParent)
          .append(" noDouble=").append(noDouble).append(" orphanDies=").append(orphan);

        // ---- tech gate: the control tower opens the starport's air rows -----
        com.xjzb.rts.core.Game tg = cleanGame("terran");
        tg.mineralsPlayer = 5000;
        tg.gasPlayer = 5000;
        // cleanGame strips every building, so the supply cap is 0 and a bare
        // trainError would report "人口已达上限" instead of the tech gate this
        // test is about. Pin the cap high for the duration of the check.
        tg.supplyCap = 200;
        float[] s2 = clearGround(tg, 3, 4);
        if (s2 == null) { System.out.println("  [v225] no clear ground (tech)"); return; }
        com.xjzb.rts.core.Game.Ent sp = tg.spawn("starport", 0, s2[0], s2[1], true);
        // a wraith is not gated (the starport itself is the gate)
        boolean wraithOk = tg.trainError("wraith") == null;
        // the dropship is gated on the control tower
        String before = tg.trainError("dropship");
        boolean gatedBefore = before != null && before.contains("控制塔");
        com.xjzb.rts.core.Game.Ent tower = tg.buildAddon(sp, "controlt");
        boolean gatedAfter = tower != null && tg.trainError("dropship") == null;
        ok &= wraithOk && gatedBefore && gatedAfter;
        sb.append(" wraith=").append(wraithOk).append(" gated=").append(gatedBefore)
          .append(" opened=").append(gatedAfter);

        // ---- scanner sweep --------------------------------------------------
        com.xjzb.rts.core.Game sg = cleanGame("terran");
        sg.gasPlayer = 5000;
        float[] s3 = clearGround(sg, 3, 4);
        if (s3 == null) { System.out.println("  [v225] no clear ground (scan)"); return; }
        com.xjzb.rts.core.Game.Ent ac2 = sg.spawn("academy", 0, s3[0], s3[1], true);
        com.xjzb.rts.core.Game.Ent cs = sg.buildAddon(ac2, "comsat");
        fullEnergy(cs);
        // Sweep a square that is genuinely unseen. The map's bottom-right
        // corner is NOT dark -- cleanGame parks a sunken colony there and its
        // 9-tile vision lights the corner -- so scan for the first unexplored
        // tile instead of assuming a coordinate.
        float fx = -1, fy = -1;
        for (int ty = 4; ty < sg.hTiles - 4 && fx < 0; ty++)
            for (int tx = 4; tx < sg.wTiles - 4; tx++)
                if (sg.fog[ty * sg.wTiles + tx] == 0) {
                    fx = tx * 32f + 16;
                    fy = ty * 32f + 16;
                    break;
                }
        if (fx < 0) { System.out.println("  [v225] map has no dark tile"); return; }
        int beforeIdx = (int) (fy / 32) * sg.wTiles + (int) (fx / 32);
        boolean wasDark = sg.fog[beforeIdx] == 0;
        boolean swept = sg.castScan(cs, fx, fy);
        boolean paid = Math.abs(cs.energy - (com.xjzb.rts.core.Game.ENERGY_MAX
                - com.xjzb.rts.core.Game.COST_SCAN)) < 0.01f;
        boolean lit = sg.fog[beforeIdx] == 2;
        boolean inSquare = sg.scanReveals(fx, fy, 0);
        boolean outSquare = !sg.scanReveals(fx + 800, fy, 0);
        // a dark templar inside the sweep is spotted with no detector anywhere
        com.xjzb.rts.core.Game.Ent dt = sg.spawn("dtemplar", 1, fx, fy, true);
        sg.update(1 / 30f);
        boolean revealed = dt.spotted;
        // and once the sweep expires it hides again
        for (int i = 0; i < (int) (com.xjzb.rts.core.Game.SCAN_DURATION * 30) + 10; i++)
            sg.update(1 / 30f);
        boolean hides = !dt.spotted;
        ok &= wasDark && swept && paid && lit && inSquare && outSquare && revealed && hides;
        sb.append(" scan=").append(swept).append(" paid=").append(paid)
          .append(" lit=").append(lit).append(" square=").append(inSquare)
          .append(" revealedCloak=").append(revealed).append(" expires=").append(hides);

        // ---- nuclear strike -------------------------------------------------
        com.xjzb.rts.core.Game ng = cleanGame("terran");
        ng.mineralsPlayer = 5000;
        ng.gasPlayer = 5000;
        float[] s4 = clearGround(ng, 3, 4);
        if (s4 == null) { System.out.println("  [v225] no clear ground (nuke)"); return; }
        com.xjzb.rts.core.Game.Ent sf = ng.spawn("sciencefac", 0, s4[0], s4[1], true);
        com.xjzb.rts.core.Game.Ent silo = ng.buildAddon(sf, "nukesilo");
        // the missile arms on its own after NUKE_BUILD_TIME
        boolean startsEmpty = silo != null && !silo.nukeArmed;
        for (int i = 0; i < (int) (com.xjzb.rts.core.Game.NUKE_BUILD_TIME * 30) + 5; i++)
            ng.update(1 / 30f);
        boolean armed = silo.nukeArmed;
        com.xjzb.rts.core.Game.Ent ghost = ng.spawn("ghost", 0, s4[0] + 200, s4[1], true);
        boolean ghostOk = ng.nukeError(ghost) == null;
        float tx = ghost.x + 64, ty = ghost.y;
        boolean called = ng.callNuke(ghost, tx, ty);
        boolean unarmed = !silo.nukeArmed;          // the missile left the silo
        boolean rooted = ghost.nukeLock > 0;
        // a rooted ghost ignores a move order
        List<com.xjzb.rts.core.Game.Ent> one = new ArrayList<>();
        one.add(ghost);
        ng.orderMove(one, ghost.x + 400, ghost.y, false);
        boolean moveBlocked = !ghost.moving;
        // The victims are PLAYER units. Two reasons: the AI drives every team-1
        // unit (it walked the first draft of these marines straight into the
        // blast, so the "outside is safe" case was untestable), and a nuke
        // hitting your own army is exactly the original's rule -- the blast has
        // no team filter -- so this doubles as the friendly-fire assertion.
        // clearGround scans from the bottom-right corner, so the map interior is
        // toward -x; +x would clamp them back inside the blast.
        com.xjzb.rts.core.Game.Ent centre = ng.spawn("marine", 0, tx, ty, true);
        com.xjzb.rts.core.Game.Ent rim = ng.spawn("marine", 0, tx - 370, ty, true);
        com.xjzb.rts.core.Game.Ent outside = ng.spawn("marine", 0, tx - 700, ty, true);
        int centreHp = centre.hp, rimHp = rim.hp, outHp = outside.hp;
        // guard: the outside marine must really be outside the blast
        float dOut = (float) Math.hypot(outside.x - tx, outside.y - ty);
        boolean outIsFar = dOut > com.xjzb.rts.core.Game.NUKE_RADIUS;
        for (int i = 0; i < (int) (com.xjzb.rts.core.Game.NUKE_DELAY * 30) + 5; i++)
            ng.update(1 / 30f);
        boolean centreHit = centre.hp < centreHp || !centre.alive();
        boolean rimHit = rim.hp < rimHp;
        boolean outSafe = !outIsFar || outside.hp == outHp;
        // a marine has 45 hp and the blast is 800: the centre must not survive
        boolean centreDead = !centre.alive();
        ok &= startsEmpty && armed && ghostOk && called && unarmed && rooted
                && moveBlocked && centreHit && rimHit && outSafe && centreDead;
        sb.append(" siloArms=").append(armed).append(" called=").append(called)
          .append(" rooted=").append(rooted).append(" moveBlocked=").append(moveBlocked)
          .append(" centre=").append(centreDead).append(" rim=").append(rimHit)
          .append(" outside=").append(outSafe);

        System.out.println("  addons/scan/nuke" + sb + " PASS=" + ok);
    }

    /**
     * v2.26: production fidelity.
     *
     *   merge -- two same-type templars standing together become one archon,
     *     both are consumed, mismatched pairs and distant pairs are refused;
     *   burrow -- any zerg ground unit can hide, a burrowed unit is invisible
     *     and untouchable by melee but still reachable by ranged fire;
     *   hangar -- a carrier fills its hangar over time and launches the
     *     interceptors only while an enemy is in range;
     *   ammo -- a reaver carries a finite rack, cannot fire empty, and reloads
     *     only beside its robotics facility.
     */
    static void v226Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- merge: two templars -> one archon -----------------------------
        com.xjzb.rts.core.Game mg = cleanGame("protoss");
        com.xjzb.rts.core.Game.Ent t1 = mg.spawn("templar", 0, 600, 600, true);
        com.xjzb.rts.core.Game.Ent t2 = mg.spawn("templar", 0, 620, 600, true);
        List<com.xjzb.rts.core.Game.Ent> pair = new ArrayList<>();
        pair.add(t1);
        pair.add(t2);
        int before = mg.ents.size();
        com.xjzb.rts.core.Game.Ent archon = mg.orderMerge(pair, null);
        mg.update(1 / 30f);
        boolean merged = archon != null && "archon".equals(archon.type.key);
        // two in, one out: the two templars are gone and the archon stands
        boolean consumed = !t1.alive() && !t2.alive();
        boolean oneLeft = mg.ents.size() == before - 1;
        // the archon keeps its shield (350) and 10 hp, the original's shape
        boolean shape = archon != null && archon.type.shield == 350
                && archon.type.hp == 10 && archon.shield == 350;
        ok &= merged && consumed && oneLeft && shape;
        sb.append(" merge=").append(merged).append(" consumed=").append(consumed)
          .append(" oneLeft=").append(oneLeft).append(" shape=").append(shape);

        // mismatched pair and distant pair are refused
        com.xjzb.rts.core.Game.Ent dt1 = mg.spawn("dtemplar", 0, 700, 600, true);
        com.xjzb.rts.core.Game.Ent zl = mg.spawn("zealot", 0, 720, 600, true);
        List<com.xjzb.rts.core.Game.Ent> bad = new ArrayList<>();
        bad.add(dt1);
        bad.add(zl);
        boolean refuseMix = mg.mergeError(bad, null) != null;
        com.xjzb.rts.core.Game.Ent dt2 = mg.spawn("dtemplar", 0, 900, 600, true);
        List<com.xjzb.rts.core.Game.Ent> far = new ArrayList<>();
        far.add(dt1);
        far.add(dt2);
        boolean refuseFar = mg.mergeError(far, null) != null;
        // and the dark pair does merge, into the dark archon -- once they are
        // standing together (the far check above used them while apart)
        dt2.x = dt1.x + 20;
        com.xjzb.rts.core.Game.Ent darchon = mg.orderMerge(far, null);
        boolean darkMerge = darchon != null && "darchon".equals(darchon.type.key);
        ok &= refuseMix && refuseFar && darkMerge;
        sb.append(" refuseMix=").append(refuseMix).append(" refuseFar=").append(refuseFar)
          .append(" darkMerge=").append(darkMerge);

        // ---- burrow: hide from everything until a detector shows up --------
        // A burrowed unit joins the cloak layer (isCloakedNow), so the single
        // gate in findEnemyInRange hides it from melee AND ranged alike until
        // one of the enemy's detectors is in reach -- which is the original's
        // rule, and the reason the missile turret is worth building.
        com.xjzb.rts.core.Game bg = cleanGame("zerg");
        com.xjzb.rts.core.Game.Ent ling = bg.spawn("zergling", 0, 600, 600, true);
        boolean canB = com.xjzb.rts.core.Game.canBurrow(ling);
        boolean down = bg.toggleBurrow(ling);
        com.xjzb.rts.core.Game.Ent marine = bg.spawn("marine", 1, 640, 600, true);
        com.xjzb.rts.core.Game.Ent zealot = bg.spawn("zealot", 1, 640, 600, true);
        bg.update(1 / 30f);      // settle the cloak layer the toggle feeds
        boolean hidden = ling.burrowed && ling.cloakActive && !ling.spotted;
        boolean rangedBlind = bg.findEnemyInRange(marine, 400) != ling;
        boolean meleeBlind = bg.findEnemyInRange(zealot, 400) != ling;
        // an ENEMY detector reveals it (detectorNear asks for the opposite
        // team, so a friendly turret would prove nothing)
        com.xjzb.rts.core.Game.Ent turret = bg.spawn("turret", 1, 640, 600, true);
        bg.update(1 / 30f);
        boolean spotted = ling.spotted;
        boolean rangedSees = bg.findEnemyInRange(marine, 400) == ling;
        // and it comes back up, becoming visible to everything again
        turret.hp = 0;
        boolean up = bg.toggleBurrow(ling) && !ling.burrowed;
        bg.update(1 / 30f);
        boolean visibleAgain = !ling.cloakActive;
        // a non-zerg unit cannot burrow at all
        com.xjzb.rts.core.Game.Ent m2 = bg.spawn("marine", 0, 700, 600, true);
        boolean refuse = !com.xjzb.rts.core.Game.canBurrow(m2)
                && bg.burrowError(m2) != null;
        ok &= canB && down && hidden && rangedBlind && meleeBlind && spotted
                && rangedSees && up && visibleAgain && refuse;
        sb.append(" burrow=").append(down).append(" hidden=").append(hidden)
          .append(" blind(noDetector)=").append(rangedBlind && meleeBlind)
          .append(" spotted=").append(spotted).append(" seesAfterDetector=").append(rangedSees)
          .append(" unburrow=").append(up).append(" refuse=").append(refuse);

        // ---- carrier hangar -------------------------------------------------
        com.xjzb.rts.core.Game hg = cleanGame("protoss");
        com.xjzb.rts.core.Game.Ent carrier = hg.spawn("carrier", 0, 600, 600, true);
        int start = carrier.interceptors;
        for (int i = 0; i < 30 * 30; i++) hg.update(1 / 30f);
        boolean filled = carrier.interceptors == com.xjzb.rts.core.Game.HANGAR_CAP;
        boolean idle = carrier.launched == 0;      // nothing to shoot
        com.xjzb.rts.core.Game.Ent foe = hg.spawn("zergling", 1, 660, 600, true);
        hg.update(1 / 30f);
        boolean launched = carrier.launched == carrier.interceptors;
        // and it recalls them once the coast is clear
        foe.hp = 0;
        hg.update(1 / 30f);
        boolean recalled = carrier.launched == 0;
        ok &= filled && idle && launched && recalled;
        sb.append(" hangar=").append(start).append("->").append(carrier.interceptors)
          .append(" idle=").append(idle).append(" launched=").append(launched)
          .append(" recalled=").append(recalled);

        // ---- reaver scarab rack ---------------------------------------------
        com.xjzb.rts.core.Game rg = cleanGame("protoss");
        com.xjzb.rts.core.Game.Ent reaver = rg.spawn("reaver", 0, 600, 600, true);
        boolean fullRack = reaver.ammo == com.xjzb.rts.core.Game.REAVER_AMMO;
        // A 400 hp ultralisk soaks all ten scarabs; a 35 hp zergling would die
        // after four and the rack would never actually empty.
        com.xjzb.rts.core.Game.Ent soak = rg.spawn("ultra", 1, 640, 600, true);
        // drain the rack
        for (int i = 0; i < 200 && reaver.ammo > 0; i++) {
            reaver.cd = 0;
            rg.update(1 / 30f);
        }
        boolean emptied = reaver.ammo == 0;
        // v2.44: park the soak out of sight once the rack is empty. Idle units
        // of BOTH teams acquire now (the v2.44 fix that lets an AI base
        // defend itself), so an ultra standing next to the reaver is not a
        // passive prop any more -- it kills the thing under test mid-reload.
        soak.x = 40; soak.y = 40; soak.target = null; soak.moving = false;
        // empty and far from a robotics bay: no reload
        for (int i = 0; i < 30 * 30; i++) rg.update(1 / 30f);
        boolean stillEmpty = reaver.ammo == 0;
        // beside a robotics bay it reloads
        rg.spawn("robotic", 0, reaver.x + 40, reaver.y, true);
        for (int i = 0; i < (int) (com.xjzb.rts.core.Game.REAVER_RELOAD_TIME * 30) + 90; i++)
            rg.update(1 / 30f);
        boolean reloaded = reaver.ammo > 0;
        ok &= fullRack && emptied && stillEmpty && reloaded;
        sb.append(" rack=").append(fullRack).append(" emptied=").append(emptied)
          .append(" noReloadAway=").append(stillEmpty).append(" reloaded=").append(reloaded);

        System.out.println("  merge/burrow/hangar/ammo" + sb + " PASS=" + ok);
    }

    /**
     * v2.27: growth and scale.
     *
     *   groups -- ten control groups, assign and recall round-trip through the
     *     core so the view's hold-duration mapping is the only UI-side part;
     *   population -- the ceiling is a research: tier 0 is the original 40,
     *     the next tier is 100 (the plan's documented fallback), a provider's
     *     output scales with the tier so a depot keeps paying for itself, and
     *     the tier survives a save/load round trip.
     */
    static void v227Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- ten control groups ---------------------------------------------
        com.xjzb.rts.core.Game gg = cleanGame("terran");
        java.util.List<com.xjzb.rts.core.Game.Ent> ten = new ArrayList<>();
        for (int i = 0; i < 10; i++)
            ten.add(gg.spawn("marine", 0, 400 + i * 20, 400, true));
        // assign groups 0..9 one at a time
        boolean assignAll = true;
        for (int g = 0; g < 10; g++) {
            for (com.xjzb.rts.core.Game.Ent e : gg.ents) e.selected = false;
            ten.get(g).selected = true;
            if (gg.groupTap(g, true) != com.xjzb.rts.core.Game.GROUP_ASSIGNED)
                assignAll = false;
        }
        boolean sized = gg.groups.size() >= 10;
        // recall group 9 and confirm only that unit is selected
        for (com.xjzb.rts.core.Game.Ent e : gg.ents) e.selected = false;
        int res = gg.groupTap(9, false);
        boolean recalled = res == com.xjzb.rts.core.Game.GROUP_RECALLED
                && gg.selected().size() == 1 && gg.selected().get(0) == ten.get(9);
        // an unassigned slot reports empty rather than throwing
        boolean empty = gg.groupTap(11, false) == com.xjzb.rts.core.Game.GROUP_EMPTY;
        ok &= assignAll && sized && recalled && empty;
        sb.append(" groups=10/10").append(assignAll).append(" sized=").append(sized)
          .append(" recall9=").append(recalled).append(" emptySlot=").append(empty);

        // ---- population tiers ------------------------------------------------
        com.xjzb.rts.core.Game pg = cleanGame("terran");
        // tier 0: a depot feeds 8, the ceiling is the original 40
        boolean tier0 = com.xjzb.rts.core.Game.SUPPLY_TIERS[0] == 40
                && com.xjzb.rts.core.Game.SUPPLY_CAP == 100
                && com.xjzb.rts.core.Game.supplyProvided("depot") == 8;
        // cleanGame keeps the player's starting base, so the absolute cap is
        // not a fixed number -- assert the DELTA a new depot makes instead.
        pg.update(1 / 30f);
        int capBefore = pg.supplyCap;
        pg.spawn("depot", 0, 460, 400, true);
        pg.update(1 / 30f);
        boolean depot8 = pg.supplyCap - capBefore == 8;
        // buy the tier: the same buildings now feed 2.5x (a depot gives 20)
        pg.mineralsPlayer = 5000;
        int capAtTier0 = pg.supplyCap;
        String why = pg.raiseSupplyCap();
        pg.update(1 / 30f);
        boolean bought = why == null && pg.capTier == 1;
        // the whole cap scales 2.5x: 10 (cc) + 8 (depot) = 18 becomes 25 + 20 = 45
        boolean scaled = pg.supplyCap == (int) (capAtTier0 * 2.5f);
        boolean cap40 = depot8 && scaled;
        // the ceiling itself is now 100
        boolean ceiling = com.xjzb.rts.core.Game.SUPPLY_CAP == 100;
        // buying again is refused (the ladder is exhausted at 100)
        boolean exhausted = pg.raiseSupplyCap() != null;
        ok &= tier0 && cap40 && bought && ceiling && exhausted;
        sb.append(" tier0=").append(tier0).append(" depot8+scale=").append(cap40)
          .append(" bought=").append(bought).append(" scaled=").append(scaled)
          .append(" ceiling=").append(ceiling).append(" exhausted=").append(exhausted);

        // ---- the tier survives a save/load round trip ------------------------
        com.xjzb.rts.core.Game sg = cleanGame("terran");
        sg.mineralsPlayer = 5000;
        sg.raiseSupplyCap();
        String blob = sg.serialize();
        com.xjzb.rts.core.Game back = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, elev, starts, units, "terran");
        boolean loaded = back.deserialize(blob);
        boolean tierKept = loaded && back.capTier == sg.capTier;
        ok &= tierKept;
        sb.append(" saveTier=").append(tierKept);

        // ---- the frame-time budget the plan asks for -------------------------
        // The plan gates 200 on a measured budget and names 100 as the
        // fallback. This is the measurement that chose 100: 400 entities in
        // sustained combat cost ~11 ms/tick on the desktop JVM, about a third
        // of the 33 ms frame -- fine here, too tight on a phone. Assert the
        // tier list so a future change has to re-run the probe deliberately.
        boolean ladder = com.xjzb.rts.core.Game.SUPPLY_TIERS.length == 2
                && com.xjzb.rts.core.Game.SUPPLY_TIERS[0] == 40
                && com.xjzb.rts.core.Game.SUPPLY_TIERS[1] == 100;
        ok &= ladder;
        sb.append(" ladder=").append(ladder);

        System.out.println("  groups/population" + sb + " PASS=" + ok);
    }

    /**
     * v2.28: the upgrade lines are per class.
     *
     *   split -- researching the infantry weapon line raises a marine's bonus
     *     and leaves a siege tank's alone (the old single axis buffed both);
     *   independence -- the three lines level separately, so buying ships does
     *     not move the infantry figure;
     *   save -- the per-class levels survive a round trip, and a save written
     *     before the split still loads (the arrays default to zero).
     */
    static void v228Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        com.xjzb.rts.core.Game g = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent inf = g.spawn("marine", 0, 500, 500, true);
        com.xjzb.rts.core.Game.Ent veh = g.spawn("tank", 0, 540, 500, true);
        com.xjzb.rts.core.Game.Ent shp = g.spawn("wraith", 0, 580, 500, true);
        boolean tagged = "infantry".equals(inf.type.upClass)
                && "vehicle".equals(veh.type.upClass)
                && "ship".equals(shp.type.upClass);
        int inf0 = inf.dmgBonus, veh0 = veh.dmgBonus, shp0 = shp.dmgBonus;

        // buy two infantry weapon levels
        g.mineralsPlayer = 5000;
        boolean b1 = g.buyWeaponUpgrade(inf) == null;
        boolean b2 = g.buyWeaponUpgrade(inf) == null;
        int infAfter = inf.dmgBonus, vehAfter = veh.dmgBonus, shpAfter = shp.dmgBonus;
        // only the infantry line moved
        boolean onlyInf = b1 && b2 && infAfter == inf0 + 4
                && vehAfter == veh0 && shpAfter == shp0;
        boolean levels = g.weaponFor("infantry") == 2
                && g.weaponFor("vehicle") == 0 && g.weaponFor("ship") == 0;
        ok &= tagged && onlyInf && levels;
        sb.append(" tagged=").append(tagged)
          .append(" inf=").append(inf0).append("->").append(infAfter)
          .append(" veh=").append(vehAfter).append(" shp=").append(shpAfter)
          .append(" levels=").append(levels);

        // the ship line levels on its own, and does not disturb infantry
        boolean s1 = g.buyWeaponUpgrade(shp) == null;
        boolean s2 = g.buyWeaponUpgrade(shp) == null;
        boolean s3 = g.buyWeaponUpgrade(shp) == null;
        boolean shipMax = s1 && s2 && s3 && g.weaponFor("ship") == 3
                && shp.dmgBonus == shp0 + 6 && inf.dmgBonus == infAfter;
        // and it refuses a fourth
        boolean shipRefuse = g.buyWeaponUpgrade(shp) != null;
        ok &= shipMax && shipRefuse;
        sb.append(" ship=").append(shp0).append("->").append(shp.dmgBonus)
          .append(" max=").append(shipMax).append(" refuse4=").append(shipRefuse);

        // armour is per class too
        int infArm0 = inf.armorBonus;
        g.mineralsPlayer = 5000;
        boolean a1 = g.buyArmorUpgrade(veh) == null;
        boolean a2 = g.buyArmorUpgrade(veh) == null;
        boolean armorSplit = a1 && a2 && veh.armorBonus == 2
                && inf.armorBonus == infArm0;
        // the aggregate the HUD reads is the max across the lines
        boolean agg = g.weaponLevel == 3 && g.armorLevel == 2;
        ok &= armorSplit && agg;
        sb.append(" armorSplit=").append(armorSplit).append(" aggregate=").append(agg);

        // a building has no line and is refused
        com.xjzb.rts.core.Game.Ent cc = g.spawn("cc", 0, 400, 400, true);
        boolean buildingRefused = "".equals(cc.type.upClass)
                && g.buyWeaponUpgrade(cc) != null;

        // ---- the split survives a save/load round trip ----------------------
        String blob = g.serialize();
        com.xjzb.rts.core.Game back = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, elev, starts, units, "terran");
        boolean loaded = back.deserialize(blob);
        boolean kept = loaded
                && back.weaponFor("infantry") == 2
                && back.weaponFor("ship") == 3
                && back.armorFor("vehicle") == 2
                && back.armorFor("infantry") == 0;
        // a v2.27-shaped save (no per-class tokens) still loads, at level 0
        String legacy = "XJZB-SAVE-1\nstate 400 0 3.0 1 300 60.0 0 5.0 0 0 0 0 0 0 terran 0\n";
        com.xjzb.rts.core.Game old = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, elev, starts, units, "terran");
        boolean legacyOk = old.deserialize(legacy)
                && old.weaponFor("infantry") == 0 && old.capTier == 0;
        ok &= buildingRefused && kept && legacyOk;
        sb.append(" buildingRefused=").append(buildingRefused)
          .append(" saveKept=").append(kept).append(" legacyLoads=").append(legacyOk);

        System.out.println("  upgrade lines" + sb + " PASS=" + ok);
    }

    /**
     * v2.29: the campaign expansion. Ten new missions (m06-m15) ship as data,
     * so the risk here is not logic but a typo: `setMission` skips an unknown
     * unit key with a bare `continue` and a wave event drops it silently, so a
     * misspelt "hydrlisk" yields a level that looks fine and simply fights with
     * one unit fewer. This walk validates every mission in index.txt against
     * the engine's own tables and the map assets each one names.
     *
     *  #1 the index row and the JSON agree (id, map) and the map exists;
     *  #2 both races are real race keys;
     *  #3 every unit key -- start units, wave/reinforce units, aiWaves -- exists
     *     in Game.TYPES;
     *  #4 every objective kind and event action is one the parser handles;
     *  #5 every level has a player town hall and an enemy hatchery. The enemy
     *     one is not cosmetic: the AI's production drain, its rally point and
     *     its structure ladder are all anchored on a hatchery (Game.java:5548,
     *     5690, 5957), so a level without one fields an enemy that never moves;
     *  #6 a protect target is actually on the board at start, or the objective
     *     fails on the first frame;
     *  #7 every authored coordinate is inside the map;
     *  #8 every start unit stands on walkable ground, checked against the map's
     *     own walk bitmap -- the same data the runtime reads;
     *  #9 an "economy": true mission really gets its mineral fields back.
     */
    static void v229Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();
        java.util.Set<String> mapIds = new java.util.HashSet<>();
        for (String line : Files.readAllLines(Paths.get(ASSETS + "/maps/index.txt"))) {
            String[] p = line.trim().split("\\|");
            if (p.length >= 3) mapIds.add(p[0]);
        }
        java.util.Set<String> races = new java.util.HashSet<>(
                java.util.Arrays.asList("terran", "zerg", "protoss"));
        java.util.Set<String> objKinds = new java.util.HashSet<>(
                java.util.Arrays.asList("destroyAll", "protect", "survive"));
        java.util.Set<String> actions = new java.util.HashSet<>(
                java.util.Arrays.asList("wave", "reinforce", "message", "win", "lose"));

        int n = 0, unknownUnits = 0, badMap = 0, badRace = 0, badKind = 0,
                noEnemyHall = 0, noPlayerHall = 0, badProtect = 0, offMap = 0,
                blocked = 0, stranded = 0, ecoMiss = 0, indexMismatch = 0;

        for (String row : Files.readAllLines(Paths.get(ASSETS + "/missions/index.txt"))) {
            String[] f = row.trim().split("\\|");
            if (f.length < 3) continue;
            n++;
            String id = f[0];
            java.nio.file.Path jp = Paths.get(ASSETS + "/missions/" + id + ".json");
            if (!Files.exists(jp)) { indexMismatch++; continue; }
            com.xjzb.rts.core.Mission m = com.xjzb.rts.core.Mission.parse(
                    new String(Files.readAllBytes(jp), java.nio.charset.StandardCharsets.UTF_8));
            if (m == null) { indexMismatch++; continue; }
            if (!id.equals(m.id) || !f[2].trim().equals(m.map)) indexMismatch++;
            if (!mapIds.contains(m.map)) { badMap++; continue; }
            if (!races.contains(m.playerRace) || !races.contains(m.enemyRace)) badRace++;

            // the map's own terrain: the same meta.txt and walk bitmap the
            // runtime loads, so "on walkable ground" means what it says.
            String meta = new String(Files.readAllBytes(
                    Paths.get(ASSETS + "/maps/" + m.map + "/meta.txt")),
                    java.nio.charset.StandardCharsets.UTF_8);
            int mw = 0, mh = 0;
            for (String ln : meta.split("\n")) {
                ln = ln.trim();
                if (ln.startsWith("w=")) mw = Integer.parseInt(ln.substring(2));
                else if (ln.startsWith("h=")) mh = Integer.parseInt(ln.substring(2));
            }
            boolean[] walkM = new boolean[mw * 4 * mh * 4];
            java.io.InputStream in = new java.util.zip.GZIPInputStream(
                    Files.newInputStream(Paths.get(ASSETS + "/maps/" + m.map + "/walk.bin.gz")));
            byte[] raw = in.readAllBytes();
            in.close();
            for (int i = 0; i < raw.length && i < walkM.length; i++) walkM[i] = raw[i] != 0;

            boolean playerHall = false, enemyHall = false;
            java.util.Set<String> startKeys = new java.util.HashSet<>();
            for (Object[] u : m.startUnits) {
                String key = (String) u[0];
                startKeys.add(key);
                com.xjzb.rts.core.Game.Type ty = com.xjzb.rts.core.Game.TYPES.get(key);
                if (ty == null) unknownUnits++;
                int team = (Integer) u[3];
                float x = (Float) u[1], y = (Float) u[2];
                if (x < 0 || y < 0 || x >= mw * 32 || y >= mh * 32) offMap++;
                // A building has to be authored on clear ground: spawn() snaps
                // it to the tile grid and stamps its footprint there, so one
                // sitting in a cliff stays in the cliff. A mobile unit is
                // allowed a single-tile pit -- setMission nudges it out, the
                // same recovery Mission.update applies to a wave spawn -- so it
                // is checked against the built game below instead.
                else if (ty != null && ty.tiles > 0
                        && !walkM[((int) (y / 8)) * mw * 4 + (int) (x / 8)]) blocked++;
                if (team == 0 && ("cc".equals(key) || "hatchery".equals(key)
                        || "nexus".equals(key))) playerHall = true;
                if (team == 1 && "hatchery".equals(key)) enemyHall = true;
            }
            if (!playerHall) noPlayerHall++;
            if (!enemyHall) noEnemyHall++;
            for (com.xjzb.rts.core.Mission.Objective o : m.objectives) {
                if (!objKinds.contains(o.kind)) badKind++;
                if ("protect".equals(o.kind) && !startKeys.contains(o.target)) badProtect++;
            }
            for (com.xjzb.rts.core.Mission.Event e : m.events) {
                if (!actions.contains(e.action)) badKind++;
                if (e.units != null)
                    for (String u : e.units)
                        if (!com.xjzb.rts.core.Game.TYPES.containsKey(u)) unknownUnits++;
                for (float[] pt : new float[][]{e.from, e.to})
                    if (pt != null && (pt[0] < 0 || pt[1] < 0
                            || pt[0] >= mw * 32 || pt[1] >= mh * 32)) offMap++;
            }
            for (String[] w : m.aiWaves)
                for (String u : w)
                    if (!com.xjzb.rts.core.Game.TYPES.containsKey(u)) unknownUnits++;

            // #8/#9: build the level and ask the engine two things -- is any
            // mobile unit standing inside terrain, and did an economy mission
            // really get the map's mineral fields back.
            com.xjzb.rts.core.Game g = missionGame(id);
            for (com.xjzb.rts.core.Game.Ent e : g.ents)
                if (e.type.tiles == 0
                        && !g.passMini((int) (e.x / 8), (int) (e.y / 8))) stranded++;
            if (m.economy && g.minerals.isEmpty()) ecoMiss++;
        }

        ok &= n >= 15 && indexMismatch == 0 && badMap == 0 && badRace == 0
                && unknownUnits == 0 && badKind == 0 && noEnemyHall == 0
                && noPlayerHall == 0 && badProtect == 0 && offMap == 0
                && blocked == 0 && stranded == 0 && ecoMiss == 0;
        sb.append(" missions=").append(n)
          .append(" index=").append(indexMismatch)
          .append(" map=").append(badMap)
          .append(" race=").append(badRace)
          .append(" unit=").append(unknownUnits)
          .append(" kind=").append(badKind)
          .append(" enemyHall=").append(noEnemyHall)
          .append(" playerHall=").append(noPlayerHall)
          .append(" protect=").append(badProtect)
          .append(" offMap=").append(offMap)
          .append(" blocked=").append(blocked)
          .append(" stranded=").append(stranded)
          .append(" economy=").append(ecoMiss);
        System.out.println("  campaign walk" + sb + " PASS=" + ok);
    }
    /**
     * v2.30: lockstep. The point of the whole batch is that two peers consume
     * the same commands in the same order on the same turn, so every assertion
     * below is about order and gating rather than about netcode.
     *
     *  #1 canonical order -- three different submission orders must release in
     *     one identical order, or the two simulations drift;
     *  #2 the canonical order is player id ascending;
     *  #3 a turn with a silent player is not ready and does not advance;
     *  #4 an empty report is a heartbeat, not a no-op: without it the match
     *     stalls forever;
     *  #5 a duplicate packet cannot run a command twice;
     *  #6 the wire round-trips, including a command that carries an index list;
     *  #7 a malformed line yields null instead of throwing;
     *  #8 a desync is detected and pinned to the turn it started;
     *  #9 a whole session serialises into a replay body, and that body drives
     *     the SAME stateHash sequence the lockstep run produced. This is the
     *     one that ties the network layer to the determinism the [v220] replay
     *     assertion already established.
     */
    static void v230Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- #1/#2: canonical order is independent of arrival order --------
        // A player reports ONCE per turn (a second report is a duplicate, see
        // #5), so canonical order is tested with one command per player across
        // three players. The same three commands are submitted in four
        // different arrival orders and must release in one identical order.
        String[][] arrivals = {
            {"A", "B", "C"},
            {"C", "B", "A"},
            {"B", "C", "A"},
            {"C", "A", "B"},
        };
        String order0 = null;
        boolean reorderSame = true;
        for (int a = 0; a < arrivals.length; a++) {
            com.xjzb.rts.core.Lockstep ls = new com.xjzb.rts.core.Lockstep(3);
            for (String piece : arrivals[a]) {
                if (piece.equals("A")) ls.submit(0, "move 0,1 400 400");
                else if (piece.equals("B")) ls.submit(1, "train 3 marine");
                else ls.submit(2, "build 2 barracks 500 500");
            }
            java.util.List<com.xjzb.rts.core.Lockstep.Cmd> out = ls.release();
            StringBuilder sig = new StringBuilder();
            for (com.xjzb.rts.core.Lockstep.Cmd c : out)
                sig.append(c.player).append(':').append(c.cmd).append('|');
            if (a == 0) order0 = sig.toString();
            else if (!sig.toString().equals(order0)) reorderSame = false;
        }
        String want = "0:move 0,1 400 400|1:train 3 marine|2:build 2 barracks 500 500|";
        boolean canonical = reorderSame && want.equals(order0);
        ok &= canonical;
        sb.append(" canonical=").append(canonical);

        // ---- #3: a silent player blocks the turn --------------------------
        com.xjzb.rts.core.Lockstep gate = new com.xjzb.rts.core.Lockstep(2);
        gate.submit(0, "move 0 100 100");
        boolean half = !gate.ready() && gate.release().isEmpty() && gate.turn == 0;
        gate.submit(1, "");
        boolean full = gate.ready();
        java.util.List<com.xjzb.rts.core.Lockstep.Cmd> one = gate.release();
        boolean advanced = gate.turn == 1 && one.size() == 1
                && one.get(0).cmd.equals("move 0 100 100");
        ok &= half && full && advanced;
        sb.append(" waitSlow=").append(half).append(" ready=").append(full)
          .append(" advance=").append(advanced);

        // ---- #4: an empty heartbeat still counts as a report ---------------
        com.xjzb.rts.core.Lockstep quiet = new com.xjzb.rts.core.Lockstep(2);
        quiet.submit(0, "");
        quiet.submit(1, "");
        boolean beat = quiet.ready() && quiet.release().isEmpty() && quiet.turn == 1;
        ok &= beat;
        sb.append(" heartbeat=").append(beat);

        // ---- #5: duplicates and out-of-order heartbeats ---------------------
        // Two rules, and the second one was a real bug: a genuine duplicate
        // packet must not run a command twice, AND a heartbeat that arrives
        // BEFORE the real command (a reordering link does this) must not
        // suppress it -- storing the empty placeholder and dropping the order
        // would silently desync one machine from the other.
        com.xjzb.rts.core.Lockstep dup = new com.xjzb.rts.core.Lockstep(2);
        dup.submit(0, "move 0 100 100");
        dup.submit(0, "move 0 200 200");   // second report ignored
        dup.submit(1, "");
        java.util.List<com.xjzb.rts.core.Lockstep.Cmd> dl = dup.release();
        boolean once = dl.size() == 1 && dl.get(0).cmd.equals("move 0 100 100");

        com.xjzb.rts.core.Lockstep rw = new com.xjzb.rts.core.Lockstep(2);
        rw.submit(0, "");                              // heartbeat lands first
        rw.submit(0, "build 4 barracks 300 300");      // real order lands second
        rw.submit(1, "");
        java.util.List<com.xjzb.rts.core.Lockstep.Cmd> rl = rw.release();
        boolean keepOrder = rl.size() == 1
                && rl.get(0).cmd.equals("build 4 barracks 300 300");
        // and the other way round: the heartbeat cannot overwrite the order
        com.xjzb.rts.core.Lockstep rw2 = new com.xjzb.rts.core.Lockstep(2);
        rw2.submit(0, "build 4 barracks 300 300");
        rw2.submit(0, "");
        rw2.submit(1, "");
        java.util.List<com.xjzb.rts.core.Lockstep.Cmd> rl2 = rw2.release();
        boolean keepOrder2 = rl2.size() == 1
                && rl2.get(0).cmd.equals("build 4 barracks 300 300");
        ok &= once && keepOrder && keepOrder2;
        sb.append(" dedup=").append(once)
          .append(" heartbeatFirst=").append(keepOrder)
          .append(" heartbeatLast=").append(keepOrder2);

        // ---- #6: the wire round-trips, heartbeat included -------------------
        // The heartbeat is the message every peer sends every single turn, so
        // it is the one that must survive the wire. It encodes with no trailing
        // field ("L 5 1"), and an earlier decode() that required a third field
        // dropped it -- which is a peer that has nothing to say looking exactly
        // like a peer that is not there.
        String complex = "build 0,2,5 barracks 640 480";
        com.xjzb.rts.core.Lockstep.Cmd enc = new com.xjzb.rts.core.Lockstep.Cmd(417, 3, complex);
        com.xjzb.rts.core.Lockstep.Cmd dec = com.xjzb.rts.core.Lockstep.decode(enc.toString());
        com.xjzb.rts.core.Lockstep.Cmd beatWire = com.xjzb.rts.core.Lockstep.decode(
                com.xjzb.rts.core.Lockstep.encode(5, 1, ""));
        boolean wire = dec != null && dec.turn == 417 && dec.player == 3
                && dec.cmd.equals(complex)
                && beatWire != null && beatWire.turn == 5 && beatWire.player == 1
                && beatWire.cmd.isEmpty();
        ok &= wire;
        sb.append(" wire=").append(wire);

        // ---- #7: garbage is refused, not thrown ----------------------------
        boolean tolerant = com.xjzb.rts.core.Lockstep.decode(null) == null
                && com.xjzb.rts.core.Lockstep.decode("") == null
                && com.xjzb.rts.core.Lockstep.decode("HELLO") == null
                && com.xjzb.rts.core.Lockstep.decode("L 12") == null
                && com.xjzb.rts.core.Lockstep.decode("L 12 0") != null
                && com.xjzb.rts.core.Lockstep.decode("L x 1 move 0 1 1") == null
                && com.xjzb.rts.core.Lockstep.decode("cmd 5 move 0 1 1") == null;
        ok &= tolerant;
        sb.append(" tolerant=").append(tolerant);

        // ---- #8: a desync is pinned to the turn it started -----------------
        com.xjzb.rts.core.Lockstep ds = new com.xjzb.rts.core.Lockstep(2);
        ds.reportHash(0, 10, 1111L);
        ds.reportHash(1, 10, 1111L);
        ds.reportHash(0, 11, 2222L);
        ds.reportHash(1, 11, 2222L);
        ds.reportHash(0, 12, 3333L);
        ds.reportHash(1, 12, 9999L);
        ds.reportHash(0, 13, 4444L);
        ds.reportHash(1, 13, 4444L);
        boolean pinned = ds.desyncTurn == 12;
        ok &= pinned;
        sb.append(" desync=").append(pinned).append("@").append(ds.desyncTurn);

        // ---- #9: a session IS a replay, and replays to the same states -----
        // Two peers run the same turns through the same command stream; the
        // session is then serialised and played back through loadReplay, and
        // every one-second stateHash sample must match.
        com.xjzb.rts.core.Game live = cleanGame("terran");
        com.xjzb.rts.core.Lockstep sess = new com.xjzb.rts.core.Lockstep(2);
        live.lockstep = sess;
        live.lockstepPlayer = 0;
        java.util.List<com.xjzb.rts.core.Game.Ent> scvs = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : live.ents)
            if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);
        java.util.List<Long> a = new ArrayList<>();
        // The harness stands in for the second machine. Both peers must report
        // every turn or update() refuses to advance (that is the gate), so
        // player 0 orders every 5 s and otherwise only sends the heartbeat.
        for (int t = 0; t < 30 * 40; t++) {
            if (t % 150 == 0 && !scvs.isEmpty())
                live.recordOrder("move", scvs, (400 + t) + " " + (400 + t));
            else
                sess.submit(0, "");
            sess.submit(1, "");
            live.update(1f / 30f);
            if (t % 30 == 29) a.add(live.stateHash());
        }
        boolean cmdsSeen = sess.commands().size() >= 3;

        String body = sess.serialize();
        com.xjzb.rts.core.Game back = cleanGame("terran");
        boolean loaded = back.loadReplay("XJZB-REPLAY-1\nmap " + mapId
                + " race terran difficulty 1\n" + body);
        java.util.List<Long> b = new ArrayList<>();
        for (int t = 0; t < 30 * 40; t++) {
            back.update(1f / 30f);
            if (t % 30 == 29) b.add(back.stateHash());
        }
        boolean sameSeq = a.size() == b.size() && a.size() >= 20;
        for (int i = 0; i < a.size() && sameSeq; i++)
            if (!a.get(i).equals(b.get(i))) sameSeq = false;
        boolean session = cmdsSeen && loaded && sameSeq;
        ok &= session;
        sb.append(" session=").append(session).append(" cmds=")
          .append(sess.commands().size()).append(" samples=").append(a.size());

        System.out.println("  lockstep" + sb + " PASS=" + ok);
    }
    /**
     * v2.31: two independent simulations, one hostile link.
     *
     * v2.30 proved a session's command stream replays to the same states on ONE
     * machine. That is necessary but not sufficient: it says nothing about two
     * machines that each own a Game and exchange orders over a wire with
     * latency, jitter and reordering. This walks exactly that -- two peers built
     * from the same map data but sharing no mutable state -- and compares their
     * state hashes.
     *
     * The comparison is PER TURN, not per frame, and that distinction is the
     * whole lesson of this assertion. A peer that is waiting for the other's
     * report is frozen on an earlier turn, so at any given FRAME the two are
     * legitimately at different points in the timeline and their hashes differ.
     * What must hold is that "the state after turn T" is the same on both
     * machines for every T they have both reached. (The first draft compared
     * per frame, which is a statement lockstep does not make and cannot keep.)
     *
     *  #1 two peers built independently start from the same hash;
     *  #2 with latency 0 they agree on every turn;
     *  #3 with latency 1 + jitter they agree on every turn;
     *  #4 with latency 2 + jitter + REORDERING they agree on every turn -- the
     *     one that matters, because "apply whatever arrived" is the bug a naive
     *     implementation ships with;
     *  #5 the two never drift apart: their turn difference stays bounded;
     *  #6 both peers' command logs are identical (canonical order is unique);
     *  #7 the two sessions serialise to the same replay body, so the match can
     *     be saved or handed to a spectator.
     */
    static void v231Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // Four link profiles, from friendly to actively hostile. The last two
        // also chop every line into random small byte chunks, so the command
        // has to survive a real byte stream (see LockstepLink.Hub.chop) rather
        // than the process-internal message boundaries the earlier profiles
        // enjoy. That is the case a TCP socket produces and a naive sender
        // breaks on.
        int[][] profiles = {
            {0, 0, 0, 0},          // latency, jitter, reorder, chop
            {1, 3, 0, 0},
            {2, 5, 1, 0},
            {2, 5, 1, 1},
            {3, 4, 0, 1},
        };
        boolean allSame = true, allLogs = true, allBodies = true, allBounded = true;
        int minTurns = Integer.MAX_VALUE;
        String detail = "";
        for (int pi = 0; pi < profiles.length; pi++) {
            int lat = profiles[pi][0], jit = profiles[pi][1];
            int reo = profiles[pi][2], chop = profiles[pi][3];
            com.xjzb.rts.core.LockstepLink.Hub hub =
                    new com.xjzb.rts.core.LockstepLink.Hub(2, lat, jit, reo != 0, 4242L);
            hub.chop = chop != 0;
            com.xjzb.rts.core.Game ga = cleanGame("terran");
            com.xjzb.rts.core.Game gb = cleanGame("terran");
            com.xjzb.rts.core.LockstepPeer pa = new com.xjzb.rts.core.LockstepPeer(
                    ga, 0, 2, hub.end(0));
            com.xjzb.rts.core.LockstepPeer pb = new com.xjzb.rts.core.LockstepPeer(
                    gb, 1, 2, hub.end(1));

            // #1: two independent constructions agree before any order
            boolean seed = ga.stateHash() == gb.stateHash();
            if (!seed) allSame = false;

            List<com.xjzb.rts.core.Game.Ent> scvs = new ArrayList<>();
            for (com.xjzb.rts.core.Game.Ent e : ga.ents)
                if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);

            // hash after each released turn, per peer
            java.util.Map<Integer, Long> byTurnA = new java.util.HashMap<>();
            java.util.Map<Integer, Long> byTurnB = new java.util.HashMap<>();
            for (int t = 0; t < 30 * 20; t++) {
                // player 0 orders every 5 s; both peers heartbeat otherwise
                String aCmd = "";
                if (t % 150 == 0 && !scvs.isEmpty()) {
                    int tx = 400 + (t / 150) * 40, ty = 400 + (t / 150) * 30;
                    aCmd = ga.commandFor("move", scvs, tx + " " + ty);
                }
                // The three phases are separated deliberately: both peers
                // receive, then both send, then both step. See LockstepPeer.
                // sendFrame() is a no-op once the peer has reported this turn,
                // so calling it every frame still puts exactly one report per
                // turn on the wire -- which is the protocol contract.
                pa.receiveFrame();
                pb.receiveFrame();
                pa.queue(aCmd);
                pa.sendFrame();
                pb.sendFrame();
                hub.tick();
                long ha = pa.stepFrame(1f / 30f);
                long hb = pb.stepFrame(1f / 30f);
                byTurnA.put(pa.turnsReleased(), ha);
                byTurnB.put(pb.turnsReleased(), hb);
                // #5: neither peer runs away from the other. The bound is the
                // worst-case delivery delay plus the two frame phases.
                if (Math.abs(pa.turnsReleased() - pb.turnsReleased()) > lat + jit + 3)
                    allBounded = false;
            }

            // #2/#3/#4: every turn both peers reached must hash the same
            int common = 0;
            for (java.util.Map.Entry<Integer, Long> e : byTurnA.entrySet()) {
                Long other = byTurnB.get(e.getKey());
                if (other == null) continue;
                common++;
                if (other.longValue() != e.getValue().longValue()) allSame = false;
            }
            if (common < 15) allSame = false;
            minTurns = Math.min(minTurns, common);

            // #6: identical command logs on the common prefix
            int n = Math.min(pa.commands().size(), pb.commands().size());
            for (int i = 0; i < n; i++) {
                com.xjzb.rts.core.Lockstep.Cmd x = pa.commands().get(i);
                com.xjzb.rts.core.Lockstep.Cmd y = pb.commands().get(i);
                if (x.turn != y.turn || x.player != y.player || !x.cmd.equals(y.cmd))
                    allLogs = false;
            }
            // #7: identical replay bodies
            if (!pa.session.serialize().equals(pb.session.serialize())) allBodies = false;
            if (pi == 0) detail = " turns=" + common + " cmds=" + pa.commands().size();
        }

        ok &= allSame && allLogs && allBodies && allBounded;
        sb.append(" samePerTurn=").append(allSame)
          .append(" boundedDrift=").append(allBounded)
          .append(" sameLog=").append(allLogs)
          .append(" sameReplay=").append(allBodies)
          .append(" minTurns=").append(minTurns).append(detail);

        System.out.println("  two peers" + sb + " PASS=" + ok);
    }
    /**
     * v2.32: framing a byte stream, and agreeing before the match starts.
     *
     *  #1 the line sequence does not depend on how the bytes were chopped --
     *     this is the whole reason the framing exists, and TCP gives no
     *     boundaries at all;
     *  #2 two messages in one feed, and one message split across feeds;
     *  #3 a partial line is withheld until it is complete, not delivered short;
     *  #4 CRLF is tolerated;
     *  #5 a matching handshake is accepted, and a mismatched one is refused
     *     with the offending field NAMED -- "cannot connect" tells a player
     *     nothing, "map mismatch: divide vs hunters" tells them what to fix;
     *  #6 race/difficulty differences are a warning, not a refusal;
     *  #7 end to end: a lockstep turn chopped into 3-byte pieces and fed
     *     through the stream decodes to exactly the same commands as a direct
     *     delivery.
     */
    static void v232Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- #1/#2/#3/#4: framing is independent of the chopping ------------
        // Include a multi-byte UTF-8 command so a split can land mid-character,
        // which is where a naive byte-oriented reader corrupts the text.
        String[] msgs = {"L 0 0 move 1,2,3,4 400 400", "L 0 1",
                         "L 1 0 build 2,5 barracks 中文坐标 640 480", "L 1 1"};
        java.io.ByteArrayOutputStream wire = new java.io.ByteArrayOutputStream();
        for (String m : msgs) wire.write(com.xjzb.rts.core.LockstepStream.encode(m));
        byte[] all = wire.toByteArray();

        int[][] chops = {{1}, {3}, {7}, {all.length}, {2, 5, 1, 9, 4}};
        String first = null;
        boolean chopSame = true;
        for (int[] plan : chops) {
            com.xjzb.rts.core.LockstepStream st = new com.xjzb.rts.core.LockstepStream();
            List<String> got = new ArrayList<>();
            int p = 0, ci = 0;
            while (p < all.length) {
                int n = Math.min(plan[ci % plan.length], all.length - p);
                st.feed(all, p, n);
                p += n;
                ci++;
                got.addAll(st.lines());
            }
            StringBuilder sig = new StringBuilder();
            for (String g : got) sig.append(g).append('|');
            if (first == null) first = sig.toString();
            else if (!sig.toString().equals(first)) chopSame = false;
        }
        boolean exact = first != null && first.equals(
                msgs[0] + "|" + msgs[1] + "|" + msgs[2] + "|" + msgs[3] + "|");
        ok &= chopSame && exact;
        sb.append(" framing=").append(chopSame && exact);

        // ---- #3: a partial line is withheld --------------------------------
        com.xjzb.rts.core.LockstepStream half = new com.xjzb.rts.core.LockstepStream();
        half.feed(com.xjzb.rts.core.LockstepStream.encode("L 2 0 move 0 5 5"));
        boolean gotFull = half.lines().size() == 1 && !half.hasPartial();
        com.xjzb.rts.core.LockstepStream part = new com.xjzb.rts.core.LockstepStream();
        part.feed("L 3 0 mov".getBytes("UTF-8"));
        boolean heldBack = part.lines().isEmpty() && part.hasPartial();
        part.feed("e 0 9 9\n".getBytes("UTF-8"));
        List<String> fin = part.lines();
        boolean completed = fin.size() == 1 && fin.get(0).equals("L 3 0 move 0 9 9");
        ok &= gotFull && heldBack && completed;
        sb.append(" partial=").append(gotFull && heldBack && completed);

        // ---- #4: CRLF ------------------------------------------------------
        com.xjzb.rts.core.LockstepStream crlf = new com.xjzb.rts.core.LockstepStream();
        crlf.feed("L 4 0 move 0 1 1\r\nL 4 1\r\n".getBytes("UTF-8"));
        List<String> cl = crlf.lines();
        boolean crOk = cl.size() == 2 && cl.get(0).equals("L 4 0 move 0 1 1")
                && cl.get(1).equals("L 4 1");
        ok &= crOk;
        sb.append(" crlf=").append(crOk);

        // ---- #5/#6: the handshake ------------------------------------------
        com.xjzb.rts.core.Handshake host = new com.xjzb.rts.core.Handshake(
                "2.32", "divide", 2, 777L, "terran", 1);
        com.xjzb.rts.core.Handshake rt = com.xjzb.rts.core.Handshake.decode(host.encode());
        boolean rtOk = rt != null && rt.version.equals("2.32") && rt.map.equals("divide")
                && rt.players == 2 && rt.seed == 777L && rt.race.equals("terran")
                && rt.difficulty == 1;
        boolean acceptOk = host.reject(rt) == null && host.warn(rt) == null;
        ok &= rtOk && acceptOk;
        sb.append(" handshake=").append(rtOk && acceptOk);

        // each fatal field, changed one at a time, must be refused BY NAME
        String[] fatals = {
            new com.xjzb.rts.core.Handshake("2.31", "divide", 2, 777L, "terran", 1).encode(),
            new com.xjzb.rts.core.Handshake("2.32", "hunters", 2, 777L, "terran", 1).encode(),
            new com.xjzb.rts.core.Handshake("2.32", "divide", 3, 777L, "terran", 1).encode(),
            new com.xjzb.rts.core.Handshake("2.32", "divide", 2, 999L, "terran", 1).encode(),
        };
        String[] wantWord = {"版本", "地图", "人数", "种子"};
        boolean allRefused = true;
        String seen = "";
        for (int i = 0; i < fatals.length; i++) {
            String why = host.reject(com.xjzb.rts.core.Handshake.decode(fatals[i]));
            if (why == null || !why.contains(wantWord[i])) allRefused = false;
            seen += " " + why;
        }
        ok &= allRefused;
        sb.append(" refuseByName=").append(allRefused);

        // a differing race or difficulty is only a warning
        com.xjzb.rts.core.Handshake soft = new com.xjzb.rts.core.Handshake(
                "2.32", "divide", 2, 777L, "zerg", 2);
        boolean softOk = host.reject(soft) == null && host.warn(soft) != null;
        // a malformed handshake is refused rather than thrown
        boolean badOk = host.reject(null) != null
                && com.xjzb.rts.core.Handshake.decode("H version") != null
                && com.xjzb.rts.core.Handshake.decode("garbage") == null
                && com.xjzb.rts.core.Handshake.decode("H players x") == null;
        ok &= softOk && badOk;
        sb.append(" soft=").append(softOk).append(" bad=").append(badOk);

        // ---- #7: a whole turn through 3-byte framing -----------------------
        // One peer's real command goes onto a byte stream in 3-byte pieces and
        // must come out the far side as the identical command.
        com.xjzb.rts.core.Game ga = cleanGame("terran");
        List<com.xjzb.rts.core.Game.Ent> scvs = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : ga.ents)
            if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);
        String cmd = ga.commandFor("move", scvs, "512 384");
        byte[] framed = com.xjzb.rts.core.LockstepStream.encode(
                com.xjzb.rts.core.Lockstep.encode(0, 0, cmd));
        com.xjzb.rts.core.LockstepStream st = new com.xjzb.rts.core.LockstepStream();
        List<String> out = new ArrayList<>();
        for (int p = 0; p < framed.length; p += 3) {
            st.feed(framed, p, Math.min(3, framed.length - p));
            out.addAll(st.lines());
        }
        com.xjzb.rts.core.Lockstep.Cmd c = out.size() == 1
                ? com.xjzb.rts.core.Lockstep.decode(out.get(0)) : null;
        boolean e2e = c != null && c.turn == 0 && c.player == 0 && c.cmd.equals(cmd);
        ok &= e2e;
        sb.append(" endToEnd=").append(e2e);

        System.out.println("  framing/handshake" + sb + " PASS=" + ok);
    }
    /**
     * v2.33: finding a room, and agreeing to start one.
     *
     *  #1 a beacon round-trips, and the beacon's own fields become the
     *     handshake both peers will check;
     *  #2 anything that is not a beacon of this build is IGNORED, not thrown:
     *     the broadcast domain carries other rooms, other versions and
     *     unrelated traffic, and a listener that errored on any of it would
     *     drop the lobby whenever a colleague's phone joined the wifi;
     *  #3 a beacon from another version is found but not joinable;
     *  #4 a joiner takes the lowest free seat;
     *  #5 a seat freed by a departure is the next one taken -- without this the
     *     room reads "4/4 connected" while the start button stays dead forever;
     *  #6 the start gate needs everyone connected AND ready AND at least two;
     *  #7 a match starts at most once, so a double tap cannot launch two;
     *  #8 after the match starts a lost peer no longer frees a seat (that case
     *     belongs to Lockstep's ready-gate, which freezes both machines on the
     *     same turn instead of silently changing the roster);
     *  #9 the lobby's own numbers, run through Handshake on both sides, are
     *     mutually accepted -- the last join between this layer and v2.32's.
     */
    static void v233Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- #1: beacon round-trip, and beacon -> handshake ----------------
        com.xjzb.rts.core.LanBeacon host = new com.xjzb.rts.core.LanBeacon(
                "房主的小米", "divide", 2, 41234, "2.33", 888L, 1);
        com.xjzb.rts.core.LanBeacon got =
                com.xjzb.rts.core.LanBeacon.decode(host.encode());
        boolean rt = got != null && got.host.equals("房主的小米") && got.map.equals("divide")
                && got.players == 2 && got.port == 41234 && got.version.equals("2.33")
                && got.seed == 888L && got.difficulty == 1;
        ok &= rt;
        sb.append(" beacon=").append(rt);

        // ---- #2: garbage is ignored, never thrown --------------------------
        String[] junk = {
            null, "", "hello", "XJZB-LAN-1", "XJZB-LAN-1 host",
            "XJZB-LAN-1 host x map y players z port 1 version 2.33 seed 1 difficulty 1",
            "XJZB-LAN-2 host x map y players 2 port 1 version 2.33 seed 1 difficulty 1",
            "XJZB-LAN-1 map divide port 41234 version 2.33 seed 1 difficulty 1",
        };
        boolean ignored = true;
        for (String s : junk) if (com.xjzb.rts.core.LanBeacon.decode(s) != null) ignored = false;
        ok &= ignored;
        sb.append(" ignoreJunk=").append(ignored);

        // ---- #3: another build's room is visible but not joinable ----------
        com.xjzb.rts.core.LanBeacon old = com.xjzb.rts.core.LanBeacon.decode(
                new com.xjzb.rts.core.LanBeacon("隔壁", "hunters", 2, 4000,
                        "2.31", 5L, 1).encode());
        boolean versionGate = old != null && !old.joinable("2.33")
                && host.joinable("2.33");
        ok &= versionGate;
        sb.append(" versionGate=").append(versionGate);

        // ---- #4: a joiner takes the lowest free seat -----------------------
        com.xjzb.rts.core.Lobby lob = new com.xjzb.rts.core.Lobby(4);
        int a = lob.join("A"), b = lob.join("B"), c = lob.join("C");
        boolean seated = a == 0 && b == 1 && c == 2 && lob.connectedCount() == 3;
        ok &= seated;
        sb.append(" seat=").append(seated);

        // ---- #5: a freed seat is reused ------------------------------------
        lob.onPeerLost(1);
        int d = lob.join("D");
        boolean reuse = d == 1 && lob.connectedCount() == 3
                && lob.slots.get(1).name.equals("D") && !lob.slots.get(1).ready;
        ok &= reuse;
        sb.append(" reuseSeat=").append(reuse);

        // ---- #6: the start gate --------------------------------------------
        boolean notReady = !lob.canStart();
        lob.setReady(0, true);
        lob.setReady(1, true);
        boolean stillNot = !lob.canStart();          // C has not readied
        lob.setReady(2, true);
        boolean ready = lob.canStart();
        String why = new com.xjzb.rts.core.Lobby(4).blockedReason();
        boolean explains = why != null && why.contains("至少");
        ok &= notReady && stillNot && ready && explains;
        sb.append(" gate=").append(notReady && stillNot && ready);

        // ---- #7: start succeeds at most once -------------------------------
        boolean first = lob.start();
        boolean second = !lob.start();
        ok &= first && second;
        sb.append(" onceOnly=").append(first && second);

        // ---- #8: after the start, a loss does not free a seat --------------
        int before = lob.connectedCount();
        lob.onPeerLost(0);
        boolean frozen = lob.connectedCount() == before;
        ok &= frozen;
        sb.append(" postStartFrozen=").append(frozen);

        // ---- #9: the lobby's numbers are a valid handshake pair ------------
        com.xjzb.rts.core.Handshake hh = host.handshake("terran");
        com.xjzb.rts.core.Handshake cc = com.xjzb.rts.core.LanBeacon
                .decode(host.encode()).handshake("terran");
        boolean linked = hh.reject(cc) == null && hh.version.equals("2.33")
                && hh.players == 2 && hh.seed == 888L;
        ok &= linked;
        sb.append(" handshakeLinked=").append(linked);

        System.out.println("  lobby/discovery" + sb + " PASS=" + ok);
    }
    /**
     * v2.34: what happens when a peer never comes back.
     *
     * v2.31 made a slow peer freeze the match, which is right for a hiccup and
     * wrong for a departure: two machines sitting on the same turn forever is
     * indistinguishable from a hung game. This adds the rule and the timeout.
     *
     *  #1 the stall counter climbs while a turn is incomplete and resets the
     *     moment it releases;
     *  #2 the stalled player is NAMED, so the message can say who went quiet;
     *  #3 stalledOut() fires exactly at the limit, not a frame early;
     *  #4 forfeit records the result and can only happen once;
     *  #5 after a forfeit the release no longer waits for the departed player,
     *     so the match can reach a result instead of hanging;
     *  #6 a peer that returns inside the limit is not a quitter -- the counter
     *     is a CONTINUOUS wait, not a total, so a shaky connection across a
     *     whole match can never accumulate into a forfeit;
     *  #7 end to end: two real peers, one goes silent, and the survivor
     *     declares the forfeit at the limit -- while every frame before that
     *     was still perfectly in sync.
     */
    static void v234Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- #1/#2: the counter and the named player -----------------------
        com.xjzb.rts.core.Lockstep ls = new com.xjzb.rts.core.Lockstep(2);
        boolean startZero = ls.stallTurns == 0 && ls.stalledPlayer() == 0;
        ls.noteStall();
        ls.noteStall();
        boolean climbed = ls.stallTurns == 2 && ls.stalledPlayer() == 0;
        ls.submit(0, "");
        boolean named = ls.stalledPlayer() == 1;
        ls.submit(1, "");
        ls.release();
        // After a release the counter is back to zero. The NEXT turn has nobody
        // reported yet, so stalledPlayer() names player 0 -- that is the fresh
        // turn waiting for both peers, not a leftover from the last one.
        boolean reset = ls.stallTurns == 0 && ls.stalledPlayer() == 0;
        ok &= startZero && climbed && named && reset;
        sb.append(" counter=").append(startZero && climbed && named && reset);

        // ---- #3: the limit fires exactly on the limit ----------------------
        com.xjzb.rts.core.Lockstep lim = new com.xjzb.rts.core.Lockstep(2);
        lim.submit(0, "");
        int limit = com.xjzb.rts.core.Lockstep.STALL_LIMIT;
        for (int i = 0; i < limit - 1; i++) lim.noteStall();
        boolean beforeLimit = !lim.stalledOut(limit);
        lim.noteStall();
        boolean atLimit = lim.stalledOut(limit);
        ok &= beforeLimit && atLimit;
        sb.append(" limit@").append(limit).append("=").append(beforeLimit && atLimit);

        // ---- #4/#5: forfeit records once and unblocks the release ----------
        boolean f1 = lim.forfeit(1);
        boolean f2 = !lim.forfeit(1);
        boolean recorded = lim.forfeitLoser == 1 && lim.forfeitWinner == 0
                && lim.isDropped(1) && !lim.isDropped(0);
        boolean unblocked = lim.ready();
        java.util.List<com.xjzb.rts.core.Lockstep.Cmd> rel = lim.release();
        boolean advanced = lim.turn == 1;
        ok &= f1 && f2 && recorded && unblocked && advanced;
        sb.append(" forfeit=").append(f1 && f2 && recorded)
          .append(" unblock=").append(unblocked && advanced);

        // ---- #6: a peer that returns inside the limit is not a quitter -----
        com.xjzb.rts.core.Lockstep flaky = new com.xjzb.rts.core.Lockstep(2);
        // 200 frames of silence, then a full turn, three times over
        for (int round = 0; round < 3; round++) {
            for (int i = 0; i < 200; i++) flaky.noteStall();
            flaky.submit(0, "");
            flaky.submit(1, "");
            flaky.release();
        }
        boolean survived = flaky.forfeitLoser < 0 && flaky.turn == 3 && flaky.stallTurns == 0;
        ok &= survived;
        sb.append(" flakyOk=").append(survived);

        // ---- #7: two real peers, one goes silent ---------------------------
        com.xjzb.rts.core.LockstepLink.Hub hub =
                new com.xjzb.rts.core.LockstepLink.Hub(2, 2, 4, true, 31337L);
        hub.chop = true;
        com.xjzb.rts.core.Game ga = cleanGame("terran");
        com.xjzb.rts.core.Game gb = cleanGame("terran");
        com.xjzb.rts.core.LockstepPeer pa = new com.xjzb.rts.core.LockstepPeer(
                ga, 0, 2, hub.end(0));
        com.xjzb.rts.core.LockstepPeer pb = new com.xjzb.rts.core.LockstepPeer(
                gb, 1, 2, hub.end(1));
        List<com.xjzb.rts.core.Game.Ent> scvs = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : ga.ents)
            if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);

        int goSilentAt = 60;
        int forfeitAt = -1;
        int stallAtForfeit = -1;
        boolean inSyncBefore = true;
        // A snapshot of "the state after turn T" per peer, exactly as [v231]
        // compares them: per FRAME the two are legitimately at different points
        // while one waits for the other, so the honest check is per turn.
        java.util.Map<Integer, Long> turnsA = new java.util.HashMap<>();
        java.util.Map<Integer, Long> turnsB = new java.util.HashMap<>();
        for (int t = 0; t < 30 * 16; t++) {
            String aCmd = "";
            if (t % 150 == 0 && !scvs.isEmpty())
                aCmd = ga.commandFor("move", scvs, (400 + t / 150 * 40) + " 400");
            pa.receiveFrame();
            if (t < goSilentAt) pb.receiveFrame();   // B stops talking after 2 s
            pa.queue(aCmd);
            pa.sendFrame();
            if (t < goSilentAt) pb.sendFrame();
            hub.tick();
            long ha = pa.stepFrame(1f / 30f);
            turnsA.put(pa.turnsReleased(), ha);
            if (t < goSilentAt) {
                long hb = pb.stepFrame(1f / 30f);
                turnsB.put(pb.turnsReleased(), hb);
            } else {
                // A notices B is gone and declares the forfeit at the limit
                if (pa.session.stalledOut(com.xjzb.rts.core.Lockstep.STALL_LIMIT)
                        && pa.session.forfeit(1)) {
                    forfeitAt = t;
                    stallAtForfeit = pa.session.stallTurns;
                }
            }
        }
        // every turn both peers reached while B was alive must hash the same
        for (java.util.Map.Entry<Integer, Long> e : turnsA.entrySet()) {
            Long other = turnsB.get(e.getKey());
            if (other != null && other.longValue() != e.getValue().longValue())
                inSyncBefore = false;
        }
        int limit2 = com.xjzb.rts.core.Lockstep.STALL_LIMIT;
        int waited = forfeitAt - goSilentAt;
        boolean declared = forfeitAt >= goSilentAt
                && pa.session.forfeitLoser == 1 && pa.session.forfeitWinner == 0;
        // The precise boundary is pinned by the deterministic unit check above
        // (#3). Here the honest invariant is about the COUNTER, not about the
        // wall frame: the forfeit must be declared at the exact frame the
        // continuous stall reaches the limit. `waited` (frames since B went
        // quiet) is a frame or two SHORT of the limit, because A had already
        // been blocked on B's last in-flight report before the silence began --
        // which is the correct behaviour, not an early forfeit.
        boolean timely = forfeitAt >= 0 && stallAtForfeit == limit2
                && waited >= limit2 - 30 && waited <= limit2 + 5;
        // After the forfeit the survivor must be able to keep playing, which is
        // the point: a departed peer cannot leave the match stuck. turn > 1
        // proves turns released after the declaration. (ready() is checked on
        // the NEXT frame's boundary, so it is not the right thing to read here.)
        boolean finished = pa.session.turn > 1 && pa.session.forfeitLoser == 1;
        ok &= inSyncBefore && declared && timely && finished;
        sb.append(" dropInSync=").append(inSyncBefore)
          .append(" declared=").append(declared)
          .append(" waited=").append(waited).append("/").append(limit2)
          .append(" stallAt=").append(stallAtForfeit)
          .append(" timely=").append(timely)
          .append(" finished=").append(finished);

        System.out.println("  stall/forfeit" + sb + " PASS=" + ok);
    }
    /**
     * v2.36: can every mission actually be won?
     *
     * [v229] proves each mission's DATA is well-formed -- keys exist, coordinates
     * are on the map, buildings sit on clear ground. None of that says a level
     * can be WON. The trap is the one the map pipeline was built around: if the
     * player's base and an enemy base sit on separate landmasses the player can
     * never reach that enemy, and a destroyAll objective becomes unreachable no
     * matter how well the player plays. The shipped map pool was filtered for
     * exactly this, but a mission authors its OWN coordinates, so the property
     * has to be checked per mission rather than inherited from the map.
     *
     * This is not hypothetical: it found m05. That level ships a second enemy
     * outpost whose hatchery snapped onto a tile inside a 28-minitile pocket
     * that the player's region does not contain, while m05's objective is
     * destroyAll -- so the level could not be completed at all. It had been that
     * way since the level was authored.
     *
     * The reachability test is the project's own: the same 8-connectivity plus
     * one-cell dilation that pipeline_maps.py's start-connectivity gate uses.
     * Game.findPath is deliberately NOT used here -- it is a short-range unit
     * pather with a 60000-expansion cap, and across a 128x128 map it gives up
     * and reports "no path" for two bases that are plainly connected.
     *
     * Scope, on purpose: every destroyAll level is checked, because its objective
     * IS reachability. A survive or protect level (m01, m08, m12) is not checked,
     * and that is not a hole: m01's enemy reaches the player by SCRIPTED wave
     * spawns at a fixed point rather than by pathing (see Mission.fire), so its
     * landmass layout does not gate the level. m01 does sit on two landmasses,
     * which is fine -- the player is not required to go anywhere.
     */
    static void v236Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();
        int checked = 0, destroyLevels = 0, unreachable = 0;
        StringBuilder bad = new StringBuilder();

        for (String row : Files.readAllLines(Paths.get(ASSETS + "/missions/index.txt"))) {
            String[] f = row.trim().split("\\|");
            if (f.length < 3) continue;
            String id = f[0];
            com.xjzb.rts.core.Game g = missionGame(id);
            if (g == null || g.mission == null) continue;

            boolean destroy = false;
            for (com.xjzb.rts.core.Mission.Objective o : g.mission.objectives)
                if ("destroyAll".equals(o.kind)) destroy = true;
            if (!destroy) continue;
            destroyLevels++;

            // the player's region, using the pipeline's connectivity rule
            com.xjzb.rts.core.Game.Ent hall = null;
            for (com.xjzb.rts.core.Game.Ent e : g.ents)
                if (e.team == 0 && hall == null && ("cc".equals(e.type.key)
                        || "hatchery".equals(e.type.key) || "nexus".equals(e.type.key)))
                    hall = e;
            if (hall == null) { unreachable++; bad.append(" ").append(id).append("(noHall)"); continue; }

            int w = g.wMini, h = g.hMini;
            boolean[] usable = new boolean[w * h];
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++) {
                    if (g.passMini(x, y)) { usable[y * w + x] = true; continue; }
                    for (int dy = -1; dy <= 1 && !usable[y * w + x]; dy++)
                        for (int dx = -1; dx <= 1; dx++) {
                            int X = x + dx, Y = y + dy;
                            if (X < 0 || Y < 0 || X >= w || Y >= h) continue;
                            if (g.passMini(X, Y)) { usable[y * w + x] = true; break; }
                        }
                }
            int[] start = g.nearestPassMini((int) (hall.x / 8), (int) (hall.y / 8), 40);
            boolean[] seen = new boolean[w * h];
            java.util.ArrayDeque<int[]> q = new java.util.ArrayDeque<>();
            q.add(start);
            seen[start[1] * w + start[0]] = true;
            int[][] D = {{1,0},{-1,0},{0,1},{0,-1},{1,1},{1,-1},{-1,1},{-1,-1}};
            while (!q.isEmpty()) {
                int[] p = q.poll();
                for (int[] d : D) {
                    int X = p[0] + d[0], Y = p[1] + d[1];
                    if (X < 0 || Y < 0 || X >= w || Y >= h) continue;
                    if (seen[Y * w + X] || !usable[Y * w + X]) continue;
                    seen[Y * w + X] = true;
                    q.add(new int[]{X, Y});
                }
            }

            // every enemy hatchery must sit in the player's region
            for (com.xjzb.rts.core.Game.Ent e : g.ents) {
                if (e.team != 1 || !"hatchery".equals(e.type.key)) continue;
                checked++;
                // the hatchery's own tile is blocked by its own footprint, so
                // snap out of it before testing membership
                int[] fs = g.nearestPassMini((int) (e.x / 8), (int) (e.y / 8), 40);
                if (fs == null || !seen[fs[1] * w + fs[0]]) {
                    unreachable++;
                    bad.append(" ").append(id).append("@")
                       .append((int) e.x).append(",").append((int) e.y);
                }
            }
        }

        ok &= destroyLevels >= 11 && checked >= 12 && unreachable == 0;
        sb.append(" destroyLevels=").append(destroyLevels)
          .append(" hallsChecked=").append(checked)
          .append(" unreachable=").append(unreachable);
        if (bad.length() > 0) sb.append(" bad:").append(bad);
        System.out.println("  mission reachability" + sb + " PASS=" + ok);
    }
    /**
     * v2.37: the Android network layer, end to end over real loopback sockets.
     *
     * com.xjzb.rts.net deliberately imports nothing from Android -- it is
     * java.net plus core -- which means the shipped host/join path can be
     * exercised here exactly as the phone will run it: a real ServerSocket, a
     * real Socket, the real handshake exchange, and a real match on top. That is
     * worth more than any amount of in-process faking, because the failures this
     * catches (a report that never goes on the wire, a handshake that admits an
     * incompatible peer) only exist once two sockets are involved.
     *
     *  #1 host + join complete, and both sides get a link;
     *  #2 the joiner is seated in the lobby, and the host's beacon carries the
     *     REAL bound port (the OS picked it, so a stale beacon means nobody can
     *     ever connect);
     *  #3 a command issued through Game.recordOrder reaches the other peer. This
     *     is the integration bug this assertion was written for: recordOrder
     *     submits straight into the session, so a peer that only ever sent its
     *     own queue() would apply the order locally and never publish it -- a
     *     desync with a delay, and invisible in every earlier test;
     *  #4 an incompatible version is refused at the door, with the field named,
     *     and is NOT given a lobby seat;
     *  #5 a full room refuses the next joiner instead of overfilling.
     */
    static void v237Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        final String version = "2.37";

        // ---- #1/#2: host and join over real loopback ------------------------
        final com.xjzb.rts.core.Lobby lobby = new com.xjzb.rts.core.Lobby(4);
        com.xjzb.rts.net.LanHost host = new com.xjzb.rts.net.LanHost(
                lobby, new com.xjzb.rts.net.LanHost.Room() {
                    @Override public com.xjzb.rts.core.LanBeacon beacon() {
                        com.xjzb.rts.core.LanBeacon b = new com.xjzb.rts.core.LanBeacon(
                                "127.0.0.1", "bloodbath", 2, 0, version, 4242L, 1);
                        return b;
                    }
                    @Override public String version() { return version; }
                });
        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanHost.Connected>
                admitted = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.atomic.AtomicReference<String> hostErr =
                new java.util.concurrent.atomic.AtomicReference<>();
        // The host writes "Y" to the joiner BEFORE it runs this callback, so the
        // joiner can be back before the host has recorded the admission. Wait on
        // the callback as well, or the seat check races the accept thread.
        final java.util.concurrent.CountDownLatch hostAdmitted =
                new java.util.concurrent.CountDownLatch(1);
        int port = host.start(new com.xjzb.rts.net.LanHost.Callback() {
            @Override public void onConnected(com.xjzb.rts.net.LanHost.Connected c) {
                admitted.set(c);
                hostAdmitted.countDown();
            }
            @Override public void onError(String message) {
                hostErr.set(message);
                hostAdmitted.countDown();
            }
        });
        boolean bound = port > 0 && host.beacon().port == port;
        sb.append(" bound=").append(bound).append("@").append(port);

        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanJoin.Result>
                joined = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.CountDownLatch done = new java.util.concurrent.CountDownLatch(1);
        com.xjzb.rts.net.LanJoin.connect(host.beacon(), version, "terran",
                r -> { joined.set(r); done.countDown(); });
        boolean answered = done.await(6, java.util.concurrent.TimeUnit.SECONDS);
        hostAdmitted.await(6, java.util.concurrent.TimeUnit.SECONDS);
        com.xjzb.rts.net.LanJoin.Result jr = joined.get();
        boolean linked = answered && jr != null && jr.ok() && jr.error == null;
        boolean seated = linked && lobby.connectedCount() == 2
                && admitted.get() != null && admitted.get().slot >= 0;
        ok &= bound && linked && seated;
        sb.append(" joinOk=").append(linked).append(" seated=").append(seated);

        // ---- #3: a recordOrder command must reach the other peer ------------
        // The host plays player 0 and the joiner player 1. The host's order is
        // issued through Game.recordOrder (the path the real UI uses), NOT
        // through the peer's queue, so this only passes if sendFrame publishes
        // what the GAME submitted.
        boolean crossed = false;
        if (seated) {
            com.xjzb.rts.core.Game ga = cleanGame("terran");
            com.xjzb.rts.core.Game gb = cleanGame("terran");
            com.xjzb.rts.net.TcpLink la = admitted.get().link;
            com.xjzb.rts.net.TcpLink lb = jr.link;
            com.xjzb.rts.core.LockstepPeer pa = new com.xjzb.rts.core.LockstepPeer(ga, 0, 2, la);
            com.xjzb.rts.core.LockstepPeer pb = new com.xjzb.rts.core.LockstepPeer(gb, 1, 2, lb);
            List<com.xjzb.rts.core.Game.Ent> scvs = new ArrayList<>();
            for (com.xjzb.rts.core.Game.Ent e : ga.ents)
                if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);
            // the command the UI would issue
            ga.recordOrder("move", scvs, "512 384");
            for (int t = 0; t < 40; t++) {
                pa.receiveFrame();
                pb.receiveFrame();
                pa.sendFrame();
                pb.sendFrame();
                pa.stepFrame(1f / 30f);
                pb.stepFrame(1f / 30f);
                Thread.sleep(1);
            }
            // B must have released the SAME command A issued
            boolean sawIt = false;
            for (com.xjzb.rts.core.Lockstep.Cmd c : pb.commands())
                if (c.player == 0 && c.cmd.startsWith("move ")) sawIt = true;
            boolean sameTurn = pa.turnsReleased() == pb.turnsReleased()
                    && pa.turnsReleased() >= 3;
            crossed = sawIt && sameTurn;
            sb.append(" orderCrossed=").append(sawIt).append(" turns=").append(pa.turnsReleased());
            la.close();
            lb.close();
        }
        ok &= crossed;
        host.stop();
        lobby.slots.clear();

        // ---- #4: an incompatible version is refused, with the field named ---
        final com.xjzb.rts.core.Lobby lobby2 = new com.xjzb.rts.core.Lobby(4);
        com.xjzb.rts.net.LanHost host2 = new com.xjzb.rts.net.LanHost(
                lobby2, new com.xjzb.rts.net.LanHost.Room() {
                    @Override public com.xjzb.rts.core.LanBeacon beacon() {
                        return new com.xjzb.rts.core.LanBeacon(
                                "127.0.0.1", "bloodbath", 2, 0, version, 4242L, 1);
                    }
                    @Override public String version() { return version; }
                });
        final java.util.concurrent.atomic.AtomicReference<String> err2 =
                new java.util.concurrent.atomic.AtomicReference<>();
        host2.start(new com.xjzb.rts.net.LanHost.Callback() {
            @Override public void onConnected(com.xjzb.rts.net.LanHost.Connected c) { }
            @Override public void onError(String message) { err2.set(message); }
        });
        // the host itself holds seat 0, so "no seat for the refused peer" means
        // the roster does not grow, not that it is empty
        int seatsBefore = lobby2.connectedCount();
        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanJoin.Result>
                bad = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.CountDownLatch done2 = new java.util.concurrent.CountDownLatch(1);
        com.xjzb.rts.net.LanJoin.connect(host2.beacon(), "2.30", "terran",
                r -> { bad.set(r); done2.countDown(); });
        done2.await(6, java.util.concurrent.TimeUnit.SECONDS);
        com.xjzb.rts.net.LanJoin.Result br = bad.get();
        boolean refused = br != null && !br.ok() && br.error != null
                && br.error.contains("版本");
        boolean noSeat = lobby2.connectedCount() == seatsBefore;
        ok &= refused && noSeat;
        sb.append(" refuseVersion=").append(refused).append(" noSeat=").append(noSeat);
        host2.stop();

        System.out.println("  android net" + sb + " PASS=" + ok);
    }
    /**
     * v2.38: a departed peer must END the match, not freeze it.
     *
     * v2.34 asserted the timeout rules and v2.37 asserted the socket layer, but
     * neither made the app actually DO anything with them: nothing called
     * forfeit(), so on a real device a peer who killed the app still left the
     * survivor on a turn that could never complete. Tested logic that nothing
     * invokes is not a feature, and this is the assertion that keeps the two
     * halves joined.
     *
     *  #1 the immediate signal: a CLOSED wire declares the peer gone on the
     *     first check, without waiting out the ten-second timer -- the transport
     *     already knows, so making the player wait would be pure theatre;
     *  #2 the slow signal still works: a link that stays open but silent is
     *     declared gone at exactly the limit;
     *  #3 neither fires while the peer is still answering;
     *  #4 the survivor ends up in a state where the match can be scored (its own
     *     turn keeps advancing after the declaration);
     *  #5 end to end over a real socket: the peer process is closed, and the
     *     survivor's checkForfeit() names it immediately.
     */
    static void v238Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- #1: a closed wire is immediate --------------------------------
        // A link that reports closed, with a session that has one silent peer.
        final com.xjzb.rts.core.LockstepLink.Link deadLink =
                new com.xjzb.rts.core.LockstepLink.Link() {
                    @Override public void send(String line) { }
                    @Override public java.util.List<String> poll() {
                        return new java.util.ArrayList<>();
                    }
                    @Override public boolean isClosed() { return true; }
                };
        com.xjzb.rts.core.Game g1 = cleanGame("terran");
        com.xjzb.rts.core.LockstepPeer p1 = new com.xjzb.rts.core.LockstepPeer(
                g1, 0, 2, deadLink);
        p1.session.submit(0, "");
        int gone1 = p1.checkForfeit(com.xjzb.rts.core.Lockstep.STALL_LIMIT);
        boolean immediate = gone1 == 1 && p1.session.forfeitLoser == 1
                && p1.session.forfeitWinner == 0 && p1.session.stallTurns == 0;
        ok &= immediate;
        sb.append(" closedImmediate=").append(immediate).append("@").append(gone1);

        // ---- #2: a silent-but-open link waits for the limit ----------------
        com.xjzb.rts.core.LockstepLink.Link openLink =
                new com.xjzb.rts.core.LockstepLink.Link() {
                    @Override public void send(String line) { }
                    @Override public java.util.List<String> poll() {
                        return new java.util.ArrayList<>();
                    }
                };
        com.xjzb.rts.core.Game g2 = cleanGame("terran");
        com.xjzb.rts.core.LockstepPeer p2 = new com.xjzb.rts.core.LockstepPeer(
                g2, 0, 2, openLink);
        int limit = com.xjzb.rts.core.Lockstep.STALL_LIMIT;
        boolean early = true, onTime = false;
        for (int t = 0; t < limit + 2; t++) {
            p2.session.submit(0, "");
            g2.update(1f / 30f);          // Game.update notes the stall
            int who = p2.checkForfeit(limit);
            if (t < limit - 1 && who >= 0) early = false;
            if (t == limit - 1 && who == 1) onTime = true;
        }
        ok &= early && onTime;
        sb.append(" silentTimeout=").append(early && onTime);

        // ---- #3: an answering peer is never declared gone ------------------
        com.xjzb.rts.core.LockstepLink.Link liveLink =
                new com.xjzb.rts.core.LockstepLink.Link() {
                    @Override public void send(String line) { }
                    @Override public java.util.List<String> poll() {
                        return new java.util.ArrayList<>();
                    }
                };
        com.xjzb.rts.core.Game g3 = cleanGame("terran");
        com.xjzb.rts.core.LockstepPeer p3 = new com.xjzb.rts.core.LockstepPeer(
                g3, 0, 2, liveLink);
        boolean neverGone = true;
        for (int t = 0; t < limit * 3; t++) {
            p3.receiveFrame();
            p3.session.submit(0, "");
            p3.session.submit(1, "");      // the peer keeps answering
            p3.stepFrame(1f / 30f);
            if (p3.checkForfeit(limit) >= 0) neverGone = false;
        }
        boolean advanced = p3.turnsReleased() > limit;   // it kept playing
        ok &= neverGone && advanced;
        sb.append(" aliveOk=").append(neverGone).append(" turns=")
          .append(p3.turnsReleased());

        // ---- #4: the survivor can keep advancing after the declaration -----
        com.xjzb.rts.core.Game g4 = cleanGame("terran");
        com.xjzb.rts.core.LockstepPeer p4 = new com.xjzb.rts.core.LockstepPeer(
                g4, 0, 2, deadLink);
        p4.session.submit(0, "");
        p4.checkForfeit(limit);
        int before = p4.turnsReleased();
        for (int t = 0; t < 60; t++) {
            p4.receiveFrame();
            p4.sendFrame();
            p4.stepFrame(1f / 30f);
        }
        boolean scored = p4.turnsReleased() > before;
        ok &= scored;
        sb.append(" afterForfeitTurns=").append(p4.turnsReleased() - before);

        // ---- #5: end to end, the peer process really goes away --------------
        final com.xjzb.rts.core.Lobby lobby5 = new com.xjzb.rts.core.Lobby(4);
        final String ver = "2.38";
        com.xjzb.rts.net.LanHost host5 = new com.xjzb.rts.net.LanHost(
                lobby5, new com.xjzb.rts.net.LanHost.Room() {
                    @Override public com.xjzb.rts.core.LanBeacon beacon() {
                        return new com.xjzb.rts.core.LanBeacon(
                                "127.0.0.1", "bloodbath", 2, 0, ver, 7L, 1);
                    }
                    @Override public String version() { return ver; }
                });
        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanHost.Connected>
                admitted5 = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.CountDownLatch admittedLatch =
                new java.util.concurrent.CountDownLatch(1);
        host5.start(new com.xjzb.rts.net.LanHost.Callback() {
            @Override public void onConnected(com.xjzb.rts.net.LanHost.Connected c) {
                admitted5.set(c);
                admittedLatch.countDown();
            }
            @Override public void onError(String message) { admittedLatch.countDown(); }
        });
        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanJoin.Result>
                jr5 = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.CountDownLatch joinLatch =
                new java.util.concurrent.CountDownLatch(1);
        com.xjzb.rts.net.LanJoin.connect(host5.beacon(), ver, "terran",
                r -> { jr5.set(r); joinLatch.countDown(); });
        admittedLatch.await(6, java.util.concurrent.TimeUnit.SECONDS);
        joinLatch.await(6, java.util.concurrent.TimeUnit.SECONDS);

        boolean e2e = false;
        if (admitted5.get() != null && jr5.get() != null && jr5.get().ok()) {
            com.xjzb.rts.core.Game gh = cleanGame("terran");
            com.xjzb.rts.core.LockstepPeer ph = new com.xjzb.rts.core.LockstepPeer(
                    gh, 0, 2, admitted5.get().link);
            ph.session.submit(0, "");
            gh.update(1f / 30f);
            boolean beforeKill = ph.checkForfeit(limit) < 0;   // peer still there
            // the joiner's process goes away
            jr5.get().link.close();
            int waited = 0;
            int who = -1;
            while (waited < 60 && (who = ph.checkForfeit(limit)) < 0) {
                ph.session.submit(0, "");
                gh.update(1f / 30f);
                Thread.sleep(20);
                waited++;
            }
            // the closed socket must be noticed well inside the 10 s timer
            e2e = beforeKill && who == 1 && waited < limit;
            sb.append(" e2eDrop=").append(who).append(" afterFrames=").append(waited);
        }
        ok &= e2e;
        host5.stop();

        System.out.println("  peer departure" + sb + " PASS=" + ok);
    }
    /**
     * v2.39: the host can actually start a match.
     *
     * This is the bug that made the whole feature unreachable: LanHost seated
     * the host but never marked it ready, and the joiner filled only its own
     * seat. So the host's roster read "1/2, host not ready" and the joiner's
     * read "1/2", and canStart() was false on BOTH phones forever -- the start
     * button could never light up. Every earlier assertion passed because they
     * all filled and readied the seats by hand; only walking the real host/join
     * flow end to end exposes it.
     *
     *  #1 hosting seats the host at 0 AND marks it ready;
     *  #2 a joined guest's local view has both seats filled and ready, so the
     *     start button is live on the joiner too;
     *  #3 end to end over real sockets: host and joiner both reach canStart(),
     *     and the host can start.
     */
    static void v239Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- #1: hosting readies the host --------------------------------
        com.xjzb.rts.core.Lobby l1 = new com.xjzb.rts.core.Lobby(2);
        int seat = l1.hostSeat("房主");
        boolean hostReady = seat == 0 && l1.slots.get(0).connected
                && l1.slots.get(0).ready && l1.connectedCount() == 1;
        // and alone it still cannot start (a one-player match is not a match)
        boolean aloneNo = !l1.canStart();
        ok &= hostReady && aloneNo;
        sb.append(" hostSeat=").append(hostReady).append(" aloneNo=").append(aloneNo);

        // ---- #2: the guest's local view is 2/2 ---------------------------
        com.xjzb.rts.core.Lobby l2 = new com.xjzb.rts.core.Lobby(2);
        l2.joinAsGuest("房主", "我");
        boolean guestView = l2.connectedCount() == 2
                && l2.slots.get(0).ready && l2.slots.get(1).ready
                && l2.canStart();
        ok &= guestView;
        sb.append(" guestView=").append(guestView);

        // ---- #3: the real host/join flow reaches canStart on both sides ---
        final String ver = "2.39";
        final com.xjzb.rts.core.Lobby hostLobby = new com.xjzb.rts.core.Lobby(2);
        com.xjzb.rts.net.LanHost host = new com.xjzb.rts.net.LanHost(
                hostLobby, new com.xjzb.rts.net.LanHost.Room() {
                    @Override public com.xjzb.rts.core.LanBeacon beacon() {
                        return new com.xjzb.rts.core.LanBeacon(
                                "127.0.0.1", "bloodbath", 2, 0, ver, 11L, 1);
                    }
                    @Override public String version() { return ver; }
                });
        final java.util.concurrent.CountDownLatch admitted =
                new java.util.concurrent.CountDownLatch(1);
        host.start(new com.xjzb.rts.net.LanHost.Callback() {
            @Override public void onConnected(com.xjzb.rts.net.LanHost.Connected c) {
                admitted.countDown();
            }
            @Override public void onError(String message) { admitted.countDown(); }
        });
        // the host's own roster after the joiner is admitted: both seats ready
        final com.xjzb.rts.core.Lobby guestLobby = new com.xjzb.rts.core.Lobby(2);
        final java.util.concurrent.CountDownLatch joined =
                new java.util.concurrent.CountDownLatch(1);
        com.xjzb.rts.net.LanJoin.connect(host.beacon(), ver, "terran", r -> {
            if (r.ok()) guestLobby.joinAsGuest("房主", "我");
            joined.countDown();
        });
        admitted.await(6, java.util.concurrent.TimeUnit.SECONDS);
        joined.await(6, java.util.concurrent.TimeUnit.SECONDS);
        // the host's roster: the guest arrives NOT ready, so the host must still
        // be able to start once it readies them -- assert the host's own half is
        // satisfied and the only thing missing is the guest's confirmation.
        boolean hostSide = hostLobby.connectedCount() == 2
                && hostLobby.slots.get(0).ready
                && hostLobby.slots.get(1).connected
                && hostLobby.blockedReason() != null
                && hostLobby.blockedReason().contains("未准备");
        hostLobby.setReady(1, true);
        boolean hostCanStart = hostLobby.canStart() && hostLobby.start();
        boolean guestCanStart = guestLobby.canStart() && guestLobby.start();
        ok &= hostSide && hostCanStart && guestCanStart;
        sb.append(" hostSide=").append(hostSide)
          .append(" hostStart=").append(hostCanStart)
          .append(" guestStart=").append(guestCanStart);
        host.stop();

        System.out.println("  lobby start" + sb + " PASS=" + ok);
    }
    /**
     * v2.40: CHARACTERIZATION of what a LAN match actually is today.
     *
     * This assertion does not test a new feature -- it pins the CURRENT
     * semantics so they are a specified behaviour rather than an accident, and
     * so a future change to them is a deliberate one that has to update this
     * text.
     *
     * What it pins: a LAN match is CO-OPERATIVE. Both peers build the same
     * board (Game's model is one human team 0 plus one AI team 1), so both
     * peers' orders land on team 0, and team 1 is driven by each machine's own
     * aiUpdate. Two phones therefore play the same side against the AI.
     *
     * Why real 1v1 is NOT a small change, which is worth recording next to the
     * assertion that documents the limitation: the command format identifies
     * units by INDEX INTO THE SHARED ents LIST ("move 0,2,5 300 400"). That list
     * grows and shrinks as units are built and killed, and the two teams' halves
     * of it change independently -- so "index i on my machine" and "index i on
     * yours" stop meaning the same unit the moment one team trains something.
     * Mirroring indices is therefore unsound, and 1v1 needs either team-relative
     * indices or a per-team entity list. That is a command-format change, and
     * applyCommand is also the replay path, so it has to be done with the
     * replay-determinism assertion ([v220]) in the same change.
     *
     *  #1 both peers' ents lists are identical in order AND team, which is what
     *     makes an index-based command stream work AT ALL between them;
     *  #2 a command issued by either peer reaches both and acts on team 0;
     *  #3 the AI still drives team 1 in a LAN match (so the match has an
     *     opponent even though it has only one human side);
     *  #4 the two peers stay in lockstep doing it (the invariant that matters).
     */
    static void v240Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        com.xjzb.rts.core.Game ga = cleanGame("terran");
        com.xjzb.rts.core.Game gb = cleanGame("terran");

        // #1: identical in order and team
        boolean sameOrder = ga.ents.size() == gb.ents.size();
        for (int i = 0; i < ga.ents.size() && sameOrder; i++) {
            com.xjzb.rts.core.Game.Ent x = ga.ents.get(i), y = gb.ents.get(i);
            if (!x.type.key.equals(y.type.key) || x.team != y.team) sameOrder = false;
        }
        ok &= sameOrder;
        sb.append(" sameBoard=").append(sameOrder);

        // #2/#3/#4: two peers over a real socket, each issuing an order for
        // its own selection (both are team 0 -- that is the point)
        final String ver = "2.40";
        final com.xjzb.rts.core.Lobby lobby = new com.xjzb.rts.core.Lobby(2);
        com.xjzb.rts.net.LanHost host = new com.xjzb.rts.net.LanHost(
                lobby, new com.xjzb.rts.net.LanHost.Room() {
                    @Override public com.xjzb.rts.core.LanBeacon beacon() {
                        return new com.xjzb.rts.core.LanBeacon(
                                "127.0.0.1", "bloodbath", 2, 0, ver, 21L, 1);
                    }
                    @Override public String version() { return ver; }
                });
        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanHost.Connected>
                admitted = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.CountDownLatch latch =
                new java.util.concurrent.CountDownLatch(1);
        host.start(new com.xjzb.rts.net.LanHost.Callback() {
            @Override public void onConnected(com.xjzb.rts.net.LanHost.Connected c) {
                admitted.set(c);
                latch.countDown();
            }
            @Override public void onError(String message) { latch.countDown(); }
        });
        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanJoin.Result>
                jr = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.CountDownLatch latch2 =
                new java.util.concurrent.CountDownLatch(1);
        com.xjzb.rts.net.LanJoin.connect(host.beacon(), ver, "terran",
                r -> { jr.set(r); latch2.countDown(); });
        latch.await(6, java.util.concurrent.TimeUnit.SECONDS);
        latch2.await(6, java.util.concurrent.TimeUnit.SECONDS);

        boolean linked = admitted.get() != null && jr.get() != null && jr.get().ok();
        sb.append(" linked=").append(linked)
          .append(" host=").append(admitted.get() != null)
          .append(" joinErr=").append(jr.get() == null ? "null" : jr.get().error);
        boolean lockstepHeld = false;
        boolean bothTouchedTeam0 = false;
        if (linked) {
            com.xjzb.rts.core.Game A = cleanGame("terran");
            com.xjzb.rts.core.Game B = cleanGame("terran");
            com.xjzb.rts.core.LockstepPeer pa = new com.xjzb.rts.core.LockstepPeer(
                    A, 0, 2, admitted.get().link);
            com.xjzb.rts.core.LockstepPeer pb = new com.xjzb.rts.core.LockstepPeer(
                    B, 1, 2, jr.get().link);
            List<com.xjzb.rts.core.Game.Ent> aSel = new ArrayList<>();
            List<com.xjzb.rts.core.Game.Ent> bSel = new ArrayList<>();
            for (com.xjzb.rts.core.Game.Ent e : A.ents)
                if (e.team == 0 && e.type.key.equals("scv")) aSel.add(e);
            for (com.xjzb.rts.core.Game.Ent e : B.ents)
                if (e.team == 0 && e.type.key.equals("scv")) bSel.add(e);

            // both peers issue orders, both for team 0
            A.recordOrder("move", aSel, "300 500");
            B.recordOrder("move", bSel, "360 500");

            boolean same = true;
            for (int t = 0; t < 30 * 6; t++) {
                pa.receiveFrame();
                pb.receiveFrame();
                pa.sendFrame();
                pb.sendFrame();
                long ha = pa.stepFrame(1f / 30f);
                long hb = pb.stepFrame(1f / 30f);
                if (ha != hb) same = false;
                Thread.sleep(1);
            }
            // A real socket costs a frame of round-trip per turn: a report
            // written at frame N is only readable by the peer during frame N+1's
            // receive, so ~180 frames releases ~90 turns, not 180. What must
            // hold is that the count is substantial AND identical on both sides
            // -- the exact ratio is a property of the loop, not of the protocol.
            lockstepHeld = same && pa.turnsReleased() == pb.turnsReleased()
                    && pa.turnsReleased() > 60;

            // both orders are in both logs, and both name team-0 indices
            int moved = 0;
            for (com.xjzb.rts.core.Lockstep.Cmd c : pa.commands())
                if (c.cmd.startsWith("move ")) moved++;
            // team 1 is still the AI's: it exists and is not the human side
            boolean aiAlive = false;
            for (com.xjzb.rts.core.Game.Ent e : A.ents) if (e.team == 1) aiAlive = true;
            bothTouchedTeam0 = moved == 2 && aiAlive;
            sb.append(" orders=").append(moved).append(" aiTeam1=").append(aiAlive);
            admitted.get().link.close();
            jr.get().link.close();
        }
        ok &= linked && lockstepHeld && bothTouchedTeam0;
        sb.append(" lockstep=").append(lockstepHeld);
        host.stop();

        System.out.println("  lan semantics" + sb + " PASS=" + ok);
    }

    /**
     * v2.41: the HUD independent-widget pass. The player read the leftover
     * top-bar/console band skeleton as "two big transparent windows"; this
     * version removes the band model itself. The invariants, pinned at source
     * level (HudLayout/GameView live on Android, so the desktop harness reads
     * the source and mirrors the arithmetic like the [layout] tests do):
     *
     *   bands -- no consoleTop/consoleHeight field or function, no hairline
     *     TOPBAR_RULE, no topBarH() gesture exemption;
     *   widgets -- six independent chips: the layout emits pause/clock/res/tally
     *     rects next to minimap/card/middle, inHud() tests each rect (no band
     *     test survives), and drawTopChips/drawBottomWidgets are the two draw
     *     entry points;
     *   camera -- the envelope is the full screen: hud.centerY is H/2 in
     *     HudLayout (mirrored in [layout]);
     *   gestures -- the drag/box guard is widget-based, edge scroll spans the
     *     full height, no consoleH() call survives anywhere;
     *   re-anchor -- toast, mission messages, replay banner and objectives
     *     anchor to widget rects, not band heights;
     *   spec -- 15 floats (5 panels x cx/cy/size), legacy 9-float saves migrate.
     */
    static void v241Tests() throws Exception {
        String root = "F:/KF/XJZB/AndroidPort/";
        String gv = new String(Files.readAllBytes(java.nio.file.Paths.get(
                root + "app/app/src/main/java/com/xjzb/rts/GameView.java")),
                java.nio.charset.StandardCharsets.UTF_8);
        String hl = new String(Files.readAllBytes(java.nio.file.Paths.get(
                root + "app/app/src/main/java/com/xjzb/rts/HudLayout.java")),
                java.nio.charset.StandardCharsets.UTF_8);
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- bands are gone ------------------------------------------------
        boolean noBandField = !hl.contains("consoleTop") && !hl.contains("consoleHeight")
                && !gv.contains("consoleTop") && !gv.contains("consoleH()")
                && !gv.contains("hudCacheConsole");
        boolean noHairline = !gv.contains("TOPBAR_RULE");
        boolean noTopGesture = !gv.contains("return y < topBarH()");
        ok &= noBandField && noHairline && noTopGesture;
        sb.append(" bandsGone=").append(noBandField && noHairline && noTopGesture);

        // ---- six independent widgets ---------------------------------------
        // v2.42: seven now -- the control-group block joined and the spec grew
        // to 18 floats; the v2.41 wording updated in place.
        boolean sixRects = hl.contains("final RectF pause = new RectF();")
                && hl.contains("final RectF clock = new RectF();")
                && hl.contains("final RectF res = new RectF();")
                && hl.contains("final RectF tally = new RectF();")
                && hl.contains("final RectF groups = new RectF();")
                && hl.contains("PANEL_COUNT = 6");
        boolean inHudByRect = gv.contains("if (hud.minimapSlot.contains(x, y)) return true;")
                && gv.contains("if (hud.clock.contains(x, y)) return true;")
                && gv.contains("if (hud.res.contains(x, y)) return true;")
                && gv.contains("if (hud.pause.contains(x, y)) return true;")
                && gv.contains("hud.groups.contains(x, y)");
        boolean twoDrawEntries = gv.contains("drawTopChips(c, W, topBarH())")
                && gv.contains("drawBottomWidgets(c, W, H);");
        ok &= sixRects && inHudByRect && twoDrawEntries;
        sb.append(" widgets=").append(sixRects && inHudByRect && twoDrawEntries);

        // ---- camera: the playfield is the whole screen ----------------------
        boolean cyHalf = hl.contains("centerY = H / 2f;")
                && gv.contains("float anchorY = hud.centerY;");
        ok &= cyHalf;
        sb.append(" cyHalf=").append(cyHalf);

        // ---- gestures follow the widgets ------------------------------------
        boolean dragGuard = gv.contains("!inHud(ev.getX(), ev.getY())")
                && !gv.contains("getHeight() - consoleH()");
        boolean edgeFull = gv.contains("if (touchY < band) dy = -speed;")
                && !gv.contains("botLimit");
        ok &= dragGuard && edgeFull;
        sb.append(" gestures=").append(dragGuard && edgeFull);

        // ---- re-anchored floaters -------------------------------------------
        boolean botAnchor = countOf(gv, "Math.min(hud.minimapSlot.top, hud.card.top)") == 2;
        boolean replayAnchor = gv.contains("hud.clock.bottom + 6 * uiScale");
        boolean objAnchor = gv.contains("Math.max(hud.pause.bottom, hud.res.bottom)");
        ok &= botAnchor && replayAnchor && objAnchor;
        sb.append(" anchors=").append(botAnchor && replayAnchor && objAnchor);

        // ---- the 15-float spec ----------------------------------------------
        // v2.42: 18 floats; the 9-float migration note survived the rewrite.
        boolean spec15 = hl.contains("SPEC_LEN = PANEL_COUNT * 3;")
                && gv.contains("new float[HudLayout.SPEC_LEN]")
                && gv.contains("for (int i = 0; i < 9 && i < p.length; i++)");
        // legacy 9-float migration appends default chip anchors
        boolean migrate = gv.contains("legacy save: default chip anchors");
        ok &= spec15 && migrate;
        sb.append(" spec15=").append(spec15 && migrate);

        System.out.println("  independent widgets" + sb + " PASS=" + ok);
    }

    /**
     * v2.42: the black-bar/bottom-HUD round. Four assertion groups:
     * A. assets -- every shipped chunk/minimap webp decodes and carries NO
     *    pure-black connected rect >= 8x8 (the void-tile bake fix);
     * B. chunk pipeline -- the draw math (floor + 4px bleed) provably covers
     *    the screen for a camera sweep, the placeholder cannot output black
     *    (bright matrix + light veil constants), and the LRU keeps the visible
     *    set resident;
     * C. groups widget -- the block is its own panel (spec 18, editor six),
     *    drawn at hud.groups in every selection state, hit-tested as a widget;
     * D. slim info panel -- INFO_H_DP 72, no English subtitle, no embedded
     *    group grid in drawSelInfo.
     */
    /** v2.42: read a whole gzip file (the shipped void.bin.gz). */
    static byte[] readGzAll(java.nio.file.Path p) throws Exception {
        try (java.util.zip.GZIPInputStream gz = new java.util.zip.GZIPInputStream(
                Files.newInputStream(p))) {
            java.io.ByteArrayOutputStream bo = new java.io.ByteArrayOutputStream();
            byte[] buf = new byte[8192];
            int n;
            while ((n = gz.read(buf)) > 0) bo.write(buf, 0, n);
            return bo.toByteArray();
        }
    }

    static void v242Tests() throws Exception {        boolean ok = true;
        StringBuilder sb = new StringBuilder();
        String root = "F:/KF/XJZB/AndroidPort/";
        String gv = new String(Files.readAllBytes(java.nio.file.Paths.get(
                root + "app/app/src/main/java/com/xjzb/rts/GameView.java")),
                java.nio.charset.StandardCharsets.UTF_8);
        String hl = new String(Files.readAllBytes(java.nio.file.Paths.get(
                root + "app/app/src/main/java/com/xjzb/rts/HudLayout.java")),
                java.nio.charset.StandardCharsets.UTF_8);
        String st = new String(Files.readAllBytes(java.nio.file.Paths.get(
                root + "app/app/src/main/java/com/xjzb/rts/Settings.java")),
                java.nio.charset.StandardCharsets.UTF_8);

        // ---- A: asset sweep -------------------------------------------------
        // v2.42: the bake turns void tiles into neighbour terrain. The check is
        // a comparison against the shipped v2.41 baseline: no map's terrain may
        // carry MORE pure-black pixels than it did before (the fix only ever
        // removes them). Custom-tileset maps like 3kingdoms legitimately draw
        // black art -- that is in the baseline too, so it does not trip the
        // gate, while a re-bake regression would.
        boolean assetsClean = true;
        int scanned = 0;
        StringBuilder bad = new StringBuilder();
        java.nio.file.Path mapsDir = java.nio.file.Paths.get(
                root + "app/app/src/main/assets/maps");
        java.util.Map<String, Integer> baseline = new java.util.HashMap<>();
        java.nio.file.Path baseFile = java.nio.file.Paths.get(root + "tools/black_baseline.txt");
        if (Files.exists(baseFile))
            for (String ln : Files.readAllLines(baseFile)) {
                int sp = ln.indexOf(' ');
                if (sp > 0) baseline.put(ln.substring(0, sp),
                        Integer.parseInt(ln.substring(sp + 1).trim()));
            }
        for (java.nio.file.Path p : (Iterable<java.nio.file.Path>)
                (Files.walk(mapsDir).filter(x -> x.toString().endsWith(".webp"))
                        .filter(x -> x.getFileName().toString().startsWith("c_"))
                        ::iterator)) {
            String key = p.getParent().getFileName() + "/" + p.getFileName();
            BufferedImage im;
            try {
                im = ImageIO.read(p.toFile());
            } catch (Exception e) {
                im = null;
            }
            scanned++;
            if (im == null) { assetsClean = false; bad.append(" NULL:").append(key); continue; }
            int W = im.getWidth(), H = im.getHeight();
            int[] pix = im.getRGB(0, 0, W, H, null, 0, W);
            int n = 0;
            for (int i = 0; i < W * H; i++) {
                int r = (pix[i] >> 16) & 255, g = (pix[i] >> 8) & 255, b = pix[i] & 255;
                if (r < 8 && g < 8 && b < 8) n++;
            }
            Integer base = baseline.get(key);
            if (base != null && n > base) {
                assetsClean = false;
                if (bad.length() < 400)
                    bad.append(' ').append(key).append('(').append(base)
                            .append("->").append(n).append(')');
            }
        }
        ok &= assetsClean && scanned > 4000;
        sb.append(" assets=").append(assetsClean).append('(').append(scanned).append(')');
        if (!assetsClean) sb.append(" offenders:").append(bad);

        // ---- B1: dst coverage -- floor + 4px bleed leaves no gap for a sweep
        // Mirrors render(): for each camera position, the visible chunk rows
        // produce dst rects; their union must cover the whole screen height.
        boolean coverage = true;
        int cs = 512;
        int wPx = 128 * 32;
        StringBuilder covBad = new StringBuilder();
        for (float z : new float[]{0.85f, 1.0f, 1.3f, 1.56f, 2.0f}) {
            for (float camY = 0; camY <= wPx; camY += 39.5f) {
                float centerY = 360f; // H/2 for 720
                int H = 720;
                float halfBot = (H - centerY) / z;
                float cam = Math.min(Math.max(camY, centerY / z),
                        Math.max(centerY / z, wPx - halfBot));
                int cy0 = Math.max(0, (int) Math.floor((cam - centerY / z) / cs));
                int cy1 = Math.min((wPx - 1) / cs,
                        (int) Math.floor((cam + (H - centerY) / z) / cs));
                // collect the dst y-intervals, clamped to the screen
                java.util.List<int[]> iv = new java.util.ArrayList<>();
                for (int cy = cy0; cy <= cy1; cy++) {
                    int dy0 = (int) Math.floor((cy * cs - cam) * z + centerY);
                    int dy1 = (int) Math.floor((Math.min(cy * cs + cs, wPx) - cam) * z + centerY);
                    dy1 += 4;                       // the unconditional bleed
                    iv.add(new int[]{Math.max(0, dy0), Math.min(H, dy1)});
                }
                iv.sort((u, v) -> Integer.compare(u[0], v[0]));
                int reach = 0;                      // highest screen y covered so far
                for (int[] seg : iv) {
                    if (seg[0] > reach + 1) { coverage = false; break; }
                    reach = Math.max(reach, seg[1]);
                }
                if (reach < H - 1) coverage = false;
                if (!coverage && covBad.length() < 120)
                    covBad.append(" z=").append(z).append(" cam=").append(Math.round(camY));
            }
        }
        ok &= coverage;
        sb.append(" coverage=").append(coverage);
        if (!coverage) sb.append("{").append(covBad).append('}');

        // ---- B2: placeholder can no longer output black ----------------------
        boolean veilLight = gv.contains("p.setAlpha(96);")
                && gv.contains("PLACEHOLDER_BRIGHT")
                && gv.contains("1.45f, 0, 0, 0, 34");
        ok &= veilLight;
        sb.append(" veil=").append(veilLight);

        // ---- B3: bilinear + wide bleed + floor ------------------------------
        boolean hardened = gv.contains("Paint(Paint.FILTER_BITMAP_FLAG);")  // fogPaint
                && gv.contains("private final Paint chunkPaint = new Paint(Paint.FILTER_BITMAP_FLAG);")
                && gv.contains("CHUNK_BLEED = 4")
                && gv.contains("Math.floor(sx(cx * cs))");
        ok &= hardened;
        sb.append(" hardened=").append(hardened);

        // ---- B4: the LRU keeps the visible set resident ----------------------
        boolean lruKeep = gv.contains("public volatile java.util.Set<String> keepAlive;")
                && gv.contains("keep == null || !keep.contains(eldest.getKey())")
                && gv.contains("keepAlive.add(cx + \"_\" + cy);");
        ok &= lruKeep;
        sb.append(" lru=").append(lruKeep);

        // ---- B5: the diagnostic instrument exists AND is reachable ----------
        // v2.42 fix: registering a settings cell is not the same as routing it.
        // "set:diag" drew, hit-tested and matched its own button -- then fell
        // through every branch of handleButton to "return false", so the tap
        // did nothing and the flag stayed false. The on-device report was
        // exactly that. Mirror handleButton's routing rules over every "set:"
        // cell drawSettings registers, so the whole class of dead settings
        // cells is caught here instead of on a phone.
        boolean diagFlag = st.contains("public boolean renderDiag = false;")
                && gv.contains("settings.renderDiag")
                // the placeholder must actually flash magenta, as the Settings
                // javadoc promises -- otherwise the instrument cannot tell an
                // undecoded chunk from a black bar living somewhere else
                && gv.contains("Color.argb(110, 255, 0, 255)")
                // and the clear colour must turn loud green, so a screenshot can
                // separate "bare canvas / dst gap" from "legitimately dark
                // terrain": a band that stays BLACK under the toggle is covered
                // by real geometry, one that turns GREEN is a coverage gap.
                && gv.contains("settings.renderDiag ? Color.rgb(0, 255, 0)")
                // the 0.5 Hz line must name the map and the missing chunks,
                // otherwise a log dump cannot be tied to a map or a tile.
                && gv.contains("\" missKeys=\"")
                && gv.contains("\" fog=\"")
                // a fling lasts a few frames, so the 0.5 Hz line alone can miss
                // the event entirely; every miss frame also logs its chunk key.
                && gv.contains("\"[diag-miss] f=\"")
                && gv.contains("diagMissLog = 0;")
                // v2.42: logcat alone was not readable in the field -- the bar is
                // gone the moment the fling ends. The readout must also be drawn
                // on screen and must LATCH the worst frame, or the numbers are
                // stale before anyone can photograph them.
                && gv.contains("private void drawDiagPanel(Canvas c, int W, int H)")
                && gv.contains("if (settings.renderDiag) drawDiagPanel(c, W, H);")
                && gv.contains("diagMissPeak = diagMiss;")
                && gv.contains("diagPeakKeys = diagMissKeys == null ? \"\" : diagMissKeys.toString().trim();")
                && gv.contains("diagLog.addLast(line);")
                // and it must stand down over a modal sheet: the panel sits
                // top-left, exactly where the settings sheet's first rows are,
                // and the diagnostic has to stay switchable OFF.
                && gv.contains("if (menuOpen || briefingOpen || layoutEdit) return;");
        int dsStart = gv.indexOf("private void drawSettings");
        int dsEnd = gv.indexOf("private void segmented", dsStart);
        String ds = dsStart < 0 || dsEnd < dsStart ? "" : gv.substring(dsStart, dsEnd);
        java.util.TreeSet<String> acts = new java.util.TreeSet<>();
        java.util.regex.Matcher am = java.util.regex.Pattern
                .compile("\"(set:[a-z0-9]+)\"").matcher(ds);
        while (am.find()) acts.add(am.group(1));
        StringBuilder dead = new StringBuilder();
        int routed = 0;
        for (String a : acts) {
            if (gv.contains("\"" + a + "\".equals(b.action)")
                    || gv.contains("b.action.startsWith(\"" + a + "\")")) routed++;
            else dead.append(' ').append(a);
        }
        boolean diag = diagFlag && acts.size() >= 10 && routed == acts.size();
        ok &= diag;
        sb.append(" diag=").append(diag);
        if (!diag)
            sb.append("{flag=").append(diagFlag).append(" cells=").append(acts.size())
              .append(" routed=").append(routed).append(" dead:").append(dead).append('}');

        // ---- C: the groups widget -------------------------------------------
        boolean g1 = hl.contains("P_GROUPS = 5");
        boolean g2 = hl.contains("PANEL_COUNT = 6");
        boolean g3 = hl.contains("SPEC_LEN = PANEL_COUNT * 3");
        boolean g4 = hl.contains("case P_GROUPS: return groups;");
        boolean g5 = gv.contains("drawFormationOnly(c, hud.groups);");
        boolean g6 = hl.contains("place(groups, c[15] * W, c[16] * H, gW, gH, W, H, dp);");
        // the embedded grid is gone from drawSelInfo
        boolean noEmbeddedGrid = !gv.contains("float gCell = (cellS - 2 * k) / 2f;");
        boolean groupsWidget = g1 && g2 && g3 && g4 && g5 && g6;
        ok &= groupsWidget && noEmbeddedGrid;
        sb.append(" groups=").append(groupsWidget && noEmbeddedGrid);
        if (!groupsWidget)
            sb.append("{g").append(g1 ? "" : "1").append(g2 ? "" : "2")
                    .append(g3 ? "" : "3").append(g4 ? "" : "4")
                    .append(g5 ? "" : "5").append(g6 ? "" : "6").append('}');

        // ---- D: the slim info panel -----------------------------------------
        boolean slim = hl.contains("INFO_H_DP = 72f")
                && gv.contains("float panelH = Math.min(hud.middle.height(),")
                && !gv.contains("c.drawText(en, tx, ty + 14 * k, p);");
        ok &= slim;
        sb.append(" slim=").append(slim);

        // ---- E: the selection card is capped in width -----------------------
        // A real-device report: selecting five SCVs drew a green hp bar across
        // most of a 2608px screen (measured 1310px bar inside a 1540px slab).
        // The cause was `multi ? infoR - infoL : ...` -- a multi-select claimed
        // the whole middle strip, and the bar hugs the panel, so the bar grew
        // with it. The card is now capped in every selection state; only a
        // genuinely mixed group may exceed the cap, and only by the filter row
        // it actually draws.
        boolean cap1 = gv.contains("private static final float INFO_CAP_DP = 165f;");
        boolean cap2 = gv.contains("float wantW = Math.min(infoR - infoL, cap);");
        boolean cap3 = gv.contains("private static int kindsOf(List<Game.Ent> sel)");
        boolean cap4 = gv.contains("cap = Math.max(cap, 20 * k + kinds * cellS");
        // the old full-strip multi branch must be gone
        boolean cap5 = !gv.contains("? infoR - infoL");
        // and the bar must still hug the (now capped) panel
        boolean cap6 = gv.contains("float barW = panel.right - 10 * k - tx;");
        // arithmetic: the reported case, replayed through the new rule. The
        // numbers are the screenshot's -- k=2, middle strip 1540px, panel
        // height 72dp*2, one kind selected (five SCVs).
        float oldW = 1540f;                 // the old multi branch: the whole strip
        float newW = infoPanelW(1, 1540f, 2f, 72f * 2f);
        boolean capNum = oldW > 1500f && newW <= 165f * 2f + 0.5f;
        // and a genuinely mixed group still gets its filter row, capped at six
        // kinds, without ever reaching the strip either
        float mixedW = infoPanelW(6, 1540f, 2f, 72f * 2f);
        boolean capMix = mixedW > newW && mixedW < 700f;
        capNum &= capMix;
        boolean infoCap = cap1 && cap2 && cap3 && cap4 && cap5 && cap6 && capNum;
        ok &= infoCap;
        sb.append(" infoCap=").append(infoCap);
        if (!infoCap)
            sb.append("{c").append(cap1 ? "" : "1").append(cap2 ? "" : "2")
                    .append(cap3 ? "" : "3").append(cap4 ? "" : "4")
                    .append(cap5 ? "" : "5").append(cap6 ? "" : "6")
                    .append(capNum ? "" : "n").append('}')
                    .append("(was ").append(Math.round(oldW)).append("px now ")
                    .append(Math.round(newW)).append("px)");

        System.out.println("  assets/coverage/placeholder/lru/diag/groups/slim/infoCap"
                + sb + " PASS=" + ok);
        v242CamSnapshotTest(gv);
    }

    /**
     * v2.42 defect B, "black bar while panning".
     *
     * The bar was bare canvas showing between chunk dsts, and the reason it
     * showed was that the camera was a plain field written by the touch thread
     * while render() was reading it: one frame got drawn from two (or more)
     * different cameras, so neighbouring chunk dsts stopped tiling. The fix is
     * a per-frame snapshot -- the renderer owns camX/camY/zoom, the touch side
     * publishes into inCamX/inCamY/inZoom and render() adopts that once.
     *
     * That invariant is easy to break by accident (one stray `camX -=` on the
     * touch path reintroduces the tearing), and it cannot be caught by any
     * on-device assertion, so it is pinned here by source shape:
     *   1. the mirrors and the dirty flag exist and are volatile;
     *   2. render() adopts BEFORE it computes anything from the camera;
     *   3. no touch-path method assigns to camX/camY/zoom at all -- they all go
     *      through tPanTo/tPanBy/tCenterOn/tZoomTo;
     *   4. the UI-side paths (restart, zoom preset) write BOTH copies, or the
     *      next adopted snapshot silently undoes them.
     */
    static void v242CamSnapshotTest(String gv) {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // 1. the snapshot fields exist and cross threads safely
        boolean fields = gv.contains("private volatile float inCamX, inCamY, inZoom = 1.3f;")
                && gv.contains("private volatile boolean camDirty;")
                && gv.contains("private float tCamX() { return camDirty ? inCamX : camX; }")
                && gv.contains("private float tCamY() { return camDirty ? inCamY : camY; }")
                && gv.contains("private float tZoom() { return camDirty ? inZoom : zoom; }");
        ok &= fields;
        sb.append(" fields=").append(fields);

        // 2. render() adopts first, then does anything with the camera. The
        //    adopt block must appear before the first use of the camera in the
        //    method body (the clear colour is not one, the clamp is).
        int rb = gv.indexOf("private void render(Canvas c) {");
        int adopt = rb < 0 ? -1 : gv.indexOf("if (camDirty) {", rb);
        int clamp = rb < 0 ? -1 : gv.indexOf("camX = Game.clamp(camX, halfW,", rb);
        int adoptBody = adopt < 0 ? -1 : gv.indexOf("camDirty = false;", adopt);
        boolean adoptFirst = rb >= 0 && adopt > rb && adoptBody > adopt
                && clamp > adoptBody
                && gv.substring(adopt, adoptBody)
                        .contains("camX = inCamX;")
                && gv.substring(adopt, adoptBody).contains("camY = inCamY;")
                && gv.substring(adopt, adoptBody).contains("zoom = inZoom;");
        ok &= adoptFirst;
        sb.append(" adopt=").append(adoptFirst);

        // 3. the touch path publishes instead of writing. Any direct assignment
        //    inside the touch handlers is the defect coming back.
        int te = gv.indexOf("public boolean onTouchEvent(MotionEvent ev) {");
        int teEnd = te < 0 ? -1 : gv.indexOf("\n    private ", te + 10);
        String touch = te < 0 || teEnd < te ? "" : gv.substring(te, teEnd);
        boolean touchPublishes = !touch.isEmpty()
                && !touch.contains("camX -=") && !touch.contains("camY -=")
                && !touch.contains("camX +=") && !touch.contains("camY +=")
                && !touch.contains("camX =") && !touch.contains("camY =")
                && !touch.contains("zoom =")
                && touch.contains("tPanBy(") && touch.contains("tZoomTo(");
        // and edgeScroll, the other per-frame camera writer, must publish too
        int es = gv.indexOf("private void edgeScroll(float dt) {");
        int esEnd = es < 0 ? -1 : gv.indexOf("\n    private ", es + 10);
        String edge = es < 0 || esEnd < es ? "" : gv.substring(es, esEnd);
        boolean edgePublishes = !edge.isEmpty() && edge.contains("tPanBy(")
                && !edge.contains("camX +=") && !edge.contains("camY +=");
        // the minimap jump and the alert jump are touch-path writes as well
        boolean jumpsPublish = gv.contains("tCenterOn(alertX, alertY);")
                && gv.contains("tCenterOn((x - minimapRect.left) / minimapRect.width() * game.wPx,");
        boolean touchClean = touchPublishes && edgePublishes && jumpsPublish;
        ok &= touchClean;
        sb.append(" touch=").append(touchClean);

        // 4. the UI-side paths keep both copies in step
        boolean uiBoth = gv.contains("camX = inCamX = x;")
                && gv.contains("camY = inCamY = y;")
                && gv.contains("zoom = inZoom = z;")
                && gv.contains("setZoomNow(Settings.zoomDefault(settings.zoomLevel));")
                && gv.contains("setCameraNow(map.starts.size() > 0 ? map.starts.get(0)[0] + 64 : 512,")
                // the constructor's start camera must seed the mirror as well
                && gv.contains("inCamX = camX;")
                && gv.contains("inCamY = camY;");
        ok &= uiBoth;
        sb.append(" ui=").append(uiBoth);

        // 5. the mechanism, numerically -- so the fix rests on arithmetic and
        //    not only on source shape. The two cameras fitted out of the
        //    reported screenshots (zoom 1.543 / camX 849 and zoom 1.561 /
        //    camX 858; camY 409 and 500) are fed through the very same dst
        //    arithmetic render() uses, on the reported screen (2608x1200) and
        //    map (divide, 2048x2048). Drawn from ONE camera every seam
        //    overlaps by the 4px bleed. Split across the two, a clear-colour
        //    gap opens -- and its size reproduces the bar that was reported.
        int W = 2608, H = 1200, cs = 512, wPx = 2048, hPx = 2048;
        float zA = 1.543f, xA = 849f, yA = 409f;
        float zB = 1.561f, xB = 858f, yB = 500f;
        // Which of the two cameras ended up on the low side of a seam depends
        // on where in the frame the write landed, so both orders are allowed --
        // the claim under test is "mixing cameras opens a seam", not which way
        // round the mix went.
        int gapXsplit = Math.max(seamGap(zB, xB, zA, xA, wPx, W / 2f, cs),
                seamGap(zA, xA, zB, xB, wPx, W / 2f, cs));
        int gapYsplit = Math.max(seamGap(zB, yB, zA, yA, hPx, H / 2f, cs),
                seamGap(zA, yA, zB, yB, hPx, H / 2f, cs));
        int gapXsame = Math.max(seamGap(zA, xA, zA, xA, wPx, W / 2f, cs),
                seamGap(zB, xB, zB, xB, wPx, W / 2f, cs));
        int gapYsame = Math.max(seamGap(zA, yA, zA, yA, hPx, H / 2f, cs),
                seamGap(zB, yB, zB, yB, hPx, H / 2f, cs));
        // a torn frame leaves a gap; a snapshot frame can only ever overlap
        boolean tears = gapXsplit > 0 && gapYsplit > 0
                && gapXsame <= 0 && gapYsame <= 0;
        ok &= tears;
        sb.append(" tears=").append(tears)
                .append("(x ").append(gapXsplit).append('/').append(gapXsame)
                .append(" y ").append(gapYsplit).append('/').append(gapYsame).append(')');

        System.out.println("  [v242] camera snapshot" + sb + " PASS=" + ok);
    }

    /**
     * v2.43 P0-a: the two per-frame O(N^2) scans in the cloak layer and the
     * idle target acquisition.
     *
     * Both are asserted by NUMBER rather than by reading the source, because
     * both are pure cost reductions: a source-shape check would pass just as
     * happily on a version that computes the same answer the slow way, and the
     * whole point of the pass is that the work goes away.
     *
     *  #1 the cloak short-circuit actually short-circuits: on a roster with no
     *     arbiter and no detector (every map this game ships), updateCloak
     *     still ASKS -- and never walks the roster;
     *  #2 the same counters prove the scan comes BACK the moment one exists,
     *     which is what makes #1 a short-circuit and not a broken cloak layer;
     *  #3 the idle-acquire stagger skips at least most of the scans it used to
     *     run, on a roster big enough to engage it;
     *  #4 and it is deterministic: two independently built peers with the
     *     stagger engaged agree on every one-second stateHash sample. The phase
     *     is keyed off (roster index, tick, roster size) -- all three are
     *     identical on both machines -- but this is the claim a desync would
     *     break, so it is measured, not argued.
     */
    static void v243Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- 1/2: the aura short-circuit ------------------------------------
        // cleanGame("terran") keeps only team 0 (a command centre, its SCVs)
        // and adds one enemy sunken, which is not a detector. So neither side
        // has an arbiter or a detector and the roster walk is unreachable.
        com.xjzb.rts.core.Game ag = cleanGame("terran");
        ag.update(1 / 30f);                 // settles the counts
        int q0 = ag.statAuraQueries, s0 = ag.statAuraScans;
        for (int i = 0; i < 60; i++) ag.update(1 / 30f);
        boolean asked = ag.statAuraQueries > q0;
        boolean shorted = asked && ag.statAuraScans == s0;

        // the positive control: a cloak layer with something to reveal must
        // bring the roster walk back. Two steps, because the gate is two-sided:
        // detectorNear is only ever ASKED about a unit that is already cloaked,
        // so a lone turret changes no counters -- it takes a permanently
        // cloaked enemy (the dark templar) to make the question get asked.
        ag.spawn("dtemplar", 1, 900, 900, true);
        ag.update(1 / 30f);
        int s1 = ag.statAuraScans;
        for (int i = 0; i < 60; i++) ag.update(1 / 30f);
        boolean stillShorted = ag.statAuraScans == s1;   // asked, but no detector to find
        ag.spawn("turret", 0, 900, 900, true);
        ag.update(1 / 30f);
        int s1b = ag.statAuraScans;
        for (int i = 0; i < 60; i++) ag.update(1 / 30f);
        boolean scansWhenNeeded = stillShorted && ag.statAuraScans > s1b;
        // ...and an arbiter must bring the aura scan back too
        com.xjzb.rts.core.Game bg = cleanGame("protoss");
        com.xjzb.rts.core.Game.Ent probe = bg.spawn("zealot", 0, 600, 600, true);
        bg.update(1 / 30f);
        boolean noAuraYet = !bg.isCloakedNow(probe);
        int s2 = bg.statAuraScans;
        bg.spawn("arbiter", 0, 620, 600, true);
        bg.update(1 / 30f);
        for (int i = 0; i < 60; i++) bg.update(1 / 30f);
        boolean auraScans = bg.statAuraScans > s2;
        // the aura itself still works (a friendly arbiter cloaks a friend)
        boolean auraWorks = bg.isCloakedNow(probe);
        boolean aura = shorted && scansWhenNeeded && auraScans && noAuraYet && auraWorks;
        ok &= aura;
        sb.append(" aura=").append(aura)
          .append("(ask ").append(asked).append(" short ").append(shorted)
          .append(" back ").append(scansWhenNeeded).append('/').append(auraScans)
          .append(" works ").append(auraWorks).append(')');

        // ---- 3: the idle-acquire stagger ------------------------------------
        // A roster past ACQUIRE_STAGGER_MIN of idle marines with nothing in
        // range: every one of them wants a scan every tick, and the stagger
        // gives each of them one tick in eight instead.
        com.xjzb.rts.core.Game sg = cleanGame("terran");
        for (int i = 0; i < 40; i++) sg.spawn("marine", 0, 400 + (i % 8) * 24, 500 + (i / 8) * 24, true);
        sg.update(1 / 30f);
        int aq0 = sg.statAcquireQueries, as0 = sg.statAcquireScans;
        for (int i = 0; i < 30 * 10; i++) sg.update(1 / 30f);
        int aq = sg.statAcquireQueries - aq0, as = sg.statAcquireScans - as0;
        // 8 phases: a quarter of the queries is a generous ceiling, and it is
        // still far below the 1:1 the un-staggered path would give.
        boolean stagger = aq > 0 && as > 0 && as * 4 < aq;
        ok &= stagger;
        sb.append(" stagger=").append(stagger)
          .append("(q ").append(aq).append(" scan ").append(as).append(')');

        // ---- 4: the stagger is deterministic ---------------------------------
        // Two peers, built independently from the same map, with the stagger
        // engaged, must agree at every one-second sample.
        com.xjzb.rts.core.Game p1 = bigRoster(), p2 = bigRoster();
        java.util.List<Long> h1 = new ArrayList<>(), h2 = new ArrayList<>();
        for (int t = 0; t < 30 * 20; t++) {
            p1.update(1 / 30f);
            p2.update(1 / 30f);
            if (t % 30 == 29) {
                h1.add(p1.stateHash());
                h2.add(p2.stateHash());
            }
        }
        boolean same = h1.size() >= 15 && h1.size() == h2.size();
        for (int i = 0; i < h1.size() && same; i++) if (!h1.get(i).equals(h2.get(i))) same = false;
        // and the comparison is worth something only if the stagger ran
        boolean engaged = p1.statAcquireScans > 0 && p1.statAcquireScans * 4 < p1.statAcquireQueries;
        boolean deterministic = same && engaged;
        ok &= deterministic;
        sb.append(" det=").append(deterministic).append("(same ").append(same)
          .append(" samples ").append(h1.size()).append(" engaged ").append(engaged).append(')');

        System.out.println("  [v243] aura/stagger" + sb + " PASS=" + ok);

        // ---- 5/6: the spatial grid ------------------------------------------
        // The grid replaces a full roster walk in separation, targeting and
        // splash. Two things have to hold: it must not change WHICH unit gets
        // picked (that would desync the lockstep peers), and it must actually
        // cut the work. Both are measured below against a reference copy of the
        // old walk.
        StringBuilder gb = new StringBuilder();
        boolean gok = true;

        // 5a: it is rebuilt once per tick, so a query always reads the roster
        // as it stood at the top of the tick.
        com.xjzb.rts.core.Game gg = cleanGame("terran");
        for (int gy = 0; gy < 12; gy++)
            for (int gx = 0; gx < 12; gx++) {
                float px = 200 + gx * 150f, py = 200 + gy * 150f;
                if (px > gg.wPx - 100 || py > gg.hPx - 100) continue;
                gg.spawn("marine", 0, px, py, true);
            }
        gg.update(1 / 30f);
        int rb0 = gg.statGridRebuilds, gq0 = gg.statGridQueries, gc0 = gg.statGridCandidates;
        for (int i = 0; i < 30 * 5; i++) gg.update(1 / 30f);
        int rbs = gg.statGridRebuilds - rb0, gq = gg.statGridQueries - gq0;
        int gc = gg.statGridCandidates - gc0;
        int gn = gg.ents.size();
        double avg = gq > 0 ? (double) gc / gq : -1;
        // one rebuild per tick is the floor; a lazy one after a mid-tick spawn
        // only ever adds to it.
        boolean perTick = rbs >= 150 && rbs < 150 * 3;
        // the whole point: a query must look at a small slice of a roster this
        // size, not at all of it. A quarter is a generous ceiling.
        boolean sparse = gq > 0 && avg > 0 && avg * 4 < gn;
        boolean rebuilt = perTick && sparse;
        gok &= rebuilt;
        gb.append(" rebuild=").append(rebuilt)
          .append("(t ").append(rbs).append(" q ").append(gq)
          .append(" avgCand ").append(String.format("%.1f", avg))
          .append(" n ").append(gn).append(')');

        // 5b: the grid must pick the SAME unit the full walk picked. Identity is
        // the right comparison -- the tie-break is "first strictly closer wins",
        // so the candidate order is part of the answer, not just the distances.
        com.xjzb.rts.core.Game gm = cleanGame("protoss");
        gm.spawn("zealot", 1, 700, 700, true);
        gm.spawn("muta", 1, 760, 700, true);            // flying
        gm.spawn("lurker_bur", 1, 700, 760, true);      // burrowed, type-keyed
        gm.spawn("zergling", 1, 740, 740, true);
        gm.spawn("over", 1, 820, 700, true);            // flying, detector
        gm.spawn("dtemplar", 1, 720, 720, true);        // permanently cloaked
        // A player turret sits next to the dark templar, so it is SPOTTED and
        // therefore targetable. Without it every observer would skip the
        // templar for the same reason on both paths, and the cloak gate would
        // never be exercised on the side that matters.
        gm.spawn("turret", 0, 700, 720, true);
        gm.update(1 / 30f);                             // sets cloakActive/spotted
        boolean spotted = false;
        for (com.xjzb.rts.core.Game.Ent e : gm.ents)
            if ("dtemplar".equals(e.type.key)) spotted = e.spotted;
        // four observers covering the layer rules: melee ground (range < 64, so
        // it can reach neither flyers nor burrowers), ground ranged, air-only
        // (valkyrie has no air-to-ground weapon) and ground-only (lurker).
        com.xjzb.rts.core.Game.Ent[] obs = {
            gm.spawn("zealot", 0, 500, 500, true),
            gm.spawn("dragoon", 0, 500, 500, true),
            gm.spawn("valkyrie", 0, 500, 500, true),
            gm.spawn("lurker", 0, 500, 500, true),
        };
        float[] ranges = {14f, 64f, 96f, 128f, 200f, 420f};
        int compared = 0, mismatched = 0;
        for (com.xjzb.rts.core.Game.Ent o : obs)
            for (float r : ranges)
                for (int oy = 600; oy <= 880; oy += 16)
                    for (int ox = 600; ox <= 880; ox += 16) {
                        com.xjzb.rts.core.Game.Ent viaGrid =
                                gm.findEnemyInRangeFrom(ox, oy, o, r);
                        com.xjzb.rts.core.Game.Ent viaWalk = bruteFindEnemy(gm, ox, oy, o, r);
                        compared++;
                        if (viaGrid != viaWalk) mismatched++;
                    }
        boolean samePick = compared > 3000 && mismatched == 0;
        // the scene is only worth anything if the layer gates actually fired.
        // Measured from just off the burrower, the four observers must NOT all
        // pick the same enemy -- otherwise the gates are dead code and the
        // comparison above proves nothing. Melee drops the flyer and the
        // burrower, air-only drops every ground target, and only the ranged
        // ground pair can reach the burrower at all.
        java.util.Set<String> picks = new java.util.HashSet<>();
        for (com.xjzb.rts.core.Game.Ent o : obs) {
            com.xjzb.rts.core.Game.Ent p = gm.findEnemyInRangeFrom(700, 760, o, 420f);
            picks.add(p == null ? "-" : p.type.key);
        }
        boolean gatesMatter = picks.size() >= 3;
        gok &= samePick && gatesMatter;
        gb.append(" pick=").append(samePick)
          .append("(n ").append(compared).append(" bad ").append(mismatched)
          .append(" spotted ").append(spotted)
          .append(" kinds ").append(picks.size()).append(')');
        // 5c: a spawn invalidates the grid, so a query issued between the spawn
        // and the next tick still sees the new unit. This is exactly what the
        // desktop harness does -- it spawns, then asserts, with no tick between.
        com.xjzb.rts.core.Game gi = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent look = gi.spawn("marine", 0, 1000, 1000, true);
        gi.update(1 / 30f);
        boolean quietBefore = gi.findEnemyInRange(look, 200) == null;
        com.xjzb.rts.core.Game.Ent fresh = gi.spawn("zergling", 1, 1060, 1000, true);
        boolean seesFresh = gi.findEnemyInRange(look, 200) == fresh;
        boolean invalidation = quietBefore && seesFresh;
        gok &= invalidation;
        gb.append(" invalidate=").append(invalidation)
          .append("(quiet ").append(quietBefore).append(" fresh ").append(seesFresh).append(')');

        // 5d: splash through the grid must land the same damage as the walk.
        // Two independently built copies of the same scene, one splashed each
        // way, then every unit's hp compared. splash() mutates hp as it goes, so
        // this cannot be done on one instance.
        int splashBad = 0, splashCompared = 0;
        float[][] bursts = {
            {1000f, 1000f, 96f, 0.5f},
            {940f, 1040f, 160f, 0.25f},
            {1100f, 900f, 48f, 1.0f},
        };
        for (float[] b : bursts) {
            com.xjzb.rts.core.Game sp1 = splashScene(), sp2 = splashScene();
            sp1.splash(b[0], b[1], 40, "explosive", null, b[2], b[3], null);
            bruteSplash(sp2, b[0], b[1], 40, "explosive", null, b[2], b[3], null);
            if (sp1.ents.size() != sp2.ents.size()) {
                splashBad++;
                continue;
            }
            for (int i = 0; i < sp1.ents.size(); i++) {
                splashCompared++;
                if (sp1.ents.get(i).hp != sp2.ents.get(i).hp) splashBad++;
            }
        }
        boolean sameSplash = splashCompared > 60 && splashBad == 0;
        gok &= sameSplash;
        gb.append(" splash=").append(sameSplash)
          .append("(n ").append(splashCompared).append(" bad ").append(splashBad).append(')');

        System.out.println("  [v243] grid" + gb + " PASS=" + gok);

        // ---- 7: the path budget ---------------------------------------------
        // An AI wave hands one destination to every attacker in the same tick,
        // which used to mean one A* per attacker inside a single frame -- the
        // measured 100 ms-plus spike. queuePath spreads those searches at
        // PATH_BUDGET per tick. Three things have to hold: the budget is really
        // enforced, a player order still resolves in the tick it was made, and
        // the queue is spent identically on both peers.
        StringBuilder pb = new StringBuilder();
        boolean pok = true;

        // 7a: 40 units asking in one tick are served at most 8 per tick, and
        // the queue does drain. Nothing here is a worker, so no auto-harvest
        // re-queues behind the counter and the count is the whole story.
        com.xjzb.rts.core.Game q1 = cleanGame("terran");
        float[] qo = openGround(q1, 420f);
        boolean capped = false, drained = false;
        int pending0 = -1, pending1 = -1, servedFirst = -1, emptyAt = -1;
        if (qo != null) {
            List<com.xjzb.rts.core.Game.Ent> crowd = new ArrayList<>();
            for (int i = 0; i < 40; i++)
                crowd.add(q1.spawn("marine", 0, qo[0] + (i % 8) * 8, qo[1] + (i / 8) * 8, true));
            for (com.xjzb.rts.core.Game.Ent e : crowd) q1.queuePath(e, qo[0] + 400f, qo[1]);
            pending0 = 0;
            for (com.xjzb.rts.core.Game.Ent e : crowd) if (e.pathGen != 0) pending0++;
            q1.update(1 / 30f);
            pending1 = 0;
            for (com.xjzb.rts.core.Game.Ent e : crowd) if (e.pathGen != 0) pending1++;
            servedFirst = pending0 - pending1;
            capped = pending0 == 40 && servedFirst > 0 && servedFirst <= 8;
            for (int t = 0; t < 12; t++) {
                q1.update(1 / 30f);
                int left = 0;
                for (com.xjzb.rts.core.Game.Ent e : crowd) if (e.pathGen != 0) left++;
                if (left == 0) { emptyAt = t + 2; break; }
            }
            // 40 requests at 8 per tick is 5 ticks; more than 12 means the queue
            // is not moving, fewer than 5 means the budget leaked.
            drained = emptyAt >= 5 && emptyAt <= 12;
        }
        boolean budget = capped && drained;
        pok &= budget;
        pb.append(" budget=").append(budget)
          .append("(queued ").append(pending0).append(" served ").append(servedFirst)
          .append(" empty@ ").append(emptyAt).append(')');

        // 7b: a player order is NOT queued. It must resolve in the tick it was
        // made -- that is what keeps "无法到达该位置" immediate and what keeps
        // the ensnare assertion's 15-frame window meaningful.
        com.xjzb.rts.core.Game q2 = cleanGame("terran");
        float[] qo2 = openGround(q2, 420f);
        boolean immediate = false;
        if (qo2 != null) {
            com.xjzb.rts.core.Game.Ent m = q2.spawn("marine", 0, qo2[0], qo2[1], true);
            List<com.xjzb.rts.core.Game.Ent> sel = new ArrayList<>();
            sel.add(m);
            q2.orderMove(sel, qo2[0] + 300f, qo2[1], false);
            immediate = m.pathGen == 0 && m.pathLen() > 0 && m.moving;
        }
        pok &= immediate;
        pb.append(" immediate=").append(immediate);

        // 7c: a cancelled request is skipped, not served. A unit ordered to
        // hold must not be dragged off a few ticks later by the path it asked
        // for before the order arrived.
        com.xjzb.rts.core.Game q3 = cleanGame("terran");
        float[] qo3 = openGround(q3, 420f);
        boolean cancelled = false;
        if (qo3 != null) {
            com.xjzb.rts.core.Game.Ent m = q3.spawn("marine", 0, qo3[0], qo3[1], true);
            q3.queuePath(m, qo3[0] + 400f, qo3[1]);
            boolean wasQueued = m.pathGen != 0;
            q3.cancelQueuedPath(m);
            for (int t = 0; t < 6; t++) q3.update(1 / 30f);
            cancelled = wasQueued && m.pathGen == 0 && m.pathLen() == 0 && !m.moving;
        }
        pok &= cancelled;
        pb.append(" cancel=").append(cancelled);

        // 7d: the queue is spent identically on both peers. Same map, same
        // roster, same requests, same tick count -- every one-second hash must
        // agree. This is the lockstep contract the budget must not break.
        com.xjzb.rts.core.Game d1 = cleanGame("terran");
        com.xjzb.rts.core.Game d2 = cleanGame("terran");
        float[] dob = openGround(d1, 420f);
        boolean qdet = false;
        if (dob != null) {
            List<com.xjzb.rts.core.Game.Ent> c1 = new ArrayList<>();
            List<com.xjzb.rts.core.Game.Ent> c2 = new ArrayList<>();
            for (int i = 0; i < 40; i++) {
                c1.add(d1.spawn("marine", 0, dob[0] + (i % 8) * 8, dob[1] + (i / 8) * 8, true));
                c2.add(d2.spawn("marine", 0, dob[0] + (i % 8) * 8, dob[1] + (i / 8) * 8, true));
            }
            for (com.xjzb.rts.core.Game.Ent e : c1) d1.queuePath(e, dob[0] + 400f, dob[1]);
            for (com.xjzb.rts.core.Game.Ent e : c2) d2.queuePath(e, dob[0] + 400f, dob[1]);
            boolean sameQ = true;
            int samples = 0;
            for (int t = 0; t < 30 * 12; t++) {
                d1.update(1 / 30f);
                d2.update(1 / 30f);
                if (t % 30 == 29) {
                    samples++;
                    if (d1.stateHash() != d2.stateHash()) { sameQ = false; break; }
                }
            }
            qdet = sameQ && samples >= 10 && d1.statPathQueued > 0 && d1.statPathDrains > 0;
        }
        pok &= qdet;
        pb.append(" det=").append(qdet)
          .append("(queued ").append(d1.statPathQueued)
          .append(" drains ").append(d1.statPathDrains).append(')');

        System.out.println("  [v243] pathbudget" + pb + " PASS=" + pok);
        v243RenderTest();
    }

    /**
     * v2.43 P1/P2 render-path invariants, pinned by source shape.
     *
     * These are the changes whose failure mode is invisible in a desktop
     * harness: a cull gate that is too tight clips sprites at the screen edge,
     * a fog throttle that never re-arms freezes the fog, and a frame-alignment
     * slip silently puts the old +14 ms floor back. None of them throw, and
     * none of them change a simulation number, so they are checked here.
     */
    static void v243RenderTest() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();
        String root = "F:/KF/XJZB/AndroidPort/";
        String gv = new String(Files.readAllBytes(java.nio.file.Paths.get(
                root + "app/app/src/main/java/com/xjzb/rts/GameView.java")),
                java.nio.charset.StandardCharsets.UTF_8);

        // ---- 1: the viewport cull gate --------------------------------------
        // The three-argument core has to exist, and the entity gate has to feed
        // it asymmetric extents (a symmetric one drops tall sprites whose base
        // is just off the bottom edge).
        boolean gateShape = gv.contains("private boolean offScreen(float wx, float wy, float halfW, float above, float below)")
                && gv.contains("private boolean offScreen(float wx, float wy, SpriteBank.Sprite s, float scale)")
                && gv.contains("private boolean offScreenEnt(Game.Ent e)")
                && gv.contains("private int frameW, frameH;")
                && gv.contains("frameW = W;")
                && gv.contains("frameH = H;");
        // The extents must come from the sheet cell, not a guessed constant,
        // for the sites that already hold a Sprite...
        boolean cellExtents = gv.contains("float w = s.fw * zoom * scale, h = s.fh * zoom * scale;")
                && gv.contains("return offScreen(wx, wy, w / 2f, h * 0.65f, h * 0.35f);");
        // ...and the entity gate must bound by the widest shipped cell rather
        // than resolving a sprite (a bank.get() per entity per frame rebuilds a
        // "#e" key String for every enemy, which is what this release removes).
        int entGate = gv.indexOf("private boolean offScreenEnt(Game.Ent e) {");
        int entGateEnd = entGate < 0 ? -1 : gv.indexOf("\n    }", entGate);
        boolean noPerFrameLookup = entGate >= 0 && entGateEnd > entGate
                && !gv.substring(entGate, entGateEnd).contains("bank.get(")
                && gv.contains("private static final float MAX_CELL = 256f;")
                && gv.contains("float half = MAX_CELL * zoom * 0.5f;");
        // Every world loop that walks a whole collection must be gated. Count
        // the gates rather than trusting one of them: a loop that loses its
        // gate silently goes back to transforming the entire map.
        int gates = 0;
        for (String call : new String[]{
                "if (offScreen(m.x, m.y, s, 1f)) continue;",
                "if (offScreen(cp.x, cp.y, s, 1f)) continue;",
                "if (offScreen(a.x, a.y, s, a.scale)) continue;",
                "!offScreenEnt(e)) drawEnt(c, e);"})
            if (gv.contains(call)) gates++;
        // the two drawEnt call sites plus the four above
        boolean gated = gates == 4
                && gv.indexOf("!offScreenEnt(e)) drawEnt(c, e);")
                   != gv.lastIndexOf("!offScreenEnt(e)) drawEnt(c, e);");
        boolean cull = gateShape && cellExtents && noPerFrameLookup && gated;
        ok &= cull;
        sb.append(" cull=").append(cull);
        if (!cull)
            sb.append("{shape=").append(gateShape ? "" : "0")
              .append("cell=").append(cellExtents ? "" : "0")
              .append("lookup=").append(noPerFrameLookup ? "" : "0")
              .append("gates=").append(gates).append('}');

        // ---- 2: the fog throttle --------------------------------------------
        // Both gates have to be there: HOK skips the bitmap outright, SC
        // rebuilds at most 10x/s, and the restart arm (`game.time < fogBuiltAt`)
        // is what stops a new match from freezing the fog forever after the
        // clock goes back to 0.
        boolean fogGate = gv.contains("private static final float FOG_REBUILD_INTERVAL = 0.1f;")
                && gv.contains("private float fogBuiltAt = -1f;")
                && gv.contains("boolean fogOn = settings.fogStyle != Settings.FOG_HOK;")
                && gv.contains("fogBuiltAt < 0f || game.time < fogBuiltAt")
                && gv.contains("|| game.time - fogBuiltAt >= FOG_REBUILD_INTERVAL)")
                && gv.contains("updateFogBitmap();\n            fogBuiltAt = game.time;");
        // the minimap shares the bitmap, so it needs the same HOK guard or it
        // keeps showing the stale SC fog after the style is switched
        boolean fogMinimap = gv.contains("if (fogBmp != null && settings.fogStyle != Settings.FOG_HOK) {");
        // and the rebuild must no longer be unconditional
        boolean fog = fogGate && fogMinimap
                && !gv.contains("\n        updateFogBitmap();\n");
        ok &= fog;
        sb.append(" fog=").append(fog);
        if (!fog)
            sb.append("{gate=").append(fogGate ? "" : "0")
              .append("mini=").append(fogMinimap ? "" : "0").append('}');

        // ---- 3: frame alignment ---------------------------------------------
        // The old form slept a flat 14 ms AFTER the work, so a 5 ms frame ran
        // at ~52 fps. The new one sleeps only the remainder of a 16 ms budget.
        boolean frame = gv.contains("long workMs = (System.nanoTime() - frameStart) / 1000000L;")
                && gv.contains("long sleepMs = 16L - workMs;")
                && gv.contains("if (sleepMs > 0) {")
                && !gv.contains("Thread.sleep(14);");
        ok &= frame;
        sb.append(" frame=").append(frame);

        // ---- 4: scratch rects -----------------------------------------------
        // Rect.set() returns void, so a scratch rect has to be bound to a local
        // first; `drawBitmap(sheet, r.set(...), ...)` does not compile. This
        // checks the fields exist and that the world loops stopped allocating:
        // a `new Rect()` inside render() is the regression.
        boolean scratch = gv.contains("private final Rect tmpSrc = new Rect();")
                && gv.contains("private final Rect tmpDst = new Rect();")
                && gv.contains("private final Rect tmpDst2 = new Rect();");
        int rb = gv.indexOf("private void render(Canvas c) {");
        int re = rb < 0 ? -1 : gv.indexOf("private void drawDiagPanel", rb);
        int allocs = 0;
        if (rb >= 0 && re > rb) {
            String body = gv.substring(rb, re);
            for (int i = body.indexOf("new Rect()"); i >= 0; i = body.indexOf("new Rect()", i + 1)) allocs++;
        }
        boolean rects = scratch && allocs == 0;
        ok &= rects;
        sb.append(" rects=").append(rects);
        if (!rects) sb.append("{allocs=").append(allocs).append('}');

        System.out.println("  [v243] render" + sb + " PASS=" + ok);
    }

    /**
     * [v244] the map / pathing / gas release. Four groups:
     *
     *   walk   -- the SHIPPED walk.bin of every map connects its starts under
     *             the engine's own rule (nearestPassMini snap, no corner-cut).
     *             pipeline_maps used to gate a relaxed bitmap (fill + dilate)
     *             and ship the raw one, so The Small Divide played with its
     *             two bases on separate landmasses: patrols froze, workers
     *             starved, and no attack wave could ever cross.
     *   tether -- a terran builder walking to its site must never open fire on
     *             it. The v2.44 edge-distance range test widened "in range"
     *             past the tether's catch radius and an SCV shot its own
     *             half-built refinery dead (hp starts at 1).
     *   gas    -- a completed refinery staffs itself (auto-assign up to 3
     *             workers), the loads deliver as gas, and a worker tapped on
     *             the gas building harvests its geyser. This is the match-side
     *             half of "对局内无法获得瓦斯": the delivery machinery existed
     *             but nothing ever sent a worker, and tapping the refinery
     *             selected the building instead of harvesting.
     *   return -- a worker's mine->deliver->mine loop actually closes on
     *             divide (the building-collider used to sit half a tile off
     *             the walkable footprint and pinned the trip home forever).
     */
    static void v244Tests() throws Exception {
        StringBuilder sb = new StringBuilder();
        boolean ok = true;

        // ---- walk: every shipped map, engine rule, shipped bytes
        String[] maps = {"bloodbath", "bottleneck", "boxer", "hunters", "darkcrystal",
                "river", "3kingdoms", "divide", "cyclone", "volcanis"};
        StringBuilder wsb = new StringBuilder();
        boolean wallOk = true;
        for (String mid : maps) {
            readMapById(mid);
            boolean c = startsConnected(game, starts) && resourcesReachable(game, starts);
            wallOk &= c;
            wsb.append(mid).append(c ? "=ok " : "=bad ");
        }
        ok &= wallOk;
        sb.append(" walk").append(wallOk).append('(').append(wsb.toString().trim()).append(')');

        // ---- tether: the builder never fires on its own constructing site
        readMapById("divide");
        com.xjzb.rts.core.Game.Mineral gey = null;
        float gbd = Float.MAX_VALUE;
        for (com.xjzb.rts.core.Game.Mineral m : game.minerals) {
            if (m.variant < 3 || m.amount <= 0 || m.refinery != null) continue;
            float d = (m.x - starts.get(0)[0]) * (m.x - starts.get(0)[0])
                    + (m.y - starts.get(0)[1]) * (m.y - starts.get(0)[1]);
            if (d < gbd) { gbd = d; gey = m; }
        }
        boolean tetherOk = gey != null;
        if (tetherOk) {
            game.mineralsPlayer = 500;
            com.xjzb.rts.core.Game.Ent scv = game.spawn("scv", 0,
                    gey.x - 120, gey.y + 96, true);
            tetherOk = game.tryBuild(scv, "refinery", gey.x, gey.y);
            if (tetherOk) {
                for (int t = 0; t < 1200 && gey.refinery != null
                        && gey.refinery.buildProgress < 1f; t++) game.update(1 / 30f);
                // the site survived its own builder
                tetherOk = gey.refinery != null && gey.refinery.alive()
                        && gey.refinery.buildProgress >= 1f;
            }
        }
        ok &= tetherOk;
        sb.append(" tether=").append(tetherOk);

        // ---- gas: auto-staff delivers gas; the manual tap harvests too
        boolean gasOk = false, manualOk = false;
        if (tetherOk) {
            int g0 = game.gasPlayer;
            for (int t = 0; t < 3600 && game.gasPlayer == g0; t++) game.update(1 / 30f);
            gasOk = game.gasPlayer > g0;
            for (int t = 0; t < 2400; t++) game.update(1 / 30f);
            com.xjzb.rts.core.Game.Ent scv2 = game.spawn("scv", 0,
                    starts.get(0)[0] + 40, starts.get(0)[1] + 40, true);
            boolean can = game.gasHarvestable(gey);
            game.orderHarvest(java.util.Collections.singletonList(scv2), gey);
            for (int t = 0; t < 2400 && scv2.carrying == 0
                    && scv2.workerState != 3; t++) game.update(1 / 30f);
            manualOk = can && (scv2.carrying > 0 || scv2.workerState == 3);
        }
        ok &= gasOk && manualOk;
        sb.append(" gas=").append(gasOk).append(" manual=").append(manualOk);

        // ---- return: the mine -> deliver -> mine loop closes
        readMapById("divide");
        boolean retOk = false;
        // the 5-arg constructor opens terran, so there is no drone to find --
        // spawn one on the first start and hand it the nearest patch (the same
        // thing a zerg opening would exercise).
        com.xjzb.rts.core.Game.Ent drone = game.spawn("drone", 0,
                starts.get(0)[0] + 48, starts.get(0)[1] + 48, true);
        com.xjzb.rts.core.Game.Mineral patch = null;
        if (drone != null) {
            float bd = Float.MAX_VALUE;
            for (com.xjzb.rts.core.Game.Mineral m : game.minerals) {
                if (m.amount <= 0 || m.variant >= 3) continue;
                float d = (m.x - drone.x) * (m.x - drone.x) + (m.y - drone.y) * (m.y - drone.y);
                if (d < bd) { bd = d; patch = m; }
            }
        }
        if (patch != null) {
            game.orderHarvest(java.util.Collections.singletonList(drone), patch);
            for (int t = 0; t < 2000 && game.mineralsMined == 0; t++) game.update(1 / 30f);
            retOk = game.mineralsMined > 0;
        }
        ok &= retOk;
        sb.append(" return=").append(retOk);

        System.out.println("  [v244] walk/tether/gas/return" + sb + " PASS=" + ok);
    }

    /**
     * [v244] engine-faithful start connectivity on the shipped walk bitmap:
     * flood from the first start's nearestPassMini snap, then require every
     * other start's snap inside the flood. Diagonal steps need both orthogonal
     * neighbours walkable, exactly like Game.findPathCapped -- a flood without
     * that rule squeezes through diagonal seams the engine cannot.
     */
    static boolean startsConnected(com.xjzb.rts.core.Game g, java.util.List<int[]> st) {
        int w = g.wMini, h = g.hMini;
        int[] s0 = snapPass(g, (int) (st.get(0)[0] / 8), (int) (st.get(0)[1] / 8));
        if (s0 == null) return false;
        boolean[] seen = new boolean[w * h];
        java.util.ArrayDeque<int[]> dq = new java.util.ArrayDeque<>();
        seen[s0[1] * w + s0[0]] = true;
        dq.add(s0);
        int[][] orth = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
        int[][] diag = {{1, 1}, {1, -1}, {-1, 1}, {-1, -1}};
        while (!dq.isEmpty()) {
            int[] c = dq.poll();
            for (int[] d : orth) {
                int nx = c[0] + d[0], ny = c[1] + d[1];
                if (g.passMini(nx, ny) && !seen[ny * w + nx]) {
                    seen[ny * w + nx] = true;
                    dq.add(new int[]{nx, ny});
                }
            }
            for (int[] d : diag) {
                int nx = c[0] + d[0], ny = c[1] + d[1];
                if (g.passMini(nx, ny) && !seen[ny * w + nx]
                        && g.passMini(c[0] + d[0], c[1])
                        && g.passMini(c[0], c[1] + d[1])) {
                    seen[ny * w + nx] = true;
                    dq.add(new int[]{nx, ny});
                }
            }
        }
        for (int i = 1; i < st.size(); i++) {
            int[] s = snapPass(g, (int) (st.get(i)[0] / 8), (int) (st.get(i)[1] / 8));
            if (s == null || !seen[s[1] * w + s[0]]) return false;
        }
        return true;
    }

    /**
     * [v244] every START must have a reachable resource patch near it -- a
     * spawn whose opening minerals sit in a sealed pocket starves no matter
     * how it is played. Far decorative clusters (volcanis grows several in
     * sealed lava pockets, exactly like the retail map) are not required to
     * connect: opening a path to them would carve the map up.
     */
    static boolean resourcesReachable(com.xjzb.rts.core.Game g, java.util.List<int[]> st) {
        int w = g.wMini, h = g.hMini;
        int[] s0 = snapPass(g, (int) (st.get(0)[0] / 8), (int) (st.get(0)[1] / 8));
        if (s0 == null) return false;
        boolean[] seen = new boolean[w * h];
        java.util.ArrayDeque<int[]> dq = new java.util.ArrayDeque<>();
        seen[s0[1] * w + s0[0]] = true;
        dq.add(s0);
        int[][] orth = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
        int[][] diag = {{1, 1}, {1, -1}, {-1, 1}, {-1, -1}};
        while (!dq.isEmpty()) {
            int[] c = dq.poll();
            for (int[] d : orth) {
                int nx = c[0] + d[0], ny = c[1] + d[1];
                if (g.passMini(nx, ny) && !seen[ny * w + nx]) {
                    seen[ny * w + nx] = true;
                    dq.add(new int[]{nx, ny});
                }
            }
            for (int[] d : diag) {
                int nx = c[0] + d[0], ny = c[1] + d[1];
                if (g.passMini(nx, ny) && !seen[ny * w + nx]
                        && g.passMini(c[0] + d[0], c[1])
                        && g.passMini(c[0], c[1] + d[1])) {
                    seen[ny * w + nx] = true;
                    dq.add(new int[]{nx, ny});
                }
            }
        }
        for (int i = 0; i < st.size(); i++) {
            boolean fed = false;
            for (com.xjzb.rts.core.Game.Mineral m : g.minerals) {
                if (m.amount <= 0) continue;
                float dx = m.x - st.get(i)[0], dy = m.y - st.get(i)[1];
                if (dx * dx + dy * dy > 600 * 600) continue;
                int[] s = snapPass(g, (int) m.x / 8, (int) m.y / 8);
                if (s != null && seen[s[1] * w + s[0]]) { fed = true; break; }
            }
            if (!fed) return false;
        }
        return true;
    }

    /** Game.nearestPassMini mirror: closest walkable minitile within r=24. */
    static int[] snapPass(com.xjzb.rts.core.Game g, int x, int y) {
        for (int r = 0; r <= 24; r++) {
            int[] best = null;
            float bd = Float.MAX_VALUE;
            for (int dy = -r; dy <= r; dy++)
                for (int dx = -r; dx <= r; dx++)
                    if (g.passMini(x + dx, y + dy)) {
                        float d = dx * dx + dy * dy;
                        if (d < bd) { bd = d; best = new int[]{x + dx, y + dy}; }
                    }
            if (best != null) return best;
        }
        return null;
    }

    /** [v244] no live building within ~40px of (wx, wy): a tile the terrain
     * calls walkable can still sit under a structure this session built. */
    static boolean spotClear(float wx, float wy) {
        for (com.xjzb.rts.core.Game.Ent e : game.ents) {
            if (!e.alive() || !e.isBuilding()) continue;
            if (Math.abs(e.x - wx) < e.type.tiles * 16 + 24
                    && Math.abs(e.y - wy) < e.type.tiles * 16 + 24) return false;
        }
        return true;
    }

    /** Rebuild the game on another shipped map (v244 walk audit). */
    static void readMapById(String id) throws Exception {
        mapId = id;
        readMap();
        game = new com.xjzb.rts.core.Game(mapW, mapH, walk, starts, units);
    }

    /**
     * The pre-v2.43 full-roster walk, kept as the reference the grid has to
     * match. Deliberately a literal copy of the gates: if the two ever drift,
     * this test is what says so.
     */
    static com.xjzb.rts.core.Game.Ent bruteFindEnemy(com.xjzb.rts.core.Game g,
            float ox, float oy, com.xjzb.rts.core.Game.Ent e, float range) {
        com.xjzb.rts.core.Game.Ent best = null;
        float bd = range * range;
        for (com.xjzb.rts.core.Game.Ent o : g.ents) {
            if (o.team == e.team || !o.alive() || o.constructing) continue;
            if (o.cargoOf != null || o.garrisoned) continue;
            if (o.cloakActive && !o.spotted) continue;
            if (o.type.flying && e.type.range < 64) continue;
            if (e.type.airOnly && !o.type.flying) continue;
            if (e.type.groundOnly && o.type.flying) continue;
            if (com.xjzb.rts.core.Game.isBurrowed(o) && e.type.range < 64) continue;
            float dx = o.x - ox, dy = o.y - oy;
            float d2 = dx * dx + dy * dy;
            if (d2 < bd) {
                bd = d2;
                best = o;
            }
        }
        return best;
    }

    /** The same full-roster walk splash() used before the grid. */
    static void bruteSplash(com.xjzb.rts.core.Game g, float x, float y, int dmg,
            String dmgType, com.xjzb.rts.core.Game.Ent from, float radius,
            float falloff, com.xjzb.rts.core.Game.Ent primary) {
        if (radius <= 0) return;
        float r2 = radius * radius;
        for (com.xjzb.rts.core.Game.Ent o : g.ents) {
            if (o == primary || o == from || !o.alive() || o.constructing) continue;
            if (com.xjzb.rts.core.Game.offField(o)) continue;
            float dx = o.x - x, dy = o.y - y;
            float d2 = dx * dx + dy * dy;
            if (d2 > r2) continue;
            float d = (float) Math.sqrt(d2);
            float mul = falloff + (1f - falloff) * (1f - d / radius);
            int hit = (int) (dmg * mul);
            if (hit < 1) hit = 1;
            g.damage(o, hit, from, dmgType);
        }
    }

    /**
     * A roster fanned out from (1000, 1000) so a burst hits some of it and
     * misses the rest, built twice for the splash comparison. No tick is run:
     * the grid rebuilds lazily on the first query, and skipping update() keeps
     * the AI from walking the targets out from under the measurement.
     */
    static com.xjzb.rts.core.Game splashScene() {
        com.xjzb.rts.core.Game g = cleanGame("terran");
        for (int i = 0; i < 30; i++) {
            double a = i * 0.7;
            float r = 20f + i * 6f;
            g.spawn("zergling", 1, 1000f + (float) Math.cos(a) * r,
                    1000f + (float) Math.sin(a) * r, true);
        }
        return g;
    }

    /** A roster big enough to engage the idle-acquire stagger, built twice. */
    static com.xjzb.rts.core.Game bigRoster() {
        com.xjzb.rts.core.Game g = cleanGame("terran");
        for (int i = 0; i < 40; i++)
            g.spawn("marine", 0, 400 + (i % 8) * 24, 500 + (i / 8) * 24, true);
        return g;
    }

    /**
     * The largest clear-colour gap the chunk grid leaves along one axis, in
     * screen px, when the chunk on the low side of every seam is drawn from
     * (zL, camL) and the one on the high side from (zR, camR). Mirrors the dst
     * arithmetic in GameView.render(): floor on both edges, then the bleed is
     * added to the far edge only. A negative result means the seams overlap.
     */
    static int seamGap(float zL, float camL, float zR, float camR,
                       int extent, float center, int cs) {
        int worst = Integer.MIN_VALUE;
        for (int c = 0; c * cs + cs < extent; c++) {
            float w = c * cs + cs;
            int far = (int) Math.floor((w - camL) * zL + center) + 4;
            int near = (int) Math.floor((w - camR) * zR + center);
            worst = Math.max(worst, near - far);
        }
        return worst;
    }
    /**
     * The width the selection card asks for, mirroring drawBottomWidgets().
     * A single selection and a uniform multi-selection both stop at
     * INFO_CAP_DP; only a mixed group is allowed past it, and then only by
     * the per-kind filter row it has to draw (one cell per kind, six kinds
     * maximum). The floor of 90dp is the same as the app's.
     */
    static float infoPanelW(int kinds, float stripW, float k, float panelH) {
        float cap = 165f * k;
        if (kinds > 1) {
            float cellS = Math.max(18 * k, Math.min(30 * k, panelH - 48 * k));
            cap = Math.max(cap,
                    20 * k + kinds * cellS + Math.max(0, kinds - 1) * 5 * k);
        }
        return Math.max(Math.min(stripW, cap), 90 * k);
    }
    /**
     * v2.21: the four tester findings from the 2.20 build.
     *
     * #1 camera black edges -- the clamp covers the whole screen for every
     *    preset AND a custom layout (mirrored arithmetic, same as the app);
     * #2 card S/M/L -- the cell edge derived from the card rect equals
     *    cardCell() for the presets and the S/M/L multiplier for the custom
     *    layout, so the icons can no longer stay M inside an L frame;
     * #3 info panel -- the custom layout's content scale is the S/M/L
     *    multiplier and 1 for the presets;
     * #4 HOK enemies -- always drawn (the gate is a constant in that mode),
     *    while the SC mode still hides what stands on unexplored ground.
     */
    static void v221Tests() {
        int W = 1280, H = 720, dp = 2;
        float topH = 40 * dp;
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- #2: the cell edge the app now derives from hud.card.width()
        for (int preset = 0; preset < 3; preset++) {
            float[] r = layoutMirror(W, H, topH, dp, preset);
            float cardW = r[6] - r[4];
            float gap = 4 * dp;
            float cs = (cardW - 2 * gap) / 3f;
            float want = HudLayoutCardCell(H, dp);
            boolean same = Math.abs(cs - want) < 0.01f;
            ok &= same;
            sb.append(" p").append(preset).append(" cs=").append((int) cs);
        }
        // custom L: the placed card is CARD_CELL_DP * dp * 1.25 wide
        float cellL = 50f * dp * 1.25f;
        float cardWL = 3 * cellL + 2 * 4 * dp;
        boolean customL = Math.abs((cardWL - 2 * 4 * dp) / 3f - cellL) < 0.01f;
        ok &= customL;
        sb.append(" customL=").append(customL);

        // ---- #3: info scale -- presets 1 (handled by the cs loop above); the
        // custom layout's multiplier is asserted through customL (the placed
        // info rect is INFO_*_DP * dp * the same SIZE_SCALE entry).

        // ---- #1b: v2.41 -- the playfield is the whole screen even for a
        // CUSTOM layout: the envelope centre is H/2 wherever the panels sit,
        // so the camera clamp keeps terrain under every pixel.
        float[] spec = {0.12f, 0.86f, 2f, 0.88f, 0.86f, 1f, 0.50f, 0.75f, 2f,
                0.50f, 0.05f, 1f, 0.28f, 0.05f, 1f};
        float[] r = layoutCustomMirror(W, H, topH, dp, spec);
        float centerY = r[20];
        float hPx = 128 * 32f;
        boolean centreOk = Math.abs(centerY - H / 2f) < 0.5f;
        for (float zoom : new float[]{1.0f, 1.3f, 2.0f}) {
            float halfTop = centerY / zoom, halfBot = (H - centerY) / zoom;
            float camBot = Math.max(halfTop, hPx - halfBot);
            float sy0 = (0 - halfTop) * zoom + centerY;
            float syH = (hPx - camBot) * zoom + centerY;
            boolean topOk = sy0 <= 0.5f, botOk = syH >= H - 0.5f;
            ok &= topOk && botOk;
            sb.append(" cust/z").append(zoom).append(topOk && botOk ? "=ok" : "=FAIL");
        }
        ok &= centreOk;
        sb.append(" cyMid=").append(centreOk);

        // ---- #4: the HOK gate is unconditional; the SC gate still reads fog
        boolean hokAlways = enemyGateMirror(true, 0);
        boolean scHidden = !enemyGateMirror(false, 0);
        boolean scShown = enemyGateMirror(false, 2);
        ok &= hokAlways && scHidden && scShown;
        sb.append(" hok=").append(hokAlways).append(" scHidden=").append(scHidden)
                .append(" scShown=").append(scShown);

        System.out.println("  card cells follow panel, info scale, full-screen"
                + " clamp on custom, HOK always-visible" + sb + " PASS=" + ok);
    }

    /** Mirror of GameView.enemyVisible for the two fog styles. */
    static boolean enemyGateMirror(boolean hok, int fog) {
        if (hok) return true;
        return fog != 0;
    }

    /** v2.13 batch D: doodad placements + the wide-map dimension guard. */
    static void mapDataTests() throws Exception {
        java.util.List<String> lines = java.nio.file.Files.readAllLines(
                java.nio.file.Paths.get(ASSETS + "/maps/river/meta.txt"));
        int w = 0, h = 0, doodads = 0, starts = 0;
        for (String line : lines) {
            line = line.trim();
            if (line.startsWith("w=")) w = Integer.parseInt(line.substring(2));
            else if (line.startsWith("h=")) h = Integer.parseInt(line.substring(2));
            else if (line.startsWith("start=")) starts++;
            else if (line.startsWith("doodad=")) {
                String[] p = line.substring(7).split(",");
                boolean ok = p.length == 3;
                for (String s : ok ? p : new String[0]) Integer.parseInt(s);
                if (ok) doodads++;
            }
        }
        boolean pass = (w == 96 && h == 256 && starts == 2 && doodads == 187);
        System.out.println("[maps]");
        System.out.println("  river dims=" + w + "x" + h + " starts=" + starts
                + " doodads=" + doodads + " PASS=" + pass);

        int bb = 0;
        for (String line : java.nio.file.Files.readAllLines(
                java.nio.file.Paths.get(ASSETS + "/maps/boxer/meta.txt")))
            if (line.startsWith("doodad=")) bb++;
        System.out.println("  boxer doodads=" + bb + " (DD2 census, art map pending) PASS="
                + (bb == 77));
    }

    /**
     * v2.15: the device-side regression that cost v2.10-v2.14 their real
     * device testing. SpriteBank used to decode EVERY manifest row (both team
     * variants) in its constructor -- ~340 MB of decoded bitmaps, past the
     * Android heap. BitmapFactory silently returns null once the heap is
     * gone, so on a phone everything past the ceiling was invisible: units
     * ("no enemies"), terrain chunks ("no map"), and the roster that was
     * supposed to prove the race picker worked. The bank now decodes lazily,
     * and this section pins the budget it must keep:
     *   - no single sheet may decode past 16 MB (a 4096-wide sheet slips in
     *     through a pipeline mistake),
     *   - the opening screen (base + first card icons) must fit ~48 MB,
     *   - the full set is printed so its growth stays visible.
     * The harness mirrors SpriteBank's decode policy from the manifest; the
     * Android side is the one that has to obey it.
     */
    static void memoryTests() throws Exception {
        System.out.println("[memory]");
        long full = 0, worst = 0;
        String worstKey = "-";
        int oversized = 0;
        for (String key : manifest.keySet()) {
            for (boolean enemy : new boolean[]{false, true}) {
                java.awt.image.BufferedImage im = sheet(key, enemy);
                if (im == null) continue;
                long bytes = (long) im.getWidth() * im.getHeight() * 4L;
                full += bytes;
                if (bytes > worst) { worst = bytes; worstKey = key; }
                if (bytes > 16L * 1024 * 1024) oversized++;
            }
        }
        long opening = 0;
        for (String key : new String[]{"cc", "scv", "barracks", "marine",
                                       "mineral", "mineral2", "mineral3",
                                       "geyser", "stank"}) {
            java.awt.image.BufferedImage im = sheet(key, false);
            if (im != null) opening += (long) im.getWidth() * im.getHeight() * 4L;
        }
        System.out.println("  full roster decode footprint: " + full / 1024 / 1024
                + " MB across " + manifest.size() + " keys; worst " + worstKey
                + " " + worst / 1024 / 1024 + " MB; oversized(>16MB)=" + oversized
                + " PASS=" + (oversized == 0));
        boolean openingOk = opening < 48L * 1024 * 1024;
        System.out.println("  opening-screen footprint: " + opening / 1024 / 1024
                + " MB (budget 48) PASS=" + openingOk);
    }

    /**
     * v2.14 batch 1 assertions: combat depth.
     *
     * Each spell runs in its own clean game so that one caster's shared
     * cooldown (EMP and irradiate both spend `empCd`, because a science vessel
     * only ever gets one cast off) cannot mask the next gate.
     *
     *   1. damage type x unit size -- the SC counter table, and the size tags
     *      the post-pass hands out.
     *   2. splash falloff -- a victim nearer the impact takes more than one
     *      further out, and the primary is really skipped.
     *   3. the hold order -- pins the spot, acquires with the exact weapon
     *      range (no +30 grace), and walks the unit home when displaced.
     *   4. the five caster spells -- EMP, irradiate, yamato, lockdown, d-web.
     *   5. the four skirmish-AI behaviours -- wave tagging, the 60% retreat
     *      rule, base defence, and the tech ladder.
     */
    static void depthTests() throws Exception {
        // ============================================ 1. damage type x size
        boolean mult = com.xjzb.rts.core.Game.typeMultiplier("explosive", "large") == 1.0f
                && com.xjzb.rts.core.Game.typeMultiplier("explosive", "small") == 0.5f
                && com.xjzb.rts.core.Game.typeMultiplier("explosive", "medium") == 0.75f
                && com.xjzb.rts.core.Game.typeMultiplier("concussive", "large") == 0.25f
                && com.xjzb.rts.core.Game.typeMultiplier("concussive", "small") == 1.0f
                && com.xjzb.rts.core.Game.typeMultiplier("concussive", "medium") == 0.5f
                && com.xjzb.rts.core.Game.typeMultiplier("normal", "large") == 1.0f
                && com.xjzb.rts.core.Game.typeMultiplier(null, "large") == 1.0f;
        System.out.println("  typeMultiplier explosive/concussive x small/med/large PASS=" + mult);

        boolean tags = com.xjzb.rts.core.Game.TYPES.get("tank").size.equals("large")
                && com.xjzb.rts.core.Game.TYPES.get("marine").size.equals("small")
                && com.xjzb.rts.core.Game.TYPES.get("hatchery").size.equals("large")
                && com.xjzb.rts.core.Game.TYPES.get("vessel").size.equals("large")
                && com.xjzb.rts.core.Game.TYPES.get("corsair").size.equals("small")
                && com.xjzb.rts.core.Game.TYPES.get("tank").dmgType.equals("explosive")
                && com.xjzb.rts.core.Game.TYPES.get("marine").dmgType.equals("concussive")
                && com.xjzb.rts.core.Game.TYPES.get("dragoon").dmgType.equals("normal");
        System.out.println("  size/dmgType tags PASS=" + tags);

        com.xjzb.rts.core.Game gd = cleanGame("terran");
        int td = gd.typedDamage(35, "explosive", "small");
        int tc = gd.typedDamage(5, "concussive", "large");
        boolean typed = td == 17 && tc == 1;
        System.out.println("  typedDamage 35 explosive/small=" + td
                + " 5 concussive/large=" + tc + " PASS=" + typed);

        // the same 20 damage against the same two bodies, twice: explosive is
        // halved on the small one, concussive is quartered on the large one.
        com.xjzb.rts.core.Game.Ent small = gd.spawn("zergling", 1, 600, 600, true);
        com.xjzb.rts.core.Game.Ent big = gd.spawn("ultra", 1, 900, 900, true);
        gd.damage(small, 20, null, "explosive");
        gd.damage(big, 20, null, "explosive");
        boolean smallHit = small.hp == 25;                 // 20 -> 10, armor 0
        boolean bigHit = big.hp == 383;                    // 20 -> 20, armor 3
        gd.damage(big, 20, null, "concussive");
        gd.damage(small, 20, null, "concussive");
        boolean bigCon = big.hp == 381;                    // 20 -> 5, armor 3
        boolean smallCon = small.hp == 5;                  // 20 -> 20, armor 0
        boolean applied = smallHit && bigHit && bigCon && smallCon;
        System.out.println("  applied explosive small=" + smallHit + " large=" + bigHit
                + " concussive large=" + bigCon + " small=" + smallCon
                + " PASS=" + applied);

        // ================================================== 2. splash
        boolean splashTag = com.xjzb.rts.core.Game.TYPES.get("tank").splashR == 40f
                && com.xjzb.rts.core.Game.TYPES.get("tank").splashFalloff == 0.5f
                && com.xjzb.rts.core.Game.TYPES.get("firebat").splashR == 32f
                && com.xjzb.rts.core.Game.TYPES.get("turret").splashR == 0f;
        System.out.println("  splashR tank=40 firebat=32 turret=0 PASS=" + splashTag);

        com.xjzb.rts.core.Game gs = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent near = gs.spawn("zergling", 1, 1010, 1000, true);
        com.xjzb.rts.core.Game.Ent far = gs.spawn("zergling", 1, 1035, 1000, true);
        gs.splash(1000f, 1000f, 40, "explosive", null, 40f, 0.5f, null);
        boolean nearMore = near.hp == 18 && far.hp == 24 && near.hp < far.hp;
        System.out.println("  splash falloff near(10px)=" + near.hp + " far(35px)=" + far.hp
                + " PASS=" + nearMore);

        // the primary is excluded by identity, not by distance
        com.xjzb.rts.core.Game.Ent prim = gs.spawn("zergling", 1, 1400, 1400, true);
        gs.splash(1400f, 1400f, 40, "explosive", null, 40f, 0.5f, prim);
        boolean skipped = prim.hp == 35;
        System.out.println("  splash skips primary PASS=" + skipped);

        // ================================================== 3. hold order
        com.xjzb.rts.core.Game gh = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent hMarine = gh.spawn("marine", 0, 1000, 1000, true);
        List<com.xjzb.rts.core.Game.Ent> one = new ArrayList<>();
        one.add(hMarine);
        gh.orderHold(one);
        boolean held = hMarine.holding && hMarine.holdX == 1000f && hMarine.holdY == 1000f
                && !hMarine.moving && hMarine.target == null;
        // displaced with nothing to shoot, it walks back to the post
        hMarine.x = 1040f;
        gh.update(1f / 30f);
        boolean walksHome = Math.abs(hMarine.goalX - 1000f) < 1f
                && Math.abs(hMarine.goalY - 1000f) < 1f;
        for (int k = 0; k < 90; k++) gh.update(1f / 30f);   // settle back on the post
        // 110px is inside range+30 (126) but outside range (96): an idle marine
        // would take the bait, a holding one must not, because it cannot commit
        // to a target it would then have to walk toward.
        com.xjzb.rts.core.Game.Ent bait = gh.spawn("zergling", 1, 1110, 1000, true);
        for (int k = 0; k < 12; k++) gh.update(1f / 30f);
        boolean noChase = hMarine.target == null;
        gh.stopHold(hMarine);
        for (int k = 0; k < 12; k++) gh.update(1f / 30f);
        boolean acquires = hMarine.target == bait;
        boolean cHold = held && walksHome && noChase && acquires;
        System.out.println("  hold held=" + held + " walks-home=" + walksHome
                + " no-chase=" + noChase + " acquires-after-release=" + acquires
                + " PASS=" + cHold);

        // orderMove must clear the flag, or a held unit could never be sent away
        gh.orderHold(one);
        gh.orderMove(one, 1300, 1000, false);
        boolean cleared = !hMarine.holding;
        System.out.println("  orderMove clears hold PASS=" + cleared);

        // ================================================== 4a. EMP
        com.xjzb.rts.core.Game ge = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent vessel = ge.spawn("vessel", 0, 1000, 1000, true);
        fullEnergy(vessel);   // v2.22: casters test at a full pool
        com.xjzb.rts.core.Game.Ent zShield = ge.spawn("zealot", 1, 1040, 1000, true);
        com.xjzb.rts.core.Game.Ent pShield = ge.spawn("probe", 0, 970, 1000, true);
        int zHp0 = zShield.hp, pShield0 = pShield.shield;
        boolean empGate = ge.empError(vessel) == null
                && "该单位无法施放电磁脉冲".equals(ge.empError(hMarine));
        boolean empCast = ge.castEmp(vessel, 1040f, 1000f);
        // 60 shield vs 200 EMP -> emptied, and hit points untouched
        boolean empEffect = zShield.shield == 0 && zShield.hp == zHp0
                && zShield.shieldDelay > 0f;
        // friendly fire: a probe of the caster's own team loses its 20 shield too
        boolean empFriendly = pShield.shield == 0 && pShield0 == 20;
        boolean empCd = vessel.empCd == 24f && ge.empError(vessel) != null;
        boolean cEmp = empGate && empCast && empEffect && empFriendly && empCd;
        System.out.println("  emp cast=" + empCast + " zealot shield=" + zShield.shield
                + " hp-intact=" + (zShield.hp == zHp0)
                + " friendly-shield=" + pShield.shield
                + " cd=" + vessel.empCd + " PASS=" + cEmp);

        // ================================================== 4b. irradiate
        com.xjzb.rts.core.Game gi = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent iVessel = gi.spawn("vessel", 0, 1000, 1000, true);
        fullEnergy(iVessel);   // v2.22: casters test at a full pool
        com.xjzb.rts.core.Game.Ent iBug = gi.spawn("zergling", 1, 1040, 1000, true);
        com.xjzb.rts.core.Game.Ent iTank = gi.spawn("tank", 0, 1000, 1200, true);
        com.xjzb.rts.core.Game.Ent iFar = gi.spawn("zergling", 1, 1600, 1000, true);
        boolean iNull = "需要选择一个目标".equals(gi.irradiateError(iVessel, null));
        boolean iMech = "辐射只能作用于生物单位".equals(gi.irradiateError(iVessel, iTank));
        boolean iRange = "目标超出施法范围".equals(gi.irradiateError(iVessel, iFar));
        boolean iWrong = "该单位无法施放辐射".equals(gi.irradiateError(hMarine, iBug));
        // clear the two helpers out so only the bug is left to tick
        gi.ents.remove(iTank);
        gi.ents.remove(iFar);
        int bugHp0 = iBug.hp;
        boolean iCast = gi.castIrradiate(iVessel, iBug);
        boolean iSet = iBug.irradiateTime == 12f && iVessel.empCd == 20f;
        for (int k = 0; k < 36; k++) gi.update(1f / 30f);   // 1.2s -> two 0.5s ticks
        boolean iTick = iBug.hp == bugHp0 - 8;
        boolean cIrr = iNull && iMech && iRange && iWrong && iCast && iSet && iTick;
        System.out.println("  irradiate null=" + iNull + " mechanical=" + iMech
                + " out-of-range=" + iRange + " wrong-caster=" + iWrong
                + " cast=" + iCast + " hp " + bugHp0 + "->" + iBug.hp
                + " PASS=" + cIrr);

        // ================================================== 4c. yamato
        com.xjzb.rts.core.Game gy = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent bc = gy.spawn("battlecruiser", 0, 1000, 1000, true);
        fullEnergy(bc);   // v2.22: casters test at a full pool
        com.xjzb.rts.core.Game.Ent yTarget = gy.spawn("ultra", 1, 1100, 1000, true);
        boolean yWrong = "该单位无法施放大和炮".equals(gy.yamatoError(hMarine, yTarget));
        boolean yCast = gy.castYamato(bc, yTarget);
        boolean yCd = bc.yamatoCd == 30f && gy.yamatoError(bc, yTarget) != null;
        boolean yShot = !gy.shots.isEmpty();
        bc.cd = 999f;                        // hold the cruiser's own gun, so the
        for (int k = 0; k < 30; k++)         // only damage is the yamato
            gy.update(1f / 30f);
        // 260 normal vs 3 armor -> 257 off a 400 hp ultralisk
        boolean yHit = yTarget.hp == 143;
        boolean cYam = yWrong && yCast && yCd && yShot && yHit;
        System.out.println("  yamato wrong-caster=" + yWrong + " cast=" + yCast
                + " cd=" + bc.yamatoCd + " shot=" + yShot
                + " ultra hp=" + yTarget.hp + " PASS=" + cYam);

        // ================================================== 4d. lockdown
        com.xjzb.rts.core.Game gl = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent ghost = gl.spawn("ghost", 0, 1000, 1000, true);
        fullEnergy(ghost);   // v2.22: casters test at a full pool
        com.xjzb.rts.core.Game.Ent lTank = gl.spawn("tank", 1, 1080, 1000, true);
        com.xjzb.rts.core.Game.Ent lBug = gl.spawn("zergling", 1, 1060, 1060, true);
        boolean lBio = "锁定只能作用于机械单位".equals(gl.lockdownError(ghost, lBug));
        boolean lWrong = "该单位无法施放锁定".equals(gl.lockdownError(hMarine, lTank));
        boolean lNull = "需要选择一个目标".equals(gl.lockdownError(ghost, null));
        boolean lCast = gl.castLockdown(ghost, lTank);
        boolean lFrozen = lTank.lockdownTime == 8f && lTank.target == null
                && !lTank.moving && ghost.lockdownCd == 20f;
        // a locked tank cannot shoot back even with a target handed to it
        int ghostHp0 = ghost.hp;
        lTank.target = ghost;
        lTank.cd = 0f;
        for (int k = 0; k < 30; k++) gl.update(1f / 30f);
        boolean lSilent = ghost.hp == ghostHp0 && lTank.lockdownTime > 0f;
        boolean cLock = lBio && lWrong && lNull && lCast && lFrozen && lSilent;
        System.out.println("  lockdown biological=" + lBio + " wrong-caster=" + lWrong
                + " cast=" + lCast + " frozen=" + lFrozen
                + " ghost hp " + ghostHp0 + "->" + ghost.hp + " PASS=" + cLock);

        // ================================================== 4e. disruption web
        com.xjzb.rts.core.Game gw = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent corsair = gw.spawn("corsair", 0, 1000, 1000, true);
        fullEnergy(corsair);   // v2.22: casters test at a full pool
        com.xjzb.rts.core.Game.Ent wMarine = gw.spawn("marine", 0, 1020, 1000, true);
        com.xjzb.rts.core.Game.Ent wBug = gw.spawn("zergling", 1, 1070, 1000, true);
        boolean wWrong = "该单位无法施放干扰网".equals(gw.dwebError(hMarine));
        boolean wCast = gw.castDweb(corsair, 1000f, 1000f);
        boolean wField = gw.dwebs.size() == 1 && gw.underDweb(1020f, 1000f)
                && !gw.underDweb(1300f, 1000f) && corsair.dwebCd == 22f;
        int wHp0 = wBug.hp;
        wMarine.target = wBug;
        wMarine.cd = 0f;
        for (int k = 0; k < 30; k++) gw.update(1f / 30f);   // 1s, still webbed
        boolean wSilent = wBug.hp == wHp0;
        for (int k = 0; k < 380; k++) gw.update(1f / 30f);  // web expires at 12s
        boolean wFires = wBug.hp < wHp0;
        boolean cWeb = wWrong && wCast && wField && wSilent && wFires;
        System.out.println("  dweb wrong-caster=" + wWrong + " cast=" + wCast
                + " field=" + wField + " silent-in-web=" + wSilent
                + " fires-after=" + wFires + " PASS=" + cWeb);

        // ================================================== 4f. science vessel
        boolean hasVessel = false;
        for (String tr : com.xjzb.rts.core.Game.TYPES.get("starport").trains)
            if ("vessel".equals(tr)) hasVessel = true;
        com.xjzb.rts.core.Game.Type vt = com.xjzb.rts.core.Game.TYPES.get("vessel");
        boolean vesselOk = hasVessel && vt != null && vt.flying && vt.dmg == 0
                && vt.unitId == 9 && vt.requires.equals("sciencefac")
                && com.xjzb.rts.core.Game.isMechanical(vessel);
        System.out.println("  vessel in starport=" + hasVessel + " dmg=0 flying unitId="
                + (vt == null ? -1 : vt.unitId) + " PASS=" + vesselOk);

        // ================================================== 4g. spell art
        // Every key the five spells play must actually exist as a sheet, and the
        // sheet must be at least as long as animFrames() plays: playAnim() would
        // otherwise walk off the end of the sheet and the effect would freeze on
        // its last cell. This is the assertion that would have caught the batch
        // shipping with no art at all -- Game.java was playing emp/dweb/plasma/
        // b_blastcan/ehamed while the manifest had none of them.
        String[] spellArt = {"emp", "ehamed", "dweb", "elect02", "b_blastcan", "plasma"};
        boolean artOk = true;
        StringBuilder artLog = new StringBuilder();
        for (String k : spellArt) {
            int[] mf = manifest.get(k);
            BufferedImage im = sheet(k, false);
            int want = com.xjzb.rts.core.Game.animFrames(k);
            boolean ok = mf != null && im != null && mf[3] >= want;
            artOk = artOk && ok;
            artLog.append(k).append("=").append(mf == null ? "MISS" : (mf[3] + "f"))
                  .append(ok ? " " : "! ");
        }
        System.out.println("  spell art " + artLog.toString().trim() + " PASS=" + artOk);

        // ================================================== 5a. tech ladder
        String[] tLadder = com.xjzb.rts.core.Game.aiBuildOrder(0);
        String[] pLadder = com.xjzb.rts.core.Game.aiBuildOrder(2);
        String[] zLadder = com.xjzb.rts.core.Game.aiBuildOrder(1);
        boolean ladders = tLadder.length == 7 && tLadder[0].equals("barracks")
                && pLadder.length == 9 && pLadder[0].equals("pylon")
                && zLadder.length == 4 && zLadder[0].equals("pool");
        System.out.println("  aiBuildOrder terran=" + tLadder.length + " protoss="
                + pLadder.length + " zerg=" + zLadder.length + " PASS=" + ladders);

        // ================================================== 5b. wave + retreat
        com.xjzb.rts.core.Game ga = cleanGame("terran");
        float[] anchor = openGround(ga, 300f);
        if (anchor == null) anchor = new float[]{1000f, 1000f};
        com.xjzb.rts.core.Game.Ent hive = ga.spawn("hatchery", 1, anchor[0], anchor[1], true);
        List<com.xjzb.rts.core.Game.Ent> wave = new ArrayList<>();
        for (int k = 0; k < 6; k++) {
            wave.add(ga.spawn("zergling", 1, anchor[0] + 60 + k * 12, anchor[1] + 70, true));
        }
        ga.aiWaveTimer = 0.01f;
        ga.update(1f / 30f);
        boolean waveFired = ga.aiWave == 1 && ga.aiWaveStrength == 6;
        boolean tagged = true;
        for (com.xjzb.rts.core.Game.Ent e : wave) tagged = tagged && e.waveUnit;
        // kill four of six: 2 * 10 < 6 * 4, the 60% rule, so the rest pull back
        for (int k = 0; k < 4; k++) wave.get(k).hp = 0;
        ga.update(1f / 30f);
        int leftTagged = 0;
        for (com.xjzb.rts.core.Game.Ent e : ga.ents)
            if (e.team == 1 && e.waveUnit && e.alive()) leftTagged++;
        boolean retreated = ga.aiWaveStrength == 0 && leftTagged == 0
                && ga.aiWaveTimer >= 25f;
        boolean cWave = waveFired && tagged && retreated;
        System.out.println("  ai wave fired=" + waveFired + " tagged=" + tagged
                + " strength=" + ga.aiWaveStrength + " still-tagged=" + leftTagged
                + " waveTimer=" + ga.aiWaveTimer + " PASS=" + cWave);

        // ================================================== 5c. base defence
        com.xjzb.rts.core.Game gb = cleanGame("terran");
        float[] bAnchor = openGround(gb, 300f);
        if (bAnchor == null) bAnchor = new float[]{1000f, 1000f};
        com.xjzb.rts.core.Game.Ent bHive =
                gb.spawn("hatchery", 1, bAnchor[0], bAnchor[1], true);
        com.xjzb.rts.core.Game.Ent raider =
                gb.spawn("zergling", 1, bAnchor[0] + 500, bAnchor[1] + 500, true);
        com.xjzb.rts.core.Game.Ent attacker =
                gb.spawn("marine", 0, bAnchor[0] + 560, bAnchor[1] + 500, true);
        boolean calm = !gb.aiIsDefending();
        gb.damage(bHive, 1, attacker);
        boolean alarmed = gb.aiIsDefending();
        float beforeX = raider.goalX;
        gb.update(1f / 30f);
        // The defender that was not already attack-moving is redirected to the
        // building that was hit. Compare against bHive's own position, not the
        // anchor we asked for: spawn() snaps a multi-tile building onto the
        // tile grid, so the two are not the same point.
        boolean recalled = Math.abs(raider.goalX - bHive.x) < 1f
                && Math.abs(raider.goalY - bHive.y) < 1f;
        boolean cDefend = calm && alarmed && recalled && beforeX != raider.goalX;
        System.out.println("  ai defence calm=" + calm + " alarmed=" + alarmed
                + " recalled=" + recalled + " PASS=" + cDefend);

        // ================================================== 5d. tech build
        com.xjzb.rts.core.Game gt = cleanGame("terran");
        gt.aiRace = 0;
        gt.aiMinerals = 100000;
        float[] tAnchor = openGround(gt, 400f);
        if (tAnchor == null) tAnchor = new float[]{1000f, 1000f};
        gt.spawn("hatchery", 1, tAnchor[0], tAnchor[1], true);
        for (int k = 0; k < 40 * 30; k++) gt.update(1f / 30f);
        boolean tech = gt.hasBuilding(1, "barracks");
        System.out.println("  ai tech terran barracks=" + tech + " PASS=" + tech);
    }

    /** v2.7 batch 9 assertions: armor math, stim window, upgrade ladder. */
    static void combatTests() throws Exception {
        com.xjzb.rts.core.Game g = new com.xjzb.rts.core.Game(mapW, mapH, walk, starts, units);
        // armor: 5 dmg vs 2 armor must land 3
        com.xjzb.rts.core.Game.Ent tank = g.spawn("tank", 1, 400, 400, true);
        int eff = g.applyArmor(tank, 5);
        System.out.println("  armor 5dmg vs 2armor -> " + eff
                + " PASS=" + (eff == 3));

        // the floor keeps a 1-dmg attacker from being useless
        int floored = g.applyArmor(tank, 1);
        System.out.println("  armor floor 1dmg vs 2armor -> " + floored
                + " PASS=" + (floored == 1));

        // stim: pay hp, fire faster, window expires
        com.xjzb.rts.core.Game.Ent marine = g.spawn("marine", 0, 420, 420, true);
        int hp0 = marine.hp;
        boolean ok = g.stim(marine);
        float fast = g.effectiveCooldown(marine);
        System.out.println("  stim ok=" + ok + " hp " + hp0 + "->" + marine.hp
                + " cd " + String.format("%.2f", fast) + " vs "
                + String.format("%.2f", marine.type.cooldown)
                + " PASS=" + (ok && marine.hp == hp0 - 10
                              && fast < marine.type.cooldown));
        boolean reStim = g.stim(marine);   // must be refused while active
        System.out.println("  stim re-use while active -> " + reStim
                + " PASS=" + (!reStim));

        // upgrades: three levels, escalating cost, and the bonus lands on the
        // units of the line that was researched (v2.28: per class, so the
        // marine's infantry line is what this exercises).
        g.mineralsPlayer = 1000;
        String e1 = g.buyWeaponUpgrade(marine);
        int after1 = g.mineralsPlayer;
        String e2 = g.buyWeaponUpgrade(marine);
        String e3 = g.buyWeaponUpgrade(marine);
        String e4 = g.buyWeaponUpgrade(marine);   // must refuse at max
        int bonus = marine.dmgBonus;
        System.out.println("  upgrades w=" + g.weaponLevel
                + " minerals 1000->" + after1 + "->" + g.mineralsPlayer
                + " bonus=" + bonus + " err4=" + e4
                + " PASS=" + (e1 == null && e2 == null && e3 == null && e4 != null
                              && g.weaponLevel == 3 && bonus == 6
                              && g.mineralsPlayer == 1000 - 450));

        // academy gate: firebat must be refused until an academy exists
        com.xjzb.rts.core.Game g2 = new com.xjzb.rts.core.Game(mapW, mapH, walk, starts, units);
        g2.mineralsPlayer = 1000;
        String noAcad = g2.trainError("firebat");
        com.xjzb.rts.core.Game.Ent br = null;
        for (com.xjzb.rts.core.Game.Ent e : g2.ents)
            if (e.team == 0 && e.type.key.equals("barracks")) br = e;
        System.out.println("  academy gate (no academy) -> " + noAcad
                + " PASS=" + (noAcad != null));
    }

    /**
     * v2.8 assertions: the two races. Checks that the opening base matches the
     * chosen race, that the new units exist with the right ids, that a zerg
     * worker mines and a zerg town hall is a drop-off, and that the race
     * survives a save/load round trip.
     */
    static void raceTests() throws Exception {
        // --- terran opening (the default, must be unchanged) ---
        com.xjzb.rts.core.Game tg = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units, "terran");
        int tcc = 0, tscv = 0;
        for (com.xjzb.rts.core.Game.Ent e : tg.ents) {
            if (e.team != 0) continue;
            if (e.type.key.equals("cc")) tcc++;
            if (e.type.key.equals("scv")) tscv++;
        }
        System.out.println("  terran opening cc=" + tcc + " scv=" + tscv
                + " race=" + tg.race
                + " PASS=" + (tcc == 1 && tscv == 4 && "terran".equals(tg.race)));

        // --- zerg opening ---
        com.xjzb.rts.core.Game zg = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units, "zerg");
        int zhat = 0, zdrone = 0, zover = 0, zcc = 0;
        for (com.xjzb.rts.core.Game.Ent e : zg.ents) {
            if (e.team != 0) continue;
            if (e.type.key.equals("hatchery")) zhat++;
            if (e.type.key.equals("drone")) zdrone++;
            if (e.type.key.equals("over")) zover++;
            if (e.type.key.equals("cc")) zcc++;
        }
        System.out.println("  zerg opening hatchery=" + zhat + " drone=" + zdrone
                + " over=" + zover + " cc=" + zcc + " race=" + zg.race
                + " PASS=" + (zhat == 1 && zdrone == 4 && zover == 1 && zcc == 0
                              && "zerg".equals(zg.race)));

        // --- the new types exist with the verified units.dat ids ---
        boolean ids = com.xjzb.rts.core.Game.TYPES.get("ghost").unitId == 1
                && com.xjzb.rts.core.Game.TYPES.get("wraith").unitId == 8
                && com.xjzb.rts.core.Game.TYPES.get("drone").unitId == 41
                && com.xjzb.rts.core.Game.TYPES.get("over").unitId == 42
                && com.xjzb.rts.core.Game.TYPES.get("extractor").unitId == 149
                && com.xjzb.rts.core.Game.TYPES.get("spire").unitId == 141
                && com.xjzb.rts.core.Game.TYPES.get("starport").unitId == 114;
        System.out.println("  v2.8 unit ids (ghost=1 wraith=8 drone=41 over=42 "
                + "extractor=149 spire=141 starport=114) PASS=" + ids);

        // --- worker/drop-off helpers are race-neutral ---
        boolean helpers = com.xjzb.rts.core.Game.isWorkerType("scv")
                && com.xjzb.rts.core.Game.isWorkerType("drone")
                && !com.xjzb.rts.core.Game.isWorkerType("marine")
                && com.xjzb.rts.core.Game.isDropOff("cc")
                && com.xjzb.rts.core.Game.isDropOff("hatchery")
                && !com.xjzb.rts.core.Game.isDropOff("depot")
                && com.xjzb.rts.core.Game.isGasBuilding("refinery")
                && com.xjzb.rts.core.Game.isGasBuilding("extractor")
                && com.xjzb.rts.core.Game.supplyProvided("hatchery") == 10
                && com.xjzb.rts.core.Game.supplyProvided("depot") == 8;
        System.out.println("  worker/dropoff helpers PASS=" + helpers);

        // --- supply comes from the hatchery and the overlord, not a depot ---
        // One tick is enough for updateEconomy to recompute the totals.
        zg.update(1 / 30f);
        int zUsed0 = zg.supplyUsed, zCap0 = zg.supplyCap;
        System.out.println("  zerg supply used=" + zUsed0 + " cap=" + zCap0
                + " PASS=" + (zUsed0 == 4 && zCap0 == 18));

        // --- a zerg drone actually mines, and the hatchery takes the delivery ---
        com.xjzb.rts.core.Game.Ent drone = null;
        for (com.xjzb.rts.core.Game.Ent e : zg.ents)
            if (e.team == 0 && e.type.key.equals("drone")) { drone = e; break; }
        boolean mined = false;
        if (drone != null && !zg.minerals.isEmpty()) {
            // nearestMineral is private to Game, so pick the closest here
            com.xjzb.rts.core.Game.Mineral m = null;
            float bd = Float.MAX_VALUE;
            for (com.xjzb.rts.core.Game.Mineral c : zg.minerals) {
                if (c.amount <= 0 || c.variant >= 3) continue;
                float d = (c.x - drone.x) * (c.x - drone.x)
                        + (c.y - drone.y) * (c.y - drone.y);
                if (d < bd) { bd = d; m = c; }
            }
            if (m != null) {
                zg.orderHarvest(java.util.Collections.singletonList(drone), m);
                // let the drone walk over, mine and haul back
                for (int i = 0; i < 2000 && zg.mineralsMined == 0; i++) zg.update(1 / 30f);
                mined = zg.mineralsMined > 0;
            }
        }
        System.out.println("  zerg drone mines -> mineralsMined=" + zg.mineralsMined
                + " PASS=" + mined);

        // --- zerg tech gates: hydra now needs a hydralisk den, muta a spire ---
        // v2.11 batch B moved the hydralisk off the spawning pool and onto its
        // own den, which is the prerequisite the manual lists. The pool is the
        // only zerg building in the opening, so hydra must now be refused --
        // this assertion used to expect null.
        zg.mineralsPlayer = 5000;
        zg.gasPlayer = 5000;
        String hydraGate = zg.trainError("hydra");   // den missing in opening
        boolean spireGate = !zg.hasBuilding(0, "spire");
        String mutaGate = zg.trainError("muta");     // must name the missing spire
        System.out.println("  zerg gates: hydra w/o den -> " + hydraGate
                + " (expect 刺蛇巢), muta w/o spire -> " + mutaGate
                + " PASS=" + (hydraGate != null && hydraGate.contains("刺蛇巢")
                              && spireGate
                              && mutaGate != null && mutaGate.contains("飞龙塔")));

        // --- race survives save/load ---
        String save = zg.serialize();
        com.xjzb.rts.core.Game re = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units, "terran");
        boolean loaded = re.deserialize(save);
        System.out.println("  save/load race " + re.race
                + " PASS=" + (loaded && "zerg".equals(re.race)));

        // --- a v2.7 save (no race field) must still load as terran ---
        StringBuilder old = new StringBuilder();
        for (String ln : save.split("\n")) {
            if (ln.startsWith("state ")) {
                String[] p = ln.split(" ");
                StringBuilder o = new StringBuilder("state");
                for (int i = 1; i < Math.min(p.length, 15); i++) o.append(' ').append(p[i]);
                old.append(o).append('\n');
            } else {
                old.append(ln).append('\n');
            }
        }
        com.xjzb.rts.core.Game legacy = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units, "terran");
        boolean okLegacy = legacy.deserialize(old.toString());
        System.out.println("  v2.7 save (no race) loads as " + legacy.race
                + " PASS=" + (okLegacy && "terran".equals(legacy.race)));

        // --- end to end: a zerg drone builds a pool, the pool trains a zergling
        com.xjzb.rts.core.Game zg2 = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units, "zerg");
        zg2.mineralsPlayer = 5000;
        zg2.gasPlayer = 5000;
        com.xjzb.rts.core.Game.Ent d2 = null;
        for (com.xjzb.rts.core.Game.Ent e : zg2.ents)
            if (e.team == 0 && e.type.key.equals("drone")) { d2 = e; break; }
        boolean built = false, trained = false;
        if (d2 != null) {
            float bx = d2.x + 60, by = d2.y + 60;
            String berr = zg2.buildError("spire", bx, by);
            zg2.tryBuild(d2, "spire", bx, by);
            for (int i = 0; i < 4000 && !zg2.hasBuilding(0, "spire"); i++) zg2.update(1 / 30f);
            built = zg2.hasBuilding(0, "spire");
            if (built) {
                com.xjzb.rts.core.Game.Ent sp = null;
                for (com.xjzb.rts.core.Game.Ent e : zg2.ents)
                    if (e.team == 0 && e.type.key.equals("spire")) { sp = e; break; }
                String terr = zg2.trainError("muta");
                if (sp != null && terr == null) {
                    zg2.tryTrain(sp, "muta");
                    for (int i = 0; i < 4000; i++) {
                        zg2.update(1 / 30f);
                        boolean found = false;
                        for (com.xjzb.rts.core.Game.Ent e : zg2.ents)
                            if (e.team == 0 && e.type.key.equals("muta")) found = true;
                        if (found) { trained = true; break; }
                    }
                }
            }
            System.out.println("  zerg build spire err='" + berr + "' built=" + built
                    + " -> trained muta=" + trained
                    + " PASS=" + (built && trained));
        }

        // v2.8: a mission authors its own units, so it also owns the race.
        // Pick zerg on the menu, then load m01 (playerRace=terran): the units
        // are terran, so the race must follow, or the build card offers
        // hatcheries no terran unit can ever place.
        {
            String json = new String(Files.readAllBytes(
                    Paths.get(ASSETS + "/missions/m01.json")),
                    java.nio.charset.StandardCharsets.UTF_8);
            com.xjzb.rts.core.Mission mm = com.xjzb.rts.core.Mission.parse(json);
            com.xjzb.rts.core.Game gm = missionGame("m01");
            gm.race = "zerg";
            gm.setMission(mm);
            int cc = 0, hatch = 0;
            for (com.xjzb.rts.core.Game.Ent e : gm.ents) {
                if (e.team != 0 || !e.isBuilding()) continue;
                if (e.type.key.equals("cc")) cc++;
                if (e.type.key.equals("hatchery")) hatch++;
            }
            boolean ok = mm.playerRace.equals(gm.race) && cc + hatch > 0
                    && (cc > 0) == "terran".equals(gm.race);
            System.out.println("  mission race m01 authored='" + mm.playerRace
                    + "' -> game.race='" + gm.race + "' cc=" + cc + " hatch=" + hatch
                    + " PASS=" + ok);
        }

        // ================= v2.10 batch A: the protoss =================
        // Eleven assertions, the acceptance list from the v2.9 plan section 3A.8.

        // --- 1. protoss opening: nexus + 4 probes + the first pylon ---
        com.xjzb.rts.core.Game pg = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units, "protoss");
        int pnex = 0, pprobe = 0, ppyl = 0, pcc = 0;
        for (com.xjzb.rts.core.Game.Ent e : pg.ents) {
            if (e.team != 0) continue;
            if (e.type.key.equals("nexus")) pnex++;
            if (e.type.key.equals("probe")) pprobe++;
            if (e.type.key.equals("pylon")) ppyl++;
            if (e.type.key.equals("cc")) pcc++;
        }
        System.out.println("  protoss opening nexus=" + pnex + " probe=" + pprobe
                + " pylon=" + ppyl + " cc=" + pcc + " race=" + pg.race
                + " PASS=" + (pnex == 1 && pprobe == 4 && ppyl == 1 && pcc == 0
                              && "protoss".equals(pg.race)));

        // --- 2. the protoss types carry the verified units.dat ids ---
        boolean pids = com.xjzb.rts.core.Game.TYPES.get("probe").unitId == 64
                && com.xjzb.rts.core.Game.TYPES.get("zealot").unitId == 65
                && com.xjzb.rts.core.Game.TYPES.get("dragoon").unitId == 66
                && com.xjzb.rts.core.Game.TYPES.get("templar").unitId == 67
                && com.xjzb.rts.core.Game.TYPES.get("archon").unitId == 68
                && com.xjzb.rts.core.Game.TYPES.get("reaver").unitId == 83
                && com.xjzb.rts.core.Game.TYPES.get("observer").unitId == 84
                && com.xjzb.rts.core.Game.TYPES.get("nexus").unitId == 154
                && com.xjzb.rts.core.Game.TYPES.get("robotic").unitId == 155
                && com.xjzb.rts.core.Game.TYPES.get("pylon").unitId == 156
                && com.xjzb.rts.core.Game.TYPES.get("assim").unitId == 157
                && com.xjzb.rts.core.Game.TYPES.get("gateway").unitId == 160
                && com.xjzb.rts.core.Game.TYPES.get("photon").unitId == 162
                && com.xjzb.rts.core.Game.TYPES.get("gencore").unitId == 164
                && com.xjzb.rts.core.Game.TYPES.get("archives").unitId == 165
                && com.xjzb.rts.core.Game.TYPES.get("stargate").unitId == 167
                && com.xjzb.rts.core.Game.TYPES.get("beacon").unitId == 169;
        System.out.println("  v2.10 protoss unit ids (probe=64 zealot=65 dragoon=66 "
                + "templar=67 archon=68 reaver=83 observer=84 nexus=154 gateway=160 "
                + "gencore=164 stargate=167 beacon=169) PASS=" + pids);

        // --- 3. the worker/dropoff/gas/supply helpers learned protoss ---
        boolean phelp = com.xjzb.rts.core.Game.isWorkerType("probe")
                && !com.xjzb.rts.core.Game.isWorkerType("zealot")
                && com.xjzb.rts.core.Game.isDropOff("nexus")
                && !com.xjzb.rts.core.Game.isDropOff("pylon")
                && com.xjzb.rts.core.Game.isGasBuilding("assim")
                && !com.xjzb.rts.core.Game.isGasBuilding("pylon")
                && com.xjzb.rts.core.Game.supplyProvided("pylon") == 8
                && com.xjzb.rts.core.Game.supplyProvided("nexus") == 0;
        System.out.println("  protoss helpers (probe/nexus/assim/pylon=8) PASS=" + phelp);

        // --- 4. supply comes from the pylon, not the nexus ---
        pg.update(1 / 30f);
        int pUsed0 = pg.supplyUsed, pCap0 = pg.supplyCap;
        System.out.println("  protoss supply used=" + pUsed0 + " cap=" + pCap0
                + " PASS=" + (pUsed0 == 4 && pCap0 == 8));

        // --- 5. a shield eats the hit before hp does, and the spill lands ---
        com.xjzb.rts.core.Game.Ent zeal = pg.spawn("zealot", 0, 420, 440, true);
        int zs0 = zeal.shield, zh0 = zeal.hp;
        pg.damage(zeal, 30, null);
        boolean absorb = zeal.shield == zs0 - 30 && zeal.hp == zh0;
        pg.damage(zeal, 40, null);      // 30 shield left, so 10 must reach hp
        boolean spill = zeal.shield == 0 && zeal.hp == zh0 - 10;
        System.out.println("  shield " + zs0 + " absorbs 30 -> shield=" + (zs0 - 30)
                + " hp=" + zh0 + " then 40 -> shield=" + zeal.shield + " hp=" + zeal.hp
                + " PASS=" + (absorb && spill));

        // --- 6. the shield comes back once the delay has elapsed ---
        com.xjzb.rts.core.Game rg2 = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units, "protoss");
        int[] st0 = starts.get(0);
        com.xjzb.rts.core.Game.Ent rz = rg2.spawn("zealot", 0,
                st0[0] + 64 + 40, st0[1] + 64 + 40, true);
        rg2.damage(rz, 50, null);
        int hurt = rz.shield;
        // inside the delay window nothing regenerates...
        for (int i = 0; i < 60; i++) rg2.update(1 / 30f);   // 2.0s < SHIELD_DELAY
        boolean held = rz.shield == hurt;
        // ...and after it, SHIELD_REGEN points per second come back.
        for (int i = 0; i < 120; i++) rg2.update(1 / 30f);  // 4.0s more
        boolean back = rz.shield > hurt && rz.shield <= rz.type.shield;
        System.out.println("  shield regen 60->" + hurt + " held at 2.0s=" + held
                + " -> " + rz.shield + "/" + rz.type.shield + " at 6.0s"
                + " PASS=" + (held && back));

        // --- 7. any hit restarts the delay, even once the shield is already bare ---
        com.xjzb.rts.core.Game rg3 = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units, "protoss");
        com.xjzb.rts.core.Game.Ent rz2 = rg3.spawn("zealot", 0,
                st0[0] + 64 + 40, st0[1] + 64 + 40, true);
        rg3.damage(rz2, 60, null);          // strip the shield completely
        int bare = rz2.shield, bareHp = rz2.hp;
        // let 2s of the 3s delay run, then hit again: the clock must reset.
        // This is the case a naive `if (shield > 0)` guard gets wrong -- with no
        // shield left the delay would never restart and the unit would quietly
        // recharge between shots.
        for (int i = 0; i < 60; i++) rg3.update(1 / 30f);
        float midDelay = rz2.shieldDelay;
        rg3.damage(rz2, 1, null);
        boolean resets = rz2.shieldDelay == com.xjzb.rts.core.Game.SHIELD_DELAY;
        System.out.println("  shield delay resets on hit: delay " + midDelay + " -> "
                + rz2.shieldDelay + " shield=" + bare + "->" + rz2.shield
                + " hp=" + bareHp + "->" + rz2.hp
                + " PASS=" + (bare == 0 && resets && rz2.shield == 0
                              && rz2.hp == bareHp - 1));

        // --- 8. the two-step tech gate: zealot<-gateway, dragoon<-gencore ---
        com.xjzb.rts.core.Game gg = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units, "protoss");
        gg.mineralsPlayer = 5000;
        gg.gasPlayer = 5000;
        String zealotGate = gg.trainError("zealot");     // needs a gateway
        String dragoonGate = gg.trainError("dragoon");   // needs the cyber core
        com.xjzb.rts.core.Game.Ent pz = null;
        for (com.xjzb.rts.core.Game.Ent e : gg.ents)
            if (e.team == 0 && e.type.key.equals("probe")) { pz = e; break; }
        boolean gw = buildNear(gg, pz, "gateway");
        String zealotOpen = gg.trainError("zealot");     // must be clear now
        String dragoonStill = gg.trainError("dragoon");  // still blocked by the core
        com.xjzb.rts.core.Game.Ent pz2 = null;
        for (com.xjzb.rts.core.Game.Ent e : gg.ents)
            if (e.team == 0 && e.type.key.equals("probe")) { pz2 = e; break; }
        boolean gc = buildNear(gg, pz2, "gencore");
        String dragoonOpen = gg.trainError("dragoon");
        System.out.println("  protoss tech gate: zealot w/o gateway -> " + zealotGate
                + ", dragoon w/o core -> " + dragoonGate
                + " | gateway built=" + gw + " zealot -> " + zealotOpen
                + " dragoon still -> " + dragoonStill
                + " | core built=" + gc + " dragoon -> " + dragoonOpen
                + " PASS=" + (zealotGate != null && zealotGate.contains("传送门")
                              && dragoonGate != null && dragoonGate.contains("机械核心")
                              && gw && zealotOpen == null
                              && dragoonStill != null && dragoonStill.contains("机械核心")
                              && gc && dragoonOpen == null));

        // --- 9. psistorm burns enemies in the radius and spares friendlies ---
        com.xjzb.rts.core.Game sg = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units, "protoss");
        com.xjzb.rts.core.Game.Ent tpl = sg.spawn("templar", 0, 500, 380, true);
        fullEnergy(tpl);   // v2.22: casters test at a full pool
        com.xjzb.rts.core.Game.Ent over1 = sg.spawn("over", 1, 500, 540, true);
        com.xjzb.rts.core.Game.Ent pal = sg.spawn("zealot", 0, 500, 460, true);
        int overHp0 = over1.hp, palHp0 = pal.hp;
        boolean cast = sg.castStorm(tpl, 500, 500);
        for (int i = 0; i < 100; i++) sg.update(1 / 30f);   // ~3.3s > STORM_DURATION
        boolean burned = over1.hp < overHp0;
        boolean spared = pal.hp == palHp0;
        boolean expired = sg.storms.isEmpty();
        System.out.println("  psistorm cast=" + cast + " enemy hp " + overHp0 + "->"
                + over1.hp + " friendly hp " + palHp0 + "->" + pal.hp
                + " storms left=" + sg.storms.size()
                + " PASS=" + (cast && burned && spared && expired));

        // --- 10. the caster is gated by its own cooldown, not by energy ---
        com.xjzb.rts.core.Game sg2 = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units, "protoss");
        com.xjzb.rts.core.Game.Ent tpl2 = sg2.spawn("templar", 0, 500, 380, true);
        fullEnergy(tpl2);   // v2.22: casters test at a full pool
        com.xjzb.rts.core.Game.Ent zl2 = sg2.spawn("probe", 0, 500, 400, true);
        boolean c1 = sg2.castStorm(tpl2, 500, 500);
        String cdErr = sg2.stormError(tpl2);        // must refuse while cooling
        boolean c2 = sg2.castStorm(tpl2, 500, 500);
        boolean notCaster = sg2.stormError(zl2) != null;
        // run past STORM_COOLDOWN and it must be usable again
        for (int i = 0; i < 400; i++) sg2.update(1 / 30f);   // ~13.3s
        boolean c3 = sg2.castStorm(tpl2, 520, 500);
        System.out.println("  psistorm cooldown: cast=" + c1 + " err='" + cdErr
                + "' recast=" + c2 + " non-caster=" + notCaster
                + " after 12s=" + c3
                + " PASS=" + (c1 && cdErr != null && cdErr.contains("冷却")
                              && !c2 && notCaster && c3));

        // --- 11. save/load carries race + shield, and a v2.9 save still loads ---
        com.xjzb.rts.core.Game lg = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units, "protoss");
        com.xjzb.rts.core.Game.Ent lz = lg.spawn("zealot", 0, 420, 440, true);
        lg.damage(lz, 25, null);
        int lzShield = lz.shield, lzHp = lz.hp;
        String lsave = lg.serialize();
        com.xjzb.rts.core.Game lre = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units, "terran");
        boolean lok = lre.deserialize(lsave);
        com.xjzb.rts.core.Game.Ent lback = null;
        for (com.xjzb.rts.core.Game.Ent e : lre.ents)
            if (e.team == 0 && e.type.key.equals("zealot")) { lback = e; break; }
        boolean round = lok && "protoss".equals(lre.race) && lback != null
                && lback.shield == lzShield && lback.hp == lzHp;
        // a v2.9 save has no shield/shieldDelay/stormCd columns: the guard must
        // read it as "full shield", not as a permanently defenceless unit.
        StringBuilder oldP = new StringBuilder();
        for (String ln : lsave.split("\n")) {
            if (ln.startsWith("e ")) {
                String[] p = ln.split(" ");
                StringBuilder o = new StringBuilder("e");
                for (int i = 1; i < Math.min(p.length, 34); i++) o.append(' ').append(p[i]);
                oldP.append(o).append('\n');
            } else {
                oldP.append(ln).append('\n');
            }
        }
        com.xjzb.rts.core.Game lold = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units, "terran");
        boolean oldOk = lold.deserialize(oldP.toString());
        com.xjzb.rts.core.Game.Ent oback = null;
        for (com.xjzb.rts.core.Game.Ent e : lold.ents)
            if (e.team == 0 && e.type.key.equals("zealot")) { oback = e; break; }
        boolean legacyShield = oldOk && oback != null
                && oback.shield == oback.type.shield;
        System.out.println("  save/load protoss race=" + lre.race + " shield "
                + lzShield + "->" + (lback == null ? "?" : lback.shield)
                + " hp " + lzHp + "->" + (lback == null ? "?" : lback.hp)
                + " | v2.9 save -> shield "
                + (oback == null ? "?" : oback.shield + "/" + oback.type.shield)
                + " PASS=" + (round && legacyShield));

        // batch A item 7: the skirmish AI mixes protoss in once the game has
        // run long enough and two waves have landed. aiPick is pure so this
        // needs no twenty minute match.
        boolean earlyPure = "zergling".equals(com.xjzb.rts.core.Game.aiPick(89f, 5, 99))
                && "zergling".equals(com.xjzb.rts.core.Game.aiPick(0f, 0, 0));
        // Before wave 2 nothing protoss can appear, whatever the roll is.
        boolean waveGate = true;
        for (int r = 0; r < 100; r++)
            for (int w = 0; w < 2; w++)
                if (isProtossUnit(com.xjzb.rts.core.Game.aiPick(300f, w, r)))
                    waveGate = false;
        boolean mix = "zealot".equals(com.xjzb.rts.core.Game.aiPick(300f, 2, 70))
                && "zealot".equals(com.xjzb.rts.core.Game.aiPick(300f, 9, 77))
                && "dragoon".equals(com.xjzb.rts.core.Game.aiPick(300f, 2, 78))
                && "dragoon".equals(com.xjzb.rts.core.Game.aiPick(300f, 2, 85))
                && "scout".equals(com.xjzb.rts.core.Game.aiPick(300f, 2, 86))
                && "scout".equals(com.xjzb.rts.core.Game.aiPick(300f, 2, 99));
        // The protoss band opens at roll 70, so rolls 0..69 must still be zerg,
        // and the zerg trio must be the only thing the early game produces.
        boolean zergBand = true;
        int seenZ = 0, seenP = 0;
        for (int r = 0; r < 70; r++) {
            String p = com.xjzb.rts.core.Game.aiPick(300f, 2, r);
            if (isProtossUnit(p)) zergBand = false;
            if (p.equals("zergling") || p.equals("hydra") || p.equals("muta")) seenZ++;
        }
        for (int r = 70; r < 100; r++) if (isProtossUnit(com.xjzb.rts.core.Game.aiPick(300f, 2, r))) seenP++;
        zergBand = zergBand && seenZ == 70 && seenP == 30;
        System.out.println("  ai protoss mix: early-pure=" + earlyPure
                + " wave-gate=" + waveGate + " mix=" + mix
                + " zerg-band=" + zergBand
                + " PASS=" + (earlyPure && waveGate && mix && zergBand));

        // ================= v2.11 batch B: the zerg completion =================
        // Six assertions, the acceptance list from the v2.9 plan section 3B.4.

        // --- B1. the building chain: pool -> lair -> hive, and what hangs off it
        com.xjzb.rts.core.Game bg = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units, "zerg");
        bg.mineralsPlayer = 20000;
        bg.gasPlayer = 20000;
        com.xjzb.rts.core.Game.Ent bd = null;
        for (com.xjzb.rts.core.Game.Ent e : bg.ents)
            if (e.team == 0 && e.type.key.equals("drone")) { bd = e; break; }
        boolean bPool = buildNear(bg, bd, "pool");
        boolean bLair = buildNear(bg, bd, "lair");
        boolean bHive = buildNear(bg, bd, "hive");
        // the rows that hang off lair/hive must name the building they lack
        String ucGate = bg.trainError("ultra");
        String qnGate = bg.trainError("queen");
        String dfGate = bg.trainError("defiler");
        String gdGate = bg.trainError("guardian");
        boolean bChain = bPool && bLair && bHive
                && com.xjzb.rts.core.Game.TYPES.get("lair").unitId == 132
                && com.xjzb.rts.core.Game.TYPES.get("hive").unitId == 133
                && "pool".equals(com.xjzb.rts.core.Game.TYPES.get("lair").requires)
                && "lair".equals(com.xjzb.rts.core.Game.TYPES.get("hive").requires)
                && ucGate != null && ucGate.contains("雷兽洞穴")
                && qnGate != null && qnGate.contains("皇后巢")
                && dfGate != null && dfGate.contains("污染者巢穴")
                && gdGate != null && gdGate.contains("大飞龙塔");
        System.out.println("  zerg chain pool=" + bPool + " lair=" + bLair
                + " hive=" + bHive + " | gates ultra->" + ucGate + " queen->" + qnGate
                + " defiler->" + dfGate + " guardian->" + gdGate
                + " PASS=" + bChain);

        // --- B2. the hydralisk den is the gate the plan asks to install ---
        boolean bDen = buildNear(bg, bd, "hydraden");
        String hydraOpen = bg.trainError("hydra");
        String lurkerOpen = bg.trainError("lurker");
        boolean bDenOk = bDen && hydraOpen == null && lurkerOpen == null
                && com.xjzb.rts.core.Game.TYPES.get("hydraden").unitId == 135
                && "pool".equals(com.xjzb.rts.core.Game.TYPES.get("hydraden").requires)
                && "hydraden".equals(com.xjzb.rts.core.Game.TYPES.get("hydra").requires);
        System.out.println("  zerg hydra den built=" + bDen + " hydra->" + hydraOpen
                + " lurker->" + lurkerOpen + " PASS=" + bDenOk);

        // --- B3. the lurker burrows -- the siege morph, reused ---
        com.xjzb.rts.core.Game ug = cleanGame("zerg");
        com.xjzb.rts.core.Game.Ent lk = ug.spawn("lurker", 0, 420, 440, true);
        boolean morphable = com.xjzb.rts.core.Game.canMorph(lk);
        boolean dug = ug.toggleSiege(lk);
        boolean isDug = dug && "lurker_bur".equals(lk.type.key)
                && com.xjzb.rts.core.Game.isBurrowed(lk)
                && lk.type.speed == 0f;
        boolean up = ug.toggleSiege(lk);
        boolean resurfaced = up && "lurker".equals(lk.type.key)
                && !com.xjzb.rts.core.Game.isBurrowed(lk);
        // a burrowed lurker is invisible to melee but still shootable
        com.xjzb.rts.core.Game.Ent bur = ug.spawn("lurker_bur", 1, 430, 440, true);
        com.xjzb.rts.core.Game.Ent melee = ug.spawn("zergling", 0, 420, 500, true);
        com.xjzb.rts.core.Game.Ent ranged = ug.spawn("marine", 0, 420, 560, true);
        boolean blind = ug.findEnemyInRange(melee, 200) != bur;
        boolean visible = ug.findEnemyInRange(ranged, 200) == bur;
        boolean bBurrow = morphable && isDug && resurfaced && blind && visible;
        System.out.println("  zerg burrow canMorph=" + morphable + " dug=" + dug
                + " speed0=" + (lk.type.speed == 0f) + " up=" + resurfaced
                + " melee-blind=" + blind + " ranged-sees=" + visible
                + " PASS=" + bBurrow);

        // --- B4. dark swarm stops ranged fire; ensnare halves movement ---
        com.xjzb.rts.core.Game sw = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent shooter = sw.spawn("marine", 1, 420, 440, true);
        com.xjzb.rts.core.Game.Ent shelter = sw.spawn("depot", 0, 430, 440, true);
        com.xjzb.rts.core.Game.Ent df = sw.spawn("defiler", 0, 400, 500, true);
        fullEnergy(df);   // v2.22: casters test at a full pool
        boolean swarmCast = sw.castDswarm(df, shelter.x, shelter.y);
        shooter.target = shelter;
        int shHp0 = shelter.hp;
        for (int i = 0; i < 60; i++) sw.update(1 / 30f);      // 2s, inside the 10s cloud
        boolean swarmBlocks = shelter.hp == shHp0;
        for (int i = 0; i < 420; i++) sw.update(1 / 30f);     // 14s: cloud long gone
        boolean swarmLifts = shelter.hp < shHp0;
        boolean swarmCooling = sw.dswarmError(df) != null;
        // melee is explicitly not stopped by the cloud -- that is the counter-play
        com.xjzb.rts.core.Game ml = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent depot2 = ml.spawn("depot", 0, 430, 440, true);
        com.xjzb.rts.core.Game.Ent ling = ml.spawn("zergling", 1, depot2.x + 24, depot2.y, true);
        com.xjzb.rts.core.Game.Ent df2 = ml.spawn("defiler", 0, 400, 500, true);
        fullEnergy(df2);   // v2.22: casters test at a full pool
        boolean swarmCast2 = ml.castDswarm(df2, depot2.x, depot2.y);
        ling.target = depot2;
        int d2Hp0 = depot2.hp;
        for (int i = 0; i < 90; i++) ml.update(1 / 30f);
        boolean meleeBites = depot2.hp < d2Hp0;
        // ensnare: same walk, same window, one of the two under a field.
        // The walk has to be long enough to measure: orderMove lays a 5-wide
        // formation out around the target, so the first unit's real goal sits
        // 36 px up-left of the point passed in. Compensate for that and ask for
        // a 300 px run -- a 40 px one finishes inside the first few frames and
        // leaves nothing for the halving to show up in.
        com.xjzb.rts.core.Game en1 = cleanGame("terran");
        com.xjzb.rts.core.Game en2 = cleanGame("terran");
        float[] og = openGround(en1, 420);
        boolean ensnareOk = false;
        if (og != null) {
            com.xjzb.rts.core.Game.Ent ma = en1.spawn("marine", 0, og[0], og[1], true);
            com.xjzb.rts.core.Game.Ent mb = en2.spawn("marine", 0, og[0], og[1], true);
            List<com.xjzb.rts.core.Game.Ent> sa = new ArrayList<>();
            sa.add(ma);
            List<com.xjzb.rts.core.Game.Ent> sb = new ArrayList<>();
            sb.add(mb);
            en1.orderMove(sa, og[0] + 336, og[1] + 36, false);
            en2.orderMove(sb, og[0] + 336, og[1] + 36, false);
            com.xjzb.rts.core.Game.Ent df3 =
                    en2.spawn("defiler", 0, og[0] + 90, og[1] + 90, true);
            fullEnergy(df3);   // v2.22: casters test at a full pool
            boolean eCast = en2.castEnsnare(df3, og[0], og[1]);
            for (int i = 0; i < 15; i++) {
                en1.update(1 / 30f);
                en2.update(1 / 30f);
            }
            float free = ma.x - og[0], slow = mb.x - og[0];
            ensnareOk = eCast && free > 10 && slow > 0 && slow < free * 0.75f;
            System.out.println("  zerg ensnare free=" + free + " slowed=" + slow
                    + " ratio=" + (free > 0 ? slow / free : -1)
                    + " PASS=" + ensnareOk);
        }
        boolean bDefiler = swarmCast && swarmBlocks && swarmLifts && swarmCooling
                && swarmCast2 && meleeBites && ensnareOk;
        System.out.println("  zerg defiler dswarm=" + swarmCast + " blocks-ranged="
                + swarmBlocks + " lifts=" + swarmLifts + " cooling=" + swarmCooling
                + " | melee-still-bites=" + meleeBites
                + " PASS=" + bDefiler);

        // --- B5. weapon layers: who may shoot at what ---
        com.xjzb.rts.core.Game lyr = cleanGame("zerg");
        com.xjzb.rts.core.Game.Ent sporeC = lyr.spawn("spore", 0, 420, 440, true);
        com.xjzb.rts.core.Game.Ent sunkenC = lyr.spawn("sunken", 0, 420, 520, true);
        com.xjzb.rts.core.Game.Ent valkC = lyr.spawn("valkyrie", 0, 420, 600, true);
        com.xjzb.rts.core.Game.Ent guardC = lyr.spawn("guardian", 0, 420, 680, true);
        com.xjzb.rts.core.Game.Ent fly = lyr.spawn("over", 1, 620, 440, true);
        com.xjzb.rts.core.Game.Ent walk1 = lyr.spawn("zergling", 1, 520, 440, true);
        boolean sporeAir = lyr.findEnemyInRange(sporeC, 400) == fly;
        boolean sunkenGround = lyr.findEnemyInRange(sunkenC, 400) == walk1;
        boolean valkAir = lyr.findEnemyInRange(valkC, 400) == fly;
        boolean guardGround = lyr.findEnemyInRange(guardC, 400) == walk1;
        boolean bLayers = sporeAir && sunkenGround && valkAir && guardGround
                && com.xjzb.rts.core.Game.TYPES.get("spore").airOnly
                && com.xjzb.rts.core.Game.TYPES.get("valkyrie").airOnly
                && com.xjzb.rts.core.Game.TYPES.get("devourer").airOnly
                && com.xjzb.rts.core.Game.TYPES.get("guardian").groundOnly
                && com.xjzb.rts.core.Game.TYPES.get("lurker").groundOnly
                && com.xjzb.rts.core.Game.TYPES.get("ultra").melee
                && com.xjzb.rts.core.Game.TYPES.get("ultra").armor == 3;
        System.out.println("  zerg layers spore->air=" + sporeAir + " sunken->ground="
                + sunkenGround + " valkyrie->air=" + valkAir + " guardian->ground="
                + guardGround + " PASS=" + bLayers);

        // --- B6. the skirmish AI wave mix reaches the new units ---
        java.util.Set<String> w4 = new java.util.TreeSet<>();
        for (int r = 0; r < 70; r++) w4.add(com.xjzb.rts.core.Game.aiPick(300f, 4, r));
        boolean heavyReachable = w4.contains("ultra") && w4.contains("guardian")
                && w4.contains("devourer") && w4.contains("lurker")
                && w4.contains("zergling") && w4.contains("hydra")
                && w4.contains("muta");
        boolean protossBandKept = true;
        for (int r = 70; r < 100; r++)
            if (!isProtossUnit(com.xjzb.rts.core.Game.aiPick(300f, 4, r)))
                protossBandKept = false;
        boolean waveGate4 = true;
        for (int r = 0; r < 100; r++)
            for (int w = 0; w < 2; w++)
                if (isProtossUnit(com.xjzb.rts.core.Game.aiPick(300f, w, r)))
                    waveGate4 = false;
        boolean earlyZerg = "zergling".equals(com.xjzb.rts.core.Game.aiPick(89f, 6, 50));
        boolean bMix = heavyReachable && protossBandKept && waveGate4 && earlyZerg;
        System.out.println("  ai zerg mix wave4=" + w4 + " early-pure=" + earlyZerg
                + " protoss-band-kept=" + protossBandKept
                + " wave-gate=" + waveGate4 + " PASS=" + bMix);

        // =============== v2.11 batch C: the terran Brood War units ===========
        // --- C1. the armoury sells the upgrades; sciencefac gates the cruiser
        com.xjzb.rts.core.Game cg = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, starts, units, "terran");
        cg.mineralsPlayer = 20000;
        cg.gasPlayer = 20000;
        boolean rowsOk = com.xjzb.rts.core.Game.TYPES.get("armory").unitId == 123
                && com.xjzb.rts.core.Game.TYPES.get("engbay").unitId == 122
                && com.xjzb.rts.core.Game.TYPES.get("sciencefac").unitId == 116
                && "factory".equals(com.xjzb.rts.core.Game.TYPES.get("armory").requires)
                && "starport".equals(com.xjzb.rts.core.Game.TYPES.get("sciencefac").requires);
        String medicGate = cg.trainError("medic");
        String valkGate = cg.trainError("valkyrie");
        String bcGate = cg.trainError("battlecruiser");
        com.xjzb.rts.core.Game.Ent csv = null;
        for (com.xjzb.rts.core.Game.Ent e : cg.ents)
            if (e.team == 0 && e.type.key.equals("scv")) { csv = e; break; }
        boolean cFac = buildNear(cg, csv, "factory");
        boolean cArm = buildNear(cg, csv, "armory");
        String valkOpen = cg.trainError("valkyrie");
        boolean cPort = buildNear(cg, csv, "starport");
        boolean cSci = buildNear(cg, csv, "sciencefac");
        String bcOpen = cg.trainError("battlecruiser");
        // v2.25: the two advanced air rows now sit behind their add-ons. The
        // chain assertion checks the add-on gate first, then attaches the
        // control tower and physics lab and confirms the rows actually open --
        // a stricter check than the old "always open" one it replaces.
        boolean valkAddonGate = valkOpen != null && valkOpen.contains("控制塔");
        boolean bcAddonGate = bcOpen != null && bcOpen.contains("物理实验室");
        com.xjzb.rts.core.Game.Ent starport = null;
        for (com.xjzb.rts.core.Game.Ent e : cg.ents) {
            if (e.team != 0 || e.constructing) continue;
            if (e.type.key.equals("starport")) starport = e;
        }
        cg.gasPlayer = 5000;
        cg.mineralsPlayer = 5000;
        boolean towerAttached = starport != null
                && cg.buildAddon(starport, "controlt") != null;
        // The sciencefac buildNear() dropped sits in the packed starting base,
        // so its +x pad is occupied by the next building along. Give the lab a
        // science facility on open ground instead -- the gate is global, so it
        // does not matter which one carries the add-on.
        float[] labSpot = clearGround(cg, 3, 4);
        com.xjzb.rts.core.Game.Ent sciFac = labSpot != null
                ? cg.spawn("sciencefac", 0, labSpot[0], labSpot[1], true) : null;
        boolean labAttached = sciFac != null
                && cg.buildAddon(sciFac, "physicslab") != null;
        String valkAfter = cg.trainError("valkyrie");
        String bcAfter = cg.trainError("battlecruiser");
        boolean valkOpenNow = valkAfter == null || !valkAfter.contains("控制塔");
        boolean bcOpenNow = bcAfter == null || !bcAfter.contains("物理实验室");
        boolean cChain = rowsOk && cFac && cArm && cPort && cSci
                && medicGate != null && medicGate.contains("学院")
                && valkGate != null && valkGate.contains("军械库")
                && bcGate != null && bcGate.contains("科学设施")
                && valkAddonGate && bcAddonGate
                && towerAttached && labAttached && valkOpenNow && bcOpenNow;
        System.out.println("  terran chain factory=" + cFac + " armory=" + cArm
                + " starport=" + cPort + " sciencefac=" + cSci
                + " | medic->" + medicGate + " valkyrie->" + valkGate + " bc->" + bcGate
                + " | addon gate valkyrie=" + valkAddonGate + " bc=" + bcAddonGate
                + " | attached tower=" + towerAttached + " lab=" + labAttached
                + " | open valkyrie=" + valkOpenNow + " bc=" + bcOpenNow
                + " PASS=" + cChain);

        // --- C2. the medic heals organic friends and pays nothing ---
        com.xjzb.rts.core.Game mg = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent medic = mg.spawn("medic", 0, 420, 440, true);
        com.xjzb.rts.core.Game.Ent wounded = mg.spawn("marine", 0, 440, 440, true);
        com.xjzb.rts.core.Game.Ent tank2 = mg.spawn("tank", 0, 460, 440, true);
        com.xjzb.rts.core.Game.Ent scv2 = mg.spawn("scv", 0, 480, 440, true);
        com.xjzb.rts.core.Game.Ent zeal2 = mg.spawn("zealot", 0, 500, 440, true);
        com.xjzb.rts.core.Game.Ent foe2 = mg.spawn("marine", 1, 560, 440, true);
        // Strip every worker, not just this SCV: idle workers auto-mine, and a
        // single ore delivery would break the "the heal cost nothing" half of
        // this assertion. Removing them leaves the mineral count frozen.
        List<com.xjzb.rts.core.Game.Ent> workers = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : mg.ents)
            if (e.team == 0 && com.xjzb.rts.core.Game.isWorkerType(e.type.key))
                workers.add(e);
        mg.ents.removeAll(workers);
        mg.mineralsPlayer = 0;
        mg.damage(wounded, 20, null);
        mg.damage(tank2, 20, null);
        mg.damage(scv2, 20, null);
        mg.damage(zeal2, 20, null);
        mg.damage(foe2, 20, null);
        int hurtHp0 = wounded.hp;
        boolean bio = com.xjzb.rts.core.Game.isBiological(wounded)
                && !com.xjzb.rts.core.Game.isBiological(tank2)
                && !com.xjzb.rts.core.Game.isBiological(scv2)
                && !com.xjzb.rts.core.Game.isBiological(zeal2)
                && com.xjzb.rts.core.Game.isBiological(medic);
        String tankErr = mg.healError(tank2);
        String scvErr = mg.healError(scv2);
        String fullErr = mg.healError(medic);
        String foeErr = mg.healError(foe2);
        List<com.xjzb.rts.core.Game.Ent> sel = new ArrayList<>();
        sel.add(medic);
        sel.add(wounded);                    // a non-medic must be ignored
        boolean ordered = mg.orderHeal(sel, wounded);
        boolean onlyMedic = medic.healTarget == wounded && wounded.healTarget == null;
        for (int i = 0; i < 60; i++) mg.update(1 / 30f);
        boolean mended = wounded.hp > hurtHp0;
        boolean free = mg.mineralsPlayer == 0;
        boolean cMedic = bio && ordered && onlyMedic && mended && free
                && tankErr != null && tankErr.contains("生物")
                && scvErr != null && scvErr.contains("生物")
                && fullErr != null && fullErr.contains("未受损")
                && foeErr != null && foeErr.contains("我方");
        System.out.println("  medic heal " + hurtHp0 + "->" + wounded.hp
                + " free(minerals=" + mg.mineralsPlayer + ")=" + free
                + " only-medic=" + onlyMedic + " tank->" + tankErr
                + " scv->" + scvErr + " full->" + fullErr + " foe->" + foeErr
                + " PASS=" + cMedic);

        // --- C3. the vulture's spider mine arms, trips and is consumed ---
        com.xjzb.rts.core.Game vg = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent vul = vg.spawn("vulture", 0, 420, 440, true);
        String mineErr = vg.mineError(vul);
        boolean planted = vg.placeMine(vul);
        com.xjzb.rts.core.Game.Ent mine = null;
        for (com.xjzb.rts.core.Game.Ent e : vg.ents)
            if (e.type.key.equals("spider")) { mine = e; break; }
        boolean cooling = vg.mineError(vul) != null;
        // take the vulture out: otherwise it shoots the trip wire's victim itself
        vg.ents.remove(vul);
        com.xjzb.rts.core.Game.Ent victim = null;
        if (mine != null) {
            victim = vg.spawn("zergling", 1, mine.x + 30, mine.y, true);
            for (int i = 0; i < 60; i++) vg.update(1 / 30f);
        }
        boolean blew = victim != null && !victim.alive();
        boolean spent = mine != null && !mine.alive();
        boolean cMine = mineErr == null && planted && mine != null && cooling
                && blew && spent;
        System.out.println("  spider mine placed=" + planted + " cooling=" + cooling
                + " victim-dead=" + blew + " mine-spent=" + spent
                + " PASS=" + cMine);
    }

    /**
     * A Game with every enemy entity removed, so a targeting assertion has
     * exactly the two units it spawned to reason about. The skirmish opening
     * puts a full zerg base down and any of its units can be nearer to the
     * probe than the one under test.
     *
     * One enemy building is put back, far from every probe coordinate: with no
     * enemy building at all `update` sets status="win" and then returns before
     * simulating anything, so every timed assertion (the swarm lifting, the
     * mine arming) would freeze on its first frame. It is a sunken colony and
     * not a hatchery on purpose -- `aiUpdate` keys off a team-1 hatchery, so a
     * hatchery here would wake the skirmish AI inside a "clean" game.
     */
    /** v2.22: fill a caster's pool for a test. Real casters arrive at 50 and
     * regen -- the tests exercise the spell paths at a full bar instead of
     * waiting game-minutes between casts. */
    static void fullEnergy(com.xjzb.rts.core.Game.Ent e) {
        if (e != null) e.energy = e.maxEnergy > 0
                ? e.maxEnergy : com.xjzb.rts.core.Game.ENERGY_MAX;
    }

    /**
     * A spot where a `tiles`x`tiles` building fits with its +x add-on pad
     * (2 tiles) clear and a margin all round. Used by the v2.25 add-on tests,
     * which need a parent that is nowhere near the map's starting base -- the
     * plain openGround() scan happily returns a square that already has a
     * command centre two tiles away. Returns {x, y} of the parent centre, or
     * null. The scan runs from the far corner so it is deterministic.
     */
    static float[] clearGround(com.xjzb.rts.core.Game g, int tiles, int margin) {
        int half = tiles / 2;
        for (int ty = g.hTiles - 4 - tiles; ty >= 4; ty--)
            for (int tx = g.wTiles - 4 - tiles - 2; tx >= 4; tx--) {
                float wx = tx * 32f + 16, wy = ty * 32f + 16;
                boolean ok = true;
                // the footprint plus the +x pad, plus a margin
                for (int dy = -half - margin; dy <= half + margin && ok; dy++)
                    for (int dx = -half - margin;
                         dx <= half + 2 + margin && ok; dx++) {
                        int mx = (int) ((wx + dx * 32) / 8);
                        int my = (int) ((wy + dy * 32) / 8);
                        if (!g.passMini(mx, my)) ok = false;
                    }
                if (!ok) continue;
                boolean clear = true;
                for (com.xjzb.rts.core.Game.Ent e : g.ents) {
                    if (!e.alive()) continue;
                    if (Math.abs(e.x - wx) < (tiles + 2) * 32
                            && Math.abs(e.y - wy) < (tiles + 2) * 32) { clear = false; break; }
                }
                for (com.xjzb.rts.core.Game.Mineral m : g.minerals) {
                    if (Math.abs(m.x - wx) < (tiles + 3) * 32
                            && Math.abs(m.y - wy) < (tiles + 3) * 32) { clear = false; break; }
                }
                if (clear) return new float[]{wx, wy};
            }
        return null;
    }

    static com.xjzb.rts.core.Game cleanGame(String race) {
        com.xjzb.rts.core.Game g = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, elev, starts, units, race);
        List<com.xjzb.rts.core.Game.Ent> drop = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : g.ents) if (e.team != 0) drop.add(e);
        g.ents.removeAll(drop);
        // Bottom-right corner: `openGround` scans from the top-left, so this
        // stays far outside the range of every probe the assertions spawn.
        g.spawn("sunken", 1, g.wPx - 64, g.hPx - 64, true);
        return g;
    }

    /**
     * A walkable spot with `need` pixels of clear ground to its right, for the
     * movement assertions. Scans from the map corner so it is deterministic and
     * far from the bases. Returns null if the map has no such corridor.
     */
    static float[] openGround(com.xjzb.rts.core.Game g, float need) {
        for (int ty = 4; ty < g.hTiles - 4; ty++)
            for (int tx = 4; tx < g.wTiles - 4; tx++) {
                float wx = tx * 32f + 16, wy = ty * 32f + 16;
                boolean ok = true;
                for (float k = 0; k <= need; k += 8f)
                    if (!g.passMini((int) ((wx + k) / 8), (int) (wy / 8))) {
                        ok = false;
                        break;
                    }
                if (ok) return new float[]{wx, wy};
            }
        return null;
    }

    /** The three protoss units the skirmish AI can slip into a wave. */
    static boolean isProtossUnit(String key) {
        return "zealot".equals(key) || "dragoon".equals(key)
                || "scout".equals(key);
    }

    /**
     * Place `key` with `worker`, trying a ring of offsets until one is legal,
     * and wait for the building to finish. Returns whether it now exists.
     * The protoss tech-gate assertion needs a real gateway before the core, and
     * a single hard-coded offset is fragile on a map with minerals nearby.
     */
    static boolean buildNear(com.xjzb.rts.core.Game g,
                             com.xjzb.rts.core.Game.Ent worker, String key) {
        if (worker == null) return false;
        float[] dx = {70, -70, 70, -70, 140, -140, 0, 0};
        float[] dy = {70, 70, -70, -70, 0, 0, 140, -140};
        for (int i = 0; i < dx.length; i++) {
            float bx = worker.x + dx[i], by = worker.y + dy[i];
            if (g.buildError(key, bx, by) != null) continue;
            if (buildAt(g, worker, key, bx, by)) return true;
        }
        // The starting base is crowded (hatchery/nexus/cc plus minerals and the
        // opening workers), so a fixed ring of eight offsets can be entirely
        // blocked. Fall back to the nearest legal tile on the whole map: the
        // assertion is about the tech gate, not about where the building lands.
        float best = Float.MAX_VALUE;
        float bx = -1, by = -1;
        for (int ty = 1; ty < g.hTiles - 1; ty++)
            for (int tx = 1; tx < g.wTiles - 1; tx++) {
                float wx = tx * 32f + 16, wy = ty * 32f + 16;
                if (g.buildError(key, wx, wy) != null) continue;
                float d = (wx - worker.x) * (wx - worker.x)
                        + (wy - worker.y) * (wy - worker.y);
                if (d < best) {
                    best = d;
                    bx = wx;
                    by = wy;
                }
            }
        return bx >= 0 && buildAt(g, worker, key, bx, by);
    }

    /** tryBuild at one spot, then wait out the construction. */
    static boolean buildAt(com.xjzb.rts.core.Game g,
                           com.xjzb.rts.core.Game.Ent worker,
                           String key, float bx, float by) {
        g.tryBuild(worker, key, bx, by);
        // Put the worker on the site once the order exists. tryBuild already
        // ran canPlace (which would refuse if the worker stood here), and the
        // build-work block only needs the worker within tiles*16+24. Without
        // this the worker has to path across the map, and a site it cannot
        // reach leaves the building unfinished forever -- the assertion is
        // about the tech gate, not about the drone's commute.
        worker.x = bx;
        worker.y = by;
        worker.moving = false;
        worker.path = Game.Ent.EMPTY_PATH;
        for (int k = 0; k < 3000 && !g.hasBuilding(0, key); k++) g.update(1 / 30f);
        return g.hasBuilding(0, key);
    }

    /** Build a Game for a mission id, loading that mission's map. */
    static com.xjzb.rts.core.Game missionGame(String id) throws Exception {
        String json = new String(Files.readAllBytes(
                Paths.get(ASSETS + "/missions/" + id + ".json")),
                java.nio.charset.StandardCharsets.UTF_8);
        com.xjzb.rts.core.Mission m = com.xjzb.rts.core.Mission.parse(json);
        if (m == null) throw new IllegalStateException("mission parse failed: " + id);
        mapId = m.map;
        readMap();
        com.xjzb.rts.core.Game g = new com.xjzb.rts.core.Game(mapW, mapH, walk, starts, units);
        g.mapMeta = mapMetaText;
        g.setMission(m);
        return g;
    }

    /** m1: the survive objective must fail into a loss when the cc dies. */
    static void missionTest1() throws Exception {
        com.xjzb.rts.core.Game g = missionGame("m01");
        boolean hasCc = false, hasZerg = false;
        for (com.xjzb.rts.core.Game.Ent e : g.ents) {
            if (e.team == 0 && e.type.key.equals("cc")) hasCc = true;
            if (e.team == 1) hasZerg = true;
        }
        // kill the command center -> protect objective fails -> lose
        for (com.xjzb.rts.core.Game.Ent e : g.ents)
            if (e.team == 0 && e.type.key.equals("cc")) e.hp = 0;
        g.update(1f / 30f);
        g.update(1f / 30f);
        System.out.println("  m01 start cc=" + hasCc + " zerg=" + hasZerg
                + " status=" + g.status
                + " PASS=" + (hasCc && hasZerg && g.status.equals("lose")));
    }

    /** m2: destroying every enemy entity must satisfy destroyAll -> win. */
    static void missionTest2() throws Exception {
        com.xjzb.rts.core.Game g = missionGame("m02");
        int enemy = 0;
        for (com.xjzb.rts.core.Game.Ent e : g.ents) if (e.team == 1) enemy++;
        for (com.xjzb.rts.core.Game.Ent e : g.ents) if (e.team == 1) e.hp = 0;
        for (int i = 0; i < 4; i++) g.update(1f / 30f);
        System.out.println("  m02 enemy=" + enemy + " status=" + g.status
                + " PASS=" + (enemy > 0 && g.status.equals("win")));
    }

    /** m3: a protect objective must fail (and lose) when its target dies. */
    static void missionTest3() throws Exception {
        com.xjzb.rts.core.Game g = missionGame("m03");
        boolean found = false;
        for (com.xjzb.rts.core.Game.Ent e : g.ents)
            if (e.team == 0 && e.type.key.equals("barracks")) {
                e.hp = 0;
                found = true;
            }
        for (int i = 0; i < 4; i++) g.update(1f / 30f);
        System.out.println("  m03 protect-barracks found=" + found
                + " status=" + g.status
                + " PASS=" + (found && g.status.equals("lose")));
    }

    /** m4 (plan 8.4): a timed wave spawns its units once the clock passes. */
    static void missionTest4() throws Exception {
        com.xjzb.rts.core.Game g = missionGame("m01");
        int before = 0;
        for (com.xjzb.rts.core.Game.Ent e : g.ents) if (e.team == 1) before++;
        // run to just past the 90 s wave
        for (int i = 0; i < 30 * 100; i++) g.update(1f / 30f);
        int after = 0;
        for (com.xjzb.rts.core.Game.Ent e : g.ents) if (e.team == 1) after++;
        com.xjzb.rts.core.Mission m = g.mission;
        boolean fired = false;
        for (com.xjzb.rts.core.Mission.Event ev : m.events)
            if ("wave".equals(ev.action) && ev.fired) fired = true;
        System.out.println("  m01 wave enemy " + before + "->" + after
                + " elapsed=" + String.format("%.0f", m.elapsed())
                + " fired=" + fired
                + " PASS=" + (after > before && fired));
    }

    /**
     * v2.7 9.5: the plan asks for a balance walk of the graduation mission on
     * all three difficulties. Simulating instead of hand-playing gives a
     * repeatable number: the enemy must keep producing units on every
     * difficulty, and the harder tiers must out-produce the easier one.
     */
    static void missionTest5() throws Exception {
        int[] produced = new int[3];
        for (int d = 0; d < 3; d++) {
            com.xjzb.rts.core.Game g = missionGame("m05");
            g.difficulty = d;
            for (int i = 0; i < 30 * 240; i++) g.update(1f / 30f);   // 4 minutes
            int n = 0;
            for (com.xjzb.rts.core.Game.Ent e : g.ents) if (e.team == 1) n++;
            produced[d] = n;
        }
        boolean allProduce = produced[0] > 0 && produced[1] > 0 && produced[2] > 0;
        boolean scales = produced[2] >= produced[0];
        System.out.println("  m05 4min enemy count easy/normal/hard = "
                + produced[0] + "/" + produced[1] + "/" + produced[2]
                + " PASS=" + (allProduce && scales));
    }

    static void readManifest() throws Exception {
        for (String line : Files.readAllLines(Paths.get(ASSETS + "/sprites/manifest.txt"))) {
            String[] p = line.trim().split(",");
            if (p.length < 6) continue;
            manifest.put(p[0], new int[]{Integer.parseInt(p[1]), Integer.parseInt(p[2]),
                    Integer.parseInt(p[3]), Integer.parseInt(p[4]), Integer.parseInt(p[5])});
        }
        System.out.println("manifest rows: " + manifest.size());
    }

    // ---- public wrappers so sibling harnesses (ShadowProof) can reuse loading ----

    static void readManifestPublic() throws Exception {
        readManifest();
    }

    static void readMapPublic(String id) throws Exception {
        mapId = id;
        readMap();
        game = new com.xjzb.rts.core.Game(mapW, mapH, walk, starts, units);
    }

    /** v2.44: decode-faithful PNG mirror of the sprite sheets, produced by
     * make_harness_sprites.py. The shipped sheets are lossless (VP8L) WEBP;
     * Android's libwebp decodes their alpha correctly, but the TwelveMonkeys
     * imageio-webp plugin on this classpath does NOT -- every sheet came back
     * opaque with garbage background RGB, which is the "coloured block behind
     * every unit" the v2.43-era art crops show. Prefer the mirror so harness
     * renders show what actually ships; fall back to the WEBP when absent. */
    static final String HARNESS_SPRITES = "F:/KF/XJZB/AndroidPort/tools/harness_sprites";

    static BufferedImage sheet(String key, boolean enemy) {
        String k = key + (enemy ? "#e" : "");
        BufferedImage img = sheets.get(k);
        if (img != null) return img;
        for (String ext : new String[]{".png"}) {
            try {
                File f = new File(HARNESS_SPRITES + "/" + key
                        + (enemy ? "_r" : "_b") + ext);
                if (f.exists()) {
                    img = ImageIO.read(f);
                    if (img != null) {
                        sheets.put(k, img);
                        return img;
                    }
                }
            } catch (Exception ex) {
                img = null;
            }
        }
        if (img == null) {
            for (String ext : new String[]{".webp", ".png"}) {
                try {
                    img = ImageIO.read(new File(ASSETS + "/sprites/" + key
                            + (enemy ? "_r" : "_b") + ext));
                    if (img != null) break;
                } catch (Exception ex) {
                    img = null;
                }
            }
        }
        if (img == null) return null;
        sheets.put(k, img);
        return img;
    }

    static void readMap() throws Exception {
        StringBuilder metaSb = new StringBuilder();
        // The harness switches maps between tests, so every per-map list has to
        // be reset here. `starts`/`units` used to accumulate across readMap
        // calls, which left a later map holding the previous map's start
        // positions and resource rows.
        starts = new ArrayList<>();
        units = new ArrayList<>();
        for (String line : Files.readAllLines(Paths.get(ASSETS + "/maps/" + mapId + "/meta.txt"))) {
            metaSb.append(line).append('\n');
            line = line.trim();
            if (line.startsWith("w=")) mapW = Integer.parseInt(line.substring(2));
            else if (line.startsWith("h=")) mapH = Integer.parseInt(line.substring(2));
            else if (line.startsWith("start=")) {
                String[] p = line.substring(6).split(",");
                starts.add(new int[]{Integer.parseInt(p[0]), Integer.parseInt(p[1])});
            } else if (line.startsWith("unit=")) {
                String[] p = line.substring(5).split(",");
                units.add(new Object[]{Integer.parseInt(p[0]),
                        Float.parseFloat(p[1]), Float.parseFloat(p[2]),
                        Integer.parseInt(p.length > 5 ? p[5] : "0")});
            }
        }
        mapMetaText = metaSb.toString();
        walk = new boolean[mapW * 4 * mapH * 4];
        // The shipped name is walk.bin.gz; aapt unpacks it to walk.bin inside
        // the APK, but on disk (and for this harness) it stays gzipped. Build
        // intermediates may hold a plain walk.bin, so accept all three names.
        byte[] raw = null;
        for (String name : new String[]{"walk.bin.gz", "walk.gz", "walk.bin"}) {
            java.nio.file.Path p = Paths.get(ASSETS + "/maps/" + mapId + "/" + name);
            if (Files.exists(p)) {
                java.io.InputStream in = name.endsWith(".gz")
                        ? new java.util.zip.GZIPInputStream(Files.newInputStream(p))
                        : Files.newInputStream(p);
                raw = in.readAllBytes();
                in.close();
                break;
            }
        }
        if (raw != null)
            for (int i = 0; i < raw.length && i < walk.length; i++) walk[i] = raw[i] != 0;
        else
            java.util.Arrays.fill(walk, true);

        // v2.23 batch C: the ground-level bitmap, same three names as the walk
        // map (the APK carries a gunzipped elev.bin). Missing means null, which
        // the Game reads as "one flat level".
        elev = null;
        byte[] eraw = null;
        for (String name : new String[]{"elev.bin.gz", "elev.gz", "elev.bin"}) {
            java.nio.file.Path p = Paths.get(ASSETS + "/maps/" + mapId + "/" + name);
            if (Files.exists(p)) {
                java.io.InputStream in = name.endsWith(".gz")
                        ? new java.util.zip.GZIPInputStream(Files.newInputStream(p))
                        : Files.newInputStream(p);
                eraw = in.readAllBytes();
                in.close();
                break;
            }
        }
        if (eraw != null && eraw.length == walk.length) elev = eraw;
    }

    static BufferedImage chunk(int cx, int cy) {
        String key = cx + "_" + cy;
        BufferedImage b = chunkCache.get(key);
        if (b == null) {
            for (String ext : new String[]{".webp", ".png"}) {
                try {
                    b = ImageIO.read(new File(ASSETS + "/maps/" + mapId + "/c_" + key + ext));
                    if (b != null) break;
                } catch (Exception e) {
                    b = null;
                }
            }
            if (b == null) return null;
            chunkCache.put(key, b);
        }
        return b;
    }

    static float camX, camY = 0, zoom = 1f;

    /**
     * v2.10 batch A: build a small protoss scene and render it. Spawns on
     * walkable ground found by scanning (bloodbath's centre is a wall), gives
     * the units a shield to show the blue bar, and fires one psionic storm so
     * the sheet-drawn effect path runs.
     */
    static void protossFrame() throws Exception {
        // v2.44: build a FRESH game. This frame used to run on the static game
        // -- the one the 180s AI simulation ended in 'lose' -- and update()
        // is a no-op once status is set (`if (!status.isEmpty()) return`), so
        // the storm never ticked and the frame assertion failed on a healthy
        // engine. spellFrame below always built its own game; this one does now
        // too.
        readMapById(mapId);
        float bx = -1, by = -1;
        outer:
        for (int ty = 6; ty < game.hTiles - 8; ty++) {
            for (int tx = 6; tx < game.wTiles - 8; tx++) {
                float wx = tx * 32f + 16, wy = ty * 32f + 16;
                boolean clear = true;
                for (int ox = -2; ox <= 4 && clear; ox++)
                    for (int oy = -2; oy <= 4 && clear; oy++)
                        if (!game.passMini((int) ((wx + ox * 32) / 8),
                                (int) ((wy + oy * 32) / 8))) clear = false;
                if (!clear) continue;
                bx = wx;
                by = wy;
                break outer;
            }
        }
        if (bx < 0) { System.out.println("protoss frame: no open ground"); return; }

        com.xjzb.rts.core.Game.Ent nexus =
                game.spawn("nexus", 0, bx, by, true);
        game.spawn("pylon", 0, bx + 150, by - 40, true);
        com.xjzb.rts.core.Game.Ent zealot =
                game.spawn("zealot", 0, bx - 90, by + 90, true);
        com.xjzb.rts.core.Game.Ent dragoon =
                game.spawn("dragoon", 0, bx - 30, by + 120, true);
        com.xjzb.rts.core.Game.Ent templar =
                game.spawn("templar", 0, bx + 40, by + 110, true);
        fullEnergy(templar);   // v2.22: casters test at a full pool
        game.spawn("scout", 0, bx + 60, by - 120, true);
        // an enemy to storm, and to give the shield bar something to show
        com.xjzb.rts.core.Game.Ent foe =
                game.spawn("zergling", 1, bx + 210, by + 130, true);
        // partial shields so the blue bar is actually visible in the render
        zealot.shield = zealot.type.shield / 2;
        dragoon.shield = dragoon.type.shield / 3;
        templar.shield = 0;
        zealot.selected = true;
        dragoon.selected = true;
        templar.selected = true;

        boolean cast = game.castStorm(templar, foe.x, foe.y);
        // run past the first storm tick (STORM_TICK is 0.25 s) so the damage
        // has actually landed, but stay well inside STORM_DURATION so the
        // effect is still at full opacity when it is captured.
        for (int i = 0; i < 18; i++) game.update(1f / 30f);

        camX = bx + 40;
        camY = by + 40;
        render("frame_protoss.png");
        System.out.println("protoss frame: nexus=" + (nexus != null)
                + " storm=" + cast + " storms=" + game.storms.size()
                + " foeHp=" + foe.hp + "/" + foe.type.hp
                + " zealotShield=" + zealot.shield + "/" + zealot.type.shield
                + " PASS=" + (nexus != null && cast && foe.hp < foe.type.hp
                              && zealot.shield > 0 && zealot.shield < zealot.type.shield));
    }

    /**
     * v2.14 batch 1.5: draw all six spell effects mid-animation so the new
     * sheets are exercised by the renderer and not only by the manifest
     * assertions. Each effect is cast by its real caster through the real entry
     * point, then the game is stepped just far enough that every animation is
     * partway through its run.
     */
    static void spellFrame() throws Exception {
        com.xjzb.rts.core.Game g = cleanGame("terran");
        float[] spot = openGround(g, 700f);
        if (spot == null) spot = new float[]{600f, 600f};
        float bx = spot[0], by = spot[1];

        com.xjzb.rts.core.Game.Ent vessel = g.spawn("vessel", 0, bx, by, true);
        fullEnergy(vessel);   // v2.22: casters test at a full pool
        com.xjzb.rts.core.Game.Ent ghost = g.spawn("ghost", 0, bx + 150, by, true);
        fullEnergy(ghost);   // v2.22: casters test at a full pool
        com.xjzb.rts.core.Game.Ent bc = g.spawn("battlecruiser", 0, bx + 300, by, true);
        fullEnergy(bc);   // v2.22: casters test at a full pool
        com.xjzb.rts.core.Game.Ent corsair = g.spawn("corsair", 0, bx + 450, by, true);
        fullEnergy(corsair);   // v2.22: casters test at a full pool
        com.xjzb.rts.core.Game.Ent medic = g.spawn("medic", 0, bx, by + 150, true);

        // the targets, laid out under their casters
        com.xjzb.rts.core.Game.Ent empTgt = g.spawn("marine", 1, bx, by + 60, true);
        com.xjzb.rts.core.Game.Ent irradTgt = g.spawn("zergling", 1, bx + 150, by + 60, true);
        com.xjzb.rts.core.Game.Ent yamatoTgt = g.spawn("ultra", 1, bx + 300, by + 60, true);
        com.xjzb.rts.core.Game.Ent lockTgt = g.spawn("tank", 1, bx + 230, by + 70, true);
        com.xjzb.rts.core.Game.Ent healTgt = g.spawn("marine", 0, bx, by + 220, true);
        healTgt.hp = 10;

        boolean emp = g.castEmp(vessel, empTgt.x, empTgt.y);
        // irradiate shares the vessel's cooldown, so clear it to show both
        vessel.empCd = 0f;
        boolean irrad = g.castIrradiate(vessel, irradTgt);
        boolean yamato = g.castYamato(bc, yamatoTgt);
        boolean lock = g.castLockdown(ghost, lockTgt);
        boolean web = g.castDweb(corsair, bx + 450, by + 60);
        boolean heal = g.orderHeal(java.util.Collections.singletonList(medic), healTgt);

        // step a third of a second: every effect is a few frames in and still
        // fully opaque, and the yamato bolt is still in flight (it is slow
        // enough that the impact plasma has not played yet), so `anims` holds
        // the caster-side blastcan spark.
        for (int i = 0; i < 10; i++) g.update(1f / 30f);

        camX = bx + 200;
        camY = by + 60;
        game = g;
        render("frame_spells.png");
        System.out.println("spell frame emp=" + emp + " irrad=" + irrad + " yamato="
                + yamato + " lockdown=" + lock + " dweb=" + web + " heal=" + heal
                + " anims=" + g.anims.size() + " PASS="
                + (emp && irrad && yamato && lock && web && heal));
    }

    static void render(String out) throws Exception {
        // v2.43 section 2: the bench reuses one image and skips the PNG encode,
        // so its render timing is drawing cost rather than ImageIO cost.
        BufferedImage img = benchImg != null ? benchImg
                : new BufferedImage(viewW, viewH, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = img.createGraphics();
        g.setColor(new Color(6, 8, 12));
        g.fillRect(0, 0, viewW, viewH);

        int cs = 512;
        int cx0 = Math.max(0, (int) ((camX - viewW / 2f) / cs));
        int cy0 = Math.max(0, (int) ((camY - viewH / 2f) / cs));
        for (int cy = cy0; cy * cs < game.hPx && cy <= cy0 + 1; cy++)
            for (int cx = cx0; cx * cs < game.wPx && cx <= cx0 + 1; cx++) {
                BufferedImage b = chunk(cx, cy);
                if (b != null) {
                    g.drawImage(b, (int) ((cx * cs - camX) + viewW / 2f),
                            (int) ((cy * cs - camY) + viewH / 2f), null);
                }
            }

        for (int ty = 0; ty < game.hTiles; ty++)
            for (int tx = 0; tx < game.wTiles; tx++) {
                int f = game.fog[ty * game.wTiles + tx];
                if (f == 2) continue;
                int x = (int) ((tx * 32 - camX) + viewW / 2f);
                int y = (int) ((ty * 32 - camY) + viewH / 2f);
                g.setColor(f == 0 ? Color.BLACK : new Color(4, 6, 10, 140));
                g.fillRect(x, y, 32, 32);
            }

        for (com.xjzb.rts.core.Game.Mineral m : game.minerals) {
            String key = m.variant >= 3 ? "geyser"
                    : (m.variant == 0 ? "mineral" : m.variant == 1 ? "mineral2" : "mineral3");
            drawSheetCell(g, key, false, m.x, m.y, 0);
        }

        for (com.xjzb.rts.core.Game.Ent e : game.ents)
            if (e.alive() && e.isBuilding()) drawEnt(g, e);
        for (com.xjzb.rts.core.Game.Ent e : game.ents)
            if (e.alive() && !e.isBuilding()) drawEnt(g, e);

        // sprite effects
        for (com.xjzb.rts.core.Game.Anim a : game.anims) {
            int[] mf = manifest.get(a.key);
            if (mf == null) continue;
            BufferedImage s = sheet(a.key, a.team == 1);
            if (s == null) continue;
            int cols = mf[4];
            int fw = s.getWidth() / cols, fh = s.getHeight() / ((mf[3] + cols - 1) / cols);
            int idx = Math.min(a.frames - 1, (int) (a.t / a.frameTime));
            int sx = (idx % cols) * fw, sy = (idx / cols) * fh;
            int x = (int) ((a.x - camX) + viewW / 2f);
            int y = (int) ((a.y - camY) + viewH / 2f);
            int w = (int) (fw * a.scale), h = (int) (fh * a.scale);
            g.drawImage(s, x - w / 2, y - h * 2 / 3, x + w / 2, y + h / 3,
                    sx, sy, sx + fw, sy + fh, null);
        }

        // v2.10: the psionic storm, drawn straight from its sheet rather than
        // through a one-shot Anim, because the effect outlives the cast. Mirror
        // of GameView's storm pass so the harness can see the batch-A effect.
        for (com.xjzb.rts.core.Game.Storm st : game.storms) {
            BufferedImage s = sheet("psistorm", st.team == 1);
            int[] mf = manifest.get("psistorm");
            if (s == null || mf == null) continue;
            int nf = Math.max(1, mf[3]);
            int fr = ((int) (st.t * 14f)) % nf;
            int cols = mf[4];
            int fw = s.getWidth() / cols;
            int fh = s.getHeight() / ((mf[3] + cols - 1) / cols);
            int x = (int) ((st.x - camX) + viewW / 2f);
            int y = (int) ((st.y - camY) + viewH / 2f);
            int w = (int) (fw * 1.1f), h = (int) (fh * 1.1f);
            int sx = (fr % cols) * fw, sy = (fr / cols) * fh;
            g.drawImage(s, x - w / 2, y - h * 2 / 3, x + w / 2, y + h / 3,
                    sx, sy, sx + fw, sy + fh, null);
        }

        g.setColor(new Color(80, 255, 120));
        for (com.xjzb.rts.core.Game.Ent e : game.ents) {
            if (!e.alive() || !e.selected || e.team != 0) continue;
            int x = (int) ((e.x - camX) + viewW / 2f);
            int y = (int) ((e.y - camY) + viewH / 2f);
            g.drawOval(x - 14, y - 14, 28, 28);
        }

        g.dispose();
        if (benchNoWrite) return;   // v2.43 section 2: bench times drawing only
        ImageIO.write(img, "png", new File(OUT + out));
    }

    /** Draw frame `frame` of a kind-1 sheet centred on a world point. */
    static void drawSheetCell(Graphics2D g, String key, boolean enemy,
                              float wx, float wy, int frame) {
        BufferedImage s = sheet(key, enemy);
        int[] mf = manifest.get(key);
        if (s == null || mf == null) return;
        int cols = mf[4];
        int fw = s.getWidth() / cols;
        int fh = s.getHeight() / ((mf[3] + cols - 1) / cols);
        frame = Math.max(0, Math.min(mf[3] - 1, frame));
        int x = (int) ((wx - camX) + viewW / 2f);
        int y = (int) ((wy - camY) + viewH / 2f);
        int sx = (frame % cols) * fw, sy = (frame / cols) * fh;
        g.drawImage(s, x - fw / 2, y - fh * 2 / 3, x + fw / 2, y + fh / 3,
                sx, sy, sx + fw, sy + fh, null);
    }

    static void drawEnt(Graphics2D g, com.xjzb.rts.core.Game.Ent e) {
        int tf = game.fog[(int) (e.y / 32) * game.wTiles + (int) (e.x / 32)];
        if (e.team == 1 && tf == 0) return;
        BufferedImage s = sheet(e.type.key, e.team == 1);
        int[] mf = manifest.get(e.type.key);
        if (s == null || mf == null) return;
        int x = (int) ((e.x - camX) + viewW / 2f);
        int y = (int) ((e.y - camY) + viewH / 2f);
        int sx, sy, fw, fh;
        if (mf[0] == 0) {                 // unit: 17 dirs
            fw = s.getWidth() / 17;
            fh = s.getHeight() / (mf[1] + mf[2]);
            int row = 0;
            if (e.flashTime > 0 && mf[2] > 0) row = mf[1];
            else if (e.moving) row = ((int) (e.animTime / 0.16f)) % Math.max(1, mf[1]);
            sx = e.dir * fw;
            sy = row * fh;
        } else {                          // sheet: pose 0
            int cols = mf[4];
            fw = s.getWidth() / cols;
            fh = s.getHeight() / ((mf[3] + cols - 1) / cols);
            sx = 0;
            sy = 0;
        }
        g.drawImage(s, x - fw / 2, y - fh * 2 / 3, x + fw / 2, y + fh / 3,
                sx, sy, sx + fw, sy + fh, null);
        if (e.hp < e.type.hp) {
            g.setColor(Color.BLACK);
            g.fillRect(x - 12, y - 20, 24, 3);
            g.setColor(e.team == 0 ? new Color(90, 230, 110) : new Color(240, 80, 70));
            g.fillRect(x - 12, y - 20, (int) (24 * e.hp / (float) e.type.hp), 3);
        }
        // v2.10: protoss shields, a blue bar one row above the health bar.
        // Drawn whenever the shield is below full -- including at full hp,
        // because a stripped shield is exactly what the player needs to see.
        // Mirror of GameView's shield pass.
        if (e.type.shield > 0 && e.shield < e.type.shield) {
            g.setColor(Color.BLACK);
            g.fillRect(x - 12, y - 24, 24, 3);
            g.setColor(new Color(90, 200, 255));
            g.fillRect(x - 12, y - 24, (int) (24 * e.shield / (float) e.type.shield), 3);
        }
    }

    /**
     * Mirror of GameView.drawEnt's ground-shadow pass, kept separate so the
     * harness can render a frame with the bug and with the fix.
     *
     * The v2.3 regression was that the shadow's Paint was left at alpha 90 and
     * then reused to draw the sprite, modulating the bitmap down to ~35%
     * opacity. GameDesktop previously drew no shadow at all, so this class of
     * bug was invisible to it. `leakAlpha` reproduces the old behaviour.
     */
    static void drawShadow(Graphics2D g, com.xjzb.rts.core.Game.Ent e,
                           int x, int y, int fw, int fh, boolean leakAlpha) {
        if (e.isBuilding()) return;               // buildings: no shadow (too wide)
        float r = Math.max(e.type.radius, e.type.tiles * 14);
        java.awt.Composite saved = g.getComposite();
        int a = e.type.flying ? 45 : 90;
        // Model Android's Paint: setting the alpha affects THIS fill AND, if not
        // reset, every later draw that reuses the Paint. So we install an
        // AlphaComposite, fill the oval, and -- in the buggy case -- leave it set.
        g.setComposite(java.awt.AlphaComposite.getInstance(
                java.awt.AlphaComposite.SRC_OVER, a / 255f));
        g.setColor(Color.BLACK);
        if (e.type.flying) {
            g.fillOval((int) (x - r * 0.55f), (int) (y + r * 0.5f),
                    (int) (r * 1.1f), (int) (r * 0.22f));
        } else {
            g.fillOval((int) (x - r * 0.8f), (int) (y - r * 0.26f),
                    (int) (r * 1.6f), (int) (r * 0.52f));
        }
        if (!leakAlpha) {
            g.setComposite(saved);               // the fix: restore alpha
        }
    }

    /** Frame with shadows drawn before sprites, optionally leaking alpha. */
    static void renderWithShadows(java.util.List<com.xjzb.rts.core.Game.Ent> ents,
                                  String out, boolean leakAlpha) throws Exception {
        BufferedImage img = new BufferedImage(viewW, viewH, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = img.createGraphics();
        g.setRenderingHint(java.awt.RenderingHints.KEY_ANTIALIASING,
                java.awt.RenderingHints.VALUE_ANTIALIAS_ON);
        g.setColor(new Color(6, 8, 12));
        g.fillRect(0, 0, viewW, viewH);
        java.util.List<int[]> boxes = new java.util.ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : ents) {
            BufferedImage s = sheet(e.type.key, e.team == 1);
            int[] mf = manifest.get(e.type.key);
            if (s == null || mf == null) continue;
            int x = (int) ((e.x - camX) + viewW / 2f);
            int y = (int) ((e.y - camY) + viewH / 2f);
            int fw, fh;
            if (mf[0] == 0) { fw = s.getWidth() / 17; fh = s.getHeight() / (mf[1] + mf[2]); }
            else { int cols = mf[4]; fw = s.getWidth() / cols;
                   fh = s.getHeight() / ((mf[3] + cols - 1) / cols); }
            boxes.add(new int[]{x, y, fw, fh});
        }
        for (int i = 0; i < ents.size() && i < boxes.size(); i++) {
            int[] b = boxes.get(i);
            drawShadow(g, ents.get(i), b[0], b[1], b[2], b[3], leakAlpha);
        }
        for (int i = 0; i < ents.size() && i < boxes.size(); i++) {
            com.xjzb.rts.core.Game.Ent e = ents.get(i);
            int[] b = boxes.get(i);
            BufferedImage s = sheet(e.type.key, e.team == 1);
            g.drawImage(s, b[0] - b[2] / 2, b[1] - b[3] * 2 / 3,
                    b[0] + b[2] / 2, b[1] + b[3] / 3, 0, 0, b[2], b[3], null);
        }
        javax.imageio.ImageIO.write(img, "png", new java.io.File(out));
        System.out.println("wrote " + out + (leakAlpha ? "  [alpha leaked]" : "  [fixed]"));
    }

    /** Render every frame of a kind-1 sheet, labelled, for visual checks. */
    static void renderSheet(String key, String out) throws Exception {
        BufferedImage s = sheet(key, false);
        int[] mf = manifest.get(key);
        if (s == null || mf == null) {
            System.out.println("renderSheet MISS " + key);
            return;
        }
        int cols = mf[4], frames = mf[3];
        int fw = s.getWidth() / cols, fh = s.getHeight() / ((frames + cols - 1) / cols);
        BufferedImage img = new BufferedImage(cols * (fw + 4), ((frames + cols - 1) / cols) * (fh + 16),
                BufferedImage.TYPE_INT_RGB);
        Graphics2D g = img.createGraphics();
        g.setColor(new Color(24, 26, 34));
        g.fillRect(0, 0, img.getWidth(), img.getHeight());
        for (int i = 0; i < frames; i++) {
            int sx = (i % cols) * fw, sy = (i / cols) * fh;
            g.drawImage(s, (i % cols) * (fw + 4) + 2, (i / cols) * (fh + 16) + 14,
                    (i % cols) * (fw + 4) + 2 + fw, (i / cols) * (fh + 16) + 14 + fh,
                    sx, sy, sx + fw, sy + fh, null);
            g.setColor(Color.GREEN);
            g.drawString(String.valueOf(i), (i % cols) * (fw + 4) + 4,
                    (i / cols) * (fh + 16) + 12);
        }
        ImageIO.write(img, "png", new File(OUT + out));
    }

    /** Render one marine sprite in each of the 16 directions to verify dir mapping. */
    static void renderDirs(String out) throws Exception {
        BufferedImage s = sheet("marine", false);
        int[] mf = manifest.get("marine");
        int fw = s.getWidth() / 17;
        int fh = s.getHeight() / (mf[1] + mf[2]);
        BufferedImage img = new BufferedImage(17 * (fw + 2), fh + 16, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = img.createGraphics();
        g.setColor(new Color(24, 26, 34));
        g.fillRect(0, 0, img.getWidth(), img.getHeight());
        for (int d = 0; d < 17; d++) {
            g.drawImage(s, d * (fw + 2) + 1, 8, d * (fw + 2) + 1 + fw, 8 + fh,
                    d * fw, 0, (d + 1) * fw, fh, null);
            g.setColor(Color.GREEN);
            g.drawString(String.valueOf(d), d * (fw + 2) + 4, 8);
        }
        ImageIO.write(img, "png", new File(OUT + out));
    }

    // ============================================================ v2.17 tests

    /**
     * v2.17 [pick]: the two-stage hit test. GameView is an Android class and
     * cannot run here, so the harness mirrors its pick math (as it already
     * mirrors SpriteBank's decode policy) and asserts the conversions:
     *   - a small unit effective radius is max(nominal, 20dp/zoom), so it never
     *     shrinks below a fingertip;
     *   - a 4-tile building is picked by its rectangle, so all four true corners
     *     (which the old circle missed) register.
     */
    static void pickTests() {
        Game g = soloGame();
        float[] spot = openGround(g, 200f);
        if (spot == null) spot = new float[]{1000f, 1000f};
        Game.Ent scv = g.spawn("scv", 0, spot[0], spot[1], true);
        float nominal = Math.max(scv.type.radius, scv.type.tiles * 14) + 6;
        boolean smallOk = true;
        StringBuilder det = new StringBuilder();
        for (float zoom : new float[]{1.0f, 1.3f, 2.0f}) {
            float eff = Math.max(nominal, 20f * UI_SCALE / zoom);
            boolean inHit = pickHit(g, scv.x + eff - 0.5f, scv.y, zoom, true);
            boolean outHit = pickHit(g, scv.x + eff + 0.5f, scv.y, zoom, true);
            boolean tightMiss = !pickHit(g, scv.x + nominal + 0.5f, scv.y, zoom, false);
            smallOk &= inHit && !outHit && tightMiss;
            det.append(String.format(" z=%.1f eff=%.1f[%s%s%s]", zoom, eff,
                    inHit ? "in" : "IN-FAIL", outHit ? "OUT-FAIL" : "out",
                    tightMiss ? " tight" : " TIGHT-FAIL"));
        }
        System.out.println("  small-unit floor nominal=" + nominal
                + det + " PASS=" + smallOk);

        // --- 4-tile building: rectangle corners
        Game g2 = soloGame();
        float[] s2 = openGround(g2, 200f);
        if (s2 == null) s2 = new float[]{1000f, 1000f};
        Game.Ent cc = g2.spawn("cc", 0, s2[0], s2[1], true);
        float he = cc.type.tiles * 16f;
        float oldR = cc.type.tiles * 14f;
        float cornerDist = (float) Math.sqrt(he * he + he * he);
        boolean c1 = pickHit(g2, cc.x + he, cc.y + he, 1f, false);
        boolean c2 = pickHit(g2, cc.x - he, cc.y + he, 1f, false);
        boolean c3 = pickHit(g2, cc.x + he, cc.y - he, 1f, false);
        boolean c4 = pickHit(g2, cc.x - he, cc.y - he, 1f, false);
        boolean inside = pickHit(g2, cc.x + he - 8f, cc.y + he - 8f, 1f, false);
        boolean outside = !pickHit(g2, cc.x + he + 12f, cc.y, 1f, false);
        boolean rectOk = c1 && c2 && c3 && c4 && inside && outside;
        System.out.println("  4-tile corners he=" + he + " oldCircle=" + oldR
                + " cornerDist=" + String.format("%.1f", cornerDist)
                + " old-miss=" + (cornerDist > oldR)
                + " corners=" + (c1 && c2 && c3 && c4)
                + " inside=" + inside + " outside=" + outside
                + " PASS=" + rectOk);

        // --- fog: an explored-but-not-visible enemy is not pickable
        Game g3 = soloGame();
        Game.Ent foe = g3.spawn("zergling", 1, 500f, 500f, true);
        int fi = (int) (foe.y / 32) * g3.wTiles + (int) (foe.x / 32);
        g3.fog[fi] = 1;
        boolean fogHidden = !pickHit(g3, foe.x, foe.y, 1f, false);
        g3.fog[fi] = 2;
        boolean fogShown = pickHit(g3, foe.x, foe.y, 1f, false);
        System.out.println("  fog gate explored(1)->hidden=" + fogHidden
                + " visible(2)=" + fogShown + " PASS=" + (fogHidden && fogShown));
    }

    /**
     * Mirror of GameView.pickNearest for the desktop harness. UI_SCALE mirrors
     * GameView.uiScale (2 on any density > 1.5 device), so the pick floor is the
     * same 20dp of screen the phone uses: 20 * UI_SCALE / zoom world pixels.
     */
    static final float UI_SCALE = 2f;

    static boolean pickHit(Game g, float wx, float wy, float zoom, boolean useFloor) {
        float floor = useFloor ? 20f * UI_SCALE / zoom : 0f;
        for (Game.Ent e : g.ents) {
            if (!e.alive()) continue;
            if (e.team == 1) {
                int tf = g.fog[(int) (e.y / 32) * g.wTiles + (int) (e.x / 32)];
                if (tf != 2) continue;
            }
            float dx = Math.abs(e.x - wx), dy = Math.abs(e.y - wy);
            if (e.isBuilding()) {
                float r = e.type.tiles * 16f + 6f;
                if (useFloor) r = Math.max(r, floor);
                if (dx <= r && dy <= r) return true;
            } else {
                float r = Math.max(e.type.radius, e.type.tiles * 14) + 6;
                if (useFloor) r = Math.max(r, floor);
                if (dx * dx + dy * dy <= r * r) return true;
            }
        }
        return false;
    }

    /**
     * A Game with no units at all, plus one far-corner sunken to keep the AI
     * quiet (it keys off a team-1 hatchery, which this deliberately is not).
     */
    static Game soloGame() {
        Game g = new Game(mapW, mapH, walk, starts, units, "terran");
        g.ents.clear();
        g.spawn("sunken", 1, g.wPx - 64, g.hPx - 64, true);
        return g;
    }

    /**
     * v2.17 [camera]: the world-to-screen anchor. The old sy() used the screen
     * centre H/2 while the clamp used the playfield half-height, so a top-edge
     * camera left a permanent black band. With the anchor on the playfield
     * centre the two agreed exactly.
     *
     * v2.21 #1 tightens the promise: the clamp now guarantees the TERRAIN
     * covers the whole screen (top bar and console band included), because the
     * old playfield clamp let the map's south edge surface inside the
     * translucent console as a black slab. sy(0) must be <= 0 and sy(hPx)
     * >= H whenever the map is tall enough at the current zoom.
     */
    static void cameraTests() {
        int W = 1280, H = 720;
        float hud = 80f, bottomH = 300f;
        boolean ok = true;
        StringBuilder sb = new StringBuilder();
        for (int tiles : new int[]{96, 128, 256}) {
            float hPx = tiles * 32f;
            for (float zoom : new float[]{1.0f, 1.3f, 2.0f}) {
                float centerY = hud + (H - hud - bottomH) / 2f;
                float halfTop = centerY / zoom;
                float halfBot = (H - centerY) / zoom;
                float camTop = halfTop;
                float sy0 = (0 - camTop) * zoom + centerY;
                float camBot = Math.max(halfTop, hPx - halfBot);
                float syH = (hPx - camBot) * zoom + centerY;
                boolean topOk = sy0 <= 0.5f;
                boolean botOk = syH >= H - 0.5f;
                float oldSy0 = (0 - halfTop) * zoom + H / 2f;
                boolean oldGap = oldSy0 > hud + 1f;
                ok &= topOk && botOk && oldGap;
                sb.append(String.format(" %dt/z%.1f top=%.0f bot=%.0f",
                        tiles, zoom, sy0, syH));
            }
        }
        System.out.println("  camera covers full screen: sy(0)<=0 & sy(hPx)>=H"
                + sb + " PASS=" + ok);
    }

    /**
     * v2.17 [build]: the resume order and the protoss/zerg self-build. A worker
     * pulled off a terran site freezes it (and can be sent back), while a
     * protoss site keeps growing on its own.
     */
    static void buildTests() {
        // --- terran: pull the SCV, progress freezes; resume finishes it
        Game gt = workerGame("terran", "scv", 2);
        gt.mineralsPlayer = 5000; gt.gasPlayer = 5000;
        Game.Ent scv = firstWorker(gt, "scv");
        Game.Ent scv2 = secondWorker(gt, "scv", scv);
        float[] spot = scv == null ? null : findBuildSpot(gt, scv, "barracks");
        int m0 = gt.mineralsPlayer;
        boolean placed = scv != null && spot != null
                && gt.tryBuild(scv, "barracks", spot[0], spot[1]);
        Game.Ent site = placed ? findConstructing(gt, 0, "barracks") : null;
        int paid = m0 - gt.mineralsPlayer;
        // Let the builder actually make some progress first, so the freeze
        // assertion proves a NON-zero percentage is preserved (not just 0%).
        if (site != null && scv != null) {
            scv.x = site.x;
            scv.y = site.y + site.type.tiles * 16 + 8;
            scv.path = Game.Ent.EMPTY_PATH;
            scv.moving = false;
            for (int i = 0; i < 2 * 30 && site.constructing; i++) gt.update(1f / 30f);
        }
        // Pull BOTH workers far away so nothing is inside the tether. park()
        // first (it clears target), THEN teleport -- otherwise the build order
        // survives and the site keeps growing.
        if (scv != null) { park(scv); scv.x = 64; scv.y = gt.hPx - 64; }
        if (scv2 != null) { park(scv2); scv2.x = gt.wPx - 64; scv2.y = 64; }
        float pAtPull = site == null ? -1 : site.buildProgress;
        for (int i = 0; i < 20 * 30 && site != null && site.constructing; i++)
            gt.update(1f / 30f);
        boolean frozen = site != null && site.constructing
                && Math.abs(site.buildProgress - pAtPull) < 1e-4f;
        // Now resume with the second SCV standing on the site. Put the worker
        // there BEFORE issuing the order, then clear only its path (not its
        // target) so updateUnit takes the construction branch immediately.
        boolean resumed = false;
        if (frozen && scv2 != null) {
            scv2.x = site.x;
            scv2.y = site.y + site.type.tiles * 16 + 8;
            resumed = gt.orderResumeBuild(java.util.Collections.singletonList(scv2), site);
            scv2.path = Game.Ent.EMPTY_PATH;
            scv2.moving = false;
            for (int i = 0; i < 30 * 30 && site.constructing; i++) gt.update(1f / 30f);
            resumed = resumed && !site.constructing && site.buildProgress >= 1f;
        }
        int mEnd = gt.mineralsPlayer;
        boolean terranOk = placed && frozen && resumed && mEnd == m0 - paid;
        System.out.println("  terran placed=" + placed + " paid=" + paid
                + " freeze@" + String.format("%.2f", pAtPull) + "=" + frozen
                + " resume=" + resumed + " minerals " + m0 + "->" + mEnd
                + " expect=" + (m0 - paid) + " PASS=" + terranOk);

        // --- protoss: pull the probe, the pylon finishes on its own
        Game gp = workerGame("protoss", "probe", 1);
        gp.mineralsPlayer = 5000; gp.gasPlayer = 5000;
        Game.Ent probe = firstWorker(gp, "probe");
        float[] ps = probe == null ? null : findBuildSpot(gp, probe, "pylon");
        int pm0 = gp.mineralsPlayer;
        boolean pPlaced = probe != null && ps != null
                && gp.tryBuild(probe, "pylon", ps[0], ps[1]);
        Game.Ent psite = pPlaced ? findConstructing(gp, 0, "pylon") : null;
        // v2.17: the probe is released the moment the structure is dropped.
        boolean workerFree = probe != null && probe.target == null
                && probe.workerState == Game.Ent.W_IDLE;
        if (probe != null) { probe.x = 64; probe.y = gp.hPx - 64; park(probe); }
        float distAtDone = -1;
        for (int i = 0; i < 30 * 30 && psite != null && psite.constructing; i++) {
            gp.update(1f / 30f);
            if (!psite.constructing && probe != null)
                distAtDone = (float) Math.hypot(probe.x - psite.x, probe.y - psite.y);
        }
        float tether = psite == null ? 0 : psite.type.tiles * 16 + 24;
        boolean selfBuilt = psite != null && !psite.constructing && distAtDone > tether;
        int pCost = pPlaced ? Game.TYPES.get("pylon").cost : 0;
        boolean pMinerals = gp.mineralsPlayer == pm0 - pCost;
        System.out.println("  protoss placed=" + pPlaced + " workerFree=" + workerFree
                + " selfBuilt=" + selfBuilt
                + " workerDist@" + String.format("%.0f", distAtDone)
                + " tether=" + tether + " minerals-consistent=" + pMinerals
                + " PASS=" + (pPlaced && workerFree && selfBuilt && pMinerals));
    }

    /** Stop a worker dead so the test controls where it is, not its pathing. */
    static void park(Game.Ent e) {
        e.path = Game.Ent.EMPTY_PATH;
        e.moving = false;
        e.target = null;
        e.workerState = Game.Ent.W_IDLE;
    }

    /**
     * A Game of `race` with every enemy removed and only `keep` workers of
     * `key` left, plus one far-corner sunken so the AI stays asleep. This keeps
     * the build assertions free of stray workers inside the construction
     * tether.
     */
    static Game workerGame(String race, String key, int keep) {
        Game g = new Game(mapW, mapH, walk, starts, units, race);
        List<Game.Ent> drop = new ArrayList<>();
        int kept = 0;
        for (Game.Ent e : g.ents) {
            if (e.team != 0) { drop.add(e); continue; }
            if (e.type.key.equals(key)) {
                if (kept < keep) { kept++; continue; }
                drop.add(e);
            }
        }
        g.ents.removeAll(drop);
        g.spawn("sunken", 1, g.wPx - 64, g.hPx - 64, true);
        return g;
    }

    static Game.Ent firstWorker(Game g, String key) {
        for (Game.Ent e : g.ents)
            if (e.team == 0 && e.alive() && e.type.key.equals(key)) return e;
        return null;
    }

    static Game.Ent secondWorker(Game g, String key, Game.Ent not) {
        for (Game.Ent e : g.ents)
            if (e.team == 0 && e.alive() && e.type.key.equals(key) && e != not) return e;
        return null;
    }

    static Game.Ent findConstructing(Game g, int team, String key) {
        for (Game.Ent e : g.ents)
            if (e.team == team && e.alive() && e.constructing && e.type.key.equals(key))
                return e;
        return null;
    }

    /**
     * Find a legal placement near a worker. v2.44: this used to try eight fixed
     * offsets (80/-80/160/-160 on each axis). That is fine while the worker
     * always ends up in the same place, but the v2.44 pathing fix (start-skip
     * 3 -> 1, plus the passability gate on path following) legitimately moves
     * workers to different resting spots -- and then all eight probes can land
     * on rock, which made replayTests() silently record two orders instead of
     * three and fail its "meaningful" check. Scan a ring of radii instead, so
     * the helper depends on there being room SOMEWHERE nearby rather than on
     * one exact worker position.
     */
    static float[] findBuildSpot(Game g, Game.Ent w, String key) {
        if (g.buildError(key, w.x, w.y) == null) return new float[]{w.x, w.y};
        for (int r = 48; r <= 320; r += 32) {
            // 16 bearings per ring, starting due east so the result is stable.
            for (int k = 0; k < 16; k++) {
                double a = k * Math.PI / 8.0;
                float bx = w.x + (float) (Math.cos(a) * r);
                float by = w.y + (float) (Math.sin(a) * r);
                if (bx < 32 || by < 32 || bx > g.wPx - 32 || by > g.hPx - 32) continue;
                if (g.buildError(key, bx, by) == null) return new float[]{bx, by};
            }
        }
        return null;
    }


    /**
     * v2.18 batch A [fog]: the two vision models share one gate. The gate lives
     * in GameView (Android), so this mirrors it exactly -- HOK shows an enemy
     * only where the fog grid is CURRENTLY visible (fog==2), SC shows anything
     * on explored ground (fog!=0). It also pins the fog grid transitions that
     * drive the gate: unexplored 0 -> visible 2 on approach -> explored 1 after
     * the friendly unit leaves.
     */
    static void fogTests() {
        // The plan asks for 96/128/256 maps: the gate reads the fog grid by
        // tile, so a bigger grid must behave identically. Synthetic all-walkable
        // maps keep this independent of the shipped asset set.
        boolean all = true;
        StringBuilder sb = new StringBuilder();
        for (int tiles : new int[]{96, 128, 256}) {
            boolean one = fogTestOne(tiles);
            all &= one;
            sb.append(" ").append(tiles).append("t=").append(one ? "ok" : "FAIL");
        }
        System.out.println("  fog grid hok/sc gate 96/128/256" + sb + " PASS=" + all);
    }

    /** One vision-model check on a synthetic `tiles`x`tiles` all-walkable map. */
    static boolean fogTestOne(int tiles) {
        boolean[] w = new boolean[tiles * 4 * tiles * 4];
        java.util.Arrays.fill(w, true);
        List<int[]> st = new ArrayList<>();
        st.add(new int[]{2, 2});
        st.add(new int[]{tiles - 6, tiles - 6});
        Game g = new Game(tiles, tiles, w, st, new ArrayList<>(), "terran");
        g.ents.clear();
        java.util.Arrays.fill(g.fog, (byte) 0);
        // A far-away enemy building keeps the match from being declared won on
        // the first update (updateFog would then never run). A sunken, not a
        // hatchery, so the skirmish AI stays asleep.
        g.spawn("sunken", 1, g.wPx - 96, g.hPx - 96, true);
        float fx = g.wPx * 0.5f, fy = g.hPx * 0.5f;
        Game.Ent foe = g.spawn("zergling", 1, fx, fy, true);
        foe.hp = 999999;                     // the marine must not kill the subject
        Game.Ent hero = g.spawn("marine", 0, fx - 900, fy, true);
        int ft = (int) (fy / 32) * g.wTiles + (int) (fx / 32);
        boolean startZero = g.fog[ft] == 0;
        boolean farHok = !enemyVisibleLike(g, foe, true);
        boolean farSc = !enemyVisibleLike(g, foe, false);

        // approach to 200 px (~6 tiles, inside the 7-tile unit vision)
        hero.x = fx - 200;
        hero.y = fy;
        g.update(1f / 30f);
        boolean lit = g.fog[ft] == 2;
        boolean nearHok = enemyVisibleLike(g, foe, true);
        boolean nearSc = enemyVisibleLike(g, foe, false);

        // retreat well outside vision and let updateFog decay 2 -> 1
        hero.x = fx - 900;
        hero.y = fy;
        for (int i = 0; i < 3; i++) g.update(1f / 30f);
        boolean decayed = g.fog[ft] == 1;
        boolean goneHok = !enemyVisibleLike(g, foe, true);
        boolean rememberedSc = enemyVisibleLike(g, foe, false);

        return startZero && farHok && farSc && lit && nearHok && nearSc
                && decayed && goneHok && rememberedSc;
    }

    static boolean enemyVisibleLike(Game g, Game.Ent e, boolean hok) {
        int tf = g.fog[(int) (e.y / 32) * g.wTiles + (int) (e.x / 32)];
        return hok ? tf == 2 : tf != 0;
    }

    /**
     * v2.18 batch B [scale]: the zoom presets. Settings lives on Android, so the
     * arithmetic is mirrored here (as the harness already mirrors SpriteBank and
     * the pick math) and pinned to the plan's exact numbers. The important
     * invariant is the floor: the lowest reachable zoom is now 0.85, not 0.7,
     * so a small unit can never be pinched down to an unreadable size.
     */
    static void scaleTests() {
        float base = 1.3f, minB = 1.0f, maxB = 2.0f;
        float[] mult = {0.85f, 1.0f, 1.2f};
        String[] names = {"低", "标准", "高"};
        float[][] expect = {{1.105f, 0.85f, 1.7f}, {1.3f, 1.0f, 2.0f}, {1.56f, 1.2f, 2.4f}};
        boolean ok = true;
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 3; i++) {
            float d = base * mult[i], mn = minB * mult[i], mx = maxB * mult[i];
            boolean e = Math.abs(d - expect[i][0]) < 1e-4f
                    && Math.abs(mn - expect[i][1]) < 1e-4f
                    && Math.abs(mx - expect[i][2]) < 1e-4f;
            ok &= e && d >= mn && d <= mx;
            sb.append(String.format(" %s=%.3f/%.2f/%.2f%s", names[i], d, mn, mx, e ? "" : "!"));
        }
        boolean floorOk = minB * mult[0] >= 0.85f && base > 1.15f;
        System.out.println("  zoom presets" + sb + " floor>=0.85=" + floorOk
                + " PASS=" + (ok && floorOk));
    }

    /**
     * v2.19 batch C [layout]: the console layout abstraction and its two
     * presets. HudLayout lives on Android (it uses RectF), so this mirrors its
     * arithmetic exactly -- the same approach the harness already takes for
     * SpriteBank's decode policy and the pick math -- and pins the invariants
     * that matter: the default preset reproduces the old numbers, mirrored
     * swaps the minimap and the card, compact floats the minimap under the top
     * bar, and in every preset the two panels stay on screen and never overlap.
     */
    static void layoutTests() {
        int W = 1280, H = 720, dp = 2;
        float topH = 40 * dp;
        boolean ok = true;
        StringBuilder sb = new StringBuilder();
        for (int preset = 0; preset < 3; preset++) {
            float[] r = layoutMirror(W, H, topH, dp, preset);
            // r = {mmL, mmT, mmR, mmB, cardL, cardT, cardR, cardB, cardH, cy, hh}
            boolean onScreen = r[0] >= 0 && r[1] >= 0 && r[2] <= W && r[3] <= H
                    && r[4] >= 0 && r[5] >= 0 && r[6] <= W && r[7] <= H;
            boolean noOverlap = r[2] <= r[4] || r[6] <= r[0]
                    || r[3] <= r[5] || r[7] <= r[1];
            // v2.41: the playfield envelope is the whole screen in every preset
            boolean envelope = Math.abs(r[9] - H / 2f) < 0.5f && r[10] > 0;
            boolean one = onScreen && noOverlap && envelope;
            ok &= one;
            sb.append(" p").append(preset).append("=").append(one ? "ok" : "FAIL");
        }
        // preset-specific: default has the minimap left of the card; mirrored
        // swaps them; compact floats the minimap under the top chips and keeps
        // only the card at the bottom.
        float[] d = layoutMirror(W, H, topH, dp, 0);
        float[] m = layoutMirror(W, H, topH, dp, 1);
        float[] c = layoutMirror(W, H, topH, dp, 2);
        boolean defaultOk = d[0] < d[4];
        boolean mirroredOk = m[4] < m[0];
        boolean compactOk = c[3] < d[3] && c[0] < W * 0.25f;
        boolean compactConsole = Math.abs(c[8] - (3 * HudLayoutCardCell(H, dp)
                + 2 * 4 * dp + 10 * dp)) < 0.5f;
        boolean pass = ok && defaultOk && mirroredOk && compactOk && compactConsole;
        System.out.println("  layout presets" + sb + " defaultL<card=" + defaultOk
                + " mirrored=" + mirroredOk + " compactFloats=" + compactOk
                + " compactConsole=" + compactConsole + " PASS=" + pass);
    }

    /**
     * v2.20 batch C step 3 [layout]; v2.41 rewrite: the custom layout is FIVE
     * independent floating panels on a full-screen battlefield (no band, no
     * consoleTop). The invariants the editor promises are pinned: every panel
     * lands on screen, two panels that share screen area are reported as
     * overlapping (the save is refused), a clean spec saves and round-trips
     * through the comma string, and the playfield envelope is always the
     * whole screen (cy = H/2) no matter where the panels sit.
     */
    static void layoutCustomTests() {
        int W = 1280, H = 720, dp = 2;
        float topH = 40 * dp;
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // a hand-made spec: minimap bottom-left, card bottom-right, info centre,
        // clock top-centre, res after the pause chip
        float[] spec = {0.12f, 0.86f, 1f, 0.88f, 0.86f, 1f, 0.50f, 0.86f, 1f,
                0.50f, 0.05f, 1f, 0.28f, 0.05f, 1f};
        float[] r = layoutCustomMirror(W, H, topH, dp, spec);
        boolean onScreen = true;
        for (int p = 0; p < 5; p++)
            onScreen &= r[p * 4] >= 0 && r[p * 4 + 1] >= 0
                    && r[p * 4 + 2] <= W && r[p * 4 + 3] <= H;
        ok &= onScreen;
        sb.append(" onScreen=").append(onScreen);

        // the same spec with the card moved onto the minimap must overlap
        float[] clash = {0.12f, 0.86f, 1f, 0.12f, 0.86f, 1f, 0.50f, 0.86f, 1f,
                0.50f, 0.05f, 1f, 0.28f, 0.05f, 1f};
        boolean overlaps = layoutCustomOverlap(W, H, topH, dp, clash);
        ok &= overlaps;
        sb.append(" clashDetected=").append(overlaps);

        // a clean spec must not
        boolean clean = layoutCustomOverlap(W, H, topH, dp, spec);
        ok &= !clean;
        sb.append(" cleanOk=").append(!clean);

        // clamp: a panel pushed off the top-left still lands on screen
        float[] edge = {-0.5f, -0.5f, 2f, 0.88f, 0.86f, 0f, 0.50f, 0.50f, 1f,
                0.50f, 0.05f, 1f, 0.28f, 0.05f, 1f};
        float[] e = layoutCustomMirror(W, H, topH, dp, edge);
        boolean clamped = e[0] >= 0 && e[1] >= 0 && e[2] <= W && e[3] <= H;
        ok &= clamped;
        sb.append(" clamp=").append(clamped);

        // v2.41: the envelope no longer follows the panels -- the playfield is
        // the whole screen whatever the arrangement.
        boolean env = Math.abs(r[20] - H / 2f) < 0.5f && r[21] > 0;
        ok &= env;
        sb.append(" fullScreenEnv=").append(env);

        // spec string round-trip: the same 4-decimal format the app persists
        String s = formatSpecMirror(spec);
        float[] back = parseSpecMirror(s);
        boolean round = back != null && back.length == 15;
        for (int i = 0; round && i < 15; i++) round = Math.abs(back[i] - spec[i]) < 1e-4f;
        ok &= round;
        sb.append(" roundTrip=").append(round);

        System.out.println("  custom layout" + sb + " PASS=" + ok);
    }

    /** Mirror of HudLayout.computeCustom. Returns 22 values: five rects of 4
     *  (minimap, card, info, clock, res) plus cy and halfH. */
    static float[] layoutCustomMirror(int W, int H, float topH, float dp, float[] c) {
        float[] sc = {0.8f, 1.0f, 1.25f};
        float mmS = 150f * dp * sc[sizeIdxMirror(c[2])];
        float cell = 50f * dp * sc[sizeIdxMirror(c[5])];
        float cardW = 3 * cell + 2 * 4f * dp;
        float infoW = 150f * dp * sc[sizeIdxMirror(c[8])];
        float infoH = 90f * dp * sc[sizeIdxMirror(c[8])];
        float clockW = 64f * dp * sc[sizeIdxMirror(c[11])];
        float chipH = 26f * dp * sc[sizeIdxMirror(c[11])];
        float resW = 180f * dp * sc[sizeIdxMirror(c[14])];
        float[] mm = placeMirror(c[0] * W, c[1] * H, mmS, mmS, W, H, dp);
        float[] cd = placeMirror(c[3] * W, c[4] * H, cardW, cardW, W, H, dp);
        float[] inf = placeMirror(c[6] * W, c[7] * H, infoW, infoH, W, H, dp);
        float[] ck = placeMirror(c[9] * W, c[10] * H, clockW, chipH, W, H, dp);
        float[] rs = placeMirror(c[12] * W, c[13] * H, resW, chipH, W, H, dp);
        float cy = H / 2f, hh = H / 2f / 1.3f;
        return new float[]{mm[0], mm[1], mm[2], mm[3], cd[0], cd[1], cd[2], cd[3],
                inf[0], inf[1], inf[2], inf[3], ck[0], ck[1], ck[2], ck[3],
                rs[0], rs[1], rs[2], rs[3], cy, hh};
    }

    static int sizeIdxMirror(float v) {
        int i = Math.round(v);
        return i < 0 ? 0 : (i > 2 ? 2 : i);
    }

    static float[] placeMirror(float cx, float cy, float w, float h,
                               int W, int H, float dp) {
        float l = cx - w / 2f, t = cy - h / 2f;
        float margin = 4 * dp;
        if (l < margin) l = margin;
        if (t < margin) t = margin;
        if (l + w > W - margin) l = W - margin - w;
        if (t + h > H - margin) t = H - margin - h;
        return new float[]{l, t, l + w, t + h};
    }

    static boolean layoutCustomOverlap(int W, int H, float topH, float dp, float[] spec) {
        float[] r = layoutCustomMirror(W, H, topH, dp, spec);
        for (int a = 0; a < 5; a++)
            for (int b = a + 1; b < 5; b++) {
                float[] ra = {r[a * 4], r[a * 4 + 1], r[a * 4 + 2], r[a * 4 + 3]};
                float[] rb = {r[b * 4], r[b * 4 + 1], r[b * 4 + 2], r[b * 4 + 3]};
                if (ra[2] > rb[0] && ra[0] < rb[2] && ra[3] > rb[1] && ra[1] < rb[3])
                    return true;
            }
        return false;
    }

    /** Mirror of GameView.formatSpec (4-decimal, comma-joined, 15 floats). */
    static String formatSpecMirror(float[] v) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 15; i++) {
            if (i > 0) sb.append(',');
            sb.append(String.format(java.util.Locale.US, "%.4f", v[i]));
        }
        return sb.toString();
    }

    /** Mirror of GameView.parseSpec; null when malformed. */
    static float[] parseSpecMirror(String s) {
        if (s == null || s.isEmpty()) return null;
        String[] p = s.split(",");
        if (p.length < 9) return null;
        float[] v = new float[15];
        try {
            for (int i = 0; i < 15 && i < p.length; i++) v[i] = Float.parseFloat(p[i]);
        } catch (Exception e) {
            return null;
        }
        return v;
    }

    /**
     * v2.20 batch 5 [replay]: the round trip the plan asks for. A live match
     * records its orders; serializing and re-injecting that stream into a fresh
     * Game must reproduce the same stateHash at every one-second sample, or the
     * simulation has a source of non-determinism. The header parse and the
     * summary line the browser shows are pinned too.
     */
    static void replayTests() {
        // A FULL match, not soloGame(): that helper has no player base, so the
        // loss check fires on the first tick and the simulation stops before a
        // single order could be recorded (or replayed).
        Game live = new Game(mapW, mapH, walk, starts, units, "terran");
        live.recording = true;
        live.mapId = "bloodbath";
        live.difficulty = 1;
        List<Game.Ent> scvs = new ArrayList<>();
        for (Game.Ent e : live.ents)
            if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);
        List<Long> a = new ArrayList<>();
        for (int t = 0; t < 40; t++) { live.update(1f / 30f); hashSample(t, live, a); }
        if (!scvs.isEmpty()) {
            live.orderMove(scvs, live.wPx / 2f, live.hPx / 2f, false);
            live.recordOrder("move", scvs, (live.wPx / 2f) + " " + (live.hPx / 2f));
        }
        for (int t = 40; t < 400; t++) { live.update(1f / 30f); hashSample(t, live, a); }
        if (!scvs.isEmpty() && !live.minerals.isEmpty()) {
            Game.Mineral m = live.minerals.get(0);
            live.orderHarvest(scvs, m);
            live.recordOrder("harvest", scvs, String.valueOf(live.minerals.indexOf(m)));
        }
        for (int t = 400; t < 900; t++) { live.update(1f / 30f); hashSample(t, live, a); }
        if (!scvs.isEmpty()) {
            float[] spot = findBuildSpot(live, scvs.get(0), "barracks");
            if (spot != null) {
                boolean placed = live.tryBuild(scvs.get(0), "barracks", spot[0], spot[1]);
                live.recordOrder("build", scvs.subList(0, 1),
                        "barracks " + spot[0] + " " + spot[1]);
                if (!placed) System.out.println("  NOTE: barracks probe placement refused");
            }
        }
        for (int t = 900; t < 1500; t++) { live.update(1f / 30f); hashSample(t, live, a); }

        String rep = live.serializeReplay();
        Game back = new Game(mapW, mapH, walk, starts, units, "terran");
        back.difficulty = 1;
        boolean loaded = back.loadReplay(rep);
        List<Long> b = new ArrayList<>();
        for (int t = 0; t < 1500; t++) { back.update(1f / 30f); hashSample(t, back, b); }

        boolean same = a.size() == b.size() && a.size() > 20;
        int firstDiff = -1;
        for (int i = 0; i < a.size() && same; i++)
            if (!a.get(i).equals(b.get(i))) { same = false; firstDiff = i; }
        boolean meaningful = live.replayLog.size() >= 3;
        System.out.println("  replay determinism samples=" + a.size() + " cmds="
                + live.replayLog.size() + " loaded=" + loaded + " status='" + live.status + "'"
                + (firstDiff >= 0 ? " firstDiff=" + firstDiff : "")
                + " PASS=" + (same && loaded && meaningful));

        // the header must carry the map/race/difficulty a re-run needs
        String header = live.replayHeader();
        boolean head = header.contains("map bloodbath") && header.contains("race terran")
                && header.contains("difficulty 1");
        // summary line: map · race · difficulty · N 指令 · T 秒
        String sum = Game.replaySummary(rep);
        boolean sumOk = sum.startsWith("bloodbath") && sum.contains("人族")
                && sum.contains("指令") && sum.contains("秒")
                && sum.contains(String.valueOf(live.replayLog.size()));
        // a replay with no rows at all must still parse, not throw
        Game empty = new Game(mapW, mapH, walk, starts, units, "terran");
        boolean emptyOk = empty.loadReplay("XJZB-REPLAY-1\nmap bloodbath race terran\n")
                && empty.replayCount() == 0;
        // an unknown verb must be skipped rather than abort the stream
        Game unknown = new Game(mapW, mapH, walk, starts, units, "terran");
        unknown.loadReplay("XJZB-REPLAY-1\nmap bloodbath\ncmd 3 warp 1 2\ncmd 3 move 0 400 400\n");
        for (int i = 0; i < 120; i++) unknown.update(1f / 30f);
        boolean unknownOk = unknown.replayInjected() == 2 && unknown.replayCount() == 2;
        System.out.println("  replay header=" + head + " summary=\"" + sum + "\""
                + " emptyOk=" + emptyOk + " unknownVerbOk=" + unknownOk
                + " PASS=" + (head && sumOk && emptyOk && unknownOk));
    }

    static void hashSample(int t, Game g, List<Long> into) {
        if (t % 30 == 29) into.add(g.stateHash());
    }

    /** Mirror of HudLayout.cardCell. */
    static float HudLayoutCardCell(int H, float dp) {
        float want = 50f * dp;
        float budget = H * 0.5f - 10f * dp - 2 * 4f * dp;
        float fit = budget / 3f;
        if (fit < want) want = Math.max(46f * dp, fit);
        return want;
    }

    /** Mirror of HudLayout.compute (v2.41: no bands, chips on a full screen). */
    static float[] layoutMirror(int W, int H, float topH, float dp, int preset) {
        float cs = HudLayoutCardCell(H, dp);
        float gap = 4 * dp;
        float gridW = 3 * cs + 2 * gap, gridH = 3 * cs + 2 * gap;
        float cardH = gridH + 10 * dp;          // card + 2dp bevel pad each side
        float mmL, mmT, mmS;
        if (preset == 2) {
            mmS = Math.min(120 * dp, W * 0.18f) + 6 * dp;
            mmL = 8 * dp; mmT = topH + 8 * dp;
        } else {
            mmS = 150 * dp + 6 * dp;
            mmL = preset == 1 ? W - 8 * dp - mmS : 8 * dp;
            mmT = H - 8 * dp - mmS;
        }
        float cardL = preset == 1 ? 12 * dp : W - 12 * dp - gridW;
        float cardT = H - 6 * dp - gridH;
        float cy = H / 2f, hh = H / 2f / 1.3f;
        return new float[]{mmL, mmT, mmL + mmS, mmT + mmS,
                cardL, cardT, cardL + gridW, cardT + gridH,
                cardH, cy, hh};
    }
}
