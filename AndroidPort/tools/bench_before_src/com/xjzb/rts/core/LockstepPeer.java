package com.xjzb.rts.core;

import java.util.List;

/**
 * v2.31: one machine in a lockstep match -- a Game, its session, and its wire.
 *
 * Kept separate from Game so the networking shape is visible in one place and
 * the simulation stays unaware of it beyond the two fields v2.30 added. The
 * whole peer is: submit my order, take the wire's arrivals into the session,
 * step. That is deliberately the smallest thing that can be wrong, because
 * everything interesting about lockstep is in what it refuses to do -- it
 * refuses to advance a turn before every peer has reported.
 *
 * There is no Android type here, which is what lets GameDesktop run two of
 * these in one process and compare their state hashes frame by frame.
 */
public final class LockstepPeer {

    public final Game game;
    public final Lockstep session;
    public final LockstepLink.Link link;
    public final int player;

    /**
     * The order waiting to be reported, and the turn it was last reported for.
     *
     * The contract is ONE report per player per turn, and this is where it is
     * enforced. Sending a fresh heartbeat every frame (which the first draft of
     * the two-peer walk did) puts several reports for the same turn on the wire;
     * with any latency they arrive at different times, the peer acts on
     * whichever lands first, and a heartbeat that overtakes the real order makes
     * one machine release a turn the other is still filling. Reporting once, at
     * the turn boundary, removes the race rather than trying to survive it.
     */
    private String pending = "";
    private int reportedTurn = -1;
    /** The turn this peer last put on the wire; guards against double reports. */
    private int sentTurn = -1;

    public LockstepPeer(Game game, int player, int players, LockstepLink.Link link) {
        this.game = game;
        this.player = player;
        this.link = link;
        this.session = new Lockstep(players);
        game.lockstep = session;
        game.lockstepPlayer = player;
    }

    /**
     * Drain the wire into the session. A malformed line is dropped rather than
     * thrown (Lockstep.decode is tolerant for the same reason loadReplay is):
     * one bad packet must not take a match down. A line for a turn already
     * released is dropped too, since applying it now would be a command the
     * other machine already ran without.
     */
    public void receive() {
        for (String line : link.poll()) {
            Lockstep.Cmd c = Lockstep.decode(line);
            if (c == null) continue;
            session.submitAt(c.player, c.turn, c.cmd);
        }
    }

    /**
     * Queue an order to be reported at the next turn boundary. At 30 Hz a turn
     * is 33 ms, so a human cannot produce two distinct orders inside one turn;
     * the last one queued wins and that is a documented limitation, not an
     * accident. Use {@link #queue} + {@link #sendFrame}, not send() directly,
     * or a turn can end up with more than one report.
     */
    public void queue(String cmd) {
        if (cmd != null && !cmd.isEmpty()) pending = cmd;
    }

    /**
     * One frame of a match, in the order a real match must use: EVERY peer
     * receives, then EVERY peer sends, then every peer steps.
     *
     * The order is not cosmetic. If peer A sends before peer B receives, A's
     * order for turn T can reach B on the frame B is still releasing turn T-1;
     * B holds it as a future turn, and the two peers release T on different
     * frames. The commands are identical and the canonical order is identical,
     * so nothing diverges -- but the peers are now one frame apart forever, and
     * that offset is exactly what a latency of 0 makes visible. Driving both
     * peers from one loop with the three phases separated removes it.
     */
    public void receiveFrame() {
        receive();
    }

    /**
     * Phase two: report exactly once for the turn I am filling. The first call
     * in a turn puts this peer's order (or the heartbeat, when it has none) on
     * the wire and feeds its own session; every later call in the same turn is
     * a no-op, so the wire never carries two reports for one turn.
     *
     * The order is only put on the wire, not applied locally: it comes back
     * through the session's release on both machines, so both apply it on the
     * same turn. The local session is fed directly too, since a hub with no
     * loopback does not deliver to the sender.
     */
    public void sendFrame() {
        if (sentTurn == session.turn) return;      // one report per turn
        // A command can already be sitting in the session because the GAME
        // submitted it (Game.recordOrder does, so that the order carries the
        // entity indices it was issued against). Prefer that; fall back to
        // whatever was queued directly; otherwise send the heartbeat. Missing
        // this is how a locally-applied order would never reach the opponent.
        String body = session.submitted(player);
        if (body == null || body.isEmpty()) {
            body = pending == null ? "" : pending;
        }
        pending = "";
        session.submit(player, body);
        link.send(Lockstep.encode(session.turn, player, body));
        sentTurn = session.turn;
        reportedTurn = session.turn;
    }

    /** Phase three: advance one tick if the turn is complete. */
    public long stepFrame(float dt) {
        game.update(dt);
        return game.stateHash();
    }

    /** Convenience for a single-peer driver: all three phases, in order. */
    public long step(String myCmd, float dt) {
        receiveFrame();
        queue(myCmd);
        sendFrame();
        return stepFrame(dt);
    }

    /** The turn this peer last reported for, or -1 before the first report. */
    public int reportedTurn() {
        return reportedTurn;
    }

    /** Publish this peer's hash for the last completed turn. */
    public void publishHash(long hash) {
        session.reportHash(player, Math.max(0, session.turn - 1), hash);
    }

    /** Turns this peer has fully released. Both peers must agree on it. */
    public int turnsReleased() {
        return session.turn;
    }

    /** True when the wire itself is gone, independent of the stall timer. */
    public boolean linkClosed() {
        return link.isClosed();
    }

    /**
     * v2.37: decide whether a peer has left, and record it. Returns the player
     * declared gone, or -1.
     *
     * Two signals, and both are needed. The stall timer catches a peer that is
     * still connected but has stopped answering (app killed, wifi dropped,
     * phone asleep) and takes STALL_LIMIT frames. A closed socket catches the
     * case where the transport already knows -- the peer's process died and the
     * FIN arrived -- and says so immediately, so the survivor is not left
     * staring at a frozen screen for ten seconds waiting out a timer whose
     * answer is already known.
     *
     * This exists because the timeout logic was asserted from v2.34 onward but
     * nothing in the app ever CALLED it: a departed peer still froze the match
     * forever on a real device. Tested logic that nothing invokes is not a
     * feature.
     */
    public int checkForfeit(int limit) {
        if (session.forfeitLoser >= 0) return -1;
        int who = session.stalledPlayer();
        if (who < 0) return -1;
        if (session.stalledOut(limit) || link.isClosed()) {
            session.forfeit(who);
            return who;
        }
        return -1;
    }

    /** This peer's released commands, in canonical order. */
    public List<Lockstep.Cmd> commands() {
        return session.commands();
    }
}
