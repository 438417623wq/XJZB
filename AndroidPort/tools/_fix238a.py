import io

# 1) Link gains isClosed(), default false so the tested Hub is unaffected.
p = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\core\LockstepLink.java"
src = io.open(p, encoding="utf-8").read()
old = '''    /** One end of the link: send a wire line, poll what has arrived. */
    public interface Link {
        void send(String line);
        List<String> poll();
    }
'''
new = '''    /** One end of the link: send a wire line, poll what has arrived. */
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
'''
assert src.count(old) == 1
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))

# 2) LockstepPeer: one call that decides whether a peer is gone.
p2 = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\core\LockstepPeer.java"
src2 = io.open(p2, encoding="utf-8").read()
old2 = '''    /** Turns this peer has fully released. Both peers must agree on it. */
    public int turnsReleased() {
        return session.turn;
    }
'''
new2 = '''    /** Turns this peer has fully released. Both peers must agree on it. */
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
'''
assert src2.count(old2) == 1
io.open(p2, "w", encoding="utf-8", newline="\n").write(src2.replace(old2, new2))
print("Link.isClosed + LockstepPeer.checkForfeit added")