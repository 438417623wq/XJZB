package com.xjzb.rts.core;

import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/**
 * v2.32: line framing for a byte stream, plus the opening handshake.
 *
 * v2.31's Link.send(String) assumed message boundaries survive the trip. They
 * do inside a process; they do NOT over TCP, which is a byte stream where one
 * send can arrive as two packets and two sends can arrive as one. So the wire
 * has to carry its own boundaries, and this class is that boundary.
 *
 * Line framing (\n-terminated UTF-8 text) is the choice because a command line
 * is already text and, by construction, contains no newline (see
 * Game.commandFor), so nothing needs escaping. It also means a capture or a log
 * is readable and is written the same way a replay file is. Half a packet and
 * two packets at once stop being protocol problems and become what they
 * actually are: a buffer on the receiving side that hands over a line only once
 * the line is complete.
 */
public final class LockstepStream {

    private final ByteArrayOutputStream buf = new ByteArrayOutputStream();

    /**
     * Feed raw bytes. Whatever the sender's write boundaries were, the result
     * is identical: only complete lines become visible.
     */
    public void feed(byte[] data) {
        if (data != null) feed(data, 0, data.length);
    }

    public void feed(byte[] data, int off, int len) {
        if (data == null || len <= 0) return;
        buf.write(data, off, len);
    }

    /**
     * Take every complete line, oldest first, and drop them from the buffer. A
     * trailing partial line stays buffered for the next feed -- that is the
     * half-packet case, and returning it early would hand the parser a
     * truncated command.
     */
    public List<String> lines() {
        byte[] all = buf.toByteArray();
        List<String> out = new ArrayList<>();
        int start = 0;
        for (int i = 0; i < all.length; i++) {
            if (all[i] != '\n') continue;
            int end = i;
            // tolerate CRLF: some stacks append \r before the newline
            if (end > start && all[end - 1] == '\r') end--;
            out.add(new String(all, start, end - start, StandardCharsets.UTF_8));
            start = i + 1;
        }
        if (start > 0) {
            buf.reset();
            if (start < all.length) buf.write(all, start, all.length - start);
        }
        return out;
    }

    /** True when a partial line is sitting in the buffer. */
    public boolean hasPartial() {
        return buf.size() > 0;
    }

    /** One line as it goes on the wire: the text plus its terminator. */
    public static byte[] encode(String line) {
        String s = line == null ? "" : line;
        return (s + "\n").getBytes(StandardCharsets.UTF_8);
    }
}