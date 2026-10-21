    /**
     * v2.38: a departed peer must END the match, not freeze it.
     *
     * v2.34 asserted the timeout rules and v2.37 asserted the socket layer, but
     * neither made the app actually DO anything with them: nothing called
     * forfeit(), so on a real device a peer who killed the app still left the
     * survivor on a turn that could never complete. Tested logic that nothing
     * invokes is not a feature, and this is the assertion that keeps the two
     * halves joined.
     *
     *  #1 the immediate signal: a CLOSED wire declares the peer gone on the
     *     first check, without waiting out the ten-second timer -- the transport
     *     already knows, so making the player wait would be pure theatre;
     *  #2 the slow signal still works: a link that stays open but silent is
     *     declared gone at exactly the limit;
     *  #3 neither fires while the peer is still answering;
     *  #4 the survivor ends up in a state where the match can be scored (its own
     *     turn keeps advancing after the declaration);
     *  #5 end to end over a real socket: the peer process is closed, and the
     *     survivor's checkForfeit() names it immediately.
     */
    static void v238Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- #1: a closed wire is immediate --------------------------------
        // A link that reports closed, with a session that has one silent peer.
        final com.xjzb.rts.core.LockstepLink.Link deadLink =
                new com.xjzb.rts.core.LockstepLink.Link() {
                    @Override public void send(String line) { }
                    @Override public java.util.List<String> poll() {
                        return new java.util.ArrayList<>();
                    }
                    @Override public boolean isClosed() { return true; }
                };
        com.xjzb.rts.core.Game g1 = cleanGame("terran");
        com.xjzb.rts.core.LockstepPeer p1 = new com.xjzb.rts.core.LockstepPeer(
                g1, 0, 2, deadLink);
        p1.session.submit(0, "");
        int gone1 = p1.checkForfeit(com.xjzb.rts.core.Lockstep.STALL_LIMIT);
        boolean immediate = gone1 == 1 && p1.session.forfeitLoser == 1
                && p1.session.forfeitWinner == 0 && p1.session.stallTurns == 0;
        ok &= immediate;
        sb.append(" closedImmediate=").append(immediate).append("@").append(gone1);

        // ---- #2: a silent-but-open link waits for the limit ----------------
        com.xjzb.rts.core.LockstepLink.Link openLink =
                new com.xjzb.rts.core.LockstepLink.Link() {
                    @Override public void send(String line) { }
                    @Override public java.util.List<String> poll() {
                        return new java.util.ArrayList<>();
                    }
                };
        com.xjzb.rts.core.Game g2 = cleanGame("terran");
        com.xjzb.rts.core.LockstepPeer p2 = new com.xjzb.rts.core.LockstepPeer(
                g2, 0, 2, openLink);
        int limit = com.xjzb.rts.core.Lockstep.STALL_LIMIT;
        boolean early = true, onTime = false;
        for (int t = 0; t < limit + 2; t++) {
            p2.session.submit(0, "");
            g2.update(1f / 30f);          // Game.update notes the stall
            int who = p2.checkForfeit(limit);
            if (t < limit - 1 && who >= 0) early = false;
            if (t == limit - 1 && who == 1) onTime = true;
        }
        ok &= early && onTime;
        sb.append(" silentTimeout=").append(early && onTime);

        // ---- #3: an answering peer is never declared gone ------------------
        com.xjzb.rts.core.LockstepLink.Link liveLink =
                new com.xjzb.rts.core.LockstepLink.Link() {
                    @Override public void send(String line) { }
                    @Override public java.util.List<String> poll() {
                        return new java.util.ArrayList<>();
                    }
                };
        com.xjzb.rts.core.Game g3 = cleanGame("terran");
        com.xjzb.rts.core.LockstepPeer p3 = new com.xjzb.rts.core.LockstepPeer(
                g3, 0, 2, liveLink);
        boolean neverGone = true;
        for (int t = 0; t < limit * 3; t++) {
            p3.receiveFrame();
            p3.session.submit(0, "");
            p3.session.submit(1, "");      // the peer keeps answering
            p3.stepFrame(1f / 30f);
            if (p3.checkForfeit(limit) >= 0) neverGone = false;
        }
        boolean advanced = p3.turnsReleased() > limit;   // it kept playing
        ok &= neverGone && advanced;
        sb.append(" aliveOk=").append(neverGone).append(" turns=")
          .append(p3.turnsReleased());

        // ---- #4: the survivor can keep advancing after the declaration -----
        com.xjzb.rts.core.Game g4 = cleanGame("terran");
        com.xjzb.rts.core.LockstepPeer p4 = new com.xjzb.rts.core.LockstepPeer(
                g4, 0, 2, deadLink);
        p4.session.submit(0, "");
        p4.checkForfeit(limit);
        int before = p4.turnsReleased();
        for (int t = 0; t < 60; t++) {
            p4.receiveFrame();
            p4.sendFrame();
            p4.stepFrame(1f / 30f);
        }
        boolean scored = p4.turnsReleased() > before;
        ok &= scored;
        sb.append(" afterForfeitTurns=").append(p4.turnsReleased() - before);

        // ---- #5: end to end, the peer process really goes away --------------
        final com.xjzb.rts.core.Lobby lobby5 = new com.xjzb.rts.core.Lobby(4);
        final String ver = "2.38";
        com.xjzb.rts.net.LanHost host5 = new com.xjzb.rts.net.LanHost(
                lobby5, new com.xjzb.rts.net.LanHost.Room() {
                    @Override public com.xjzb.rts.core.LanBeacon beacon() {
                        return new com.xjzb.rts.core.LanBeacon(
                                "127.0.0.1", "bloodbath", 2, 0, ver, 7L, 1);
                    }
                    @Override public String version() { return ver; }
                });
        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanHost.Connected>
                admitted5 = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.CountDownLatch admittedLatch =
                new java.util.concurrent.CountDownLatch(1);
        host5.start(new com.xjzb.rts.net.LanHost.Callback() {
            @Override public void onConnected(com.xjzb.rts.net.LanHost.Connected c) {
                admitted5.set(c);
                admittedLatch.countDown();
            }
            @Override public void onError(String message) { admittedLatch.countDown(); }
        });
        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanJoin.Result>
                jr5 = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.CountDownLatch joinLatch =
                new java.util.concurrent.CountDownLatch(1);
        com.xjzb.rts.net.LanJoin.connect(host5.beacon(), ver, "terran",
                r -> { jr5.set(r); joinLatch.countDown(); });
        admittedLatch.await(6, java.util.concurrent.TimeUnit.SECONDS);
        joinLatch.await(6, java.util.concurrent.TimeUnit.SECONDS);

        boolean e2e = false;
        if (admitted5.get() != null && jr5.get() != null && jr5.get().ok()) {
            com.xjzb.rts.core.Game gh = cleanGame("terran");
            com.xjzb.rts.core.LockstepPeer ph = new com.xjzb.rts.core.LockstepPeer(
                    gh, 0, 2, admitted5.get().link);
            ph.session.submit(0, "");
            gh.update(1f / 30f);
            boolean beforeKill = ph.checkForfeit(limit) < 0;   // peer still there
            // the joiner's process goes away
            jr5.get().link.close();
            int waited = 0;
            int who = -1;
            while (waited < 60 && (who = ph.checkForfeit(limit)) < 0) {
                ph.session.submit(0, "");
                gh.update(1f / 30f);
                Thread.sleep(20);
                waited++;
            }
            // the closed socket must be noticed well inside the 10 s timer
            e2e = beforeKill && who == 1 && waited < limit;
            sb.append(" e2eDrop=").append(who).append(" afterFrames=").append(waited);
        }
        ok &= e2e;
        host5.stop();

        System.out.println("  peer departure" + sb + " PASS=" + ok);
    }
