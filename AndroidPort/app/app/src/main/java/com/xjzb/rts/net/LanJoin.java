package com.xjzb.rts.net;

import com.xjzb.rts.core.Handshake;
import com.xjzb.rts.core.LanBeacon;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.net.InetSocketAddress;
import java.net.Socket;

/**
 * v2.37: the joiner side -- connect to a beacon's host, swap handshakes, and
 * come back with a TcpLink or a sentence explaining why not.
 *
 * Blocking on a worker thread, never on the UI thread: connecting to a phone
 * that has walked out of range takes as long as the TCP timeout, and a frozen
 * lobby is worse than a late one.
 */
public final class LanJoin {

    /** A connected peer, or the reason there is none. */
    public static final class Result {
        public final TcpLink link;
        public final Handshake peer;
        public final String error;

        Result(TcpLink link, Handshake peer, String error) {
            this.link = link;
            this.peer = peer;
            this.error = error;
        }

        public boolean ok() {
            return link != null;
        }
    }

    public interface Callback {
        void onResult(Result r);
    }

    /**
     * Connect and handshake against `beacon`, then report on the caller's
     * thread... no: on THIS worker thread. The caller posts to the UI itself,
     * because this class must not know about Android's Looper -- that keeps it
     * usable from a plain test.
     */
    public static void connect(final LanBeacon beacon, final String myVersion,
                               final String myRace, final Callback cb) {
        new Thread(() -> {
            Socket sock = null;
            try {
                sock = new Socket();
                sock.connect(new InetSocketAddress(beacon.host, beacon.port), 4000);
                sock.setTcpNoDelay(true);
                Handshake mine = new Handshake(myVersion, beacon.map, beacon.players,
                        beacon.seed, myRace, beacon.difficulty);
                Writer w = new OutputStreamWriter(sock.getOutputStream(), "UTF-8");
                w.write(mine.encode() + "\n");
                w.flush();
                BufferedReader in = new BufferedReader(
                        new InputStreamReader(sock.getInputStream(), "UTF-8"));
                String line = in.readLine();
                if (line == null) {
                    cb.onResult(new Result(null, null, "对方没有回应"));
                    return;
                }
                if (line.startsWith("N ")) {
                    cb.onResult(new Result(null, null, line.substring(2)));
                    return;
                }
                if (!line.startsWith("Y ")) {
                    cb.onResult(new Result(null, null, "对方回应无法识别"));
                    return;
                }
                Handshake peer = Handshake.decode(line.substring(2));
                String why = mine.reject(peer);
                if (why != null) {
                    cb.onResult(new Result(null, null, why));
                    return;
                }
                cb.onResult(new Result(new TcpLink(sock), peer, null));
            } catch (Exception e) {
                if (sock != null) {
                    try { sock.close(); } catch (Exception ignored) { }
                }
                cb.onResult(new Result(null, null, "连接失败:" + e.getMessage()));
            }
        }, "xjzb-net-join").start();
    }
}