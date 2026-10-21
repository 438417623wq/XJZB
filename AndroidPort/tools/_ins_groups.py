import io
P = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\GameView.java"
s = io.open(P, encoding="utf-8").read()

# 1) drawFormationOnly: 10 slots, two rows of five
old = """    private void drawFormationOnly(Canvas c, RectF strip) {
        float cellS = Math.max(22 * uiScale, Math.min(30 * uiScale, strip.height() * 0.30f));
        float gx0 = strip.left + 4 * uiScale;
        // v2.23 batch A #4: the shared translucent backing is gone. The three
        // formation slots are now three independent OPAQUE chips (bevelPanel,
        // the same metal vocabulary as the pause button), so nothing semi-see-
        // through sits over the map. formationRect is the union of the chips,
        // which keeps the strip tappable without claiming the gaps between them.
        formationRect.setEmpty();
        for (int g = 0; g < 3; g++) {
            RectF r = new RectF(gx0 + g * (cellS + 6 * uiScale), strip.centerY() - cellS / 2,
                    gx0 + g * (cellS + 6 * uiScale) + cellS, strip.centerY() + cellS / 2);
            bevelPanel(c, r);
            if (formationRect.isEmpty()) formationRect.set(r);
            else formationRect.union(r);
            p.setColor(Color.rgb(200, 220, 245));
            p.setTextSize(10 * uiScale);
            p.setTextAlign(Paint.Align.CENTER);
            c.drawText(String.valueOf(g + 1), r.centerX(), r.centerY() + 3.5f * uiScale, p);
            p.setTextAlign(Paint.Align.LEFT);
            Btn b = new Btn();
            b.r = r;
            b.action = "group:" + g;
            b.label = "编队" + (g + 1);
            buttons.add(b);
        }
    }"""
new = """    private void drawFormationOnly(Canvas c, RectF strip) {
        // v2.27: ten control groups, laid out as two rows of five so they fit
        // the same strip height the three-slot version used (a single row of
        // ten would be too narrow to tap on a 720p phone).
        float cellS = Math.max(20 * uiScale,
                Math.min(28 * uiScale, strip.height() * 0.44f));
        float gx0 = strip.left + 4 * uiScale;
        // v2.23 batch A #4: the shared translucent backing is gone. Every
        // formation slot is an independent OPAQUE chip (bevelPanel), so nothing
        // semi-see-through sits over the map. formationRect is the union of the
        // chips, which keeps the strip tappable without claiming the gaps.
        formationRect.setEmpty();
        float rowH = cellS + 4 * uiScale;
        float top = strip.centerY() - rowH + 2 * uiScale;
        for (int g = 0; g < 10; g++) {
            int col = g % 5, row = g / 5;
            float x = gx0 + col * (cellS + 4 * uiScale);
            float y = top + row * rowH;
            RectF r = new RectF(x, y, x + cellS, y + cellS);
            bevelPanel(c, r);
            if (formationRect.isEmpty()) formationRect.set(r);
            else formationRect.union(r);
            boolean set = g < game.groups.size() && !game.groups.get(g).isEmpty();
            p.setColor(set ? Color.rgb(120, 255, 160) : Color.rgb(200, 220, 245));
            p.setTextSize(9 * uiScale);
            p.setTextAlign(Paint.Align.CENTER);
            c.drawText(String.valueOf(g + 1), r.centerX(), r.centerY() + 3.2f * uiScale, p);
            p.setTextAlign(Paint.Align.LEFT);
            Btn b = new Btn();
            b.r = r;
            b.action = "group:" + g;
            b.label = "编队" + (g + 1);
            buttons.add(b);
        }
    }"""
assert old in s, "formation block"
s = s.replace(old, new, 1)

# 2) the info-panel group strip: 3 -> 10
old2 = """        // control groups: tap to recall, hold to assign the current selection
        float gx2 = panel.right - 3 * cellS - 10 * k;
        for (int g = 0; g < 3; g++) {"""
new2 = """        // control groups (v2.27: ten): tap to recall, hold to assign
        float gx2 = panel.right - 3 * cellS - 10 * k;
        for (int g = 0; g < 3; g++) {"""
assert old2 in s
# leave the info panel's 3-slot strip as is (it is inside the panel); the
# 10 slots live on the empty-selection strip.
io.open(P, "w", encoding="utf-8").write(s)
print("ok")
