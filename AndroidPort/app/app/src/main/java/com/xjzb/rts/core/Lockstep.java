package com.xjzb.rts.core;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * v2.30: deterministic lockstep for a local-network match.
 *
 * The port already had both halves of the hard part before this class existed:
 * the simulation is a fixed 30 Hz step (Game.tick), orders are a text command
 * stream keyed by tick and entity index (Game.recordOrder / applyCommand), and
 * the [v220] replay assertion proves that re-running one command stream twice
 * produces an identical stateHash at every one-second sample. So "two machines,
 * same map, same orders, same result" is already established.
 *
 * What was missing is the only thing a network adds: making both machines
 * consume the SAME orders on the SAME tick, in the SAME order. That is all this
 * class does, and it does it without inventing a second command format -- a
 * turn's payload is the same "<verb> <idx,idx,...> <args>" line the replay log
 * stores, so a whole session serialises to a file Game.loadReplay can play
 * back. The network layer, the replay layer and the desktop assertions all
 * share one command channel, and there is no "online only" hidden state.
 *
 * A turn is one tick. Every player must report for the current turn (even with
 * nothing to say -- that heartbeat is what stops a quiet player from stalling
 * the match forever). Once all have reported, the turn's commands are released
 * in canonical order (player id ascending, then submission order) and the turn
 * advances. Both machines sort identically, so both apply identically.
 */
public class Lockstep {

    /** Turns per second. Matches the fixed simulation step the port already uses. */
    public static final int TURN_HZ = 30;

    /** One player's order for one turn. */
    public static final class Cmd {
        public final int turn;
        public final int player;
        public final String cmd;

        public Cmd(int turn, int player, String cmd) {
            this.turn = turn;
            this.player = player;
            this.cmd = cmd == null ? "" : cmd;
        }

        @Override
        public String toString() {
            return "L " + turn + " " + player + " " + cmd;
        }
    }

    /** How many players this session expects. 2 for a duel. */
    public final int players;
    /** The turn both sides are currently filling. */
    public int turn;

    /** turn -> player -> that player's command (null when they had none). */
    private final Map<Integer, String[]> reports = new LinkedHashMap<>();
    /** Released turns, kept so the session can be serialised as a replay. */
    private final List<Cmd> log = new ArrayList<>();

    /**
     * The first turn whose state hashes disagreed, or -1. Set by
     * {@link #reportHash}. This is the evidence an observer or a replay needs
     * to say "someone diverged", and it is the one thing a lockstep session
     * cannot repair on its own.
     */
    public int desyncTurn = -1;
    /** Peer hashes, for the desync message. player -> turn -> hash. */
    private final Map<Integer, Map<Integer, Long>> hashes = new LinkedHashMap<>();

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

    // ------------------------------------------------------------- reporting

    /**
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

    /**
     * What a player has submitted for the current turn, or null. The peer needs
     * this because a command can be submitted by the GAME (recordOrder does it
     * directly) rather than by the peer, and the peer still has to put it on the
     * wire -- a command applied locally but never sent is a desync with a delay.
     */
    public String submitted(int player) {
        String[] row = reports.get(turn);
        if (row == null || player < 0 || player >= players) return null;
        return row[player];
    }

    /** True once the given player has reported for the current turn. */
    public boolean reported(int player) {
        if (player < 0 || player >= players) return false;
        if (dropped[player]) return true;
        String[] row = reports.get(turn);
        return row != null && row[player] != null;
    }

    /**
     * Record one player's order for the current turn. An empty command is the
     * heartbeat a player with nothing to do must still send. A second report
     * from the same player in one turn is ignored rather than queued, so a
     * duplicated packet cannot make one side run a command twice.
     */
    public void submit(int player, String cmd) {
        submitAt(player, turn, cmd);
    }

