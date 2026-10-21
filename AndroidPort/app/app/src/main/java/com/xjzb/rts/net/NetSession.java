package com.xjzb.rts.net;

import com.xjzb.rts.core.Handshake;
import com.xjzb.rts.core.LockstepPeer;

/**
 * v2.37: the one live network session, handed from the lobby to the match.
 *
 * A Socket cannot travel in an Intent, so the lobby parks the connected link
 * here and the match activity picks it up. It is a single static slot on
 * purpose: a phone runs one match at a time, and a static that can only hold one
 * session cannot leak a second one into a match by accident.
 *
 * Everything is null in a normal offline launch, and every reader must tolerate
 * that -- the offline path is the common case and must not grow a null check in
 * its hot loop.
 */
public final class NetSession {

    /** Who is in this match, and on what. */
    public static final class Config {
        public String map = "bloodbath";
        public int players = 2;
        public long seed = 12345L;
        public int difficulty = 1;
        public String race = "terran";
        /** 0 = host, 1.. = joiner. Index into the lockstep canonical order. */
        public int localPlayer;
        public boolean host;
    }

    private static Config config;
    private static LockstepPeer peer;
    private static TcpLink link;
    private static Handshake peerHandshake;

    private NetSession() {
    }

    /** Install a connected session. Called by the lobby once the handshake is done. */
    public static synchronized void install(Config c, TcpLink l, Handshake peerHs) {
        clear();
        config = c;
        link = l;
        peerHandshake = peerHs;
    }

    /** The session's settings, or null when this is an offline launch. */
    public static synchronized Config config() {
        return config;
    }

    public static synchronized TcpLink link() {
        return link;
    }

    public static synchronized Handshake peerHandshake() {
        return peerHandshake;
    }

    /**
     * The peer bound to a Game. Created lazily by the match once it has a Game,
     * because LockstepPeer needs the Game to exist first.
     */
    public static synchronized void bind(LockstepPeer p) {
        peer = p;
    }

    public static synchronized LockstepPeer peer() {
        return peer;
    }

    public static boolean active() {
        return config != null && link != null;
    }

    /** Drop the session. Called when a match ends or the player backs out. */
    public static synchronized void clear() {
        if (link != null) link.close();
        link = null;
        config = null;
        peer = null;
        peerHandshake = null;
    }
}