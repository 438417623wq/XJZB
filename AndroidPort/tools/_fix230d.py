import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()

# ---- #1/#2: one report per player per turn, so use three players ----
old1 = '''        // Player 0's two commands are always submitted in the order (A0, A1);
        // player 1's single command B is interleaved three different ways. The
        // released order must be A0, A1, B every time -- player id ascending,
        // then that player's own submission order.
        String[][] arrivals = {
            {"A0", "A1", "B"},
            {"B", "A0", "A1"},
            {"A0", "B", "A1"},
        };
        String order0 = null;
        boolean reorderSame = true;
        for (int a = 0; a < arrivals.length; a++) {
            com.xjzb.rts.core.Lockstep ls = new com.xjzb.rts.core.Lockstep(2);
            for (String piece : arrivals[a]) {
                if (piece.equals("A0")) ls.submit(0, "move 0,1 400 400");
                else if (piece.equals("A1")) ls.submit(0, "build 2 barracks 500 500");
                else ls.submit(1, "train 3 marine");
            }
            java.util.List<com.xjzb.rts.core.Lockstep.Cmd> out = ls.release();
            StringBuilder sig = new StringBuilder();
            for (com.xjzb.rts.core.Lockstep.Cmd c : out)
                sig.append(c.player).append(':').append(c.cmd).append('|');
            if (a == 0) order0 = sig.toString();
            else if (!sig.toString().equals(order0)) reorderSame = false;
        }
        String want = "0:move 0,1 400 400|0:build 2 barracks 500 500|1:train 3 marine|";
        boolean canonical = reorderSame && want.equals(order0);
        ok &= canonical;
        sb.append(" canonical=").append(canonical);
'''
new1 = '''        // A player reports ONCE per turn (a second report is a duplicate, see
        // #5), so canonical order is tested with one command per player across
        // three players. The same three commands are submitted in four
        // different arrival orders and must release in one identical order.
        String[][] arrivals = {
            {"A", "B", "C"},
            {"C", "B", "A"},
            {"B", "C", "A"},
            {"C", "A", "B"},
        };
        String order0 = null;
        boolean reorderSame = true;
        for (int a = 0; a < arrivals.length; a++) {
            com.xjzb.rts.core.Lockstep ls = new com.xjzb.rts.core.Lockstep(3);
            for (String piece : arrivals[a]) {
                if (piece.equals("A")) ls.submit(0, "move 0,1 400 400");
                else if (piece.equals("B")) ls.submit(1, "train 3 marine");
                else ls.submit(2, "build 2 barracks 500 500");
            }
            java.util.List<com.xjzb.rts.core.Lockstep.Cmd> out = ls.release();
            StringBuilder sig = new StringBuilder();
            for (com.xjzb.rts.core.Lockstep.Cmd c : out)
                sig.append(c.player).append(':').append(c.cmd).append('|');
            if (a == 0) order0 = sig.toString();
            else if (!sig.toString().equals(order0)) reorderSame = false;
        }
        String want = "0:move 0,1 400 400|1:train 3 marine|2:build 2 barracks 500 500|";
        boolean canonical = reorderSame && want.equals(order0);
        ok &= canonical;
        sb.append(" canonical=").append(canonical);
'''
assert src.count(old1) == 1, src.count(old1)
src = src.replace(old1, new1)

# ---- #9: the driver must advance a turn per frame, with both reports ----
old2 = '''        java.util.List<Long> a = new ArrayList<>();
        for (int t = 0; t < 30 * 40; t++) {
            // The harness stands in for the second machine: player 0 issues an
            // order every 10 s, player 1 only ever sends the heartbeat. Both
            // reports must land before update() will advance the turn.
            if (t % 300 == 0 && !scvs.isEmpty())
                live.recordOrder("move", scvs, (400 + t) + " " + (400 + t));
            sess.submit(1, "");
            live.update(1f / 30f);
            if (t % 30 == 29) a.add(live.stateHash());
        }
'''
new2 = '''        java.util.List<Long> a = new ArrayList<>();
        // The harness stands in for the second machine. Both peers must report
        // every turn or update() refuses to advance (that is the gate), so
        // player 0 orders every 5 s and otherwise only sends the heartbeat.
        for (int t = 0; t < 30 * 40; t++) {
            if (t % 150 == 0 && !scvs.isEmpty())
                live.recordOrder("move", scvs, (400 + t) + " " + (400 + t));
            else
                sess.submit(0, "");
            sess.submit(1, "");
            live.update(1f / 30f);
            if (t % 30 == 29) a.add(live.stateHash());
        }
'''
assert src.count(old2) == 1, src.count(old2)
src = src.replace(old2, new2)

io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("patched")