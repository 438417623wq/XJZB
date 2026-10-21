import io

# 1) LanDiscovery: the Listener parameter shadowed the Thread field.
p = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\net\LanDiscovery.java"
src = io.open(p, encoding="utf-8").read()
src = src.replace("public void listen(final String myVersion, final Listener listener) {",
                  "public void listen(final String myVersion, final Listener cb) {")
src = src.replace("        listener_ = listener;\n", "        listener_ = cb;\n")
assert "final Listener cb) {" in src and "listener_ = cb;" in src
io.open(p, "w", encoding="utf-8", newline="\n").write(src)

# 2) LanHost: the host is a player too, so it must hold a seat -- otherwise a
#    2-player room reports 1/2 connected and can never start.
p2 = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\net\LanHost.java"
src2 = io.open(p2, encoding="utf-8").read()
old = '''        beacon.version = room.version();
        beacon.port = server.getLocalPort();
        running = true;
'''
new = '''        beacon.version = room.version();
        beacon.port = server.getLocalPort();
        // The host is a player, not a spectator: it takes seat 0. Without this a
        // two-player room reports "1/2 connected" and canStart() is never true.
        if (lobby.connectedCount() == 0) {
            lobby.join(beacon.host == null || beacon.host.isEmpty() ? "房主" : beacon.host);
        }
        running = true;
'''
assert src2.count(old) == 1
io.open(p2, "w", encoding="utf-8", newline="\n").write(src2.replace(old, new))
print("patched LanDiscovery + LanHost")