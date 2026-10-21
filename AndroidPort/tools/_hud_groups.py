import io
P = r"F:\KF\XJZB\AndroidPort\tools\HudPreview.java"
s = io.open(P, encoding="utf-8").read()
old = """            // v2.23 batch A: nothing selected draws only three independent
            // OPAQUE formation chips -- no translucent backing (mirrors
            // GameView.drawFormationOnly).
            float cellS = Math.max(22 * uiScale,
                    Math.min(30 * uiScale, info.height * 0.30f));
            float gx0 = info.x + 4 * uiScale;
            for (int gidx = 0; gidx < 3; gidx++) {
                Rectangle gr = new Rectangle((int) (gx0 + gidx * (cellS + 6 * uiScale)),
                        (int) (info.y + info.height / 2f - cellS / 2),
                        (int) cellS, (int) cellS);
                bevelPanel(g, gr, uiScale);
                g.setColor(new Color(200, 220, 245));
                g.setFont(new Font("SansSerif", Font.PLAIN, (int) (10 * uiScale)));
                FontMetrics gfm = g.getFontMetrics();
                String gs = String.valueOf(gidx + 1);
                g.drawString(gs, gr.x + (gr.width - gfm.stringWidth(gs)) / 2,
                        gr.y + (gr.height + gfm.getAscent() - gfm.getDescent()) / 2);
            }
            System.out.printf("   [empty] 3 opaque formation chips from x=%d (rest of strip handed to map)%n",
                    (int) gx0);"""
new = """            // v2.23 batch A: nothing selected draws only independent OPAQUE
            // formation chips -- no translucent backing. v2.27: ten of them,
            // two rows of five, mirroring GameView.drawFormationOnly.
            float cellS = Math.max(20 * uiScale,
                    Math.min(28 * uiScale, info.height * 0.44f));
            float gx0 = info.x + 4 * uiScale;
            float rowH = cellS + 4 * uiScale;
            float top = info.y + info.height / 2f - rowH + 2 * uiScale;
            for (int gidx = 0; gidx < 10; gidx++) {
                int col = gidx % 5, row = gidx / 5;
                Rectangle gr = new Rectangle((int) (gx0 + col * (cellS + 4 * uiScale)),
                        (int) (top + row * rowH), (int) cellS, (int) cellS);
                bevelPanel(g, gr, uiScale);
                g.setColor(new Color(200, 220, 245));
                g.setFont(new Font("SansSerif", Font.PLAIN, (int) (9 * uiScale)));
                FontMetrics gfm = g.getFontMetrics();
                String gs = String.valueOf(gidx + 1);
                g.drawString(gs, gr.x + (gr.width - gfm.stringWidth(gs)) / 2,
                        gr.y + (gr.height + gfm.getAscent() - gfm.getDescent()) / 2);
            }
            System.out.printf("   [empty] 10 opaque formation chips from x=%d (rest of strip handed to map)%n",
                    (int) gx0);"""
assert old in s, "formation mirror"
s = s.replace(old, new, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("ok")
