    /**
     * v2.30: lockstep. The point of the whole batch is that two peers consume
     * the same commands in the same order on the same turn, so every assertion
     * below is about order and gating rather than about netcode.
     *
     *  #1 canonical order -- three different submission orders must release in
     *     one identical order, or the two simulations drift;
     *  #2 the canonical order is player id ascending;
     *  #3 a turn with a silent player is not ready and does not advance;
     *  #4 an empty report is a heartbeat, not a no-op: without it the match
     *     stalls forever;
     *  #5 a duplicate packet cannot run a command twice;
     *  #6 the wire round-trips, including a command that carries an index list;
     *  #7 a malformed line yields null instead of throwing;
     *  #8 a desync is detected and pinned to the turn it started;
     *  #9 a whole session serialises into a replay body, and that body drives
     *     the SAME stateHash sequence the lockstep run produced. This is the
     *     one that ties the network layer to the determinism the [v220] replay
     *     assertion already established.
     */
    static void v230Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- #1/#2: canonical order is independent of arrival order --------
        String[][] arrivals = {
            {"move 0,1 400 400", "build 2 barracks 500 500", "train 3 marine"},
            {"train 3 marine", "build 2 barracks 500 500", "move 0,1 400 400"},
            {"build 2 barracks 500 500", "train 3 marine", "move 0,1 400 400"},
        };
        StringBuilder order0 = new StringBuilder();
        for (int a = 0; a < arrivals.length; a++) {
            Lockstep ls = new Lockstep(2);
            // player 0 always speaks first in the array; player 1 second
            ls.submit(1, arrivals[a][2]);
            ls.submit(0, arrivals[a][0]);
            ls.submit(1, arrivals[a][1]);   // duplicate report, ignored
            ls.submit(0, "");
            java.util.List<Lockstep.Cmd> out = ls.release();
            StringBuilder sig = new StringBuilder();
            for (Lockstep.Cmd c : out) sig.append(c.player).append(':').append(c.cmd).append('|');
            if (a == 0) order0 = sig;
            else if (!sig.toString().equals(order0.toString())) ok = false;
        }
        // the expected canonical order: player 0's two commands, then player 1's
        String want = "0:move 0,1 400 400|0:build 2 barracks 500 500|1:train 3 marine|";
        boolean canonical = order0.toString().equals(want);
        ok &= canonical;
        sb.append(" canonical=").append(canonical);

        // ---- #3: a silent player blocks the turn --------------------------
        Lockstep gate = new Lockstep(2);
        gate.submit(0, "move 0 100 100");
        boolean half = !gate.ready() && gate.release().isEmpty() && gate.turn == 0;
        gate.submit(1, "");
        boolean full = gate.ready();
        java.util.List<Lockstep.Cmd> one = gate.release();
        boolean advanced = gate.turn == 1 && one.size() == 1
                && one.get(0).cmd.equals("move 0 100 100");
        ok &= half && full && advanced;
        sb.append(" waitSlow=").append(half).append(" ready=").append(full)
          .append(" advance=").append(advanced);

        // ---- #4: an empty heartbeat still counts as a report ---------------
        Lockstep quiet = new Lockstep(2);
        quiet.submit(0, "");
        quiet.submit(1, "");
        boolean beat = quiet.ready() && quiet.release().isEmpty() && quiet.turn == 1;
        ok &= beat;
        sb.append(" heartbeat=").append(beat);

        // ---- #5: a duplicate packet cannot run twice -----------------------
        Lockstep dup = new Lockstep(2);
        dup.submit(0, "move 0 100 100");
        dup.submit(0, "move 0 200 200");   // second report ignored
        dup.submit(1, "");
        java.util.List<Lockstep.Cmd> dl = dup.release();
        boolean once = dl.size() == 1 && dl.get(0).cmd.equals("move 0 100 100");
        ok &= once;
        sb.append(" dedup=").append(once);

        // ---- #6: the wire round-trips --------------------------------------
        String complex = "build 0,2,5 barracks 640 480";
        Lockstep.Cmd enc = new Lockstep.Cmd(417, 3, complex);
        Lockstep.Cmd dec = Lockstep.decode(enc.toString());
        boolean wire = dec != null && dec.turn == 417 && dec.player == 3
                && dec.cmd.equals(complex);
        ok &= wire;
        sb.append(" wire=").append(wire);

        // ---- #7: garbage is refused, not thrown ----------------------------
        boolean tolerant = Lockstep.decode(null) == null
                && Lockstep.decode("") == null
                && Lockstep.decode("HELLO") == null
                && Lockstep.decode("L 12") == null
                && Lockstep.decode("L x 1 move 0 1 1") == null
                && Lockstep.decode("cmd 5 move 0 1 1") == null;
        ok &= tolerant;
        sb.append(" tolerant=").append(tolerant);

        // ---- #8: a desync is pinned to the turn it started -----------------
        Lockstep ds = new Lockstep(2);
        ds.reportHash(0, 10, 1111L);
        ds.reportHash(1, 10, 1111L);
        ds.reportHash(0, 11, 2222L);
        ds.reportHash(1, 11, 2222L);
        ds.reportHash(0, 12, 3333L);
        ds.reportHash(1, 12, 9999L);
        ds.reportHash(0, 13, 4444L);
        ds.reportHash(1, 13, 4444L);
        boolean pinned = ds.desyncTurn == 12;
        ok &= pinned;
        sb.append(" desync=").append(pinned).append("@").append(ds.desyncTurn);

        // ---- #9: a session IS a replay, and replays to the same states -----
        // Two peers run the same turns through the same command stream; the
        // session is then serialised and played back through loadReplay, and
        // every one-second stateHash sample must match.
        com.xjzb.rts.core.Game live = cleanGame("terran");
        live.lockstep = new Lockstep(2);
        live.lockstepPlayer = 0;
        java.util.List<com.xjzb.rts.core.Game.Ent> scvs = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : live.ents)
            if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);
        java.util.List<Long> a = new ArrayList<>();
        for (int t = 0; t < 30 * 40; t++) {
            // both peers must report every turn, so the harness stands in for
            // the second machine: player 0 speaks every 10 s, player 1 never.
            if (live.lockstep.turn == live.lockstep.turn) {
                if (t % 300 == 0 && !scvs.isEmpty())
                    live.recordOrder("move", scvs, (400 + t) + " " + (400 + t));
                live.lockstep.submit(1, "");
            }
            live.update(1f / 30f);
            if (t % 30 == 29) a.add(live.stateHash());
        }
        boolean cmdsSeen = live.lockstep.commands().size() >= 3;

        String body = live.lockstep.serialize();
        com.xjzb.rts.core.Game back = cleanGame("terran");
        boolean loaded = back.loadReplay("XJZB-REPLAY-1\nmap " + mapId
                + " race terran difficulty 1\n" + body);
        java.util.List<Long> b = new ArrayList<>();
        for (int t = 0; t < 30 * 40; t++) {
            back.update(1f / 30f);
            if (t % 30 == 29) b.add(back.stateHash());
        }
        boolean sameSeq = a.size() == b.size() && a.size() >= 20;
        for (int i = 0; i < a.size() && sameSeq; i++)
            if (!a.get(i).equals(b.get(i))) sameSeq = false;
        boolean session = cmdsSeen && loaded && sameSeq;
        ok &= session;
        sb.append(" session=").append(session).append(" cmds=")
          .append(live.lockstep.commands().size()).append(" samples=").append(a.size());

        System.out.println("  lockstep" + sb + " PASS=" + ok);
    }
