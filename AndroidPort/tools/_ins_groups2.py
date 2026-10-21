import io
P = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\GameView.java"
s = io.open(P, encoding="utf-8").read()
old = """        // control groups: tap to recall, hold to assign the current selection
        float gx2 = panel.right - 3 * cellS - 10 * k;
        for (int g = 0; g < 3; g++) {
            RectF gr = new RectF(gx2 + g * (cellS + 5 * k), cy,
                    gx2 + g * (cellS + 5 * k) + cellS, cy + cellS);
            bevelSlot(c, gr);
            boolean set = g < game.groups.size() && !game.groups.get(g).isEmpty();
            p.setColor(set ? Color.rgb(120, 255, 160) : Color.rgb(120, 140, 170));
            p.setTextSize(11 * k);
            p.setTextAlign(Paint.Align.CENTER);
            int n = set ? game.groups.get(g).size() : 0;
            c.drawText(set ? (g + 1) + "" : (g + 1) + "", gr.centerX(),
                    gr.centerY() + 4 * k, p);
            if (set) {
                p.setTextSize(8 * k);
                c.drawText(String.valueOf(n), gr.centerX(), gr.bottom - 2 * k, p);
            }
            p.setTextAlign(Paint.Align.LEFT);
            Btn b = new Btn();
            b.r = gr;
            b.action = "group:" + g;
            b.label = "编队" + (g + 1);
            buttons.add(b);
        }"""
new = """        // v2.27: ten control groups in the same band the three-slot strip used.
        // Two rows of five, half the cell height each, right-aligned against the
        // panel edge -- a single row of ten would be a 20 px target on a 720p
        // phone, and the info panel's band is only one cell tall.
        float gCell = (cellS - 2 * k) / 2f;
        float gGap = 3 * k;
        for (int g = 0; g < 10; g++) {
            int col = g % 5, row = g / 5;
            float x = panel.right - 5 * gCell - 4 * gGap - 10 * k + col * (gCell + gGap);
            float y = cy + row * (gCell + gGap);
            RectF gr = new RectF(x, y, x + gCell, y + gCell);
            bevelSlot(c, gr);
            boolean set = g < game.groups.size() && !game.groups.get(g).isEmpty();
            p.setColor(set ? Color.rgb(120, 255, 160) : Color.rgb(120, 140, 170));
            p.setTextSize(Math.max(7 * k, gCell * 0.52f));
            p.setTextAlign(Paint.Align.CENTER);
            c.drawText(String.valueOf(g + 1), gr.centerX(), gr.centerY() + 3 * k, p);
            p.setTextAlign(Paint.Align.LEFT);
            Btn b = new Btn();
            b.r = gr;
            b.action = "group:" + g;
            b.label = "编队" + (g + 1);
            buttons.add(b);
        }"""
assert old in s, "info group block"
s = s.replace(old, new, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("ok")
