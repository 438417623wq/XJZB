import io
P = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\core\Game.java"
s = io.open(P, encoding="utf-8").read()

# serialize: append the per-class arrays after capTier
old = """                .append(' ').append(race)
                .append(' ').append(capTier)
                .append('\\n');"""
new = """                .append(' ').append(race)
                .append(' ').append(capTier)
                // v2.28: the per-class upgrade levels, one token per line
                // ("w0,w1,w2;a0,a1,a2"). Appended last so a v2.27 save still
                // loads (it stops at capTier and keeps the arrays at 0).
                .append(' ').append(joinInts(weaponByClass))
                .append(' ').append(joinInts(armorByClass))
                .append('\\n');"""
assert old in s, "serialize state"
s = s.replace(old, new, 1)

# deserialize
old2 = """                        // v2.27: the supply tier. Older saves stop at p[15]
                        // and keep tier 0 (the original 40 ceiling).
                        if (p.length > 16) capTier = Integer.parseInt(p[16]);
                        status = "";"""
new2 = """                        // v2.27: the supply tier. Older saves stop at p[15]
                        // and keep tier 0 (the original 40 ceiling).
                        if (p.length > 16) capTier = Integer.parseInt(p[16]);
                        // v2.28: the per-class levels. A v2.27 save stops at
                        // p[16] and keeps every line at 0.
                        if (p.length > 17) parseInts(p[17], weaponByClass);
                        if (p.length > 18) parseInts(p[18], armorByClass);
                        status = "";"""
assert old2 in s, "deserialize state"
s = s.replace(old2, new2, 1)

# helpers next to the class helpers
old3 = """    public int armorFor(String cls) {
        int i = classIndex(cls);
        return i < 0 ? 0 : armorByClass[i];
    }
"""
new3 = """    public int armorFor(String cls) {
        int i = classIndex(cls);
        return i < 0 ? 0 : armorByClass[i];
    }

    /** "1,0,2" -- the save format's encoding for a per-class level array. */
    private static String joinInts(int[] a) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < a.length; i++) {
            if (i > 0) sb.append(',');
            sb.append(a[i]);
        }
        return sb.toString();
    }

    private static void parseInts(String s, int[] into) {
        String[] p = s.split(",");
        for (int i = 0; i < into.length && i < p.length; i++) {
            try {
                into[i] = Integer.parseInt(p[i].trim());
            } catch (NumberFormatException ignored) {
            }
        }
    }
"""
assert old3 in s, "helpers"
s = s.replace(old3, new3, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("ok")
