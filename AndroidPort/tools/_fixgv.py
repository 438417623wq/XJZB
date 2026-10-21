import io
p = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\GameView.java"
src = io.open(p, encoding="utf-8").read()
# net.game IS the game we handed it, so the reassignment is dead weight that
# reads like the peer might swap games underneath us.
old = '''                    net.stepFrame(dt);
                    if (net.game != game) game = net.game;
'''
new = '''                    net.stepFrame(dt);
'''
assert src.count(old) == 1
src = src.replace(old, new)

# A LAN match must not be restarted/saved/loaded: each of those builds a fresh
# Game, and the peer would keep pointing at the old one -- the two machines would
# silently part ways. Refuse them with a sentence instead.
old2 = '''    /** Rebuild the simulation in place for the pause menu's restart option. */
    private void restart() {
'''
new2 = '''    /** Rebuild the simulation in place for the pause menu's restart option. */
    private void restart() {
        // v2.37: a networked match cannot be rebuilt from one side. The peer
        // holds the old Game and the opponent holds its own state, so a restart
        // here would desync the match rather than restart it.
        if (net != null) {
            toast = "联机对战不能重新开始";
            toastT = 1.8f;
            menuOpen = false;
            return;
        }
'''
assert src.count(old2) == 1
src = src.replace(old2, new2)
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("patched")