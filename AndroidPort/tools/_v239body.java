    /**
     * v2.39: the host can actually start a match.
     *
     * This is the bug that made the whole feature unreachable: LanHost seated
     * the host but never marked it ready, and the joiner filled only its own
     * seat. So the host's roster read "1/2, host not ready" and the joiner's
     * read "1/2", and canStart() was false on BOTH phones forever -- the start
     * button could never light up. Every earlier assertion passed because they
     * all filled and readied the seats by hand; only walking the real host/join
     * flow end to end exposes it.
     *
     *  #1 hosting seats the host at 0 AND marks it ready;
     *  #2 a joined guest's local view has both seats filled and ready, so the
     *     start button is live on the joiner too;
     *  #3 end to end over real sockets: host and joiner both reach canStart(),
     *     and the host can start.
     */
    static void v239Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- #1: hosting readies the host --------------------------------
        com.xjzb.rts.core.Lobby l1 = new com.xjzb.rts.core.Lobby(2);
        int seat = l1.hostSeat("房主");
        boolean hostReady = seat == 0 && l1.slots.get(0).connected
                && l1.slots.get(0).ready && l1.connectedCount() == 1;
        // and alone it still cannot start (a one-player match is not a match)
        boolean aloneNo = !l1.canStart();
        ok &= hostReady && aloneNo;
        sb.append(" hostSeat=").append(hostReady).append(" aloneNo=").append(aloneNo);

        // ---- #2: the guest's local view is 2/2 ---------------------------
        com.xjzb.rts.core.Lobby l2 = new com.xjzb.rts.core.Lobby(2);
        l2.joinAsGuest("房主", "我");
        boolean guestView = l2.connectedCount() == 2
                && l2.slots.get(0).ready && l2.slots.get(1).ready
                && l2.canStart();
        ok &= guestView;
        sb.append(" guestView=").append(guestView);

        // ---- #3: the real host/join flow reaches canStart on both sides ---
        final String ver = "2.39";
        final com.xjzb.rts.core.Lobby hostLobby = new com.xjzb.rts.core.Lobby(2);
        com.xjzb.rts.net.LanHost host = new com.xjzb.rts.net.LanHost(
                hostLobby, new com.xjzb.rts.net.LanHost.Room() {
                    @Override public com.xjzb.rts.core.LanBeacon beacon() {
                        return new com.xjzb.rts.core.LanBeacon(
                                "127.0.0.1", "bloodbath", 2, 0, ver, 11L, 1);
                    }
                    @Override public String version() { return ver; }
                });
        final java.util.concurrent.CountDownLatch admitted =
                new java.util.concurrent.CountDownLatch(1);
        host.start(new com.xjzb.rts.net.LanHost.Callback() {
            @Override public void onConnected(com.xjzb.rts.net.LanHost.Connected c) {
                admitted.countDown();
            }
            @Override public void onError(String message) { admitted.countDown(); }
        });
        // the host's own roster after the joiner is admitted: both seats ready
        final com.xjzb.rts.core.Lobby guestLobby = new com.xjzb.rts.core.Lobby(2);
        final java.util.concurrent.CountDownLatch joined =
                new java.util.concurrent.CountDownLatch(1);
        com.xjzb.rts.net.LanJoin.connect(host.beacon(), ver, "terran", r -> {
            if (r.ok()) guestLobby.joinAsGuest("房主", "我");
            joined.countDown();
        });
        admitted.await(6, java.util.concurrent.TimeUnit.SECONDS);
        joined.await(6, java.util.concurrent.TimeUnit.SECONDS);
        // the host's roster: the guest arrives NOT ready, so the host must still
        // be able to start once it readies them -- assert the host's own half is
        // satisfied and the only thing missing is the guest's confirmation.
        boolean hostSide = hostLobby.connectedCount() == 2
                && hostLobby.slots.get(0).ready
                && hostLobby.slots.get(1).connected
                && hostLobby.blockedReason() != null
                && hostLobby.blockedReason().contains("未准备");
        hostLobby.setReady(1, true);
        boolean hostCanStart = hostLobby.canStart() && hostLobby.start();
        boolean guestCanStart = guestLobby.canStart() && guestLobby.start();
        ok &= hostSide && hostCanStart && guestCanStart;
        sb.append(" hostSide=").append(hostSide)
          .append(" hostStart=").append(hostCanStart)
          .append(" guestStart=").append(guestCanStart);
        host.stop();

        System.out.println("  lobby start" + sb + " PASS=" + ok);
    }
