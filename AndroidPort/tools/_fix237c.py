import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()
old = '''        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanJoin.Result>
                bad = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.CountDownLatch done2 = new java.util.concurrent.CountDownLatch(1);
        com.xjzb.rts.net.LanJoin.connect(host2.beacon(), "2.30", "terran",
                r -> { bad.set(r); done2.countDown(); });
        done2.await(6, java.util.concurrent.TimeUnit.SECONDS);
        com.xjzb.rts.net.LanJoin.Result br = bad.get();
        boolean refused = br != null && !br.ok() && br.error != null
                && br.error.contains("版本");
        boolean noSeat = lobby2.connectedCount() == 0;
'''
new = '''        // the host itself holds seat 0, so "no seat for the refused peer" means
        // the roster does not grow, not that it is empty
        int seatsBefore = lobby2.connectedCount();
        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanJoin.Result>
                bad = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.CountDownLatch done2 = new java.util.concurrent.CountDownLatch(1);
        com.xjzb.rts.net.LanJoin.connect(host2.beacon(), "2.30", "terran",
                r -> { bad.set(r); done2.countDown(); });
        done2.await(6, java.util.concurrent.TimeUnit.SECONDS);
        com.xjzb.rts.net.LanJoin.Result br = bad.get();
        boolean refused = br != null && !br.ok() && br.error != null
                && br.error.contains("版本");
        boolean noSeat = lobby2.connectedCount() == seatsBefore;
'''
assert src.count(old) == 1
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
print("patched")