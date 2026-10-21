import io

# 1) Lockstep: expose what a player has submitted for the current turn, so the
#    peer can put THAT on the wire (a command from Game.recordOrder is submitted
#    by the game, not by the peer, and the first draft never sent it).
p = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\core\Lockstep.java"
src = io.open(p, encoding="utf-8").read()
old = '''    /** True once the given player has reported for the current turn. */
    public boolean reported(int player) {'''
new = '''    /**
     * What a player has submitted for the current turn, or null. The peer needs
     * this because a command can be submitted by the GAME (recordOrder does it
     * directly) rather than by the peer, and the peer still has to put it on the
     * wire -- a command applied locally but never sent is a desync with a delay.
     */
    public String submitted(int player) {
        String[] row = reports.get(turn);
        if (row == null || player < 0 || player >= players) return null;
        return row[player];
    }

    /** True once the given player has reported for the current turn. */
    public boolean reported(int player) {'''
assert src.count(old) == 1
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))

# 2) LockstepPeer.sendFrame: publish whatever the game submitted this turn.
p2 = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\core\LockstepPeer.java"
src2 = io.open(p2, encoding="utf-8").read()
old2 = '''    private String pending = "";
    private int reportedTurn = -1;
'''
new2 = '''    private String pending = "";
    private int reportedTurn = -1;
    /** The turn this peer last put on the wire; guards against double reports. */
    private int sentTurn = -1;
'''
assert src2.count(old2) == 1
src2 = src2.replace(old2, new2)

old3 = '''    public void sendFrame() {
        if (session.reported(player)) return;      // one report per turn
        String body = pending == null ? "" : pending;
        pending = "";
        session.submit(player, body);
        link.send(Lockstep.encode(session.turn, player, body));
        reportedTurn = session.turn;
    }
'''
new3 = '''    public void sendFrame() {
        if (sentTurn == session.turn) return;      // one report per turn
        // A command can already be sitting in the session because the GAME
        // submitted it (Game.recordOrder does, so that the order carries the
        // entity indices it was issued against). Prefer that; fall back to
        // whatever was queued directly; otherwise send the heartbeat. Missing
        // this is how a locally-applied order would never reach the opponent.
        String body = session.submitted(player);
        if (body == null || body.isEmpty()) {
            body = pending == null ? "" : pending;
        }
        pending = "";
        session.submit(player, body);
        link.send(Lockstep.encode(session.turn, player, body));
        sentTurn = session.turn;
        reportedTurn = session.turn;
    }
'''
assert src2.count(old3) == 1
src2 = src2.replace(old3, new3)
io.open(p2, "w", encoding="utf-8", newline="\n").write(src2)
print("patched Lockstep + LockstepPeer")