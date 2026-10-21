package com.xjzb.rts.core;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Data-driven mission scripting (v2.7 batch 8).
 *
 * Deliberately NOT a TRIG bytecode interpreter: the original trigger VM is a
 * large, undocumented surface and the project's whole verification story rests
 * on "the core is plain Java and GameDesktop can regression-test it". Instead a
 * mission is a JSON document with objectives and timed/triggered events, and
 * this class is the interpreter for exactly five atomic actions.
 *
 * Parsing is a small hand-written JSON reader (no dependencies, matching the
 * rest of core/). It only needs objects, arrays, strings, numbers and booleans,
 * which is all a mission file uses.
 *
 * Lifecycle: {@link Game#setMission} installs one, {@link #update} is called
 * once per frame from Game.update, and {@link #finish} records the result.
 */
public class Mission {

    // ---------------------------------------------------------------- model

    /** One objective the player is graded on. */
    public static class Objective {
        public String kind;        // destroyAll | protect | survive
        public String desc;
        public String target;      // protect: type key that must live
        public float time;         // survive: seconds that must elapse
        public boolean optional;   // optional objectives only affect the grade
        public boolean done;
        public boolean failed;
    }

    /** A scripted event: a trigger plus one atomic action. */
    public static class Event {
        public float atTime = -1;      // seconds; -1 = no time trigger
        public float[] atArea;         // {x, y, r}; null = no area trigger
        public int areaSide = -1;      // 0 = player enters, 1 = enemy enters
        public String atLost;          // type key whose death fires this
        public boolean fired;

        public String action;          // wave | reinforce | message | win | lose
        public String text;            // message
        public String[] units;         // wave / reinforce: type keys
        public float[] from;           // wave: {x, y} spawn point
        public float[] to;             // wave: {x, y} attack destination
        public float delay;            // wave: stagger between units
    }

    public String id = "";
    public String name = "";
    public String map = "";
    public String playerRace = "terran";
    public String enemyRace = "zerg";
    public int difficulty = 1;
    /**
     * v2.29: author the map's resource fields. `Game.setMission` clears the
     * skirmish resource list, so a mission that omits this key starts with an
     * empty map -- no mineral patch anywhere, `mineralsMined` frozen at 0 and
     * the m01 briefing's "the workers will mine" a lie. The flag re-parses the
     * map's own meta.txt at install time, so a mission picks up the map's real
     * economy instead of a hand-copied list of coordinates.
     */
    public boolean economy = false;
    public final List<String> briefing = new ArrayList<>();
    public final List<Object[]> startUnits = new ArrayList<>();   // {key,x,y,team}
    public final List<Objective> objectives = new ArrayList<>();
    public final List<Event> events = new ArrayList<>();

    /** Wave plans the enemy AI should use instead of its random weighting. */
    public final List<String[]> aiWaves = new ArrayList<>();

    // --------------------------------------------------------------- runtime

    /** Objectives met so far, for the HUD ticks. */
    public boolean victory, defeat;
    public String resultReason = "";
    /** Set once so a loss cannot be overwritten by a later win, and vice versa. */
    public boolean finished;
    /** Optional-objective tally, used for the S/A/B/C grade. */
    public int optionalDone, optionalTotal;

    private float elapsed;
    private final List<float[]> pendingWaves = new ArrayList<>();  // x,y,keyIdx,delay
    private final List<Object[]> spawnQueue = new ArrayList<>();   // key,x,y,team,at

    public Mission() {
    }

    public static Mission parse(String json) {
        Object root = Json.parse(json);
        if (!(root instanceof Map)) return null;
        Mission m = new Mission();
        Map<?, ?> o = (Map<?, ?>) root;
        m.id = Json.str(o, "id", "");
        m.name = Json.str(o, "name", m.id);
        m.map = Json.str(o, "map", "");
        m.playerRace = Json.str(o, "playerRace", "terran");
        m.enemyRace = Json.str(o, "enemyRace", "zerg");
        m.difficulty = (int) Json.num(o, "difficulty", 1);
        m.economy = Json.bool(o, "economy", false);

        for (Object b : Json.arr(o, "briefing")) m.briefing.add(String.valueOf(b));

        for (Object su : Json.arr(o, "startUnits")) {
            if (!(su instanceof Map)) continue;
            Map<?, ?> s = (Map<?, ?>) su;
            m.startUnits.add(new Object[]{
                    Json.str(s, "type", ""),
                    (float) Json.num(s, "x", 0),
                    (float) Json.num(s, "y", 0),
                    (int) Json.num(s, "team", 0)});
        }

        for (Object ob : Json.arr(o, "objectives")) {
            if (!(ob instanceof Map)) continue;
            Map<?, ?> j = (Map<?, ?>) ob;
            Objective x = new Objective();
            x.kind = Json.str(j, "kind", "");
            x.desc = Json.str(j, "desc", "");
            x.target = Json.str(j, "target", "");
            x.time = (float) Json.num(j, "time", 0);
            x.optional = Json.bool(j, "optional", false);
            m.objectives.add(x);
        }

        for (Object ev : Json.arr(o, "events")) {
            if (!(ev instanceof Map)) continue;
            Map<?, ?> j = (Map<?, ?>) ev;
            Event e = new Event();
            Object at = j.get("at");
            if (at instanceof Map) {
                Map<?, ?> a = (Map<?, ?>) at;
                if (a.containsKey("time")) e.atTime = (float) Json.num(a, "time", -1);
                if (a.containsKey("area")) {
                    List<Object> ar = Json.arr(a, "area");
                    if (ar.size() >= 3)
                        e.atArea = new float[]{(float) Json.num(ar.get(0), 0),
                                (float) Json.num(ar.get(1), 0), (float) Json.num(ar.get(2), 0)};
                    e.areaSide = (int) Json.num(a, "side", 0);
                }
                if (a.containsKey("lost")) e.atLost = Json.str(a, "lost", null);
            }
            e.action = Json.str(j, "action", "");
            e.text = Json.str(j, "text", null);
            List<Object> us = Json.arr(j, "units");
            if (!us.isEmpty()) {
                e.units = new String[us.size()];
                for (int i = 0; i < us.size(); i++) e.units[i] = String.valueOf(us.get(i));
            }
            List<Object> fr = Json.arr(j, "from");
            if (fr.size() >= 2)
                e.from = new float[]{(float) Json.num(fr.get(0), 0), (float) Json.num(fr.get(1), 0)};
            List<Object> to = Json.arr(j, "to");
            if (to.size() >= 2)
                e.to = new float[]{(float) Json.num(to.get(0), 0), (float) Json.num(to.get(1), 0)};
            e.delay = (float) Json.num(j, "delay", 0.6);
            m.events.add(e);
        }

        for (Object w : Json.arr(o, "aiWaves")) {
            if (!(w instanceof List)) continue;
            List<?> wl = (List<?>) w;
            String[] row = new String[wl.size()];
            for (int i = 0; i < wl.size(); i++) row[i] = String.valueOf(wl.get(i));
            m.aiWaves.add(row);
        }

        m.optionalTotal = 0;
        for (Objective x : m.objectives) if (x.optional) m.optionalTotal++;
        return m;
    }

    /** True while the player is still being graded. */
    public boolean active() {
        return !finished;
    }

    /**
     * One frame of mission logic. Checks objectives, fires due events and
     * resolves win/lose. Called from Game.update so it runs on the game thread.
     */
    public void update(Game g, float dt) {
        if (finished) return;
        elapsed += dt;

        // deferred spawns from waves/reinforcements
        for (int i = spawnQueue.size() - 1; i >= 0; i--) {
            Object[] s = spawnQueue.get(i);
            if ((Float) s[4] > elapsed) continue;
            spawnQueue.remove(i);
            String key = (String) s[0];
            float x = (Float) s[1], y = (Float) s[2];
            int team = (Integer) s[3];
            // batch-6 lesson: an event spawn must land on a walkable minitile or
            // the unit's pathfinding returns empty and it stands in the wall.
            int[] spot = g.nearestPassMini((int) (x / 8), (int) (y / 8), 12);
            if (spot == null) continue;
            Game.Ent e = g.spawn(key, team, spot[0] * 8 + 4, spot[1] * 8 + 4, true);
            if (team == 1 && s.length > 5 && s[5] != null) {
                float[] dest = (float[]) s[5];
                e.aiTimer = -1;
                g.setPath(e, dest[0], dest[1]);
            }
        }

        // events
        for (Event e : events) {
            if (e.fired) continue;
            if (!triggered(g, e)) continue;
            e.fired = true;
            fire(g, e);
            if (finished) return;
        }

        // objectives
        for (Objective o : objectives) {
            if (o.done || o.failed) continue;
            switch (o.kind) {
                case "destroyAll": {
                    boolean any = false;
                    for (Game.Ent e : g.ents)
                        if (e.team == 1 && e.alive()) { any = true; break; }
                    if (!any) {
                        o.done = true;
                        finish(true, o.desc);
                        return;
                    }
                    break;
                }
                case "protect": {
                    boolean alive = false;
                    for (Game.Ent e : g.ents)
                        if (e.team == 0 && e.alive() && e.type.key.equals(o.target)) {
                            alive = true;
                            break;
                        }
                    if (!alive) {
                        o.failed = true;
                        if (!o.optional) {
                            finish(false, o.desc + " 失败");
                            return;
                        }
                    }
                    break;
                }
                case "survive": {
                    if (elapsed >= o.time) {
                        o.done = true;
                        finish(true, o.desc);
                        return;
                    }
                    break;
                }
                default:
                    break;
            }
        }
    }

    private boolean triggered(Game g, Event e) {
        if (e.atTime >= 0 && elapsed >= e.atTime) return true;
        if (e.atLost != null) {
            for (Game.Ent ent : g.ents)
                if (ent.type.key.equals(e.atLost) && ent.alive()) return false;
            return true;
        }
        if (e.atArea != null) {
            for (Game.Ent ent : g.ents) {
                if (!ent.alive() || ent.team != e.areaSide) continue;
                float dx = ent.x - e.atArea[0], dy = ent.y - e.atArea[1];
                if (dx * dx + dy * dy <= e.atArea[2] * e.atArea[2]) return true;
            }
        }
        return false;
    }

    private void fire(Game g, Event e) {
        switch (e.action) {
            case "wave":
            case "reinforce": {
                if (e.units == null) break;
                int team = e.action.equals("wave") ? 1 : 0;
                // v2.7 9.3: an enemy wave scales with difficulty. The scripted
                // unit list is the normal-difficulty shape; easy drops the last
                // third and hard repeats it, so the same mission reads as three
                // different fights without authoring three files.
                String[] spawn = e.units;
                if (team == 1 && difficulty != 1 && e.units.length > 0) {
                    int n = e.units.length;
                    if (difficulty == 0) {
                        n = Math.max(1, (n * 2) / 3);
                        spawn = new String[n];
                        System.arraycopy(e.units, 0, spawn, 0, n);
                    } else {
                        spawn = new String[n * 2];
                        for (int k = 0; k < n * 2; k++) spawn[k] = e.units[k % n];
                    }
                }
                float[] from = e.from;
                for (int i = 0; i < spawn.length; i++) {
                    float x, y;
                    if (from != null) {
                        x = from[0] + (i % 4) * 26;
                        y = from[1] + (i / 4) * 26;
                    } else {
                        // no explicit origin: use the team's own base
                        float[] base = team == 1 ? g.findEnemyBase() : g.findPlayerStart();
                        x = base[0] + (i % 4) * 26;
                        y = base[1] + (i / 4) * 26;
                    }
                    spawnQueue.add(new Object[]{spawn[i], x, y, team,
                            elapsed + i * e.delay, e.to});
                }
                break;
            }
            case "message":
                g.events.add(new Object[]{"mission_msg", e.text == null ? "" : e.text});
                break;
            case "win":
                finish(true, e.text == null ? "" : e.text);
                break;
            case "lose":
                finish(false, e.text == null ? "" : e.text);
                break;
            default:
                break;
        }
    }

    private void finish(boolean won, String reason) {
        if (finished) return;
        finished = true;
        victory = won;
        defeat = !won;
        resultReason = reason == null ? "" : reason;
        for (Objective o : objectives) if (o.optional && o.done) optionalDone++;
    }

    /** Elapsed mission time, for the HUD clock and survive objectives. */
    public float elapsed() {
        return elapsed;
    }

    /** S/A/B/C grade from the optional objectives and the loss count. */
    public String grade(int losses) {
        if (defeat) return "C";
        if (optionalTotal > 0 && optionalDone < optionalTotal) return "B";
        if (losses == 0) return "S";
        if (losses <= 4) return "A";
        return "B";
    }

    // ------------------------------------------------------------ tiny JSON
    /**
     * Minimal JSON reader: objects, arrays, strings, numbers, booleans, null.
     * Enough for a mission file and small enough to keep core/ dependency-free
     * (the same reason the rest of the simulation is plain Java).
     */
    static final class Json {
        private final String s;
        private int i;

        private Json(String s) {
            this.s = s;
        }

        static Object parse(String s) {
            if (s == null) return null;
            Json j = new Json(s);
            j.ws();
            if (j.i >= s.length()) return null;
            return j.value();
        }

        private void ws() {
            while (i < s.length()) {
                char c = s.charAt(i);
                if (c == ' ' || c == '\t' || c == '\n' || c == '\r') i++;
                else if (c == '/' && i + 1 < s.length() && s.charAt(i + 1) == '/') {
                    while (i < s.length() && s.charAt(i) != '\n') i++;
                } else break;
            }
        }

        private Object value() {
            ws();
            if (i >= s.length()) return null;
            char c = s.charAt(i);
            if (c == '{') return object();
            if (c == '[') return array();
            if (c == '"') return string();
            if (c == 't') { i += 4; return Boolean.TRUE; }
            if (c == 'f') { i += 5; return Boolean.FALSE; }
            if (c == 'n') { i += 4; return null; }
            return number();
        }

        private Map<String, Object> object() {
            Map<String, Object> m = new LinkedHashMap<>();
            i++;   // {
            ws();
            if (i < s.length() && s.charAt(i) == '}') { i++; return m; }
            while (i < s.length()) {
                ws();
                String k = string();
                ws();
                if (i < s.length() && s.charAt(i) == ':') i++;
                Object v = value();
                m.put(k, v);
                ws();
                if (i < s.length() && s.charAt(i) == ',') { i++; continue; }
                if (i < s.length() && s.charAt(i) == '}') { i++; break; }
                break;
            }
            return m;
        }

        private List<Object> array() {
            List<Object> a = new ArrayList<>();
            i++;   // [
            ws();
            if (i < s.length() && s.charAt(i) == ']') { i++; return a; }
            while (i < s.length()) {
                a.add(value());
                ws();
                if (i < s.length() && s.charAt(i) == ',') { i++; continue; }
                if (i < s.length() && s.charAt(i) == ']') { i++; break; }
                break;
            }
            return a;
        }

        private String string() {
            StringBuilder b = new StringBuilder();
            if (i < s.length() && s.charAt(i) == '"') i++;
            while (i < s.length()) {
                char c = s.charAt(i++);
                if (c == '"') break;
                if (c == '\\' && i < s.length()) {
                    char e = s.charAt(i++);
                    switch (e) {
                        case 'n': b.append('\n'); break;
                        case 't': b.append('\t'); break;
                        case 'r': b.append('\r'); break;
                        case 'u':
                            if (i + 4 <= s.length()) {
                                b.append((char) Integer.parseInt(s.substring(i, i + 4), 16));
                                i += 4;
                            }
                            break;
                        default: b.append(e); break;
                    }
                } else b.append(c);
            }
            return b.toString();
        }

        private Object number() {
            int st = i;
            while (i < s.length()) {
                char c = s.charAt(i);
                if ((c >= '0' && c <= '9') || c == '-' || c == '+' || c == '.'
                        || c == 'e' || c == 'E') i++;
                else break;
            }
            if (st == i) { i++; return 0.0; }
            try {
                return Double.parseDouble(s.substring(st, i));
            } catch (NumberFormatException ex) {
                return 0.0;
            }
        }

        // ---- typed getters
        static String str(Map<?, ?> o, String k, String def) {
            Object v = o.get(k);
            return v == null ? def : String.valueOf(v);
        }

        static double num(Map<?, ?> o, String k, double def) {
            Object v = o.get(k);
            return v instanceof Number ? ((Number) v).doubleValue() : def;
        }

        static double num(Object v, double def) {
            return v instanceof Number ? ((Number) v).doubleValue() : def;
        }

        static boolean bool(Map<?, ?> o, String k, boolean def) {
            Object v = o.get(k);
            return v instanceof Boolean ? (Boolean) v : def;
        }

        @SuppressWarnings("unchecked")
        static List<Object> arr(Map<?, ?> o, String k) {
            Object v = o.get(k);
            return v instanceof List ? (List<Object>) v : java.util.Collections.emptyList();
        }
    }
}
