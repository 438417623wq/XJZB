import io
P = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\core\Game.java"
s = io.open(P, encoding="utf-8").read()

# 1) Type: add the upgrade class tag
old = """        public int ammoCap;
"""
new = """        public int ammoCap;
        /**
         * v2.28: the upgrade line this type belongs to. The original sells
         * weapon and armour upgrades per CLASS -- infantry, vehicles, ships for
         * the terran and protoss, melee/ranged/carapace for the zerg -- so a
         * marine's rifle upgrade does nothing for a siege tank. Before this the
         * game had two global axes, which meant one research buffed the whole
         * army. The tag is assigned in the post-pass by key, and a type with no
         * tag (every building, and anything a later batch adds) simply never
         * receives an upgrade.
         */
        public String upClass = "";
"""
assert old in s, "Type ammoCap"
s = s.replace(old, new, 1)

# 2) the upgrade state: three lines per race instead of two globals
old2 = """    public int weaponLevel, armorLevel;
"""
new2 = """    public int weaponLevel, armorLevel;

    /**
     * v2.28: per-class upgrade levels. Indexed by the class tag, so the game
     * can carry a different weapon and armour level for each of the three
     * lines the race actually has. The old global weaponLevel/armorLevel stay
     * as the aggregate the UI and the AI read (they are the max across the
     * lines), and the save format keeps writing them so an older build can
     * still read a v2.28 save.
     */
    public static final String[] CLASSES = {"infantry", "vehicle", "ship"};
    public final int[] weaponByClass = new int[CLASSES.length];
    public final int[] armorByClass = new int[CLASSES.length];

    public static int classIndex(String cls) {
        for (int i = 0; i < CLASSES.length; i++)
            if (CLASSES[i].equals(cls)) return i;
        return -1;
    }

    /** The weapon level that applies to a type, 0 when it has no line. */
    public int weaponFor(String cls) {
        int i = classIndex(cls);
        return i < 0 ? 0 : weaponByClass[i];
    }

    public int armorFor(String cls) {
        int i = classIndex(cls);
        return i < 0 ? 0 : armorByClass[i];
    }
"""
assert old2 in s, "upgrade state"
s = s.replace(old2, new2, 1)

# 3) buy per class
old3 = """    /** Buy the next weapon level. Returns a reason string, or null on success. */
    public String buyWeaponUpgrade() {
        if (weaponLevel >= UPGRADE_MAX) return "武器升级已满级";
        int cost = UPGRADE_COST[weaponLevel];
        if (mineralsPlayer < cost) return "晶体矿不足";
        mineralsPlayer -= cost;
        weaponLevel++;
        applyUpgrades();
        return null;
    }

    public String buyArmorUpgrade() {
        if (armorLevel >= UPGRADE_MAX) return "防御升级已满级";
        int cost = UPGRADE_COST[armorLevel];
        if (mineralsPlayer < cost) return "晶体矿不足";
        mineralsPlayer -= cost;
        armorLevel++;
        applyUpgrades();
        return null;
    }

    /** Push the current upgrade levels onto every player unit. */
    private void applyUpgrades() {
        for (Ent e : ents) {
            if (e.team != 0 || !e.alive()) continue;
            e.dmgBonus = weaponLevel * UPGRADE_DMG;
            e.armorBonus = armorLevel * UPGRADE_ARMOR;
        }
    }"""
new3 = """    /**
     * Buy the next weapon level for one class. Returns a reason, or null.
     * The class index -1 means "no line" (a building), which is refused.
     */
    public String buyWeaponUpgrade(String cls) {
        int i = classIndex(cls);
        if (i < 0) return "该单位没有武器升级线";
        if (weaponByClass[i] >= UPGRADE_MAX) return "武器升级已满级";
        int cost = UPGRADE_COST[weaponByClass[i]];
        if (mineralsPlayer < cost) return "晶体矿不足";
        mineralsPlayer -= cost;
        weaponByClass[i]++;
        applyUpgrades();
        return null;
    }

    public String buyArmorUpgrade(String cls) {
        int i = classIndex(cls);
        if (i < 0) return "该单位没有防御升级线";
        if (armorByClass[i] >= UPGRADE_MAX) return "防御升级已满级";
        int cost = UPGRADE_COST[armorByClass[i]];
        if (mineralsPlayer < cost) return "晶体矿不足";
        mineralsPlayer -= cost;
        armorByClass[i]++;
        applyUpgrades();
        return null;
    }

    /** Back-compat: the two-argument form buys the line the given unit is in. */
    public String buyWeaponUpgrade(Ent e) {
        return e == null ? "目标无效" : buyWeaponUpgrade(e.type.upClass);
    }

    public String buyArmorUpgrade(Ent e) {
        return e == null ? "目标无效" : buyArmorUpgrade(e.type.upClass);
    }

    /**
     * Push the per-class levels onto every player unit, and refresh the
     * aggregate weaponLevel/armorLevel the HUD and the AI read (the max across
     * the lines, so "武器 2/3" still means something).
     */
    private void applyUpgrades() {
        for (Ent e : ents) {
            if (e.team != 0 || !e.alive()) continue;
            int i = classIndex(e.type.upClass);
            e.dmgBonus = (i < 0 ? 0 : weaponByClass[i]) * UPGRADE_DMG;
            e.armorBonus = (i < 0 ? 0 : armorByClass[i]) * UPGRADE_ARMOR;
        }
        weaponLevel = 0;
        armorLevel = 0;
        for (int i = 0; i < CLASSES.length; i++) {
            weaponLevel = Math.max(weaponLevel, weaponByClass[i]);
            armorLevel = Math.max(armorLevel, armorByClass[i]);
        }
    }"""
assert old3 in s, "buy block"
s = s.replace(old3, new3, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("ok")
