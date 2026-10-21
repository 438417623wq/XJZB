import io
P = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\GameView.java"
s = io.open(P, encoding="utf-8").read()
anchor = """                } else if (b.action.equals("load")) {
                    // v2.23 batch A: arm a friendly-unit pick."""
assert anchor in s, "anchor missing"
ins = """                } else if (b.action.equals("merge")) {
                    // v2.26: the templar merge. Immediate -- the two units are
                    // already named by the selection, so there is nothing to
                    // aim. Both are consumed and the archon appears between
                    // them (see Game.orderMerge).
                    List<Game.Ent> sel = new ArrayList<>(game.selected());
                    String why = game.mergeError(sel, null);
                    if (why != null) {
                        toast = why;
                        toastT = 2.0f;
                        play("error", 0.9f);
                    } else {
                        final List<Game.Ent> pair = new ArrayList<>(sel);
                        game.post(() -> {
                            game.recordOrder("merge", pair, "");
                            game.orderMerge(pair, null);
                        });
                        play("click", 0.9f);
                    }
                } else if (b.action.equals("burrow")) {
                    // v2.26: the burrow toggle -- an immediate order recorded
                    // like siege/cloak so a replay replays it.
                    final List<Game.Ent> sel = new ArrayList<>(game.selected());
                    boolean any = false;
                    for (Game.Ent e : sel) if (game.burrowError(e) == null) any = true;
                    if (!any) {
                        toast = "无法钻地";
                        toastT = 2.0f;
                        play("error", 0.9f);
                    } else {
                        game.post(() -> {
                            for (Game.Ent e : sel) {
                                if (game.burrowError(e) != null) continue;
                                game.recordOrder("burrow",
                                        java.util.Collections.singletonList(e), "");
                                game.toggleBurrow(e);
                            }
                        });
                        play("click", 0.9f);
                    }
                } else if (b.action.equals("load")) {
                    // v2.23 batch A: arm a friendly-unit pick."""
s = s.replace(anchor, ins, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("inserted merge/burrow handlers")
