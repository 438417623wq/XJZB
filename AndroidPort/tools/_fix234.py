import io
p = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\core\Lockstep.java"
src = io.open(p, encoding="utf-8").read()

old = '''    private final Map<Integer, Map<Integer, Long>> hashes = new LinkedHashMap<>();

    public Lockstep(int players) {
        this.players = Math.max(1, players);
        for (int i = 0; i < this.players; i++) hashes.put(i, new LinkedHashMap<>());
    }
'''
new = '''    private final Map<Integer, Map<Integer, Long>> hashes = new LinkedHashMap<>();

    // ---- v2.34: a peer that never comes back -----------------------------
    /**
     * How many consecutive frames a turn may sit incomplete before a silent
     * peer is declared gone. 300 frames at 30 Hz is ten seconds: below that a
     * peer who is merely switching apps gets called a quitter, above it the
     * player has already decided the game has hung. Counted in FRAMES, not wall
     * clock, so a desktop assertion can drive it deterministically.
     */
    public static final int STALL_LIMIT = 300;
    /** Consecutive frames the current turn has waited. Reset when it releases. */
    public int stallTurns;
    /** Set by {@link #forfeit}; -1 until somebody is declared gone. */
    public int forfeitLoser = -1;
    public int forfeitWinner = -1;
    /** Players declared gone. Their missing report no longer blocks a release. */
    private final boolean[] dropped;

    public Lockstep(int players) {
        this.players = Math.max(1, players);
        this.dropped = new boolean[this.players];
        for (int i = 0; i < this.players; i++) hashes.put(i, new LinkedHashMap<>());
    }
'''
assert src.count(old) == 1, src.count(old)
src = src.replace(old, new)

# ready(): a dropped player counts as reported, so the match can finish
old2 = '''    /** True once every player has reported for the current turn. */
    public boolean ready() {
        String[] row = reports.get(turn);
        if (row == null) return false;
        for (String s : row) if (s == null) return false;
        return true;
    }
'''
new2 = '''    /**
     * True once every player has reported for the current turn. A player
     * declared gone by {@link #forfeit} no longer blocks the release -- that is
     * the whole point of declaring them gone, and without it a match whose
     * opponent vanished would sit on the same turn forever, which on a phone
     * reads as a hung game rather than as a win.
     */
    public boolean ready() {
        for (int p = 0; p < players; p++) {
            if (dropped[p]) continue;
            if (!reported(p)) return false;
        }
        return true;
    }
'''
assert src.count(old2) == 1, src.count(old2)
src = src.replace(old2, new2)

# release(): an absent row for a dropped player must not NPE
old3 = '''    public List<Cmd> release() {
        if (!ready()) return Collections.emptyList();
        String[] row = reports.remove(turn);
        List<Cmd> out = new ArrayList<>();
'''
new3 = '''    public List<Cmd> release() {
        if (!ready()) return Collections.emptyList();
        String[] row = reports.remove(turn);
        if (row == null) row = new String[players];
        stallTurns = 0;
        List<Cmd> out = new ArrayList<>();
'''
assert src.count(old3) == 1, src.count(old3)
src = src.replace(old3, new3)

# append the stall / forfeit API before the desync section
old4 = '''    // ------------------------------------------------------------- desync
'''
new4 = '''    // ------------------------------------------------- v2.34: stall / forfeit

    /**
     * One frame passed with the current turn incomplete. Called from
     * Game.update on the not-ready path; a frame that DOES release resets the
     * counter (see release), so this only ever counts a continuous wait. That
     * matters: a peer that comes back inside the limit must not accumulate
     * stalls across the whole match and eventually be called a quitter.
     */
    public void noteStall() {
        stallTurns++;
    }

    /**
     * Who has not reported for the current turn, or -1 when nobody is missing.
     * Named rather than a bare boolean so the message can say WHICH player went
     * quiet -- "connection problem" tells the player nothing they can act on.
     */
    public int stalledPlayer() {
        for (int p = 0; p < players; p++) {
            if (dropped[p]) continue;
            if (!reported(p)) return p;
        }
        return -1;
    }

    /** Has a silent peer been silent for long enough to be considered gone? */
    public boolean stalledOut(int limit) {
        return stallTurns >= limit;
    }

    /**
     * Declare a player gone: record the result and stop waiting for them. Only
     * the first call counts, so two peers deciding at once cannot record two
     * different outcomes.
     */
    public boolean forfeit(int player) {
        if (forfeitLoser >= 0) return false;
        if (player < 0 || player >= players) return false;
        forfeitLoser = player;
        // The winner is whoever is left; with two players that is unambiguous.
        for (int p = 0; p < players; p++) {
            if (p != player) { forfeitWinner = p; break; }
        }
        dropped[player] = true;
        return true;
    }

    /** True once the player has been declared gone. */
    public boolean isDropped(int player) {
        return player >= 0 && player < players && dropped[player];
    }

    // ------------------------------------------------------------- desync
'''
assert src.count(old4) == 1, src.count(old4)
src = src.replace(old4, new4)

# submitAt / reported: a dropped player stays "reported" so ready() is stable
old5 = '''    /** True once the given player has reported for the current turn. */
    public boolean reported(int player) {
        String[] row = reports.get(turn);
        return row != null && player >= 0 && player < players && row[player] != null;
    }
'''
new5 = '''    /** True once the given player has reported for the current turn. */
    public boolean reported(int player) {
        if (player < 0 || player >= players) return false;
        if (dropped[player]) return true;
        String[] row = reports.get(turn);
        return row != null && row[player] != null;
    }
'''
assert src.count(old5) == 1, src.count(old5)
src = src.replace(old5, new5)

io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("Lockstep patched")