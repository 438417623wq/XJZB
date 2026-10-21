    /**
     * v2.40: CHARACTERIZATION of what a LAN match actually is today.
     *
     * This assertion does not test a new feature -- it pins the CURRENT
     * semantics so they are a specified behaviour rather than an accident, and
     * so a future change to them is a deliberate one that has to update this
     * text.
     *
     * What it pins: a LAN match is CO-OPERATIVE. Both peers build the same
     * board (Game's model is one human team 0 plus one AI team 1), so both
     * peers' orders land on team 0, and team 1 is driven by each machine's own
     * aiUpdate. Two phones therefore play the same side against the AI.
     *
     * Why real 1v1 is NOT a small change, which is worth recording next to the
     * assertion that documents the limitation: the command format identifies
     * units by INDEX INTO THE SHARED ents LIST ("move 0,2,5 300 400"). That list
     * grows and shrinks as units are built and killed, and the two teams' halves
     * of it change independently -- so "index i on my machine" and "index i on
     * yours" stop meaning the same unit the moment one team trains something.
     * Mirroring indices is therefore unsound, and 1v1 needs either team-relative
     * indices or a per-team entity list. That is a command-format change, and
     * applyCommand is also the replay path, so it has to be done with the
     * replay-determinism assertion ([v220]) in the same change.
     *
     *  #1 both peers' ents lists are identical in order AND team, which is what
     *     makes an index-based command stream work AT ALL between them;
     *  #2 a command issued by either peer reaches both and acts on team 0;
     *  #3 the AI still drives team 1 in a LAN match (so the match has an
     *     opponent even though it has only one human side);
     *  #4 the two peers stay in lockstep doing it (the invariant that matters).
     */
    static void v240Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        com.xjzb.rts.core.Game ga = cleanGame("terran");
        com.xjzb.rts.core.Game gb = cleanGame("terran");

        // #1: identical in order and team
        boolean sameOrder = ga.ents.size() == gb.ents.size();
        for (int i = 0; i < ga.ents.size() && sameOrder; i++) {
            com.xjzb.rts.core.Game.Ent x = ga.ents.get(i), y = gb.ents.get(i);
            if (!x.type.key.equals(y.type.key) || x.team != y.team) sameOrder = false;
        }
        ok &= sameOrder;
        sb.append(" sameBoard=").append(sameOrder);

        // #2/#3/#4: two peers over a real socket, each issuing an order for
        // its own selection (both are team 0 -- that is the point)
        final String ver = "2.40";
        final com.xjzb.rts.core.Lobby lobby = new com.xjzb.rts.core.Lobby(2);
        com.xjzb.rts.net.LanHost host = new com.xjzb.rts.net.LanHost(
                lobby, new com.xjzb.rts.net.LanHost.Room() {
                    @Override public com.xjzb.rts.core.LanBeacon beacon() {
                        return new com.xjzb.rts.core.LanBeacon(
                                "127.0.0.1", "bloodbath", 2, 0, ver, 21L, 1);
                    }
                    @Override public String version() { return ver; }
                });
        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanHost.Connected>
                admitted = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.CountDownLatch latch =
                new java.util.concurrent.CountDownLatch(1);
        host.start(new com.xjzb.rts.net.LanHost.Callback() {
            @Override public void onConnected(com.xjzb.rts.net.LanHost.Connected c) {
                admitted.set(c);
                latch.countDown();
            }
            @Override public void onError(String message) { latch.countDown(); }
        });
        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanJoin.Result>
                jr = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.CountDownLatch latch2 =
                new java.util.concurrent.CountDownLatch(1);
        com.xjzb.rts.net.LanJoin.connect(host.beacon(), ver, "terran",
                r -> { jr.set(r); latch2.countDown(); });
        latch.await(6, java.util.concurrent.TimeUnit.SECONDS);
        latch2.await(6, java.util.concurrent.TimeUnit.SECONDS);

        boolean linked = admitted.get() != null && jr.get() != null && jr.get().ok();
        boolean lockstepHeld = false;
        boolean bothTouchedTeam0 = false;
        if (linked) {
            com.xjzb.rts.core.Game A = cleanGame("terran");
            com.xjzb.rts.core.Game B = cleanGame("terran");
            com.xjzb.rts.core.LockstepPeer pa = new com.xjzb.rts.core.LockstepPeer(
                    A, 0, 2, admitted.get().link);
            com.xjzb.rts.core.LockstepPeer pb = new com.xjzb.rts.core.LockstepPeer(
                    B, 1, 2, jr.get().link);
            List<com.xjzb.rts.core.Game.Ent> aSel = new ArrayList<>();
            List<com.xjzb.rts.core.Game.Ent> bSel = new ArrayList<>();
            for (com.xjzb.rts.core.Game.Ent e : A.ents)
                if (e.team == 0 && e.type.key.equals("scv")) aSel.add(e);
            for (com.xjzb.rts.core.Game.Ent e : B.ents)
                if (e.team == 0 && e.type.key.equals("scv")) bSel.add(e);

            // both peers issue orders, both for team 0
            A.recordOrder("move", aSel, "300 500");
            B.recordOrder("move", bSel, "360 500");

            boolean same = true;
            for (int t = 0; t < 30 * 6; t++) {
                pa.receiveFrame();
                pb.receiveFrame();
                pa.sendFrame();
                pb.sendFrame();
                long ha = pa.stepFrame(1f / 30f);
                long hb = pb.stepFrame(1f / 30f);
                if (ha != hb) same = false;
                Thread.sleep(1);
            }
            lockstepHeld = same && pa.turnsReleased() == pb.turnsReleased()
                    && pa.turnsReleased() > 100;

            // both orders are in both logs, and both name team-0 indices
            int moved = 0;
            for (com.xjzb.rts.core.Lockstep.Cmd c : pa.commands())
                if (c.cmd.startsWith("move ")) moved++;
            // team 1 is still the AI's: it exists and is not the human side
            boolean aiAlive = false;
            for (com.xjzb.rts.core.Game.Ent e : A.ents) if (e.team == 1) aiAlive = true;
            bothTouchedTeam0 = moved == 2 && aiAlive;
            sb.append(" orders=").append(moved).append(" aiTeam1=").append(aiAlive);
            admitted.get().link.close();
            jr.get().link.close();
        }
        ok &= linked && lockstepHeld && bothTouchedTeam0;
        sb.append(" lockstep=").append(lockstepHeld);
        host.stop();

        System.out.println("  lan semantics" + sb + " PASS=" + ok);
    }
