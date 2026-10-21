import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()

old = '''        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanHost.Connected>
                admitted = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.atomic.AtomicReference<String> hostErr =
                new java.util.concurrent.atomic.AtomicReference<>();
        int port = host.start(new com.xjzb.rts.net.LanHost.Callback() {
            @Override public void onConnected(com.xjzb.rts.net.LanHost.Connected c) {
                admitted.set(c);
            }
            @Override public void onError(String message) { hostErr.set(message); }
        });
'''
new = '''        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanHost.Connected>
                admitted = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.atomic.AtomicReference<String> hostErr =
                new java.util.concurrent.atomic.AtomicReference<>();
        // The host writes "Y" to the joiner BEFORE it runs this callback, so the
        // joiner can be back before the host has recorded the admission. Wait on
        // the callback as well, or the seat check races the accept thread.
        final java.util.concurrent.CountDownLatch hostAdmitted =
                new java.util.concurrent.CountDownLatch(1);
        int port = host.start(new com.xjzb.rts.net.LanHost.Callback() {
            @Override public void onConnected(com.xjzb.rts.net.LanHost.Connected c) {
                admitted.set(c);
                hostAdmitted.countDown();
            }
            @Override public void onError(String message) {
                hostErr.set(message);
                hostAdmitted.countDown();
            }
        });
'''
assert src.count(old) == 1
src = src.replace(old, new)

old2 = '''        com.xjzb.rts.net.LanJoin.Result jr = joined.get();
        boolean linked = answered && jr != null && jr.ok() && jr.error == null;
        boolean seated = linked && lobby.connectedCount() == 2
                && admitted.get() != null && admitted.get().slot >= 0;
'''
new2 = '''        hostAdmitted.await(6, java.util.concurrent.TimeUnit.SECONDS);
        com.xjzb.rts.net.LanJoin.Result jr = joined.get();
        boolean linked = answered && jr != null && jr.ok() && jr.error == null;
        boolean seated = linked && lobby.connectedCount() == 2
                && admitted.get() != null && admitted.get().slot >= 0;
'''
assert src.count(old2) == 1
src = src.replace(old2, new2)
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("patched")