import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()
old = '''        // Three link profiles, from friendly to actively hostile.
        int[][] profiles = {
            {0, 0, 0},          // latency, jitter, reorder
            {1, 3, 0},
            {2, 5, 1},
        };
'''
new = '''        // Four link profiles, from friendly to actively hostile. The last two
        // also chop every line into random small byte chunks, so the command
        // has to survive a real byte stream (see LockstepLink.Hub.chop) rather
        // than the process-internal message boundaries the earlier profiles
        // enjoy. That is the case a TCP socket produces and a naive sender
        // breaks on.
        int[][] profiles = {
            {0, 0, 0, 0},          // latency, jitter, reorder, chop
            {1, 3, 0, 0},
            {2, 5, 1, 0},
            {2, 5, 1, 1},
            {3, 4, 0, 1},
        };
'''
assert src.count(old) == 1, src.count(old)
src = src.replace(old, new)

old2 = '''            int lat = profiles[pi][0], jit = profiles[pi][1], reo = profiles[pi][2];
            com.xjzb.rts.core.LockstepLink.Hub hub =
                    new com.xjzb.rts.core.LockstepLink.Hub(2, lat, jit, reo != 0, 4242L);
'''
new2 = '''            int lat = profiles[pi][0], jit = profiles[pi][1];
            int reo = profiles[pi][2], chop = profiles[pi][3];
            com.xjzb.rts.core.LockstepLink.Hub hub =
                    new com.xjzb.rts.core.LockstepLink.Hub(2, lat, jit, reo != 0, 4242L);
            hub.chop = chop != 0;
'''
assert src.count(old2) == 1, src.count(old2)
src = src.replace(old2, new2)
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("patched")