import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()

old = '''        // ---- #1/#2: canonical order is independent of arrival order --------
        String[][] arrivals = {
            {"move 0,1 400 400", "build 2 barracks 500 500", "train 3 marine"},
            {"train 3 marine", "build 2 barracks 500 500", "move 0,1 400 400"},
            {"build 2 barracks 500 500", "train 3 marine", "move 0,1 400 400"},
        };
        StringBuilder order0 = new StringBuilder();
        for (int a = 0; a < arrivals.length; a++) {
            com.xjzb.rts.core.Lockstep ls = new com.xjzb.rts.core.Lockstep(2);
            // player 0 always speaks first in the array; player 1 second
            ls.submit(1, arrivals[a][2]);
            ls.submit(0, arrivals[a][0]);
            ls.submit(1, arrivals[a][1]);   // duplicate report, ignored
            ls.submit(0, "");
            java.util.List<com.xjzb.rts.core.Lockstep.Cmd> out = ls.release();
            StringBuilder sig = new StringBuilder();
            for (com.xjzb.rts.core.Lockstep.Cmd c : out) sig.append(c.player).append(':').append(c.cmd).append('|');
            if (a == 0) order0 = sig;
            else if (!sig.toString().equals(order0.toString())) ok = false;
        }
        // the expected canonical order: player 0's two commands, then player 1's
        String want = "0:move 0,1 400 400|0:build 2 barracks 500 500|1:train 3 marine|";
        boolean canonical = order0.toString().equals(want);
        ok &= canonical;
        sb.append(" canonical=").append(canonical);
'''
new = '''        // ---- #1/#2: canonical order is independent of arrival order --------
        // Player 0's two commands are always submitted in the order (A0, A1);
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
assert src.count(old) == 1, src.count(old)
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
print("patched")