package com.xjzb.rts.net;

import com.xjzb.rts.core.LockstepLink;
import com.xjzb.rts.core.LockstepStream;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.Socket;
import java.util.ArrayList;
import java.util.List;

/**
 * v2.37: the real socket behind the Link the protocol was written against.
 *
 * This is deliberately the thinnest possible thing: a reader thread that pumps
 * bytes through a LockstepStream and a poll() that hands over whatever whole
 * lines have arrived. Everything actually hard about a network match lives in
 * core/ and is asserted on the desktop -- the framing, the ordering, the
 * ready-gate, the timeout. What is left here is only the part that cannot exist
 * without a socket.
 *
 * The reader thread is separate from the game loop on purpose. If the game loop
 * read the socket itself it would block waiting for the peer's bytes, and the
 * peer would be blocking waiting for ours: a deadlock, and one that only shows
 * up over a real socket (the in-process harness cannot produce it). This is
 * exactly the arrangement tools/TcpLockstep.java runs, so the tested shape and
 * the shipped shape are the same.
 */
public final class TcpLink implements LockstepLink.Link {

    private final Socket socket;
    private final OutputStream out;
    private final LockstepStream stream = new LockstepStream();
    private final List<String> arrived = new ArrayList<>();
    private final Object lock = new Object();
    private volatile boolean closed;
    private Thread reader;

    public TcpLink(Socket s) throws IOException {
        this.socket = s;
        // A 40 ms Nagle delay on a 33 ms turn is a whole extra turn of lag, and
        // every message here is small and already latency-critical.
        s.setTcpNoDelay(true);
        this.out = s.getOutputStream();
        startReader(s);
    }

    private void startReader(final Socket s) {
        reader = new Thread(() -> {
            byte[] buf = new byte[1024];
            try {
                InputStream in = s.getInputStream();
                int n;
                while (!closed && (n = in.read(buf)) > 0) {
                    synchronized (lock) {
                        stream.feed(buf, 0, n);
                        arrived.addAll(stream.lines());
                    }
                }
            } catch (Exception ignored) {
                // A closed socket is the normal way this ends; the caller finds
                // out through isClosed() rather than an exception here.
            } finally {
                closed = true;
            }
        }, "xjzb-net-read");
        reader.setDaemon(true);
        reader.start();
    }

    @Override
    public void send(String line) {
        if (closed) return;
        try {
            synchronized (lock) {
                out.write(LockstepStream.encode(line));
                out.flush();
            }
        } catch (Exception e) {
            closed = true;
        }
    }

    @Override
    public List<String> poll() {
        synchronized (lock) {
            if (arrived.isEmpty()) return new ArrayList<>();
            List<String> got = new ArrayList<>(arrived);
            arrived.clear();
            return got;
        }
    }

    public boolean isClosed() {
        return closed || socket.isClosed();
    }

    public void close() {
        closed = true;
        try {
            socket.close();
        } catch (Exception ignored) {
        }
    }
}