    /**
     * Record an order for an explicit turn (used when a packet arrives early).
     *
     * The heartbeat and the order are not competing reports, and treating them
     * as such was a real bug: with a reordering link a player's heartbeat can
     * arrive BEFORE their command for the same turn, and a plain "first arrival
     * wins" dedup then stored the empty placeholder and dropped the actual
     * order -- silently, on one machine only, which is a desync. So the rule is
     * about content, not arrival: a real command always takes the slot, and an
     * empty heartbeat only fills a slot that is still empty.
     */
    public void submitAt(int player, int atTurn, String cmd) {
        if (player < 0 || player >= players) return;
        if (atTurn < turn) return;             // already released; a late packet
        String[] row = reports.get(atTurn);
        if (row == null) {
            row = new String[players];
            reports.put(atTurn, row);
        }
        String body = cmd == null ? "" : cmd.trim();
        String have = row[player];
        if (have == null || (have.isEmpty() && !body.isEmpty())) {
            row[player] = body;
        }
        // else: a genuine duplicate, or a heartbeat arriving after the order --
        // both are correctly ignored.
    }

    /**
     * Release the current turn's commands in canonical order and advance.
     * Returns an empty list when the turn is not ready -- callers should gate
     * on {@link #ready()} rather than treat that as "nothing happened", or a
     * single slow player would let the match run ahead on one machine only.
     */
    public List<Cmd> release() {
        if (!ready()) return Collections.emptyList();
        String[] row = reports.remove(turn);
        if (row == null) row = new String[players];
        stallTurns = 0;
        List<Cmd> out = new ArrayList<>();
        // Canonical order: player id ascending. Both machines sort the same
        // way, which is the whole reason the two simulations stay identical.
        for (int p = 0; p < players; p++) {
            String c = row[p];
            if (c == null || c.isEmpty()) continue;
            Cmd cmd = new Cmd(turn, p, c);
            out.add(cmd);
            log.add(cmd);
        }
        turn++;
        return out;
    }

    /** The turns released so far, in canonical order. */
    public List<Cmd> commands() {
        return Collections.unmodifiableList(log);
    }

    // ------------------------------------------------- v2.34: stall / forfeit

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

    /**
     * Publish this machine's stateHash for a turn. When a peer's hash for the
     * same turn is already known and differs, that turn is recorded as the
     * divergence point. The first such turn wins: later turns are all
     * downstream of it and would just be noise.
     */
    public void reportHash(int player, int atTurn, long hash) {
        if (player < 0 || player >= players) return;
        Map<Integer, Long> mine = hashes.get(player);
        if (mine == null) return;
        mine.put(atTurn, hash);
        if (desyncTurn >= 0) return;
        for (int p = 0; p < players; p++) {
            if (p == player) continue;
            Long other = hashes.get(p).get(atTurn);
            if (other != null && other.longValue() != hash) {
                desyncTurn = atTurn;
                return;
            }
        }
    }

    // ------------------------------------------------------------- wire

    /** One command as a wire line: "L <turn> <player> <cmd>". */
    public static String encode(int turn, int player, String cmd) {
        // No trailing space for the heartbeat. It matters: the empty command is
        // the one message every peer sends every single turn, so it is the one
        // that must survive the wire intact.
        String body = cmd == null ? "" : cmd;
        return body.isEmpty()
                ? "L " + turn + " " + player
                : "L " + turn + " " + player + " " + body;
    }

    /**
     * Parse a wire line. Tolerant on purpose, exactly like
     * {@link Game#loadReplay}: an unknown or malformed line yields null rather
     * than throwing, so one bad packet cannot take the match down.
     */
    public static Cmd decode(String line) {
        if (line == null) return null;
        String s = line.trim();
        if (!s.startsWith("L ")) return null;
        // Two fields minimum (turn, player) and the command is optional: a
        // heartbeat encodes as "L 3 0" with nothing after it. Requiring a third
        // field here was the bug that broke the two-peer walk -- the heartbeat
        // decoded to null and was silently dropped, so a peer that had nothing
        // to say was indistinguishable from a peer that was not there.
        String[] p = s.substring(2).trim().split(" ", 3);
        if (p.length < 2) return null;
        try {
            int turn = Integer.parseInt(p[0]);
            int player = Integer.parseInt(p[1]);
            return new Cmd(turn, player, p.length >= 3 ? p[2] : "");
        } catch (NumberFormatException e) {
            return null;
        }
    }

    /** The whole session as a replay body: "cmd <turn> <cmd>" lines, player-ordered. */
    public String serialize() {
        StringBuilder sb = new StringBuilder();
        for (Cmd c : log) sb.append("cmd ").append(c.turn).append(' ').append(c.cmd).append('\n');
        return sb.toString();
    }
}
