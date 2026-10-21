package com.xjzb.rts.core;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * v2.31: the two halves of a headless lockstep link.
 *
 * {@link Link} is the whole surface the protocol needs: fire a line, collect
 * whatever arrived this frame. An Android TCP implementation is a thin wrapper
 * over a socket; the desktop assertion uses {@link Hub}, which lives in this
 * process and is deliberately unfriendly.
 *
 * The hub models latency, jitter and reordering, and it does NOT model packet
 * loss -- on purpose. Discovery rides a UDP broadcast, but the command stream
 * itself goes over TCP (or a reliable-UDP transport), so "a packet vanished"
 * is not part of this protocol's contract. Latency, jitter and reordering are
 * things TCP still delivers to the application, and they are exactly what a
 * lockstep session has to survive: if a peer can run a turn before the other
 * peer's report for that turn arrives, the two simulations diverge. The
 * session's ready-gate is what prevents it, and this is the harness that
 * proves it.
 *
 * The internal Random is seeded, so the same parameters produce the same
 * delivery schedule on every run and an assertion can be reproduced.
 */
public final class LockstepLink {

    /** One end of the link: send a wire line, poll what has arrived. */
    public interface Link {
        void send(String line);
        List<String> poll();

        /**
         * v2.37: true once the wire is gone (a closed socket). Default false so
         * the in-process hub -- which has no socket and cannot fail -- needs no
         * change. This is the immediate half of the departure signal: a closed
         * socket means the peer is gone NOW, where the stall timer can only say
         * it after ten seconds of silence.
         */
        default boolean isClosed() {
            return false;
        }
    }

    /** An in-process star hub connecting `n` ends with a hostile schedule. */
    public static final class Hub {
        /** Base delivery delay, in frames. */
        public int latency;
        /** Extra delay, 0..jitter frames, drawn per message. */
        public int jitter;
        /** When true, messages that fall due on the same frame may swap order. */
        public boolean reorder;
        /**
         * v2.32: when true the hub stops preserving message boundaries -- each
         * line is framed to bytes and delivered in random small chunks, and
         * each end reassembles with a {@link LockstepStream}. That is what a
         * real TCP socket does to a naive sender, so turning it on here is what
         * makes the two-peer walk exercise the framing instead of assuming it
         * away. The Link surface stays String-based, so the framing sits inside
         * the link exactly where a socket implementation would put it.
         */
        public boolean chop;
        /** Largest chunk the chopped mode will deliver, in bytes. */
        public int chopMax = 7;
        /**
         * How many chunks one poll may hand over. Bounded on purpose: if a poll
         * drained every chunk, a line would always be reassembled inside one
         * poll and the interesting case -- a line that is still half-arrived
         * when the frame ends -- would never happen. A socket read returns
         * whatever is in the buffer, which is often less than a full message.
         */
        public int chopPerPoll = 2;

        private final int n;
        private final Random rnd;
        /** per destination: pending {dueFrame, line} */
        private final List<List<Object[]>> queues = new ArrayList<>();
        /** per destination: the reassembly buffer, used when chop is on */
        private final List<LockstepStream> streams = new ArrayList<>();
        /** per destination: raw byte chunks still to be handed over */
        private final List<List<byte[]>> wireBuf = new ArrayList<>();
        /** current frame, advanced by pump() */
        private int frame;

        public Hub(int peers) {
            this(peers, 0, 0, false, 12345L);
        }

        public Hub(int peers, int latency, int jitter, boolean reorder, long seed) {
            this.n = Math.max(1, peers);
            this.latency = latency;
            this.jitter = jitter;
            this.reorder = reorder;
            this.rnd = new Random(seed);
            for (int i = 0; i < this.n; i++) {
                queues.add(new ArrayList<>());
                streams.add(new LockstepStream());
                wireBuf.add(new ArrayList<>());
            }
        }

        public int frame() {
            return frame;
        }

        /** One end of this hub. */
        public Link end(final int peer) {
            return new Link() {
                @Override
                public void send(String line) {
                    // Broadcast to everyone but the sender, which is what a
                    // star hub with no loopback does. The sender's own commands
                    // reach it through its own session, not through the wire.
                    int due = frame + latency + (jitter > 0 ? rnd.nextInt(jitter + 1) : 0);
                    for (int d = 0; d < n; d++) {
                        if (d == peer) continue;
                        queues.get(d).add(new Object[]{due, line});
                    }
                }

                @Override
                public List<String> poll() {
                    List<String> due = collect(peer, frame);
                    if (!chop) return due;
                    // Chopped mode: the lines the hub has "sent" become bytes,
                    // split at arbitrary points, and only complete lines come
                    // back out. A half-delivered line simply is not ready yet.
                    for (String line : due) {
                        byte[] bytes = LockstepStream.encode(line);
                        int p = 0;
                        while (p < bytes.length) {
                            int take = 1 + rnd.nextInt(Math.max(1, chopMax));
                            take = Math.min(take, bytes.length - p);
                            byte[] chunk = new byte[take];
                            System.arraycopy(bytes, p, chunk, 0, take);
                            wireBuf.get(peer).add(chunk);
                            p += take;
                        }
                    }
                    List<byte[]> pending = wireBuf.get(peer);
                    if (pending.isEmpty()) return new ArrayList<>();
                    LockstepStream st = streams.get(peer);
                    int n = Math.min(chopPerPoll, pending.size());
                    for (int i = 0; i < n; i++) st.feed(pending.remove(0));
                    return st.lines();
                }
            };
        }

        private List<String> collect(int dest, int atFrame) {
            List<Object[]> q = queues.get(dest);
            List<Object[]> due = new ArrayList<>();
            for (int i = q.size() - 1; i >= 0; i--) {
                if (((Integer) q.get(i)[0]) <= atFrame) due.add(0, q.remove(i));
            }
            if (reorder && due.size() > 1) {
                // Shuffle in place: same-frame arrivals may be delivered in any
                // order. The session sorts them, so this must not matter.
                for (int i = due.size() - 1; i > 0; i--) {
                    int j = rnd.nextInt(i + 1);
                    Object[] t = due.get(i);
                    due.set(i, due.get(j));
                    due.set(j, t);
                }
            }
            List<String> out = new ArrayList<>();
            for (Object[] o : due) out.add((String) o[1]);
            return out;
        }

        /**
         * Advance the hub's clock one frame. Deliberately does NOT collect:
         * collection is the receiver's job ({@link Link#poll}), and a hub that
         * also drained the queues would swallow a message that a peer had not
         * looked for yet -- with latency 0 the sender and the receiver share a
         * frame, so that race is not hypothetical.
         */
        public void tick() {
            frame++;
        }
    }
}
