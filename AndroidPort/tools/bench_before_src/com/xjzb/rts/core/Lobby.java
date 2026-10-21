package com.xjzb.rts.core;

import java.util.ArrayList;
import java.util.List;

/**
 * v2.33: the lobby -- who is here, who is ready, and whether the match may
 * start. Pure state, no sockets and no UI, so the rules can be asserted
 * headlessly and the Android screen becomes a thin view over them.
 *
 * The one rule that is easy to get wrong is what happens to a slot when a peer
 * disappears BEFORE the match starts: it has to be freed, or the room shows
 * "4/4 connected" while canStart() stays false forever and the host can never
 * begin. After the match starts a lost peer is not the lobby's problem at all --
 * that is what Lockstep's ready-gate is for, and it fails visibly (everyone
 * freezes on the same turn) rather than silently.
 */
public final class Lobby {

    /** One seat. A disconnected slot is free and can be taken by someone else. */
    public static final class Slot {
        public String name = "";
        public boolean connected;
        public boolean ready;

        public boolean filled() {
            return connected;
        }

        @Override
        public String toString() {
            return (connected ? name : "-") + (ready ? "*" : "");
        }
    }

    public final int capacity;
    public final List<Slot> slots = new ArrayList<>();
    /** True once start() has succeeded; a lobby is single-use. */
    public boolean started;

    public Lobby(int capacity) {
        this.capacity = Math.max(2, capacity);
        for (int i = 0; i < this.capacity; i++) slots.add(new Slot());
    }

    /**
     * Seat a peer in the lowest free slot. Returns the slot index, or -1 when
     * the room is full. A joiner always lands in the first gap, so a slot freed
     * by a departure is the next one taken.
     */
    public int join(String name) {
        for (int i = 0; i < capacity; i++) {
            Slot s = slots.get(i);
            if (s.connected) continue;
            s.name = name == null ? "?" : name;
            s.connected = true;
            s.ready = false;
            return i;
        }
        return -1;
    }

    /**
     * v2.39: the host takes seat 0 and is ready by definition -- it pressed
     * "host", so there is nothing left for it to confirm. Returns the seat, or
     * -1. Without this the host's own roster is "1/2, host not ready" and its
     * start button can never light up, which is a hard blocker for the whole
     * feature: the host is the one who starts the match.
     */
    public int hostSeat(String name) {
        int i = join(name);
        if (i >= 0) setReady(i, true);
        return i;
    }

    /**
     * v2.39: the joiner's LOCAL view of a room it just joined. It knows two
     * things for certain -- the host is connected (it just handshook with it)
     * and it is itself ready -- so the view is 2/2 and the start button is live
     * on BOTH phones. Filling only its own seat leaves the joiner's roster at
     * "1/2", where canStart() is false for the same reason as the host's.
     */
    public void joinAsGuest(String hostName, String selfName) {
        join(hostName);
        setReady(0, true);
        join(selfName);
        setReady(1, true);
    }

    public void setReady(int i, boolean ready) {
        if (i < 0 || i >= capacity) return;
        Slot s = slots.get(i);
        if (!s.connected) return;
        s.ready = ready;
    }

    /**
     * A peer left. Before the match starts its slot is freed so someone else
     * can take it; after the match starts nothing changes here (see the class
     * comment -- Lockstep owns that case).
     */
    public void onPeerLost(int i) {
        if (started || i < 0 || i >= capacity) return;
        Slot s = slots.get(i);
        s.connected = false;
        s.ready = false;
        s.name = "";
    }

    public int connectedCount() {
        int n = 0;
        for (Slot s : slots) if (s.connected) n++;
        return n;
    }

    /** Every seat filled and every occupant ready, with at least two players. */
    public boolean canStart() {
        if (started) return false;
        int n = 0;
        for (Slot s : slots) {
            if (!s.connected) continue;
            if (!s.ready) return false;
            n++;
        }
        return n >= 2;
    }

    /**
     * Begin the match. Succeeds at most once: a second call returns false, so a
     * double tap on "start" cannot launch two matches.
     */
    public boolean start() {
        if (!canStart()) return false;
        started = true;
        return true;
    }

    /** Why the start button is off, for the UI to show. */
    public String blockedReason() {
        if (started) return "对局已开始";
        int n = connectedCount();
        if (n < 2) return "至少需要两名玩家(" + n + "/2)";
        for (Slot s : slots) if (s.connected && !s.ready) return s.name + " 尚未准备";
        return null;
    }
}