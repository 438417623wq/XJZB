import io

# --- Lobby: the two "fill the roster" rules, in core so they can be asserted ---
p = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\core\Lobby.java"
src = io.open(p, encoding="utf-8").read()
old = '''    public void setReady(int i, boolean ready) {'''
new = '''    /**
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

    public void setReady(int i, boolean ready) {'''
assert src.count(old) == 1
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))

# --- LanHost: seat the host through the new helper ---
p2 = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\net\LanHost.java"
src2 = io.open(p2, encoding="utf-8").read()
old2 = '''        // The host is a player, not a spectator: it takes seat 0. Without this a
        // two-player room reports "1/2 connected" and canStart() is never true.
        if (lobby.connectedCount() == 0) {
            lobby.join(beacon.host == null || beacon.host.isEmpty() ? "房主" : beacon.host);
        }
'''
new2 = '''        // The host is a player, not a spectator: it takes seat 0 AND is ready,
        // because pressing "host" is the confirmation. Seat 0 must also be
        // ready or canStart() is false and the host -- the only one who can
        // start a match -- is stuck forever.
        if (lobby.connectedCount() == 0) {
            lobby.hostSeat(beacon.host == null || beacon.host.isEmpty()
                    ? "房主" : beacon.host);
        }
'''
assert src2.count(old2) == 1
io.open(p2, "w", encoding="utf-8", newline="\n").write(src2.replace(old2, new2))

# --- LobbyActivity: the joiner fills both seats ---
p3 = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\LobbyActivity.java"
src3 = io.open(p3, encoding="utf-8").read()
old3 = '''            // the joiner is a player: take a seat so the host's roster matches
            lobby.join("我");
            lobby.setReady(0, true);
            lobby.setReady(1, true);
'''
new3 = '''            // The joiner's local roster: the host (which it just handshook
            // with) plus itself, both ready, so the start button is live here
            // too. Filling only its own seat leaves this view at "1/2".
            lobby.joinAsGuest(b.host, "我");
'''
assert src3.count(old3) == 1
io.open(p3, "w", encoding="utf-8", newline="\n").write(src3.replace(old3, new3))
print("hostSeat + joinAsGuest added and wired")