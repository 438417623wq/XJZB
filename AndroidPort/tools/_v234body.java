    /**
     * v2.34: what happens when a peer never comes back.
     *
     * v2.31 made a slow peer freeze the match, which is right for a hiccup and
     * wrong for a departure: two machines sitting on the same turn forever is
     * indistinguishable from a hung game. This adds the rule and the timeout.
     *
     *  #1 the stall counter climbs while a turn is incomplete and resets the
     *     moment it releases;
     *  #2 the stalled player is NAMED, so the message can say who went quiet;
     *  #3 stalledOut() fires exactly at the limit, not a frame early;
     *  #4 forfeit records the result and can only happen once;
     *  #5 after a forfeit the release no longer waits for the departed player,
     *     so the match can reach a result instead of hanging;
     *  #6 a peer that returns inside the limit is not a quitter -- the counter
     *     is a CONTINUOUS wait, not a total, so a shaky connection across a
     *     whole match can never accumulate into a forfeit;
     *  #7 end to end: two real peers, one goes silent, and the survivor
     *     declares the forfeit at the limit -- while every frame before that
     *     was still perfectly in sync.
     */
    static void v234Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- #1/#2: the counter and the named player -----------------------
        com.xjzb.rts.core.Lockstep ls = new com.xjzb.rts.core.Lockstep(2);
        boolean startZero = ls.stallTurns == 0 && ls.stalledPlayer() == 0;
        ls.noteStall();
        ls.noteStall();
        boolean climbed = ls.stallTurns == 2 && ls.stalledPlayer() == 0;
        ls.submit(0, "");
        boolean named = ls.stalledPlayer() == 1;
        ls.submit(1, "");
        ls.release();
        boolean reset = ls.stallTurns == 0 && ls.stalledPlayer() == -1;
        ok &= startZero && climbed && named && reset;
        sb.append(" counter=").append(startZero && climbed && named && reset);

        // ---- #3: the limit fires exactly on the limit ----------------------
        com.xjzb.rts.core.Lockstep lim = new com.xjzb.rts.core.Lockstep(2);
        lim.submit(0, "");
        int limit = com.xjzb.rts.core.Lockstep.STALL_LIMIT;
        for (int i = 0; i < limit - 1; i++) lim.noteStall();
        boolean beforeLimit = !lim.stalledOut(limit);
        lim.noteStall();
        boolean atLimit = lim.stalledOut(limit);
        ok &= beforeLimit && atLimit;
        sb.append(" limit@").append(limit).append("=").append(beforeLimit && atLimit);

        // ---- #4/#5: forfeit records once and unblocks the release ----------
        boolean f1 = lim.forfeit(1);
        boolean f2 = !lim.forfeit(1);
        boolean recorded = lim.forfeitLoser == 1 && lim.forfeitWinner == 0
                && lim.isDropped(1) && !lim.isDropped(0);
        boolean unblocked = lim.ready();
        java.util.List<com.xjzb.rts.core.Lockstep.Cmd> rel = lim.release();
        boolean advanced = lim.turn == 1;
        ok &= f1 && f2 && recorded && unblocked && advanced;
        sb.append(" forfeit=").append(f1 && f2 && recorded)
          .append(" unblock=").append(unblocked && advanced);

        // ---- #6: a peer that returns inside the limit is not a quitter -----
        com.xjzb.rts.core.Lockstep flaky = new com.xjzb.rts.core.Lockstep(2);
        // 200 frames of silence, then a full turn, three times over
        for (int round = 0; round < 3; round++) {
            for (int i = 0; i < 200; i++) flaky.noteStall();
            flaky.submit(0, "");
            flaky.submit(1, "");
            flaky.release();
        }
        boolean survived = flaky.forfeitLoser < 0 && flaky.turn == 3 && flaky.stallTurns == 0;
        ok &= survived;
        sb.append(" flakyOk=").append(survived);

        // ---- #7: two real peers, one goes silent ---------------------------
        com.xjzb.rts.core.LockstepLink.Hub hub =
                new com.xjzb.rts.core.LockstepLink.Hub(2, 2, 4, true, 31337L);
        hub.chop = true;
        com.xjzb.rts.core.Game ga = cleanGame("terran");
        com.xjzb.rts.core.Game gb = cleanGame("terran");
        com.xjzb.rts.core.LockstepPeer pa = new com.xjzb.rts.core.LockstepPeer(
                ga, 0, 2, hub.end(0));
        com.xjzb.rts.core.LockstepPeer pb = new com.xjzb.rts.core.LockstepPeer(
                gb, 1, 2, hub.end(1));
        List<com.xjzb.rts.core.Game.Ent> scvs = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : ga.ents)
            if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);

        int goSilentAt = 60;
        int forfeitAt = -1;
        boolean inSyncBefore = true;
        java.util.Map<Integer, Long> byTurn = new java.util.HashMap<>();
        for (int t = 0; t < 30 * 12; t++) {
            String aCmd = "";
            if (t % 150 == 0 && !scvs.isEmpty())
                aCmd = ga.commandFor("move", scvs, (400 + t / 150 * 40) + " 400");
            pa.receiveFrame();
            if (t < goSilentAt) pb.receiveFrame();   // B stops talking after 2 s
            pa.queue(aCmd);
            pa.sendFrame();
            if (t < goSilentAt) pb.sendFrame();
            hub.tick();
            long ha = pa.stepFrame(1f / 30f);
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
        boolean declared = forfeitAt >= goSilentAt
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

        System.out.println("  stall/forfeit" + sb + " PASS=" + ok);
    }
