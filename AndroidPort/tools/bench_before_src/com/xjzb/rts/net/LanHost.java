package com.xjzb.rts.net;

import com.xjzb.rts.core.Handshake;
import com.xjzb.rts.core.LanBeacon;
import com.xjzb.rts.core.Lobby;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;

/**
 * v2.37: the host side of a LAN match -- bind, announce, accept, handshake, then
 * hand back a connected TcpLink. Everything the two peers then DO with that link
 * is in core/ and already asserted (Lockstep, LockstepStream, Handshake); this
 * class only does the socket dance.
 *
 * The handshake is checked BEFORE a seat is granted, and a mismatch is reported
 * with the field that disagreed. Discovering a version mismatch at turn 400 is a
 * desync with no explanation; refusing it at the door is a sentence the player
 * can act on. It also keeps the lobby honest: a peer we cannot play with must
 * not occupy a slot, or the room shows a full roster whose start button can
 * never light up.
 */
public final class LanHost {

    /** Everything the room needs to describe itself; supplied by the caller. */
    public interface Room {
        /** Map id, player count, seed, difficulty -- the room's settings. */
        LanBeacon beacon();
        /** Our build's version string. */
        String version();
    }

    /** A successful accept + handshake. */
    public static final class Connected {
        public final TcpLink link;
        public final Handshake peer;
        public final int slot;

        Connected(TcpLink link, Handshake peer, int slot) {
            this.link = link;
            this.peer = peer;
            this.slot = slot;
        }
    }

    public interface Callback {
        void onConnected(Connected c);
        void onError(String message);
    }

    private final Lobby lobby;
    private final Room room;
    private ServerSocket server;
    private Thread thread;
    private volatile boolean running;
    private final LanBeacon beacon = new LanBeacon();

    public LanHost(Lobby lobby, Room room) {
        this.lobby = lobby;
        this.room = room;
    }

    /**
     * Bind and start accepting. Returns the real port, or -1 on failure. Port 0
     * lets the OS pick a free one, so a phone can host while also holding some
     * other socket; the chosen port goes into the beacon, which is why the
     * beacon is built here and not by the caller.
     */
    public int start(final Callback cb) {
        stop();
        try {
            server = new ServerSocket();
            server.setReuseAddress(true);
            server.bind(new InetSocketAddress(0));
        } catch (Exception e) {
            cb.onError("无法开房:端口不可用");
            return -1;
        }
        LanBeacon base = room.beacon();
        if (base != null) {
            beacon.host = base.host;
            beacon.map = base.map;
            beacon.players = base.players;
            beacon.seed = base.seed;
            beacon.difficulty = base.difficulty;
        }
        beacon.version = room.version();
        beacon.port = server.getLocalPort();
        // The host is a player, not a spectator: it takes seat 0 AND is ready,
        // because pressing "host" is the confirmation. Seat 0 must also be
        // ready or canStart() is false and the host -- the only one who can
        // start a match -- is stuck forever.
        if (lobby.connectedCount() == 0) {
            lobby.hostSeat(beacon.host == null || beacon.host.isEmpty()
                    ? "房主" : beacon.host);
        }
        running = true;

        thread = new Thread(() -> {
            while (running) {
                Socket sock = null;
                try {
                    sock = server.accept();
                    admit(sock, cb);
                } catch (Exception e) {
                    if (running) {
                        try {
                            if (sock != null) sock.close();
                        } catch (Exception ignored) {
                        }
                    }
                }
            }
        }, "xjzb-net-host");
        thread.setDaemon(true);
        thread.start();
        return beacon.port;
    }

    private void admit(Socket sock, Callback cb) throws Exception {
        Handshake mine = new Handshake(beacon.version, beacon.map, beacon.players,
                beacon.seed, "terran", beacon.difficulty);
        BufferedReader in = new BufferedReader(
                new InputStreamReader(sock.getInputStream(), "UTF-8"));
        Writer w = new OutputStreamWriter(sock.getOutputStream(), "UTF-8");
        String line = in.readLine();
        Handshake peer = Handshake.decode(line);
        String why = mine.reject(peer);
        if (why != null) {
            w.write("N " + why + "\n");
            w.flush();
            sock.close();
            cb.onError("已拒绝一名玩家:" + why);
            return;
        }
        int slot = lobby.join(peer.race);
        if (slot < 0) {
            w.write("N 房间已满\n");
            w.flush();
            sock.close();
            cb.onError("房间已满,已拒绝一名玩家");
            return;
        }
        w.write("Y " + mine.encode() + "\n");
        w.flush();
        cb.onConnected(new Connected(new TcpLink(sock), peer, slot));
    }

    /** The beacon to broadcast. Its port is only valid after start(). */
    public LanBeacon beacon() {
        return beacon;
    }

    public int port() {
        return server == null ? -1 : server.getLocalPort();
    }

    public void stop() {
        running = false;
        try {
            if (server != null) server.close();
        } catch (Exception ignored) {
        }
        server = null;
        if (thread != null) thread.interrupt();
        thread = null;
    }
}