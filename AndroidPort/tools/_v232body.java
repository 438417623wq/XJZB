    /**
     * v2.32: framing a byte stream, and agreeing before the match starts.
     *
     *  #1 the line sequence does not depend on how the bytes were chopped --
     *     this is the whole reason the framing exists, and TCP gives no
     *     boundaries at all;
     *  #2 two messages in one feed, and one message split across feeds;
     *  #3 a partial line is withheld until it is complete, not delivered short;
     *  #4 CRLF is tolerated;
     *  #5 a matching handshake is accepted, and a mismatched one is refused
     *     with the offending field NAMED -- "cannot connect" tells a player
     *     nothing, "map mismatch: divide vs hunters" tells them what to fix;
     *  #6 race/difficulty differences are a warning, not a refusal;
     *  #7 end to end: a lockstep turn chopped into 3-byte pieces and fed
     *     through the stream decodes to exactly the same commands as a direct
     *     delivery.
     */
    static void v232Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- #1/#2/#3/#4: framing is independent of the chopping ------------
        // Include a multi-byte UTF-8 command so a split can land mid-character,
        // which is where a naive byte-oriented reader corrupts the text.
        String[] msgs = {"L 0 0 move 1,2,3,4 400 400", "L 0 1",
                         "L 1 0 build 2,5 barracks 中文坐标 640 480", "L 1 1"};
        java.io.ByteArrayOutputStream wire = new java.io.ByteArrayOutputStream();
        for (String m : msgs) wire.write(com.xjzb.rts.core.LockstepStream.encode(m));
        byte[] all = wire.toByteArray();

        int[][] chops = {{1}, {3}, {7}, {all.length}, {2, 5, 1, 9, 4}};
        String first = null;
        boolean chopSame = true;
        for (int[] plan : chops) {
            com.xjzb.rts.core.LockstepStream st = new com.xjzb.rts.core.LockstepStream();
            List<String> got = new ArrayList<>();
            int p = 0, ci = 0;
            while (p < all.length) {
                int n = Math.min(plan[ci % plan.length], all.length - p);
                st.feed(all, p, n);
                p += n;
                ci++;
                got.addAll(st.lines());
            }
            StringBuilder sig = new StringBuilder();
            for (String g : got) sig.append(g).append('|');
            if (first == null) first = sig.toString();
            else if (!sig.toString().equals(first)) chopSame = false;
        }
        boolean exact = first != null && first.equals(
                msgs[0] + "|" + msgs[1] + "|" + msgs[2] + "|" + msgs[3] + "|");
        ok &= chopSame && exact;
        sb.append(" framing=").append(chopSame && exact);

        // ---- #3: a partial line is withheld --------------------------------
        com.xjzb.rts.core.LockstepStream half = new com.xjzb.rts.core.LockstepStream();
        half.feed(com.xjzb.rts.core.LockstepStream.encode("L 2 0 move 0 5 5"));
        boolean gotFull = half.lines().size() == 1 && !half.hasPartial();
        com.xjzb.rts.core.LockstepStream part = new com.xjzb.rts.core.LockstepStream();
        part.feed("L 3 0 mov".getBytes("UTF-8"));
        boolean heldBack = part.lines().isEmpty() && part.hasPartial();
        part.feed("e 0 9 9\n".getBytes("UTF-8"));
        List<String> fin = part.lines();
        boolean completed = fin.size() == 1 && fin.get(0).equals("L 3 0 move 0 9 9");
        ok &= gotFull && heldBack && completed;
        sb.append(" partial=").append(gotFull && heldBack && completed);

        // ---- #4: CRLF ------------------------------------------------------
        com.xjzb.rts.core.LockstepStream crlf = new com.xjzb.rts.core.LockstepStream();
        crlf.feed("L 4 0 move 0 1 1\r\nL 4 1\r\n".getBytes("UTF-8"));
        List<String> cl = crlf.lines();
        boolean crOk = cl.size() == 2 && cl.get(0).equals("L 4 0 move 0 1 1")
                && cl.get(1).equals("L 4 1");
        ok &= crOk;
        sb.append(" crlf=").append(crOk);

        // ---- #5/#6: the handshake ------------------------------------------
        com.xjzb.rts.core.Handshake host = new com.xjzb.rts.core.Handshake(
                "2.32", "divide", 2, 777L, "terran", 1);
        com.xjzb.rts.core.Handshake rt = com.xjzb.rts.core.Handshake.decode(host.encode());
        boolean rtOk = rt != null && rt.version.equals("2.32") && rt.map.equals("divide")
                && rt.players == 2 && rt.seed == 777L && rt.race.equals("terran")
                && rt.difficulty == 1;
        boolean acceptOk = host.reject(rt) == null && host.warn(rt) == null;
        ok &= rtOk && acceptOk;
        sb.append(" handshake=").append(rtOk && acceptOk);

        // each fatal field, changed one at a time, must be refused BY NAME
        String[] fatals = {
            new com.xjzb.rts.core.Handshake("2.31", "divide", 2, 777L, "terran", 1).encode(),
            new com.xjzb.rts.core.Handshake("2.32", "hunters", 2, 777L, "terran", 1).encode(),
            new com.xjzb.rts.core.Handshake("2.32", "divide", 3, 777L, "terran", 1).encode(),
            new com.xjzb.rts.core.Handshake("2.32", "divide", 2, 999L, "terran", 1).encode(),
        };
        String[] wantWord = {"版本", "地图", "人数", "种子"};
        boolean allRefused = true;
        String seen = "";
        for (int i = 0; i < fatals.length; i++) {
            String why = host.reject(com.xjzb.rts.core.Handshake.decode(fatals[i]));
            if (why == null || !why.contains(wantWord[i])) allRefused = false;
            seen += " " + why;
        }
        ok &= allRefused;
        sb.append(" refuseByName=").append(allRefused);

        // a differing race or difficulty is only a warning
        com.xjzb.rts.core.Handshake soft = new com.xjzb.rts.core.Handshake(
                "2.32", "divide", 2, 777L, "zerg", 2);
        boolean softOk = host.reject(soft) == null && host.warn(soft) != null;
        // a malformed handshake is refused rather than thrown
        boolean badOk = host.reject(null) != null
                && com.xjzb.rts.core.Handshake.decode("H version") != null
                && com.xjzb.rts.core.Handshake.decode("garbage") == null
                && com.xjzb.rts.core.Handshake.decode("H players x") == null;
        ok &= softOk && badOk;
        sb.append(" soft=").append(softOk).append(" bad=").append(badOk);

        // ---- #7: a whole turn through 3-byte framing -----------------------
        // One peer's real command goes onto a byte stream in 3-byte pieces and
        // must come out the far side as the identical command.
        com.xjzb.rts.core.Game ga = cleanGame("terran");
        List<com.xjzb.rts.core.Game.Ent> scvs = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : ga.ents)
            if (e.team == 0 && e.type.key.equals("scv")) scvs.add(e);
        String cmd = ga.commandFor("move", scvs, "512 384");
        byte[] framed = com.xjzb.rts.core.LockstepStream.encode(
                com.xjzb.rts.core.Lockstep.encode(0, 0, cmd));
        com.xjzb.rts.core.LockstepStream st = new com.xjzb.rts.core.LockstepStream();
        List<String> out = new ArrayList<>();
        for (int p = 0; p < framed.length; p += 3) {
            st.feed(framed, p, Math.min(3, framed.length - p));
            out.addAll(st.lines());
        }
        com.xjzb.rts.core.Lockstep.Cmd c = out.size() == 1
                ? com.xjzb.rts.core.Lockstep.decode(out.get(0)) : null;
        boolean e2e = c != null && c.turn == 0 && c.player == 0 && c.cmd.equals(cmd);
        ok &= e2e;
        sb.append(" endToEnd=").append(e2e);

        System.out.println("  framing/handshake" + sb + " PASS=" + ok);
    }
