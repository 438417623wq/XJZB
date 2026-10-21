    /**
     * v2.33: finding a room, and agreeing to start one.
     *
     *  #1 a beacon round-trips, and the beacon's own fields become the
     *     handshake both peers will check;
     *  #2 anything that is not a beacon of this build is IGNORED, not thrown:
     *     the broadcast domain carries other rooms, other versions and
     *     unrelated traffic, and a listener that errored on any of it would
     *     drop the lobby whenever a colleague's phone joined the wifi;
     *  #3 a beacon from another version is found but not joinable;
     *  #4 a joiner takes the lowest free seat;
     *  #5 a seat freed by a departure is the next one taken -- without this the
     *     room reads "4/4 connected" while the start button stays dead forever;
     *  #6 the start gate needs everyone connected AND ready AND at least two;
     *  #7 a match starts at most once, so a double tap cannot launch two;
     *  #8 after the match starts a lost peer no longer frees a seat (that case
     *     belongs to Lockstep's ready-gate, which freezes both machines on the
     *     same turn instead of silently changing the roster);
     *  #9 the lobby's own numbers, run through Handshake on both sides, are
     *     mutually accepted -- the last join between this layer and v2.32's.
     */
    static void v233Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- #1: beacon round-trip, and beacon -> handshake ----------------
        com.xjzb.rts.core.LanBeacon host = new com.xjzb.rts.core.LanBeacon(
                "房主的小米", "divide", 2, 41234, "2.33", 888L, 1);
        com.xjzb.rts.core.LanBeacon got =
                com.xjzb.rts.core.LanBeacon.decode(host.encode());
        boolean rt = got != null && got.host.equals("房主的小米") && got.map.equals("divide")
                && got.players == 2 && got.port == 41234 && got.version.equals("2.33")
                && got.seed == 888L && got.difficulty == 1;
        ok &= rt;
        sb.append(" beacon=").append(rt);

        // ---- #2: garbage is ignored, never thrown --------------------------
        String[] junk = {
            null, "", "hello", "XJZB-LAN-1", "XJZB-LAN-1 host",
            "XJZB-LAN-1 host x map y players z port 1 version 2.33 seed 1 difficulty 1",
            "XJZB-LAN-2 host x map y players 2 port 1 version 2.33 seed 1 difficulty 1",
            "XJZB-LAN-1 map divide port 41234 version 2.33 seed 1 difficulty 1",
        };
        boolean ignored = true;
        for (String s : junk) if (com.xjzb.rts.core.LanBeacon.decode(s) != null) ignored = false;
        ok &= ignored;
        sb.append(" ignoreJunk=").append(ignored);

        // ---- #3: another build's room is visible but not joinable ----------
        com.xjzb.rts.core.LanBeacon old = com.xjzb.rts.core.LanBeacon.decode(
                new com.xjzb.rts.core.LanBeacon("隔壁", "hunters", 2, 4000,
                        "2.31", 5L, 1).encode());
        boolean versionGate = old != null && !old.joinable("2.33")
                && host.joinable("2.33");
        ok &= versionGate;
        sb.append(" versionGate=").append(versionGate);

        // ---- #4: a joiner takes the lowest free seat -----------------------
        com.xjzb.rts.core.Lobby lob = new com.xjzb.rts.core.Lobby(4);
        int a = lob.join("A"), b = lob.join("B"), c = lob.join("C");
        boolean seated = a == 0 && b == 1 && c == 2 && lob.connectedCount() == 3;
        ok &= seated;
        sb.append(" seat=").append(seated);

        // ---- #5: a freed seat is reused ------------------------------------
        lob.onPeerLost(1);
        int d = lob.join("D");
        boolean reuse = d == 1 && lob.connectedCount() == 3
                && lob.slots.get(1).name.equals("D") && !lob.slots.get(1).ready;
        ok &= reuse;
        sb.append(" reuseSeat=").append(reuse);

        // ---- #6: the start gate --------------------------------------------
        boolean notReady = !lob.canStart();
        lob.setReady(0, true);
        lob.setReady(1, true);
        boolean stillNot = !lob.canStart();          // C has not readied
        lob.setReady(2, true);
        boolean ready = lob.canStart();
        String why = new com.xjzb.rts.core.Lobby(4).blockedReason();
        boolean explains = why != null && why.contains("至少");
        ok &= notReady && stillNot && ready && explains;
        sb.append(" gate=").append(notReady && stillNot && ready);

        // ---- #7: start succeeds at most once -------------------------------
        boolean first = lob.start();
        boolean second = !lob.start();
        ok &= first && second;
        sb.append(" onceOnly=").append(first && second);

        // ---- #8: after the start, a loss does not free a seat --------------
        int before = lob.connectedCount();
        lob.onPeerLost(0);
        boolean frozen = lob.connectedCount() == before;
        ok &= frozen;
        sb.append(" postStartFrozen=").append(frozen);

        // ---- #9: the lobby's numbers are a valid handshake pair ------------
        com.xjzb.rts.core.Handshake hh = host.handshake("terran");
        com.xjzb.rts.core.Handshake cc = com.xjzb.rts.core.LanBeacon
                .decode(host.encode()).handshake("terran");
        boolean linked = hh.reject(cc) == null && hh.version.equals("2.33")
                && hh.players == 2 && hh.seed == 888L;
        ok &= linked;
        sb.append(" handshakeLinked=").append(linked);

        System.out.println("  lobby/discovery" + sb + " PASS=" + ok);
    }
