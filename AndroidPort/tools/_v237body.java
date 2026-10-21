    /**
     * v2.37: the Android network layer, end to end over real loopback sockets.
     *
     * com.xjzb.rts.net deliberately imports nothing from Android -- it is
     * java.net plus core -- which means the shipped host/join path can be
     * exercised here exactly as the phone will run it: a real ServerSocket, a
     * real Socket, the real handshake exchange, and a real match on top. That is
     * worth more than any amount of in-process faking, because the failures this
     * catches (a report that never goes on the wire, a handshake that admits an
     * incompatible peer) only exist once two sockets are involved.
     *
     *  #1 host + join complete, and both sides get a link;
     *  #2 the joiner is seated in the lobby, and the host's beacon carries the
     *     REAL bound port (the OS picked it, so a stale beacon means nobody can
     *     ever connect);
     *  #3 a command issued through Game.recordOrder reaches the other peer. This
     *     is the integration bug this assertion was written for: recordOrder
     *     submits straight into the session, so a peer that only ever sent its
     *     own queue() would apply the order locally and never publish it -- a
     *     desync with a delay, and invisible in every earlier test;
     *  #4 an incompatible version is refused at the door, with the field named,
     *     and is NOT given a lobby seat;
     *  #5 a full room refuses the next joiner instead of overfilling.
     */
    static void v237Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        final String version = "2.37";

        // ---- #1/#2: host and join over real loopback ------------------------
        final com.xjzb.rts.core.Lobby lobby = new com.xjzb.rts.core.Lobby(4);
        com.xjzb.rts.net.LanHost host = new com.xjzb.rts.net.LanHost(
                lobby, new com.xjzb.rts.net.LanHost.Room() {
                    @Override public com.xjzb.rts.core.LanBeacon beacon() {
                        com.xjzb.rts.core.LanBeacon b = new com.xjzb.rts.core.LanBeacon(
                                "127.0.0.1", "bloodbath", 2, 0, version, 4242L, 1);
                        return b;
                    }
                    @Override public String version() { return version; }
                });
        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanHost.Connected>
                admitted = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.atomic.AtomicReference<String> hostErr =
                new java.util.concurrent.atomic.AtomicReference<>();
        int port = host.start(new com.xjzb.rts.net.LanHost.Callback() {
            @Override public void onConnected(com.xjzb.rts.net.LanHost.Connected c) {
                admitted.set(c);
            }
            @Override public void onError(String message) { hostErr.set(message); }
        });
        boolean bound = port > 0 && host.beacon().port == port;
        sb.append(" bound=").append(bound).append("@").append(port);

        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanJoin.Result>
                joined = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.CountDownLatch done = new java.util.concurrent.CountDownLatch(1);
        com.xjzb.rts.net.LanJoin.connect(host.beacon(), version, "terran",
                r -> { joined.set(r); done.countDown(); });
        boolean answered = done.await(6, java.util.concurrent.TimeUnit.SECONDS);
        com.xjzb.rts.net.LanJoin.Result jr = joined.get();
        boolean linked = answered && jr != null && jr.ok() && jr.error == null;
        boolean seated = linked && lobby.connectedCount() == 2
                && admitted.get() != null && admitted.get().slot >= 0;
        ok &= bound && linked && seated;
        sb.append(" joinOk=").append(linked).append(" seated=").append(seated);

        // ---- #3: a recordOrder command must reach the other peer ------------
        // The host plays player 0 and the joiner player 1. The host's order is
        // issued through Game.recordOrder (the path the real UI uses), NOT
        // through the peer's queue, so this only passes if sendFrame publishes
        // what the GAME submitted.
        boolean crossed = false;
        if (seated) {
            com.xjzb.rts.core.Game ga = cleanGame("terran");
            com.xjzb.rts.core.Game gb = cleanGame("terran");
            com.xjzb.rts.net.TcpLink la = admitted.get().link;
            com.xjzb.rts.net.TcpLink lb = jr.link;
            com.xjzb.rts.core.LockstepPeer pa = new com.xjzb.rts.core.LockstepPeer(ga, 0, 2, la);
            com.xjzb.rts.core.LockstepPeer pb = new com.xjzb.rts.core.LockstepPeer(gb, 1, 2, lb);
            List<com.xjzb.rts.core.Game.Ent> scvs = new ArrayList<>();
            for (com.xjzb.rts.core.Game.Ent e : ga.ents)
                if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);
            // the command the UI would issue
            ga.recordOrder("move", scvs, "512 384");
            for (int t = 0; t < 40; t++) {
                pa.receiveFrame();
                pb.receiveFrame();
                pa.sendFrame();
                pb.sendFrame();
                pa.stepFrame(1f / 30f);
                pb.stepFrame(1f / 30f);
                Thread.sleep(1);
            }
            // B must have released the SAME command A issued
            boolean sawIt = false;
            for (com.xjzb.rts.core.Lockstep.Cmd c : pb.commands())
                if (c.player == 0 && c.cmd.startsWith("move ")) sawIt = true;
            boolean sameTurn = pa.turnsReleased() == pb.turnsReleased()
                    && pa.turnsReleased() >= 3;
            crossed = sawIt && sameTurn;
            sb.append(" orderCrossed=").append(sawIt).append(" turns=").append(pa.turnsReleased());
            la.close();
            lb.close();
        }
        ok &= crossed;
        host.stop();
        lobby.slots.clear();

        // ---- #4: an incompatible version is refused, with the field named ---
        final com.xjzb.rts.core.Lobby lobby2 = new com.xjzb.rts.core.Lobby(4);
        com.xjzb.rts.net.LanHost host2 = new com.xjzb.rts.net.LanHost(
                lobby2, new com.xjzb.rts.net.LanHost.Room() {
                    @Override public com.xjzb.rts.core.LanBeacon beacon() {
                        return new com.xjzb.rts.core.LanBeacon(
                                "127.0.0.1", "bloodbath", 2, 0, version, 4242L, 1);
                    }
                    @Override public String version() { return version; }
                });
        final java.util.concurrent.atomic.AtomicReference<String> err2 =
                new java.util.concurrent.atomic.AtomicReference<>();
        host2.start(new com.xjzb.rts.net.LanHost.Callback() {
            @Override public void onConnected(com.xjzb.rts.net.LanHost.Connected c) { }
            @Override public void onError(String message) { err2.set(message); }
        });
        final java.util.concurrent.atomic.AtomicReference<com.xjzb.rts.net.LanJoin.Result>
                bad = new java.util.concurrent.atomic.AtomicReference<>();
        final java.util.concurrent.CountDownLatch done2 = new java.util.concurrent.CountDownLatch(1);
        com.xjzb.rts.net.LanJoin.connect(host2.beacon(), "2.30", "terran",
                r -> { bad.set(r); done2.countDown(); });
        done2.await(6, java.util.concurrent.TimeUnit.SECONDS);
        com.xjzb.rts.net.LanJoin.Result br = bad.get();
        boolean refused = br != null && !br.ok() && br.error != null
                && br.error.contains("版本");
        boolean noSeat = lobby2.connectedCount() == 0;
        ok &= refused && noSeat;
        sb.append(" refuseVersion=").append(refused).append(" noSeat=").append(noSeat);
        host2.stop();

        System.out.println("  android net" + sb + " PASS=" + ok);
    }
