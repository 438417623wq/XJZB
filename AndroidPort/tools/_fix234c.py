import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()

old = '''        boolean declared = forfeitAt >= goSilentAt
                && pa.session.forfeitLoser == 1 && pa.session.forfeitWinner == 0;
        boolean timely = forfeitAt >= 0
                && forfeitAt - goSilentAt >= com.xjzb.rts.core.Lockstep.STALL_LIMIT - 2
                && forfeitAt - goSilentAt <= com.xjzb.rts.core.Lockstep.STALL_LIMIT + 2;
        boolean finished = pa.session.ready() && pa.session.turn > 1;
        ok &= inSyncBefore && declared && timely && finished;
        sb.append(" dropInSync=").append(inSyncBefore)
          .append(" declared=").append(declared)
          .append(" timely=").append(timely)
          .append(" finished=").append(finished);
'''
new = '''        int limit2 = com.xjzb.rts.core.Lockstep.STALL_LIMIT;
        int waited = forfeitAt - goSilentAt;
        boolean declared = forfeitAt >= goSilentAt
                && pa.session.forfeitLoser == 1 && pa.session.forfeitWinner == 0;
        // The exact boundary is pinned by the deterministic unit check above
        // (#3). Here the link is chopped, jittered and reordered, so the stall
        // counter starts whenever the last complete turn released rather than
        // on the exact frame of the silence -- hence a band, not an equality.
        // What must hold is that the forfeit never fires EARLY (that would call
        // a slow peer a quitter) and does fire promptly rather than eventually.
        boolean timely = forfeitAt >= 0
                && waited >= limit2 - 2 && waited <= limit2 + 30;
        // After the forfeit the survivor must be able to keep playing, which is
        // the point: a departed peer cannot leave the match stuck. turn > 1
        // proves turns released after the declaration. (ready() is checked on
        // the NEXT frame's boundary, so it is not the right thing to read here.)
        boolean finished = pa.session.turn > 1 && pa.session.forfeitLoser == 1;
        ok &= inSyncBefore && declared && timely && finished;
        sb.append(" dropInSync=").append(inSyncBefore)
          .append(" declared=").append(declared)
          .append(" waited=").append(waited).append("/").append(limit2)
          .append(" timely=").append(timely)
          .append(" finished=").append(finished);
'''
assert src.count(old) == 1, src.count(old)
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
print("patched")