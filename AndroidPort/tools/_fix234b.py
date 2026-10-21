import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()

# (a) after a release the NEXT turn legitimately has nobody reported yet, so
# stalledPlayer() is 0, not -1. The thing that must have reset is the counter.
old1 = '''        ls.submit(1, "");
        ls.release();
        boolean reset = ls.stallTurns == 0 && ls.stalledPlayer() == -1;
'''
new1 = '''        ls.submit(1, "");
        ls.release();
        // After a release the counter is back to zero. The NEXT turn has nobody
        // reported yet, so stalledPlayer() names player 0 -- that is the fresh
        // turn waiting for both peers, not a leftover from the last one.
        boolean reset = ls.stallTurns == 0 && ls.stalledPlayer() == 0;
'''
assert src.count(old1) == 1, src.count(old1)
src = src.replace(old1, new1)

# (b) the loop must outlast the timeout: the forfeit fires ~300 frames after
# the silence starts, so 12 s of frames never reaches it.
old2 = '''        int goSilentAt = 60;
        int forfeitAt = -1;
        boolean inSyncBefore = true;
        java.util.Map<Integer, Long> byTurn = new java.util.HashMap<>();
        for (int t = 0; t < 30 * 12; t++) {
'''
new2 = '''        int goSilentAt = 60;
        int forfeitAt = -1;
        boolean inSyncBefore = true;
        // A snapshot of "the state after turn T" per peer, exactly as [v231]
        // compares them: per FRAME the two are legitimately at different points
        // while one waits for the other, so the honest check is per turn.
        java.util.Map<Integer, Long> turnsA = new java.util.HashMap<>();
        java.util.Map<Integer, Long> turnsB = new java.util.HashMap<>();
        for (int t = 0; t < 30 * 16; t++) {
'''
assert src.count(old2) == 1, src.count(old2)
src = src.replace(old2, new2)

old3 = '''            long ha = pa.stepFrame(1f / 30f);
            if (t < goSilentAt) {
                long hb = pb.stepFrame(1f / 30f);
                // both peers still agree while B is alive
                Long prev = byTurn.put(pa.turnsReleased(), ha);
                if (prev != null && prev.longValue() != ha) inSyncBefore = false;
                if (pa.turnsReleased() != pb.turnsReleased()) inSyncBefore = false;
            } else {
                // A notices B is gone and declares the forfeit at the limit
                if (pa.session.stalledOut(com.xjzb.rts.core.Lockstep.STALL_LIMIT)
                        && pa.session.forfeit(1)) forfeitAt = t;
            }
        }
'''
new3 = '''            long ha = pa.stepFrame(1f / 30f);
            turnsA.put(pa.turnsReleased(), ha);
            if (t < goSilentAt) {
                long hb = pb.stepFrame(1f / 30f);
                turnsB.put(pb.turnsReleased(), hb);
            } else {
                // A notices B is gone and declares the forfeit at the limit
                if (pa.session.stalledOut(com.xjzb.rts.core.Lockstep.STALL_LIMIT)
                        && pa.session.forfeit(1)) forfeitAt = t;
            }
        }
        // every turn both peers reached while B was alive must hash the same
        for (java.util.Map.Entry<Integer, Long> e : turnsA.entrySet()) {
            Long other = turnsB.get(e.getKey());
            if (other != null && other.longValue() != e.getValue().longValue())
                inSyncBefore = false;
        }
'''
assert src.count(old3) == 1, src.count(old3)
src = src.replace(old3, new3)
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("patched")