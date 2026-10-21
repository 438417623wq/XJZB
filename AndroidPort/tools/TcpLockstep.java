import java.io.ByteArrayOutputStream;
import java.io.OutputStream;
import java.io.PrintStream;
import java.io.UnsupportedEncodingException;
import java.util.ArrayList;
import java.util.List;

import com.xjzb.rts.core.Game;

/**
 * v2.35 desktop harness: a REAL TCP loopback match, not an in-process hub.
 *
 * Every lockstep assertion up to v2.34 drove the protocol through an in-process
 * fake. That is the right way to test the rules, and it is exactly the wrong way
 * to discover that the rules do not survive contact with a socket: sockets give
 * you threads, blocking reads, real partial reads and real write coalescing, and
 * none of those exist in a fake. This runs two peers over ServerSocket and
 * Socket on 127.0.0.1 and compares their state hashes per turn, which is the
 * same invariant [v231] checks -- now over an actual TCP connection.
 *
 * A protocol failure has no other symptom here: the two peers simply stop
 * agreeing, or one stops advancing, so the assertions print the numbers that
 * make the failure readable.
 */
public class TcpLockstep {

    public static void main(String[] args) throws Exception {
        GameDesktop.readManifestPublic();
        GameDesktop.readMapPublic("bloodbath");

        final int turns = 30 * 15;             // 15 simulated seconds
        final int port = 45917;

        final java.util.Map<Integer, Long> turnsA = new java.util.concurrent.ConcurrentHashMap<>();
        final java.util.Map<Integer, Long> turnsB = new java.util.concurrent.ConcurrentHashMap<>();
        final boolean[] ready = new boolean[2];

        // ---- the host: accept, then run peer 0 -----------------------------
        final java.net.ServerSocket server = new java.net.ServerSocket(port);
        Thread host = new Thread(() -> {
            try {
                java.net.Socket s = server.accept();
                runPeer(0, s, turns, turnsA, ready);
            } catch (Exception e) {
                System.out.println("HOST ERROR " + e);
            }
        }, "host");
        host.setDaemon(true);
        host.start();

        // ---- the joiner: connect, then run peer 1 --------------------------
        java.net.Socket client = new java.net.Socket("127.0.0.1", port);
        runPeer(1, client, turns, turnsB, ready);
        host.join(4000);

        // ---- compare per turn ----------------------------------------------
        int common = 0, diff = 0;
        for (java.util.Map.Entry<Integer, Long> e : turnsA.entrySet()) {
            Long other = turnsB.get(e.getKey());
            if (other == null) continue;
            common++;
            if (other.longValue() != e.getValue().longValue()) diff++;
        }
        int aTurns = turnsA.size(), bTurns = turnsB.size();
        boolean same = common >= 100 && diff == 0;
        boolean bothRan = aTurns >= 100 && bTurns >= 100
                && Math.abs(aTurns - bTurns) <= 30;
        System.out.println("  tcp match commonTurns=" + common + " diffTurns=" + diff
                + " aTurns=" + aTurns + " bTurns=" + bTurns
                + " samePerTurn=" + same + " bothRan=" + bothRan
                + " PASS=" + (same && bothRan));
    }

    /**
     * One peer over a real socket. The three phases of a frame are separated
     * exactly as in the in-process walk, and the socket is drained with a
     * non-blocking-ish read before sending, so a peer never blocks waiting for
     * the other mid-frame (which is what makes a naive socket loop deadlock).
     */
    static void runPeer(int player, java.net.Socket sock, int turns,
                        java.util.Map<Integer, Long> byTurn, boolean[] ready)
            throws Exception {
        sock.setTcpNoDelay(true);
        OutputStream out = sock.getOutputStream();
        final java.io.InputStream in = sock.getInputStream();
        final com.xjzb.rts.core.LockstepStream stream =
                new com.xjzb.rts.core.LockstepStream();
        final List<String> arrived = new ArrayList<>();
        final Object lock = new Object();

        Thread reader = new Thread(() -> {
            byte[] buf = new byte[512];
            try {
                int n;
                while ((n = in.read(buf)) > 0) {
                    synchronized (lock) {
                        stream.feed(buf, 0, n);
                        arrived.addAll(stream.lines());
                    }
                }
            } catch (Exception ignored) {
            }
        }, "read-" + player);
        reader.setDaemon(true);
        reader.start();

        Game g = GameDesktop.cleanGame("terran");
        com.xjzb.rts.core.Lockstep session = new com.xjzb.rts.core.Lockstep(2);
        g.lockstep = session;
        g.lockstepPlayer = player;
        List<Game.Ent> scvs = new ArrayList<>();
        for (Game.Ent e : g.ents)
            if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);

        ready[player] = true;
        for (int t = 0; t < turns; t++) {
            // phase 1: take whatever the socket has delivered
            List<String> got;
            synchronized (lock) {
                got = new ArrayList<>(arrived);
                arrived.clear();
            }
            for (String line : got) {
                com.xjzb.rts.core.Lockstep.Cmd c = com.xjzb.rts.core.Lockstep.decode(line);
                if (c != null) session.submitAt(c.player, c.turn, c.cmd);
            }

            // phase 2: report once for this turn (player 0 orders every 5 s)
            if (!session.reported(player)) {
                String body = "";
                if (player == 0 && t % 150 == 0 && !scvs.isEmpty())
                    body = g.commandFor("move", scvs, (400 + t / 150 * 40) + " 400");
                session.submit(player, body);
                out.write(com.xjzb.rts.core.LockstepStream.encode(
                        com.xjzb.rts.core.Lockstep.encode(session.turn, player, body)));
                out.flush();
            }

            // phase 3: step if the turn is complete
            g.update(1f / 30f);
            byTurn.put(session.turn, g.stateHash());

            // give the other side a chance to make progress; a real match is
            // not a spin loop, and without this both peers would starve
            Thread.sleep(0, 200000);
        }
        try { sock.close(); } catch (Exception ignored) { }
    }
}