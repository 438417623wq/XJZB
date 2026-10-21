import io
P = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
s = io.open(P, encoding="utf-8").read()
old = """        // one command centre + one depot at tier 0 gives 18
        pg.spawn("cc", 0, 400, 400, true);
        pg.spawn("depot", 0, 460, 400, true);
        pg.update(1 / 30f);
        boolean cap40 = pg.supplyCap == 18;
        // buy the tier: the same two buildings now feed 25 + 20 = 45
        pg.mineralsPlayer = 5000;
        String why = pg.raiseSupplyCap();
        pg.update(1 / 30f);
        boolean bought = why == null && pg.capTier == 1;
        boolean cap100 = pg.supplyCap == 45;"""
new = """        // cleanGame keeps the player's starting base, so the absolute cap is
        // not a fixed number -- assert the DELTA a new depot makes instead.
        pg.update(1 / 30f);
        int capBefore = pg.supplyCap;
        pg.spawn("depot", 0, 460, 400, true);
        pg.update(1 / 30f);
        boolean depot8 = pg.supplyCap - capBefore == 8;
        // buy the tier: the same buildings now feed 2.5x (a depot gives 20)
        pg.mineralsPlayer = 5000;
        int capAtTier0 = pg.supplyCap;
        String why = pg.raiseSupplyCap();
        pg.update(1 / 30f);
        boolean bought = why == null && pg.capTier == 1;
        boolean scaled = pg.supplyCap == (int) (capAtTier0 * 2.5f)
                && pg.supplyCap - capAtTier0 == 12;
        boolean cap40 = depot8 && scaled;"""
assert old in s, "pop block"
s = s.replace(old, new, 1)
s = s.replace("""        sb.append(" tier0=").append(tier0).append(" cap18=").append(cap40)""",
              """        sb.append(" tier0=").append(tier0).append(" depot8+scale=").append(cap40)""", 1)
s = s.replace("""          .append(" bought=").append(bought).append(" cap45=").append(cap100)""",
              """          .append(" bought=").append(bought).append(" scaled=").append(scaled)""", 1)
io.open(P, "w", encoding="utf-8").write(s)
print("ok")
