    /**
     * v2.31: two independent simulations, one hostile link.
     *
     * v2.30 proved a session's command stream replays to the same states on ONE
     * machine. That is necessary but not sufficient: it says nothing about two
     * machines that each own a Game and exchange orders over a wire with
     * latency, jitter and reordering. This walks exactly that -- two peers built
     * from the same map data but sharing no mutable state -- and compares their
     * state hashes.
     *
     * The comparison is PER TURN, not per frame, and that distinction is the
     * whole lesson of this assertion. A peer that is waiting for the other's
     * report is frozen on an earlier turn, so at any given FRAME the two are
     * legitimately at different points in the timeline and their hashes differ.
     * What must hold is that "the state after turn T" is the same on both
     * machines for every T they have both reached. (The first draft compared
     * per frame, which is a statement lockstep does not make and cannot keep.)
     *
     *  #1 two peers built independently start from the same hash;
     *  #2 with latency 0 they agree on every turn;
     *  #3 with latency 1 + jitter they agree on every turn;
     *  #4 with latency 2 + jitter + REORDERING they agree on every turn -- the
     *     one that matters, because "apply whatever arrived" is the bug a naive
     *     implementation ships with;
     *  #5 the two never drift apart: their turn difference stays bounded;
     *  #6 both peers' command logs are identical (canonical order is unique);
     *  #7 the two sessions serialise to the same replay body, so the match can
     *     be saved or handed to a spectator.
     */
    static void v231Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // Three link profiles, from friendly to actively hostile.
        int[][] profiles = {
            {0, 0, 0},          // latency, jitter, reorder
            {1, 3, 0},
            {2, 5, 1},
        };
        boolean allSame = true, allLogs = true, allBodies = true, allBounded = true;
        int minTurns = Integer.MAX_VALUE;
        String detail = "";
        for (int pi = 0; pi < profiles.length; pi++) {
            int lat = profiles[pi][0], jit = profiles[pi][1], reo = profiles[pi][2];
            com.xjzb.rts.core.LockstepLink.Hub hub =
                    new com.xjzb.rts.core.LockstepLink.Hub(2, lat, jit, reo != 0, 4242L);
            com.xjzb.rts.core.Game ga = cleanGame("terran");
            com.xjzb.rts.core.Game gb = cleanGame("terran");
            com.xjzb.rts.core.LockstepPeer pa = new com.xjzb.rts.core.LockstepPeer(
                    ga, 0, 2, hub.end(0));
            com.xjzb.rts.core.LockstepPeer pb = new com.xjzb.rts.core.LockstepPeer(
                    gb, 1, 2, hub.end(1));

            // #1: two independent constructions agree before any order
            boolean seed = ga.stateHash() == gb.stateHash();
            if (!seed) allSame = false;

            List<com.xjzb.rts.core.Game.Ent> scvs = new ArrayList<>();
            for (com.xjzb.rts.core.Game.Ent e : ga.ents)
                if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);

            // hash after each released turn, per peer
            java.util.Map<Integer, Long> byTurnA = new java.util.HashMap<>();
            java.util.Map<Integer, Long> byTurnB = new java.util.HashMap<>();
            for (int t = 0; t < 30 * 20; t++) {
                // player 0 orders every 5 s; both peers heartbeat otherwise
                String aCmd = "";
                if (t % 150 == 0 && !scvs.isEmpty()) {
                    int tx = 400 + (t / 150) * 40, ty = 400 + (t / 150) * 30;
                    aCmd = ga.commandFor("move", scvs, tx + " " + ty);
                }
                // The three phases are separated deliberately: both peers
                // receive, then both send, then both step. See LockstepPeer.
                pa.receiveFrame();
                pb.receiveFrame();
                pa.sendFrame(aCmd);
                pb.sendFrame("");
                hub.tick();
                long ha = pa.stepFrame(1f / 30f);
                long hb = pb.stepFrame(1f / 30f);
                byTurnA.put(pa.turnsReleased(), ha);
                byTurnB.put(pb.turnsReleased(), hb);
                // #5: neither peer runs away from the other. The bound is the
                // worst-case delivery delay plus the two frame phases.
                if (Math.abs(pa.turnsReleased() - pb.turnsReleased()) > lat + jit + 3)
                    allBounded = false;
            }

            // #2/#3/#4: every turn both peers reached must hash the same
            int common = 0;
            for (java.util.Map.Entry<Integer, Long> e : byTurnA.entrySet()) {
                Long other = byTurnB.get(e.getKey());
                if (other == null) continue;
                common++;
                if (other.longValue() != e.getValue().longValue()) allSame = false;
            }
            if (common < 15) allSame = false;
            minTurns = Math.min(minTurns, common);

            // #6: identical command logs on the common prefix
            int n = Math.min(pa.commands().size(), pb.commands().size());
            for (int i = 0; i < n; i++) {
                com.xjzb.rts.core.Lockstep.Cmd x = pa.commands().get(i);
                com.xjzb.rts.core.Lockstep.Cmd y = pb.commands().get(i);
                if (x.turn != y.turn || x.player != y.player || !x.cmd.equals(y.cmd))
                    allLogs = false;
            }
            // #7: identical replay bodies
            if (!pa.session.serialize().equals(pb.session.serialize())) allBodies = false;
            if (pi == 0) detail = " turns=" + common + " cmds=" + pa.commands().size();
        }

        ok &= allSame && allLogs && allBodies && allBounded;
        sb.append(" samePerTurn=").append(allSame)
          .append(" boundedDrift=").append(allBounded)
          .append(" sameLog=").append(allLogs)
          .append(" sameReplay=").append(allBodies)
          .append(" minTurns=").append(minTurns).append(detail);

        System.out.println("  two peers" + sb + " PASS=" + ok);
    }
