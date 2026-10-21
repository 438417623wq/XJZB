package com.xjzb.rts.core;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Random;

/**
 * Data-driven RTS simulation. Pure Java (no android imports) so the same code
 * runs on the JVM for asset/render verification.
 *
 * Coordinates: world pixels, 32 px per tile. Walkability grid: 8 px minitiles.
 */
public class Game {

    // ------------------------------------------------------------ unit types
    public static class Type {
        public String key;        // sprite key
        public String name;       // display name
        public int hp;
        public int dmg;
        public int range;         // px, 0 = melee-ish short
        public float cooldown;
        public float speed;       // px/s
        public int supply;        // 0 for buildings
        public int cost;
        public float buildTime;
        public int tiles;         // building footprint (n x n tiles), 0 = unit
        public float radius;
        public boolean flying;
        public String[] trains;   // what this building trains
        public String requires;   // required building key for training ("")
        public int gasCost;       // vespene cost
        public String siegesTo;   // tank siege morph target
        public int unitId;        // units.dat id: wireframe portrait + stat_txt key
        /**
         * v2.7 9.2: flat damage reduction. Deliberately one dimension, not the
         * original Small/Medium/Large table -- one axis is enough to open the
         * "lings barely scratch a tank, a tank one-shots a ling" gap, and the
         * full table would cost far more balance work than it returns here.
         */
        public int armor;
        /**
         * v2.10: Protoss energy shield. Damage drains this before hp, and it
         * recharges on its own after a few seconds without being hit. Set as a
         * post-pass (like armor) so the t() overloads keep their arity; 0 means
         * the type has no shield at all, which is every terran and zerg row.
         */
        public int shield;
        /**
         * v2.11: weapon layer restriction. StarCraft gives several Brood War
         * units a weapon that can only ever hit one half of the battlefield --
         * the valkyrie and the devourer shoot air only, the lurker and the
         * guardian ground only -- and without these flags the generic
         * findEnemyInRange() would happily let them shoot the wrong thing.
         * Set as a post-pass, like armor and shield, so t() keeps its arity.
         */
        public boolean airOnly, groundOnly;
        /**
         * v2.11: this type has no ranged shot, it just stabs whatever it is
         * standing next to (ultralisk, broodling, zergling). Kept as a flag so
         * fire() can skip the muzzle-flash/shot pipeline for them.
         */
        public boolean melee;

        /**
         * v2.22: the cloak model. 0 = visible, 1 = permanently cloaked
         * (dark templar, observer), 2 = personal toggle on an energy cost
         * (ghost, wraith). The burrowed lurker and the arbiter's aura are
         * NOT modelled here -- isCloakedNow() adds them at runtime, because
         * burrowing is a state of the lurker and the aura is a property of
         * a different unit (the arbiter) than the one it hides.
         */
        public int cloak;

        /**
         * v2.22: reveals cloaked enemies inside DETECTOR_RANGE. The original's
         * detector list for the units this game ships: missile turret, spore
         * colony, photon cannon, overlord, observer. Set as a post-pass.
         */
        public boolean detector;

        /**
         * v2.22: this unit owns an energy pool (the seven castable types).
         * Everything the pool does -- spawn level, regen, spell prices --
         * hangs off this flag, so the t() overloads keep their arity.
         */
        public boolean caster;

        /**
         * v2.14: the original's weapon damage class. Together with `size` this
         * is the counter triangle v2.7 deliberately left out (see the armor
         * comment above): a marine's gauss rifle is concussive and therefore
         * does a quarter damage to a tank, while a siege tank's shell is
         * explosive and halves against a zergling. One flat armor value could
         * never express that -- it is the same subtraction for every pairing --
         * so the whole point of this field is that "lings scratch a tank, a
         * tank wipes lings" falls out of the table instead of out of hand-tuned
         * hp/damage numbers.
         *   normal     -- 100% against every size
         *   explosive  -- 100% large, 75% medium, 50% small
         *   concussive -- 100% small, 50% medium, 25% large
         */
        public String dmgType = "normal";
        /**
         * v2.14: the unit's size class, the other half of the table above.
         * Set as a post-pass like armor/shield so the t() overloads keep their
         * arity; "medium" is the neutral default, which is what every row that
         * is not explicitly listed below ends up as.
         */
        public String size = "medium";
        /**
         * v2.14: splash. `splashR` is the radius in world pixels (0 = single
         * target, the overwhelmingly common case) and `splashFalloff` is the
         * fraction of full damage a target takes at the very edge of it; the
         * falloff in between is linear. Splash deliberately ignores teams --
         * see impact() -- because that is the rule that makes a tank line a
         * liability when its own zerglings are in the way.
         */
        public float splashR;
        public float splashFalloff = 0.5f;

        /**
         * v2.23 batch B: the anti-air half of a dual weapon. The original gives
         * the goliath two separate guns -- a ground autocannon and a heavier
         * air missile -- and this game's single `dmg` axis cannot express that.
         * -1 means "no separate air axis, use dmg against everything", which is
         * every row except the goliath; fire() picks the axis from the target.
         */
        public int dmgAir = -1;

        /**
         * v2.23 batch A: transport capacity in supply slots. The shuttle and
         * the dropship carry 8 (the original's figure); the overlord joins them
         * -- the campaign's Ventral Sacs upgrade is simplified to "always
         * available", as the plan allows. 0 means "not a transport", which is
         * every other row.
         */
        public int cargoCap;

        /**
         * v2.23 batch B: bunker garrison slots, in supply. The original holds
         * four infantry slots, which is 4 marines or 2 firebats (a firebat
         * costs 2) -- so the one number covers both cases the plan names. 0
         * means "not a bunker".
         */
        public int bunkerCap;

        /**
         * v2.25: the Terran add-ons. An add-on is built by its parent building
         * (barracks/factory/starport/sciencefac) and hangs off one side of it,
         * occupying a 2x2 pad. `addonFor` is the parent key -- empty for
         * everything that is not an add-on; `addonSlot` is which of the
         * parent's four pads it owns. The parent key of a row is also what the
         * placement rule checks, so the two never disagree.
         */
        public String addonFor = "";
        public int addonSlot;
        /**
         * v2.25: when set, this building needs a live add-on of this key before
         * it can train the rows that name it. The starport needs a control
         * tower, the science facility a physics lab, and the science facility
         * also a covert ops -- which this repack has no art for, so the ghost
         * keeps its academy gate instead.
         */
        public String addonNeeded = "";
        /**
         * v2.26: this type carries a hangar of interceptors (the carrier).
         * The number is the hangar's capacity; the per-unit count lives on
         * the entity, because two carriers can be at different fill levels.
         */
        public int hangarCap;
        /**
         * v2.26: this type fires a limited-ammo projectile (the reaver's
         * scarab). Ammo lives on the entity and is replenished beside the
         * building that builds the unit.
         */
        public int ammoCap;
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
    }

    public static final java.util.HashMap<String, Type> TYPES = new java.util.HashMap<>();

    private static Type t(String key, String name, int hp, int dmg, int range,
                          float cd, float speed, int supply, int cost, float time,
                          int tiles, float radius, boolean flying,
                          String[] trains, String requires) {
        return t(key, name, hp, dmg, range, cd, speed, supply, cost, time,
                tiles, radius, flying, trains, requires, 0, null, 0);
    }

    private static Type t(String key, String name, int hp, int dmg, int range,
                          float cd, float speed, int supply, int cost, float time,
                          int tiles, float radius, boolean flying,
                          String[] trains, String requires, int gasCost,
                          String siegesTo) {
        return t(key, name, hp, dmg, range, cd, speed, supply, cost, time,
                tiles, radius, flying, trains, requires, gasCost, siegesTo, 0);
    }

    private static Type t(String key, String name, int hp, int dmg, int range,
                          float cd, float speed, int supply, int cost, float time,
                          int tiles, float radius, boolean flying,
                          String[] trains, String requires, int gasCost,
                          String siegesTo, int unitId) {
        Type t = new Type();
        t.key = key;
        t.name = name;
        t.hp = hp;
        t.dmg = dmg;
        t.range = range;
        t.cooldown = cd;
        t.speed = speed;
        t.supply = supply;
        t.cost = cost;
        t.buildTime = time;
        t.tiles = tiles;
        t.radius = radius;
        t.flying = flying;
        t.trains = trains;
        t.requires = requires;
        t.gasCost = gasCost;
        t.siegesTo = siegesTo;
        t.unitId = unitId;
        TYPES.put(key, t);
        return t;
    }

    public static final String[] NO_TRAIN = new String[0];

    static {
        // unitId = units.dat id, keyed to unit\wirefram\wirefram.grp frames and
        // rez/stat_txt.tbl rows (verified: 0='Terran Marine', 7='Terran SCV').
        t("scv", "SCV", 60, 5, 14, 1.0f, 66, 1, 50, 12, 0, 9, false, NO_TRAIN, "", 0, null, 7);
        t("marine", "机枪兵", 45, 6, 96, 0.9f, 62, 1, 50, 15, 0, 9, false, NO_TRAIN, "", 0, null, 0);
        t("firebat", "喷火兵", 65, 16, 36, 1.2f, 58, 2, 75, 20, 0, 10, false, NO_TRAIN, "academy", 25, null, 32);
        t("vulture", "雷车", 80, 20, 128, 1.5f, 100, 2, 75, 20, 0, 11, false, NO_TRAIN, "factory", 0, null, 2);
        t("tank", "攻城坦克", 150, 35, 208, 2.4f, 52, 2, 150, 30, 0, 13, false, NO_TRAIN, "factory", 75, "stank", 5);
        // Siege mode: same chassis, immobile (speed 0), longer range, heavier shell.
        t("stank", "攻城坦克(架起)", 150, 45, 280, 2.4f, 0, 2, 150, 30, 0, 13, false, NO_TRAIN, "factory", 75, "tank", 5);
        t("zergling", "小狗", 35, 5, 10, 0.7f, 95, 1, 25, 8, 0, 7, false, NO_TRAIN, "pool", 0, null, 37);
        t("hydra", "刺蛇", 80, 12, 112, 1.1f, 70, 1, 75, 18, 0, 10, false, NO_TRAIN, "pool", 25, null, 38);
        // v2.8: the mutalisk now really needs the spire -- without this the
        // spire would be a 600/150 building that unlocked nothing.
        t("muta", "飞龙", 120, 10, 96, 1.3f, 112, 2, 100, 24, 0, 11, true, NO_TRAIN, "spire", 50, null, 43);

        t("cc", "指挥中心", 1500, 0, 0, 0, 0, 0, 400, 40, 4, 40, false,
                new String[]{"scv"}, "", 0, null, 106);
        t("depot", "补给站", 500, 0, 0, 0, 0, 0, 100, 16, 2, 18, false, NO_TRAIN, "", 0, null, 109);
        t("refinery", "炼油厂", 1000, 0, 0, 0, 0, 0, 150, 20, 3, 24, false, NO_TRAIN, "", 0, null, 110);
        // v2.11: the barracks gains the medic, the starport the valkyrie and
        // the battlecruiser (see the batch C rows below).
        t("barracks", "兵营", 1000, 0, 0, 0, 0, 0, 150, 25, 3, 24, false,
                new String[]{"marine", "firebat", "medic"}, "", 0, null, 111);
        t("factory", "重工厂", 1250, 0, 0, 0, 0, 0, 200, 40, 3, 26, false,
                new String[]{"vulture", "tank", "goliath"}, "barracks", 0, null, 113);
        // v2.7 9.1: the tech-tree buildings the plan asks for. unitId 112 is
        // Academy, 122 Engineering Bay, 123 Armory and 114 Starport in
        // stat_txt.tbl, the same table the wireframes and command icons are
        // indexed by. v2.8: this row said 116, which is the Science Facility,
        // so the academy showed the wrong console wireframe and name.
        t("academy", "学院", 1000, 0, 0, 0, 0, 0, 150, 22, 3, 24, false,
                NO_TRAIN, "", 0, null, 112);
        t("engbay", "工程湾", 850, 0, 0, 0, 0, 0, 125, 20, 3, 24, false,
                NO_TRAIN, "", 0, null, 122);
        t("turret", "导弹塔", 800, 12, 160, 1.0f, 0, 0, 100, 18, 2, 16, false, NO_TRAIN, "", 0, null, 124);
        t("hatchery", "孵化场", 1500, 0, 0, 0, 0, 0, 300, 60, 4, 40, false,
                new String[]{"drone", "over", "zergling"}, "", 0, null, 131);
        t("pool", "孵化池", 750, 0, 0, 0, 0, 0, 200, 40, 3, 24, false,
                new String[]{"zergling"}, "hatchery", 0, null, 142);
        t("sunken", "地刺", 800, 18, 112, 1.5f, 0, 0, 150, 30, 2, 16, false, NO_TRAIN, "", 0, null, 146);

        // v2.8: the two Terran units the plan gated behind art verification.
        // unitId 1 = Ghost, 8 = Wraith (both confirmed against wirefram.grp
        // frames and the labelled cmdicons grid).
        t("ghost", "幽灵", 45, 10, 160, 1.0f, 62, 1, 25, 50, 0, 9, false, NO_TRAIN, "academy", 75, null, 1);
        t("wraith", "幽灵战机", 120, 20, 160, 1.2f, 118, 2, 150, 60, 0, 12, true, NO_TRAIN, "starport", 100, null, 8);
        t("starport", "星港", 1300, 0, 0, 0, 0, 0, 150, 50, 3, 26, false,
                new String[]{"wraith", "valkyrie", "battlecruiser", "vessel", "dropship"},
                "factory", 100, null, 114);

        // v2.8: the zerg half of the tech tree. Costs and build times matter
        // for a player-built base, so pool/sunken stop being AI-only rows.
        t("drone", "工蜂", 40, 5, 14, 1.0f, 66, 1, 50, 12, 0, 9, false, NO_TRAIN, "", 0, null, 41);
        t("over", "领主", 200, 0, 0, 0, 0, 0, 100, 40, 0, 18, true, NO_TRAIN, "", 0, null, 42);
        t("larva", "幼虫", 25, 0, 0, 0, 0, 0, 0, 0, 0, 8, false, NO_TRAIN, "", 0, null, 35);
        t("extractor", "萃取场", 750, 0, 0, 0, 0, 0, 50, 25, 3, 24, false,
                NO_TRAIN, "", 0, null, 149);
        t("spire", "飞龙塔", 600, 0, 0, 0, 0, 0, 200, 60, 3, 24, false,
                new String[]{"muta"}, "pool", 150, null, 141);

        // ---------------------------------------------------------- protoss
        // v2.10 batch A. Shields are set in the post-pass below (Type.shield),
        // never here, so every row keeps the t() arity the other two races use.
        // unitId values are the units.dat ids the icon extractor keyed on
        // (ic_zealot 65, ic_nexus 154, ...), verified against the labelled
        // cmdicons grid.
        t("probe", "探测机", 20, 5, 14, 1.0f, 66, 1, 50, 12, 0, 9, false, NO_TRAIN, "", 0, null, 64);
        t("zealot", "狂热者", 100, 16, 14, 1.0f, 62, 2, 100, 20, 0, 10, false, NO_TRAIN, "gateway", 0, null, 65);
        // The dragoon is the tech-gate unit: it needs the cybernetics core, and
        // the core needs a gateway. That two-step is what raceTests asserts.
        t("dragoon", "龙骑士", 100, 20, 128, 1.5f, 70, 2, 125, 30, 0, 11, false, NO_TRAIN, "gencore", 50, null, 66);
        t("templar", "圣堂武士", 40, 0, 128, 1.2f, 60, 2, 50, 30, 0, 10, false, NO_TRAIN, "archives", 150, null, 67);
        t("dtemplar", "黑暗圣堂", 80, 25, 14, 1.0f, 62, 2, 125, 30, 0, 10, false, NO_TRAIN, "archives", 100, null, 61);
        // Archon: 10 hp but a 350 shield, so it dies to sustained fire only.
        // The merge animation (two templar -> one archon) is deliberately not
        // modelled; it is trained directly, as the plan allows.
        t("archon", "执政官", 10, 30, 96, 1.2f, 62, 4, 100, 30, 0, 12, false, NO_TRAIN, "archives", 300, null, 68);
        t("darchon", "黑暗执政官", 25, 30, 128, 1.2f, 62, 4, 100, 30, 0, 12, false, NO_TRAIN, "archives", 300, null, 63);
        t("shuttle", "运输机", 80, 0, 0, 0, 118, 2, 200, 30, 0, 12, true, NO_TRAIN, "robotic", 0, null, 69);
        t("scout", "侦察机", 150, 20, 160, 1.2f, 118, 3, 275, 40, 0, 12, true, NO_TRAIN, "stargate", 125, null, 70);
        t("corsair", "海盗船", 100, 15, 160, 1.2f, 118, 2, 150, 30, 0, 11, true, NO_TRAIN, "stargate", 100, null, 60);
        t("arbiter", "仲裁机", 150, 10, 160, 1.5f, 118, 3, 200, 50, 0, 12, true, NO_TRAIN, "beacon", 350, null, 71);
        // Carrier simplified to a long-range heavy gunship; no interceptor
        // hangar, so `intercep` exists as a type but nothing trains it.
        t("carrier", "航空母舰", 300, 30, 200, 2.0f, 84, 4, 350, 60, 0, 13, true, NO_TRAIN, "beacon", 250, null, 72);
        t("intercep", "拦截机", 40, 6, 128, 1.0f, 140, 0, 0, 0, 0, 8, true, NO_TRAIN, "", 0, null, 73);
        t("reaver", "金甲虫", 100, 40, 160, 2.5f, 40, 3, 200, 40, 0, 12, false, NO_TRAIN, "robotic", 100, null, 83);
        // Observer: flying scout. The original's cloak is not modelled (it would
        // need a real detection layer); the plan defers that, so this is a fast
        // cheap eye with no weapon.
        t("observer", "观察者", 40, 0, 0, 0, 100, 1, 25, 20, 0, 9, true, NO_TRAIN, "robotic", 75, null, 84);

        t("nexus", "星灵枢纽", 1500, 0, 0, 0, 0, 0, 400, 40, 4, 40, false,
                new String[]{"probe"}, "", 0, null, 154);
        // Pylon is the protoss supply building (8 supply, same as a depot).
        t("pylon", "水晶塔", 300, 0, 0, 0, 0, 0, 100, 16, 2, 18, false, NO_TRAIN, "", 0, null, 156);
        t("assim", "吸收站", 1000, 0, 0, 0, 0, 0, 100, 20, 3, 24, false, NO_TRAIN, "", 0, null, 157);
        t("gateway", "传送门", 1000, 0, 0, 0, 0, 0, 150, 25, 3, 24, false,
                new String[]{"zealot"}, "nexus", 0, null, 160);
        t("forge", "锻造厂", 550, 0, 0, 0, 0, 0, 100, 20, 3, 24, false,
                NO_TRAIN, "nexus", 0, null, 166);
        t("photon", "光子炮台", 800, 20, 160, 1.0f, 0, 0, 150, 20, 2, 16, false, NO_TRAIN, "forge", 0, null, 162);
        t("gencore", "机械核心", 500, 0, 0, 0, 0, 0, 200, 30, 3, 24, false,
                new String[]{"dragoon"}, "gateway", 0, null, 164);
        t("citadel", "阿顿圣殿", 500, 0, 0, 0, 0, 0, 150, 25, 3, 24, false,
                NO_TRAIN, "gencore", 0, null, 163);
        t("archives", "圣堂档案馆", 500, 0, 0, 0, 0, 0, 150, 40, 3, 24, false,
                new String[]{"templar", "dtemplar", "archon", "darchon"}, "citadel", 200, null, 165);
        // The robotics line carries reaver/observer/shuttle. There is no
        // observatory in the art set (no GRP exists in any of the four MPQs),
        // so observer is gated on the facility itself rather than on a missing
        // building -- see the note in pipeline_sprites.py.
        t("robotic", "机器人工厂", 500, 0, 0, 0, 0, 0, 200, 40, 3, 26, false,
                new String[]{"reaver", "observer", "shuttle"}, "gencore", 200, null, 155);
        t("stargate", "星门", 600, 0, 0, 0, 0, 0, 150, 40, 3, 26, false,
                new String[]{"scout", "corsair"}, "gencore", 150, null, 167);
        t("beacon", "舰队航标", 500, 0, 0, 0, 0, 0, 300, 40, 3, 24, false,
                new String[]{"arbiter", "carrier"}, "stargate", 200, null, 169);

        // ------------------------------------------------- v2.11 batch B (zerg)
        // Numbers come from BroodUnits.doc (the official Brood War manual
        // shipped in F:\KF\XJZB) where it is specific -- lurker spines are
        // ground-only, devourer venom air-only, ultralisk is a 400 hp melee
        // battering ram -- and from the existing rows' scale where it is not,
        // so a new unit sits next to the old ones instead of beside them.
        // unitIds are stat_txt.tbl rows (39 Ultralisk, 44 Guardian, ...).
        t("ultra", "雷兽", 400, 20, 14, 1.0f, 90, 4, 200, 40, 0, 16, false,
                NO_TRAIN, "ucereb", 200, null, 39);
        t("guardian", "守护者", 150, 20, 224, 2.0f, 60, 2, 150, 40, 0, 15, true,
                NO_TRAIN, "greatspire", 100, null, 44);
        t("devourer", "吞噬者", 250, 25, 160, 2.0f, 90, 2, 150, 40, 0, 15, true,
                NO_TRAIN, "greatspire", 150, null, 62);
        t("queen", "皇后", 120, 0, 0, 0, 0, 2, 100, 40, 0, 13, true,
                NO_TRAIN, "nest", 100, null, 45);
        t("defiler", "污染者", 80, 0, 0, 0, 0, 2, 50, 30, 0, 12, false,
                NO_TRAIN, "mutapit", 150, null, 46);
        // The lurker burrows. Burrowing is modelled with the siege-tank morph
        // the game already has (Type.siegesTo + toggleSiege) rather than a new
        // mechanism: "lurker" is the mobile form, "lurker_bur" the immobile
        // one, and the pair point at each other so the button toggles.
        t("lurker", "潜伏者", 125, 20, 160, 1.5f, 70, 2, 100, 30, 0, 13, false,
                NO_TRAIN, "hydraden", 50, "lurker_bur", 103);
        t("lurker_bur", "潜伏者(钻地)", 125, 20, 160, 1.5f, 0, 2, 100, 30, 0, 13, false,
                NO_TRAIN, "hydraden", 50, "lurker", 103);
        t("broodling", "寄生虫", 30, 4, 10, 0.6f, 110, 0, 0, 0, 0, 8, false,
                NO_TRAIN, "", 0, null, 40);

        t("creep", "菌毯殖地", 400, 0, 0, 0, 0, 0, 75, 20, 2, 16, false,
                NO_TRAIN, "hatchery", 0, null, 143);
        t("spore", "孢子殖地", 400, 15, 224, 1.2f, 0, 0, 100, 25, 2, 16, false,
                NO_TRAIN, "evolcham", 0, null, 144);
        t("evolcham", "进化腔", 750, 0, 0, 0, 0, 0, 75, 30, 3, 24, false,
                NO_TRAIN, "hatchery", 0, null, 139);
        // v2.11: this row is the fix the plan asks for -- v2.8 hung the
        // hydralisk straight off the spawning pool, which made the hydralisk
        // den art (135, present in the archive all along) unreachable.
        t("hydraden", "刺蛇巢", 850, 0, 0, 0, 0, 0, 100, 30, 3, 24, false,
                new String[]{"hydra", "lurker"}, "pool", 0, null, 135);
        t("mutapit", "污染者巢穴", 850, 0, 0, 0, 0, 0, 150, 40, 3, 24, false,
                new String[]{"defiler"}, "hive", 0, null, 136);
        t("nest", "皇后巢", 850, 0, 0, 0, 0, 0, 150, 40, 3, 24, false,
                new String[]{"queen"}, "lair", 0, null, 138);
        t("nydus", "虫道", 600, 0, 0, 0, 0, 0, 150, 40, 3, 24, false,
                NO_TRAIN, "hive", 0, null, 134);
        t("ucereb", "雷兽洞穴", 1000, 0, 0, 0, 0, 0, 200, 50, 3, 24, false,
                new String[]{"ultra"}, "hive", 0, null, 140);
        t("cerebrate", "脑虫", 500, 0, 0, 0, 0, 0, 100, 40, 3, 24, false,
                NO_TRAIN, "hatchery", 0, null, 151);
        t("greatspire", "大飞龙塔", 700, 0, 0, 0, 0, 0, 250, 60, 3, 24, false,
                new String[]{"guardian", "devourer"}, "spire", 150, null, 137);
        // v2.11: lair and hive existed as art-only rows with no prerequisites,
        // so the zerg tree was flat. These two rows give the chain its links
        // (pool -> lair -> hive) that mutapit/nest/nydus/ucereb gate on.
        t("lair", "兽穴", 1800, 0, 0, 0, 0, 0, 300, 60, 4, 40, false,
                new String[]{"drone", "over", "zergling"}, "pool", 100, null, 132);
        t("hive", "虫巢", 2500, 0, 0, 0, 0, 0, 400, 80, 4, 40, false,
                new String[]{"drone", "over", "zergling"}, "lair", 200, null, 133);

        // ----------------------------------------------- v2.11 batch C (terran)
        // Brood War's terran half. BroodUnits.doc gives the medics' and
        // valkyries' prerequisites (Barracks+Academy, Starport+Armory) and the
        // manual's own tech text in stat_txt.tbl gives the battlecruiser's
        // (Science Facility). The engineering bay keeps its art; the armoury
        // is what actually sells the upgrades now (see buyWeaponUpgrade).
        t("armory", "军械库", 750, 0, 0, 0, 0, 0, 100, 25, 3, 24, false,
                NO_TRAIN, "factory", 0, null, 123);
        t("sciencefac", "科学设施", 850, 0, 0, 0, 0, 0, 125, 30, 3, 26, false,
                NO_TRAIN, "starport", 0, null, 116);
        t("medic", "医护兵", 60, 0, 0, 0, 0, 1, 50, 20, 0, 9, false,
                NO_TRAIN, "academy", 25, null, 34);
        t("valkyrie", "瓦格雷", 200, 40, 192, 2.0f, 118, 3, 250, 50, 0, 14, true,
                NO_TRAIN, "armory", 125, null, 58);
        t("battlecruiser", "战列巡航舰", 500, 25, 192, 1.5f, 82, 6, 400, 60, 0, 16, true,
                NO_TRAIN, "sciencefac", 300, null, 12);
        // v2.14 batch 1.5: the Science Vessel. It has no weapon at all -- both
        // of its buttons are spells (EMP and Irradiate), which is why its dmg
        // and range are 0 and why it is the one terran unit whose value is
        // entirely in the command card. unitId 9 is the Science Vessel in
        // units.dat, the id ic_science was extracted against.
        t("vessel", "科学球", 200, 0, 0, 0, 100, 2, 100, 50, 0, 18, true,
                NO_TRAIN, "sciencefac", 225, null, 9);
        // Spider mine: dropped by a vulture, immobile, detonates once. dmg is
        // the blast, not a weapon cooldown, so cooldown is irrelevant and the
        // unit is removed by its own explosion (see updateUnit).
        t("spider", "蜘蛛雷", 20, 50, 32, 0, 0, 0, 0, 0, 0, 8, false,
                NO_TRAIN, "", 0, null, 13);

        // ------------------------------------------------- v2.23 batch A/B
        // The dropship is the terran half of the transport layer; the shuttle
        // already existed as a "fast eye" with no load/unload, and now carries
        // cargo through the same channel. Both are 8 supply slots (the
        // original figure, which the plan pins as a constant). unitId 11 is the
        // Dropship in units.dat -- the same id ic_dropship was cut against.
        t("dropship", "运输船", 150, 0, 0, 0, 100, 2, 100, 50, 0, 12, true,
                NO_TRAIN, "starport", 100, null, 11);
        // The goliath is the dual-weapon showcase: 12 ground / 20 air, the
        // original two guns on one chassis. dmgAir is set in the post-pass
        // below so the t() overload keeps its arity. unitId 3 is the Goliath.
        t("goliath", "歌利亚", 125, 12, 160, 1.2f, 82, 2, 100, 40, 0, 12, false,
                NO_TRAIN, "factory", 50, null, 3);
        // The bunker: 4 garrison slots, no weapon of its own -- everything it
        // shoots with comes from the marines standing inside it. unitId 125 is
        // the Bunker, matching ic_bunker slot in the cmdicons grid.
        t("bunker", "地堡", 400, 0, 0, 0, 0, 0, 100, 20, 2, 16, false,
                NO_TRAIN, "barracks", 0, null, 125);

        // v2.11: the hydralisk moves off the spawning pool onto its own den --
        // the "补正" the plan calls for. Done as a post-pass so the original
        // v2.8 row above stays readable.
        TYPES.get("hydra").requires = "hydraden";

        // ------------------------------------------------------ v2.25 add-ons
        // The five Terran add-ons this repack has art for (the GRP names come
        // from BrooDat's arr\images.tbl -- see pipeline_sprites.py). Every one
        // is a 2x2 pad, costs 50/25, and is built by its parent rather than by
        // an SCV: addonFor names the parent, addonSlot which of the parent's
        // four pads it owns (0 = +x, 1 = -x, 2 = +y, 3 = -y).
        //
        // unitIds are units.dat, the same id rule the wireframes and command
        // icons are indexed by: 107 Comsat, 115 Control Tower, 118 Physics Lab,
        // 120 Machine Shop, 108 Nuclear Silo. Covert Ops (117) has no art at
        // all in this repack and is deliberately absent.
        t("comsat", "雷达站", 500, 0, 0, 0, 0, 0, 50, 25, 2, 16, false,
                NO_TRAIN, "", 25, null, 107);
        t("controlt", "控制塔", 500, 0, 0, 0, 0, 0, 50, 25, 2, 16, false,
                NO_TRAIN, "", 25, null, 115);
        t("machineshop", "机械车间", 750, 0, 0, 0, 0, 0, 50, 25, 2, 16, false,
                NO_TRAIN, "", 25, null, 120);
        t("physicslab", "物理实验室", 600, 0, 0, 0, 0, 0, 50, 25, 2, 16, false,
                NO_TRAIN, "", 25, null, 118);
        t("nukesilo", "核弹井", 600, 0, 0, 0, 0, 0, 100, 40, 2, 16, false,
                NO_TRAIN, "", 100, null, 108);
    }

    /**
     * v2.7 9.2: armor per type. Applied as a post-pass so the t()
     * overloads keep their original arity -- armor is the one field a
     * type may want to set without every other row growing an argument.
     */
    static {
        TYPES.get("firebat").armor = 1;
        TYPES.get("hydra").armor = 1;
        TYPES.get("muta").armor = 1;
        TYPES.get("stank").armor = 2;
        TYPES.get("sunken").armor = 2;
        TYPES.get("tank").armor = 2;
        TYPES.get("turret").armor = 2;
        TYPES.get("vulture").armor = 1;
    }

    /**
     * v2.11 batch B/C: armor and weapon-layer flags for the Brood War rows.
     * Same post-pass shape as the two blocks around it, for the same reason --
     * neither field belongs in the t() argument list. The layer flags are what
     * make "valkyrie cannot touch a zergling, lurker cannot touch a mutalisk"
     * true without special-casing either unit anywhere else.
     */
    static {
        TYPES.get("ultra").armor = 3;
        TYPES.get("guardian").armor = 1;
        TYPES.get("devourer").armor = 2;
        TYPES.get("lurker").armor = 1;
        TYPES.get("lurker_bur").armor = 1;
        TYPES.get("battlecruiser").armor = 3;
        TYPES.get("valkyrie").armor = 1;
        TYPES.get("spore").armor = 2;
        TYPES.get("ucereb").armor = 2;
        TYPES.get("cerebrate").armor = 2;

        // Air-only shooters: valkyrie (Halo Rockets), devourer (Corrosive
        // Venom), spore colony (the zerg anti-air static). Ground-only:
        // lurker (Subterranean Spines), guardian, and the sunken colony the
        // game already shipped, which until now could plink at overlords.
        TYPES.get("valkyrie").airOnly = true;
        TYPES.get("devourer").airOnly = true;
        TYPES.get("spore").airOnly = true;
        TYPES.get("lurker").groundOnly = true;
        TYPES.get("lurker_bur").groundOnly = true;
        TYPES.get("guardian").groundOnly = true;
        TYPES.get("sunken").groundOnly = true;

        // No projectile, just teeth.
        TYPES.get("ultra").melee = true;
        TYPES.get("broodling").melee = true;
        TYPES.get("zergling").melee = true;
    }

    /**
     * v2.10 batch A: Protoss shields. Same post-pass trick as armor, for the
     * same reason. Values follow the original's shape -- a shield is roughly
     * equal to the unit's hp for the fighting castes, and buildings get a
     * smaller one so a nexus is not effectively 3000 hp. Terran and zerg rows
     * are untouched and stay at 0, which is what makes "no shield bar drawn"
     * fall out for free.
     */
    static {
        TYPES.get("probe").shield = 20;
        TYPES.get("zealot").shield = 60;
        TYPES.get("dragoon").shield = 80;
        TYPES.get("templar").shield = 40;
        TYPES.get("dtemplar").shield = 40;
        // Archon is the shield showcase: 350 shield over 10 hp, so it absorbs
        // a long burst and then dies almost instantly once the shield drops.
        TYPES.get("archon").shield = 350;
        TYPES.get("darchon").shield = 300;
        TYPES.get("shuttle").shield = 60;
        TYPES.get("scout").shield = 100;
        TYPES.get("corsair").shield = 80;
        TYPES.get("arbiter").shield = 150;
        TYPES.get("carrier").shield = 150;
        TYPES.get("reaver").shield = 80;
        TYPES.get("observer").shield = 40;
        TYPES.get("nexus").shield = 300;
        TYPES.get("pylon").shield = 150;
        TYPES.get("assim").shield = 200;
        TYPES.get("gateway").shield = 200;
        TYPES.get("forge").shield = 150;
        TYPES.get("photon").shield = 150;
        TYPES.get("gencore").shield = 150;
        TYPES.get("citadel").shield = 150;
        TYPES.get("archives").shield = 150;
        TYPES.get("robotic").shield = 150;
        TYPES.get("stargate").shield = 150;
        TYPES.get("beacon").shield = 150;
    }

    /**
     * v2.14 batch 1: the damage-class x size table. Both halves are set here,
     * as a post-pass, for the reason the three blocks above already give --
     * neither field belongs in the t() argument list, and a reader who wants to
     * see the whole counter triangle in one place should not have to walk 200
     * rows of unit data to find it.
     *
     * Sizes follow the original's assignment where this game has the unit:
     * marines, zerglings, zealots, workers and most casters are small; the
     * heavier infantry (firebat, hydra, dragoon) and most flyers are medium;
     * tanks, ultralisks, battlecruisers, carriers and every building are large.
     *
     * Damage classes are only interesting where they differ from normal, which
     * is why the list is short: the concussive weapons are the fast small-arms
     * (marine, zergling, zealot, and the ghost's rifle), and the explosive ones
     * are the artillery and area weapons (tank, siege tank, vulture, valkyrie,
     * devourer, reaver, guardian, firebat). Everything else stays normal.
     */
    static {
        // --- size: small ---------------------------------------------------
        String[] small = {"scv", "marine", "zergling", "zealot", "probe", "drone",
                "medic", "ghost", "templar", "dtemplar", "queen", "defiler",
                "broodling", "larva", "vulture", "corsair", "observer", "scarab"};
        for (String k : small) if (TYPES.containsKey(k)) TYPES.get(k).size = "small";

        // --- size: large ---------------------------------------------------
        // Buildings are large by definition (the original gives every structure
        // the large class), plus the heavy chassis and the capital ships.
        String[] large = {"tank", "stank", "ultra", "battlecruiser", "carrier",
                "guardian", "devourer", "valkyrie", "reaver", "arbiter",
                "shuttle", "scout", "wraith", "sciencevessel", "vessel",
                "dropship", "goliath"};
        for (String k : large) if (TYPES.containsKey(k)) TYPES.get(k).size = "large";
        for (Type ty : TYPES.values()) if (ty.tiles > 0) ty.size = "large";

        // --- damage class --------------------------------------------------
        String[] concussive = {"marine", "zergling", "zealot", "ghost", "firebat",
                "scv", "probe", "drone", "medic", "broodling"};
        for (String k : concussive) if (TYPES.containsKey(k)) TYPES.get(k).dmgType = "concussive";

        // The spider mine is deliberately NOT explosive: it is a flat 50-damage
        // bomb that already carries its own 56 px splash, and halving it against
        // a small unit would leave a zergling alive on a direct hit.
        String[] explosive = {"tank", "stank", "vulture", "valkyrie", "devourer",
                "reaver", "guardian", "turret", "photon", "sunken",
                "spore", "scarab"};
        for (String k : explosive) if (TYPES.containsKey(k)) TYPES.get(k).dmgType = "explosive";
    }

    /**
     * v2.14 batch 1: splash weapons. The radius is in world pixels; 32 px is a
     * tile, so 40 covers "the two zerglings standing next to the target".
     * Falloff is the fraction of full damage at the rim, linear in between.
     *
     * The siege tank is the showcase: 56 px at 0.35 means a shell that lands in
     * a ling pack hits everything, and the units right next to the impact take
     * nearly full damage. The firebat's 32 px is deliberately smaller than its
     * 36 px range so it does not splash onto things it could not reach.
     */
    static {
        TYPES.get("tank").splashR = 40f;
        TYPES.get("tank").splashFalloff = 0.5f;
        TYPES.get("stank").splashR = 56f;
        TYPES.get("stank").splashFalloff = 0.35f;
        TYPES.get("firebat").splashR = 32f;
        TYPES.get("firebat").splashFalloff = 0.4f;
        TYPES.get("valkyrie").splashR = 48f;
        TYPES.get("valkyrie").splashFalloff = 0.5f;
        TYPES.get("devourer").splashR = 44f;
        TYPES.get("devourer").splashFalloff = 0.5f;
        TYPES.get("guardian").splashR = 36f;
        TYPES.get("guardian").splashFalloff = 0.4f;
        TYPES.get("spider").splashR = 56f;
        TYPES.get("spider").splashFalloff = 0.5f;
        TYPES.get("turret").splashR = 0f;

        // --- v2.22: cloak / detector / caster post-pass -----------------------
        // Permanent cloak: the two units the original makes invisible without
        // any player action. Personal toggle: ghost and wraith spend energy on
        // it (see CLOAK_COST / CLOAK_DRAIN). The burrowed lurker and the
        // arbiter's aura join at runtime; detectors reveal them all.
        TYPES.get("dtemplar").cloak = 1;
        TYPES.get("observer").cloak = 1;
        TYPES.get("ghost").cloak = 2;
        TYPES.get("wraith").cloak = 2;
        // Detectors are the original's list for the units this game ships --
        // three defensive structures and two eye-in-the-sky units. The zerg
        // overlord is registered under its short key "over".
        for (String k : new String[]{"turret", "spore", "photon", "over",
                "observer"}) {
            TYPES.get(k).detector = true;
        }
        // The seven types that carry an energy pool. The arbiter is
        // deliberately absent: its one job in this build (the cloak aura) is
        // free in the original too, and it has no castable spell here yet.
        for (String k : new String[]{"templar", "defiler", "vessel",
                "battlecruiser", "ghost", "corsair", "wraith"}) {
            TYPES.get(k).caster = true;
        }
        // v2.25: the comsat owns the scanner sweep, so it carries a pool too.
        // It is a building, so the spawn path (which only fills pools for
        // tiles == 0) leaves it empty; updateProduction tops it up instead --
        // see the comsat branch there. The ghost's nuclear strike is free
        // (the silo is the cost), so the ghost needs no new pool.
        TYPES.get("comsat").caster = true;

        // --- v2.23: transports, the bunker and the goliath dual weapon ------
        // The three terran/protoss airlift hulls share one capacity constant
        // (8 supply slots). The overlord joins them on the plan explicit
        // permission to skip the Ventral Sacs upgrade; if a later pass wants
        // the upgrade back, it only has to clear cargoCap here.
        for (String k : new String[]{"shuttle", "dropship", "over"}) {
            TYPES.get(k).cargoCap = Game.CARGO_CAP;
        }
        // The bunker holds four infantry supply slots: four marines, or two
        // firebats at 2 slots each. One number covers both.
        TYPES.get("bunker").bunkerCap = Game.BUNKER_CAP;
        // The goliath two guns. 20 air against 12 ground is the original
        // shape and the reason the field exists at all.
        TYPES.get("goliath").dmgAir = 20;

        // --- v2.25: add-on ownership and the tech they unlock --------------
        // Parent -> add-on, and the pad each add-on claims. The science
        // facility is the only parent with two pads in use (physics lab and,
        // in the original, covert ops); this repack ships the lab only.
        TYPES.get("comsat").addonFor = "academy";
        TYPES.get("comsat").addonSlot = 0;
        TYPES.get("controlt").addonFor = "starport";
        TYPES.get("controlt").addonSlot = 0;
        TYPES.get("machineshop").addonFor = "factory";
        TYPES.get("machineshop").addonSlot = 0;
        TYPES.get("physicslab").addonFor = "sciencefac";
        TYPES.get("physicslab").addonSlot = 0;
        TYPES.get("nukesilo").addonFor = "sciencefac";
        TYPES.get("nukesilo").addonSlot = 2;
        // The unit rows the original gates behind an add-on. The field lives on
        // the UNIT (not the building) because a starport with no control tower
        // still builds wraiths -- only the advanced air rows close. The
        // battlecruiser needs the physics lab (the original also wants the
        // control tower, but one gate is enough and the lab is the deeper one).
        TYPES.get("dropship").addonNeeded = "controlt";
        TYPES.get("valkyrie").addonNeeded = "controlt";
        TYPES.get("battlecruiser").addonNeeded = "physicslab";

        // --- v2.26: hangars and ammunition ----------------------------------
        // The carrier's hangar and the reaver's scarab rack. Both are the
        // original's shape and both are what make the unit a siege piece
        // rather than a rifleman: the carrier has to wait for its interceptors
        // and the reaver has to go home for more shells.
        // Qualified names on purpose: the static initializer runs before these
        // constants are declared in source order, and an unqualified forward
        // reference is a compile error (the same reason the cargo block above
        // writes Game.CARGO_CAP).
        TYPES.get("carrier").hangarCap = Game.HANGAR_CAP;
        TYPES.get("reaver").ammoCap = Game.REAVER_AMMO;

        // --- v2.28: upgrade classes ------------------------------------------
        // The original sells weapon and armour upgrades per class. The tags
        // below are that split, mapped onto the three lines this game has room
        // for. The engineering bay / forge / evolution chamber sells the
        // infantry line, the armoury / cybernetics core the vehicle line and
        // the science facility / fleet beacon the ship line -- see the command
        // card, which offers the line of whatever building is selected.
        // infantry: the terran foot soldiers and every protoss/zerg ground
        // unit (the original groups zealots, dragoons and all zerg ground
        // under one ground-weapons line, which is the infantry tag here)
        for (String k : new String[]{"scv", "marine", "firebat", "medic", "ghost",
                "zealot", "dragoon", "templar", "dtemplar", "archon", "darchon",
                "zergling", "hydra", "lurker", "lurker_bur", "ultra", "defiler",
                "broodling", "queen", "drone"}) {
            if (TYPES.containsKey(k)) TYPES.get(k).upClass = "infantry";
        }
        // ships: every aircraft of the three races
        for (String k : new String[]{"wraith", "valkyrie", "battlecruiser",
                "vessel", "dropship", "scout", "corsair", "arbiter", "carrier",
                "intercep", "shuttle", "observer", "over", "muta", "guardian",
                "devourer"}) {
            if (TYPES.containsKey(k)) TYPES.get(k).upClass = "ship";
        }
        // vehicles: the terran mech and the protoss robotics -- units that walk
        // but are neither infantry nor aircraft.
        for (String k : new String[]{"vulture", "goliath", "tank", "stank",
                "reaver", "spider", "larva"}) {
            if (TYPES.containsKey(k)) TYPES.get(k).upClass = "vehicle";
        }
    }

    // ---------------------------------------------------------------- entity
    public static class Ent {
        public Type type;
        public int team;          // 0 player, 1 enemy
        public float x, y;
        public int hp;
        public float cd;          // attack cooldown
        public float facing;      // radians
        public boolean selected;
        public int dir;           // sprite direction 0..16

        /**
         * v2.43 P1: the shared empty path. Clearing a path is a field store
         * instead of an ArrayList.clear(), and a unit that never moved holds no
         * array at all -- with a few hundred units alive that is a few hundred
         * allocations the GC never has to look at.
         */
        public static final int[] EMPTY_PATH = new int[0];

        // movement
        // v2.43 P1: flat packed path -- [x0,y0, x1,y1, ...] in minitile
        // coordinates, no per-node object. The old List<int[]> allocated one
        // int[2] per path node plus the ArrayList's growth, on every path the
        // simulation asked for; an AI wave could do that for dozens of units in
        // one tick. Nothing outside this class indexes the list itself, and the
        // path is never serialised, so the layout is a private detail.
        public int[] path = EMPTY_PATH;
        public int pathIndex;

        /** Number of nodes in {@link #path} (two ints per node). */
        public int pathLen() { return path.length >> 1; }

        /** Drop the path. Shares the immutable empty array, so no allocation. */
        public void clearPath() { path = EMPTY_PATH; }
        public float goalX, goalY;
        public boolean moving;
        // v2.43 P0-c: 0 when no path request of this unit is waiting in the
        // budget queue; otherwise the generation of the one that is. A unit
        // holds at most one queued request (queuePath refreshes goalX/goalY in
        // place rather than adding a second slot), and cancelling is a single
        // store of 0 -- the stale queue slot is then skipped when the consumer
        // sees the generation no longer match. Never serialised: it describes
        // work not yet done, not state.
        public int pathGen;

        // combat
        public Ent target;
        public float animTime;

        // worker state
        public static final int W_IDLE = 0, W_TO_MINE = 1, W_MINING = 2, W_TO_RETURN = 3;
        public int workerState = W_IDLE;
        public Mineral mineTarget;
        public int carrying;
        public boolean haulingGas;
        public Mineral geyser;        // for refineries

        // patrol (v2.5 batch-6): two endpoints the unit walks between forever
        public boolean patrolling;
        public float patrolAX, patrolAY, patrolBX, patrolBY;

        // repair (v2.5 batch-6): SCV mending a friendly damaged unit/building
        public Ent repairTarget;

        /**
         * v2.11: medic heal order. Kept separate from repairTarget even though
         * the two behave almost identically, because they differ in exactly
         * the two ways the plan cares about -- a medic heals for free and may
         * only target living tissue, an SCV pays ore and may fix anything.
         * Folding them together would have meant a boolean on repairTarget
         * that every existing repair call site then had to reason about.
         */
        public Ent healTarget;

        /**
         * v2.11: defiler spell cooldowns, same time-gated shape as stormCd
         * (this game has no energy pool). Dark Swarm makes everything standing
         * inside it untouchable by ranged fire; Ensnare slows what it catches.
         */
        public float dswarmCd, ensnareCd;

        /**
         * v2.11: a spider mine is inert until something hostile walks into it,
         * then it arms for a beat and detonates once. armTime > 0 means it has
         * already tripped and is counting down; it is never re-armed.
         */
        public float armTime;

        // building production
        public List<String> queue = new ArrayList<>();
        public float queueProgress;
        public float rallyX = -1, rallyY = -1;
        public float buildProgress;   // under-construction progress 0..1
        public boolean constructing;
        /**
         * v2.17: protoss and zerg structures build themselves once placed (the
         * original drops the probe/drone and the structure grows on its own),
         * so their sites must not depend on a worker standing next to them.
         * Terran keeps the classic SCV tether: false here means the existing
         * worker-in-range rule still owns the progress.
         */
        public boolean selfBuilding;

        // v2.7 9.1: stimpack window. While > 0 the unit fires faster but has
        // already paid the HP cost up front (see Game.stim()).
        public float stimTime;
        /** Damage/armor bonus this unit has been upgraded to. */
        public int dmgBonus, armorBonus;

        /**
         * v2.10: remaining energy shield. Damage drains this before hp; see
         * Game.damage(). It regenerates after shieldDelay seconds without being
         * hit, so a protoss unit that disengages and comes back is at full
         * strength again -- that regen, not the raw pool, is what makes the
         * shield feel like a shield rather than extra hp.
         */
        public int shield;
        public float shieldDelay;     // counts down; regen resumes at 0
        /**
         * Sub-point carry for shield regen. Without it, an 8 pt/s trickle at
         * 60 fps is 0.13 points a frame, and truncating that to an int every
         * frame would round to nothing and the shield would never recharge.
         */
        public float shieldCarry;

        /**
         * v2.10: psionic storm cooldown, per caster. The game has no energy
         * resource to spend, so the storm is gated on time alone -- a templar
         * that just cast cannot cast again until this hits zero.
         */
        public float stormCd;

        // misc
        public float aiTimer;
        public float flashTime;       // muzzle flash

        /**
         * v2.44: re-path bookkeeping for an attack-moving unit that has stopped
         * short of its goal (see the "nothing in sight" branch in updateUnit).
         * Before this existed the unit simply ended its attack-move lock and
         * stood there forever, which is how AI waves died at their spawn point.
         * Both fields are plain per-unit state advanced by dt, so they stay in
         * lockstep without any extra care.
         */
        public float aiRepathCd;
        public int aiRepathTries;

        /**
         * v2.14 batch 1.3: Hold Position. `holding` is the order; holdX/holdY is
         * the spot the unit was standing on when it was given. The difference
         * from attack-move is exactly one rule: a holding unit never walks. It
         * shoots anything that comes inside its weapon range, but if it is
         * attacked from outside that range -- or charged by melee -- it stands
         * there and takes it. That refusal to chase is the whole point of the
         * order (it is what lets a tank line keep its spacing) and is why this
         * cannot just reuse the attack-move flag.
         */
        public boolean holding;
        public float holdX, holdY;

        /**
         * v2.14 batch 1.5: the four new spell timers, same time-gated shape as
         * stormCd/dswarmCd. `lockdownTime` and `irradiateTime` are the two
         * DURATION effects rather than cooldowns: a locked-down mechanical unit
         * is frozen in place for the window, and an irradiated biological one
         * bleeds hp for the window. Both are applied to the VICTIM, not the
         * caster, which is why they live here next to shieldDelay.
         */
        public float empCd, yamatoCd, lockdownCd, dwebCd;
        public float lockdownTime, irradiateTime, irradiateTick;

        /**
         * v2.22 batch A: the energy pool. Spawned at ENERGY_SPAWN, regenerates
         * at ENERGY_REGEN per second, spent by the nine spell gates. A unit
         * whose type is not `caster` keeps maxEnergy 0 and every gate treats
         * it as "no energy" -- the view grays its cells for free.
         */
        public float energy, maxEnergy;

        /**
         * v2.22 batch B: the cloak state. `cloakOn` is the player's toggle
         * (type.cloak == 2 only); `cloakActive` is the per-tick net result --
         * permanent types, the toggle, the burrowed lurker, or standing in an
         * arbiter's aura. `spotted` is the per-tick answer to "an enemy
         * detector sees this unit". Both are recomputed in updateCloak(), so
         * targeting and drawing read a flag instead of rescanning the map.
         */
        public boolean cloakOn, cloakActive, spotted;

        /**
         * v2.23 batch A: transport cargo. A loaded unit is taken off the field
         * without leaving the roster: `cargoOf` points at its carrier, and
         * every field interaction (targeting, pathing, fog, splash, drawing,
         * picking) tests it and skips the unit. Keeping it in `ents` is what
         * lets the original's supply rule and the save format stay untouched --
         * a loaded marine still costs its one supply, exactly as it does in
         * StarCraft. `cargo` is the carrier's side of the same relation.
         */
        public Ent cargoOf;
        public final List<Ent> cargo = new ArrayList<>();

        /**
         * v2.23 batch B: true while this unit is garrisoned inside a bunker.
         * Same shape as cargo -- the unit is off the field, keeps its supply --
         * but a garrisoned unit still SHOOTS (the bunker is a firing position,
         * not a parking spot), so it is a separate flag rather than a reuse of
         * cargoOf.
         */
        public boolean garrisoned;

        /** v2.23 batch B: the bunker this unit is standing in, or null. */
        public Ent bunker;

        // ------------------------------------------------ v2.25 add-ons
        /**
         * The parent building this entity is an add-on of, resolved at
         * placement. Null for everything that is not an add-on. Kept as a
         * reference rather than a coordinate because the pad is fixed to the
         * parent and the parent's death is then a single scan.
         */
        public Ent addonParent;
        /**
         * The armed state of a nuclear silo: true once a missile has finished
         * building and the silo is waiting for a ghost to call the strike.
         * Only ever set on nukesilo.
         */
        public boolean nukeArmed;
        /** Build progress of the missile in an armed silo, 0..1. */
        public float nukeProgress;
        /**
         * A ghost calling a nuclear strike is rooted for the countdown: while
         * nukeLock > 0 the unit ignores move orders, which is the window the
         * original gives the defender to kill the spotter and cancel the hit.
         */
        public float nukeLock;
        /** Where the pending strike was called, for the ghost's aiming pose. */
        public float nukeX, nukeY;
        /**
         * v2.26: the carrier's hangar. `interceptors` is how many are docked,
         * `launched` how many are currently out (they fly home when the
         * carrier dies or the count exceeds what the hangar holds).
         */
        public int interceptors, launched;
        /** v2.26: the reaver's scarab ammo, refilled beside its factory. */
        public int ammo;
        /** v2.26: an interceptor tracks the carrier it belongs to. */
        public Ent carrier;
        /** v2.26: a scarab is in flight from this reaver to its target. */
        public float scarabT;
        public Ent scarabTarget;
        /** v2.26: true while a zerg unit is hiding underground. */
        public boolean burrowed;
        /** v2.26: the carrier's interceptor build clock and the reaver's reload. */
        public float interceptorCd, ammoCd;

        /**
         * v2.23 batch A: the unit this transport has been told to collect.
         * The pickup sweep runs only while this is set, so a transport never
         * hoovers up friendly units on its own -- which matters because the
         * overlord is a transport too and it drifts over the player base all
         * game. Cleared once the unit is aboard.
         */
        public Ent loadTarget;

        /**
         * v2.14 batch 1.5: disruption web. Unlike ensnare this is NOT stored on
         * the victim -- it is a placed field (see the Dweb class) because the
         * web blocks the SHOOTER, and a shooter has to be able to ask "am I
         * standing in one" without having been touched by anything. `dwebTime`
         * is kept for the view's per-unit tint.
         */
        public float dwebTime;

        /**
         * v2.14 batch 1.6: true while this unit belongs to the AI's current
         * attacking wave. It exists so the retreat test can measure the wave's
         * losses -- counting every AI unit would include the ones still being
         * produced at home, and the army would never look depleted.
         */
        public boolean waveUnit;

        public boolean alive() {
            return hp > 0;
        }

        public boolean isBuilding() {
            return type.tiles > 0;
        }
    }

    public static class Mineral {
        public float x, y;
        public int amount;
        public int variant;       // 0..2 mineral, 3 = geyser
        public Ent refinery;      // set when a refinery sits on this geyser
        public List<Ent> claimers = new ArrayList<>();
    }

    // ------------------------------------------------------------- animations
    /** Sprite key of the death sequence for a unit type, or null if none. */
    public static String deathAnimFor(String typeKey) {
        if (typeKey.equals("marine")) return "death_marine";
        if (typeKey.equals("zergling")) return "death_zergling";
        if (typeKey.equals("hydra")) return "death_hydra";
        // v2.10: the three protoss ground castes have real death sequences in
        // their GRPs (zealot block 13, dragoon block 24, templar block 17 --
        // found by probe_v210o.py's cyan/brightness scan, not by eye).
        if (typeKey.equals("zealot")) return "death_zealot";
        if (typeKey.equals("dragoon")) return "death_dragoon";
        if (typeKey.equals("templar")) return "death_templar";
        // v2.11: the Brood War rows that actually contain a death block in
        // their GRP. Only these five do -- probe_v211bl.py's red-burst scan
        // found no death block at all in queen, guardian, broodling or
        // devourer, so those fall through to the generic explosion, which is
        // what they look like in the original too.
        if (typeKey.equals("ultra")) return "death_ultra";
        if (typeKey.equals("defiler")) return "death_defiler";
        if (typeKey.equals("lurker")) return "death_lurker";
        if (typeKey.equals("lurker_bur")) return "death_lurker_bur";
        if (typeKey.equals("medic")) return "death_medic";
        return null;
    }

    /** Sprite key of the explosion for a building footprint. */
    public static String bangFor(int tiles) {
        if (tiles >= 4) return "bang_l";
        if (tiles >= 3) return "bang_m";
        return "bang_s";
    }

    /** Frame count of each effect sheet, so one-shot anims end exactly on time. */
    public static int animFrames(String key) {
        if (key == null) return 0;
        switch (key) {
            case "bang_s": return 9;
            case "bang_m": return 10;
            case "bang_l": return 14;
            case "death_marine": return 8;
            case "death_zergling": return 7;
            case "death_hydra": return 8;
            case "death_terran": return 4;
            case "flsh_s": return 9;
            case "flsh_m": return 9;
            case "flsh_l": return 10;
            case "smoke": return 8;
            case "hit": return 12;
            // v2.10 protoss: three death sequences (7 frames each -- the death
            // block of the source GRP) plus the effect sheets.
            case "death_zealot": return 7;
            case "death_dragoon": return 7;
            case "death_templar": return 7;
            case "psistorm": return 14;
            case "pshield": return 68;
            case "b_pspark": return 8;
            case "pcirglow": return 4;
            // v2.11 batch B/C. Every one of these sheets is written with 8
            // columns, and a one-shot effect plays one column-run -- so 8 is
            // the count for all of them except the small ensnare goo, which
            // only has 4 frames in its GRP. This is the same convention the
            // terran/protoss death anims above already use.
            case "death_ultra": return 8;
            case "death_defiler": return 8;
            case "death_lurker": return 8;
            case "death_lurker_bur": return 8;
            case "death_medic": return 8;
            case "dswarm": return 8;
            case "ensgoo_s": return 4;
            case "ensgoo_m": return 4;
            case "ensgoo_l": return 4;
            case "maelhit": return 8;
            case "heal": return 8;
            // v2.14 batch 1.5: the caster-spell effects. The counts are the
            // real frame counts of the GRPs behind them, NOT the usual 8: emp
            // is 7 frames, empl (the green irradiate cloud) 7, elect02 (the
            // lockdown crackle) 6, and the rest are capped by the pipeline's
            // ANIM_COUNTS so they play one readable pass instead of the whole
            // file. Playing more frames than the sheet has would just hold the
            // last cell, so these must track the pipeline.
            case "emp": return 7;
            case "ehamed": return 7;
            case "elect02": return 6;
            case "dweb": return 8;
            case "b_blastcan": return 8;
            case "plasma": return 17;
            // v2.25: the nuclear burst and the falling trail. Counts match
            // ANIM_COUNTS in pipeline_sprites.py, which caps the sheets.
            case "nukehit": return 26;
            case "nukebeam": return 20;
            case "nuketarg": return 2;
            default: return 8;
        }
    }

    /** Play a one-shot sprite animation. `fps` is frames per second. */
    public void playAnim(String key, float x, float y, int frames, int team,
                         float fps, float scale) {
        if (key == null || frames <= 0) return;
        Anim a = new Anim();
        a.key = key;
        a.x = x;
        a.y = y;
        a.frames = frames;
        a.frameTime = 1f / fps;
        a.team = team;
        a.scale = scale;
        anims.add(a);
    }

    // ---------------------------------------------------------------- world
    public final int wTiles, hTiles;
    public final int wMini, hMini;
    public final boolean[] walk;          // minitile grid (wMini x hMini)
    /**
     * v2.23 batch C: the ground level, one byte per minitile, same grid as
     * `walk`: 0 = low, 1 = mid, 2 = high. The VF4 minitile flag words carry it
     * in bit 1 (mid, 0x0002) and bit 2 (high, 0x0004); bit 0 is walkability and
     * bit 4 marks a ramp.
     *
     * Both elevated levels are kept rather than a single high/low flag because
     * the shipped maps use them differently: Lost Temple has no "high" ground
     * at all and puts its mains on mid plateaus, while King of the Hill has
     * both. Comparing levels instead of testing a boolean is what makes the
     * miss rule work on both. Null when the map ships no elevation data, which
     * makes every test read the same level and the whole rule a no-op on an
     * old asset tree.
     */
    public final byte[] elev;
    public final byte[] fog;              // 0 unseen, 1 explored, 2 visible (per tile)
    public final int wPx, hPx;

    /**
     * v2.43 P1: plain ArrayList, not CopyOnWriteArrayList.
     *
     * The roster is only ever touched from the thread that runs update() and
     * render(): the renderer drives update() itself (GameView.run), every
     * GameView call site runs on that same thread, and the one cross-thread
     * write channel -- Game.post() -- queues Runnables into a separate
     * synchronized list that is drained at the top of update(). The decode
     * pool threads only touch MapData chunks. So there is no reader to protect
     * and COW was buying nothing but a full array copy on every spawn, death
     * and shot resolution.
     *
     * Determinism is unaffected: iteration order is still the insertion order
     * of a single writer, which is what the lockstep peers both see.
     */
    public final List<Ent> ents = new ArrayList<>();

    /**
     * v2.43 P0-a: how many live arbiters and detectors each team has on the
     * field.
     *
     * isCloakedNow() used to walk the whole roster looking for a friendly
     * arbiter on EVERY query, and detectorNear() did the same for detectors --
     * and updateCloak() asks both once per unit per tick. With no arbiter or
     * detector anywhere on the map (every map this game ships, and every game
     * until someone builds one) that was two full N x N scans per tick whose
     * only possible answer was "false".
     *
     * These counts are rebuilt by one O(N) pass per tick, right before the
     * only consumer. That pass is the same order as updateFog(), which already
     * walks the roster every tick, so it is free next to the N x N it removes.
     *
     * A dirty-flag version would have been cheaper still, but it has a failure
     * mode this one does not: any path that mutates the roster without telling
     * the counts (the desktop harness does exactly that) leaves the count too
     * LOW, and a too-low count hides a real arbiter -- a gameplay bug. One
     * unconditional pass cannot be stale at all.
     */
    private final int[] arbCount = new int[2];
    private final int[] detCount = new int[2];

    /**
     * v2.43 P0-b: the arbiters and the detectors themselves.
     *
     * The count above answers "is there one at all" in O(1), which is what
     * makes the short-circuit work on the maps this game actually ships. On a
     * map that DOES have one, the old code fell back to a full roster walk --
     * per cloaked unit, per tick -- to find the handful of entries the count
     * had already proven existed. These lists are filled by the same pass that
     * fills the counts, so that walk becomes "iterate the two arbiters".
     *
     * References rather than roster indices on purpose. An index would be
     * cheaper still, but it goes stale the moment anything removes from the
     * roster out of band (the desktop harness does exactly that), and a stale
     * index either throws or silently points at a different unit. A reference
     * cannot do either: the worst a stale entry can do is be filtered by the
     * liveness gate the query already applies, which is what the old full
     * scan did with a corpse that had not been swept yet.
     *
     * Filled in roster order, so a query that stops at the first match stops
     * on the same entry the old full scan would have stopped on. Both methods
     * return a boolean, but that boolean is read by the lockstep simulation,
     * so "same answer" is not enough -- both peers have to reach it the same
     * way, and roster order is what both of them agree on.
     */
    private Ent[] arbList = new Ent[8];
    private int arbListN;
    private Ent[] detList = new Ent[8];
    private int detListN;

    /**
     * v2.43 P0-a: false until the counts have been built at least once.
     *
     * The per-tick rebuild in update() is what keeps them fresh; this flag
     * exists only so a query made before the first tick (a unit test, or a
     * caller poking isCloakedNow() on a fresh Game) rebuilds rather than
     * reading an all-zero array and reporting "no arbiter anywhere".
     */
    private boolean auraCountsValid;

    /**
     * v2.43 P0-a: rebuild the arbiter/detector counts unconditionally.
     *
     * Called once per tick from update(), immediately before the only
     * consumer. One O(N) pass per tick is the same order as updateFog(),
     * which already walks the roster every tick, so it is free next to the
     * N x N it removes.
     *
     * A dirty-flag version would be cheaper still, but it has a failure mode
     * this one does not: any path that mutates the roster without telling the
     * counts (the desktop harness does exactly that) leaves the count too
     * LOW, and a too-low count hides a real arbiter -- a gameplay bug. An
     * unconditional pass cannot be stale at all.
     *
     * Note what is NOT filtered here: liveness and `constructing`. The counts
     * answer "does the roster even contain one of these", not "is one of them
     * currently working". Counting a still-constructing arbiter or a corpse
     * that has not been swept yet only makes the count too HIGH, which costs
     * the full scan we used to always do and is therefore always correct.
     * Filtering them here would make the count too LOW for the tick between a
     * stargate finishing an arbiter and the next rebuild.
     */
    private void rebuildAuraCounts() {
        arbCount[0] = 0;
        arbCount[1] = 0;
        detCount[0] = 0;
        detCount[1] = 0;
        arbListN = 0;
        detListN = 0;
        for (int i = 0, n = ents.size(); i < n; i++) {
            Ent e = ents.get(i);
            int t = e.team == 1 ? 1 : 0;
            if ("arbiter".equals(e.type.key)) {
                arbCount[t]++;
                if (arbListN == arbList.length) arbList = java.util.Arrays.copyOf(arbList, arbListN * 2);
                arbList[arbListN++] = e;
            }
            if (e.type.detector) {
                detCount[t]++;
                if (detListN == detList.length) detList = java.util.Arrays.copyOf(detList, detListN * 2);
                detList[detListN++] = e;
            }
        }
        auraCountsValid = true;
    }

    /**
     * v2.43 P0-a: mark the arbiter/detector counts as needing a rebuild.
     *
     * Called from every path that can change the roster's type composition:
     * spawn, the death sweep, the mission/load clears, and toggleSiege. The
     * per-tick rebuild would catch all of those on the next tick anyway --
     * this is what makes a query issued between the mutation and the next
     * tick see the truth instead of the previous tick's answer.
     */
    private void invalidateAuraCounts() {
        auraCountsValid = false;
        // v2.43 P0-b: the spatial grid is indexed by roster position and the
        // building list by type, so every path that invalidates the aura
        // counts invalidates both structures for exactly the same reason -- the
        // roster's composition changed. Sharing the hook keeps the two from
        // drifting apart, which is the failure mode that would show up as "a
        // unit is invisible to targeting until something else forces a
        // rebuild". The per-tick rebuild in update() is what keeps them fresh
        // during play; this is the fallback for a query issued between a
        // mutation and the next tick (the desktop harness does exactly that).
        spatialValid = false;
    }

    /**
     * v2.43 P0-a: rebuild the counts only if the tick has not done it yet.
     *
     * The per-tick rebuild in update() is what keeps them fresh; this is the
     * fallback for a query made before the first tick -- a unit test, or a
     * caller poking isCloakedNow() on a fresh Game. Without it such a query
     * would read an all-zero array and answer "no arbiter anywhere".
     */
    private void ensureAuraCounts() {
        if (!auraCountsValid) rebuildAuraCounts();
    }

    // ------------------------------------------------------------------
    // v2.43 P0-b: the spatial grid
    //
    // Seven loops in this class used to walk the whole roster once per unit,
    // per tick -- separation, building collision, enemy acquisition, splash,
    // and the "nearest building" helpers. At 200 units that is 280k gate
    // evaluations per tick before the renderer has drawn anything, and it is
    // the largest single reason a big battle stutters.
    //
    // The grid replaces "walk everything and reject" with "walk the few cells
    // that could possibly hold a hit". It is rebuilt from scratch once per
    // tick in a single O(N) pass, because incremental maintenance is where
    // this kind of structure usually goes wrong: an incremental grid has to be
    // patched by every spawn, every death and every teleport (a building
    // push-out moves a unit much further than it walks), and one missed patch
    // shows up as a unit that mysteriously cannot be shot.
    //
    // ORDER IS THE CONTRACT. The old loops visited candidates in roster order
    // and three of the call sites depend on it: separation accumulates a float
    // sum (floating-point addition is not associative), building collision
    // mutates the unit's position as it goes, and the "nearest" helpers break
    // ties by keeping the first strictly-closer candidate. gatherNear() hands
    // back candidates sorted by roster index, so every rewritten loop sees
    // exactly the sequence the full scan would have produced. That is what
    // keeps the assertion suite and any recorded replay identical to v2.42.
    //
    // Determinism: the grid is built from the roster in roster order and read
    // in a fixed cell order, so two lockstep peers build and read identical
    // structures. Sorting can only ever produce the one sorted answer, no
    // matter which algorithm the runtime uses to get there.
    // ------------------------------------------------------------------

    /** World px per grid cell. */
    private static final int GRID_CELL = 64;

    /**
     * Slack, in world px, added to every query box.
     *
     * The grid records where units were when the tick started, but a query can
     * run after those units have moved. Displacement within one tick is bounded
     * by the path step (140 px/s at 1/60 s is 2.3 px) plus the separation push,
     * itself capped below that step. A whole cell of slack is sixteen times the
     * realistic worst case, which leaves room for the pathological one: a
     * building push-out can move a unit tens of px in a single frame. The box
     * only decides who gets looked at; every call site still applies its exact
     * distance test.
     */
    private static final int GRID_MARGIN = 64;

    private boolean spatialValid;
    private int gridW, gridH;
    private int[] cellCount;    // scratch: per-cell population, then write cursor
    private int[] cellStart;    // gridW*gridH+1 prefix offsets into cellItems
    private int[] cellItems;    // roster indices, cell-major, roster order within a cell
    private int[] qScratch = new int[256];   // candidates for the query in flight
    private int qScratchN;
    private Ent[] bldList = new Ent[64];     // live non-flying buildings, roster order
    private int bldListN;
    private Ent[] dropList = new Ent[32];    // live completed team-0 buildings, roster order
    private int dropListN;
    private static float maxUnitRadiusCache = -1f;
    private static float maxBuildHalfCache = -1f;

    public int statGridRebuilds;
    public int statGridQueries;
    public int statGridCandidates;

    /** Largest radius among the non-building types; the reach separation needs. */
    private static float maxUnitRadius() {
        if (maxUnitRadiusCache < 0f) {
            float m = 0f;
            for (Type t : TYPES.values()) if (t.tiles == 0 && t.radius > m) m = t.radius;
            maxUnitRadiusCache = m;
        }
        return maxUnitRadiusCache;
    }

    /** Largest half-footprint among the building types, i.e. max(tiles) * 16. */
    private static float maxBuildingHalf() {
        if (maxBuildHalfCache < 0f) {
            float m = 0f;
            for (Type t : TYPES.values()) if (t.tiles > 0 && t.tiles * 16 > m) m = t.tiles * 16;
            maxBuildHalfCache = m;
        }
        return maxBuildHalfCache;
    }

    private int cellX(float x) {
        int c = (int) Math.floor(x / GRID_CELL);
        return c < 0 ? 0 : (c >= gridW ? gridW - 1 : c);
    }

    private int cellY(float y) {
        int c = (int) Math.floor(y / GRID_CELL);
        return c < 0 ? 0 : (c >= gridH ? gridH - 1 : c);
    }

    /**
     * One O(N) pass: bucket every roster entry by the cell it stands in, and
     * collect the completed team-0 buildings.
     *
     * Counting sort rather than a list per cell, so a rebuild allocates
     * nothing in the steady state and the buckets come out contiguous, which
     * is what makes a query a pair of array reads per cell.
     */
    private void rebuildSpatial() {
        int gw = (wPx + GRID_CELL - 1) / GRID_CELL;
        int gh = (hPx + GRID_CELL - 1) / GRID_CELL;
        if (gw < 1) gw = 1;
        if (gh < 1) gh = 1;
        int cells = gw * gh;
        if (cellCount == null || cellCount.length != cells) {
            cellCount = new int[cells];
            cellStart = new int[cells + 1];
        }
        gridW = gw;
        gridH = gh;
        int n = ents.size();
        if (cellItems == null || cellItems.length < n) {
            cellItems = new int[Math.max(16, n)];
        }
        java.util.Arrays.fill(cellCount, 0);
        bldListN = 0;
        dropListN = 0;
        // pass 1: population per cell, plus the building lists
        for (int i = 0; i < n; i++) {
            Ent e = ents.get(i);
            cellCount[cellY(e.y) * gw + cellX(e.x)]++;
            if (e.isBuilding() && e.alive() && !e.type.flying) {
                if (bldListN == bldList.length) {
                    bldList = java.util.Arrays.copyOf(bldList, bldListN * 2);
                }
                bldList[bldListN++] = e;
            }
            if (e.team == 0 && e.isBuilding() && e.alive() && !e.constructing) {
                if (dropListN == dropList.length) {
                    dropList = java.util.Arrays.copyOf(dropList, dropListN * 2);
                }
                dropList[dropListN++] = e;
            }
        }
        // prefix sums
        int acc = 0;
        for (int c = 0; c < cells; c++) {
            cellStart[c] = acc;
            acc += cellCount[c];
        }
        cellStart[cells] = acc;
        // pass 2: scatter in roster order, so each bucket is in roster order
        for (int c = 0; c < cells; c++) cellCount[c] = cellStart[c];
        for (int i = 0; i < n; i++) {
            Ent e = ents.get(i);
            cellItems[cellCount[cellY(e.y) * gw + cellX(e.x)]++] = i;
        }
        spatialValid = true;
        statGridRebuilds++;
    }

    private void ensureSpatial() {
        if (!spatialValid) rebuildSpatial();
    }

    private void ensureScratch(int need) {
        if (qScratch.length < need) {
            qScratch = new int[Math.max(need, qScratch.length * 2)];
        }
    }

    /**
     * Roster indices of everything that could be within `reach` world px of
     * (x, y), ascending, in qScratch; returns how many.
     *
     * Ascending by roster index is the whole point -- see the block comment
     * above. A query that covers most of the map falls back to a full walk,
     * which is both cheaper than touching every cell and trivially ordered.
     *
     * NOT reentrant: qScratch is shared. Every current call site consumes its
     * candidates before anything else can ask for a set.
     */
    private int gatherNear(float x, float y, float reach) {
        ensureSpatial();
        statGridQueries++;
        qScratchN = 0;
        float span = reach + GRID_MARGIN;
        int cx0 = cellX(x - span), cx1 = cellX(x + span);
        int cy0 = cellY(y - span), cy1 = cellY(y + span);
        int boxCells = (cx1 - cx0 + 1) * (cy1 - cy0 + 1);
        int n = ents.size();
        if (boxCells * 4 >= gridW * gridH) {
            ensureScratch(n);
            for (int i = 0; i < n; i++) qScratch[qScratchN++] = i;
            statGridCandidates += qScratchN;
            return qScratchN;
        }
        int need = 0;
        for (int cy = cy0; cy <= cy1; cy++) {
            int base = cy * gridW;
            for (int cx = cx0; cx <= cx1; cx++) {
                int c = base + cx;
                need += cellStart[c + 1] - cellStart[c];
            }
        }
        ensureScratch(need);
        for (int cy = cy0; cy <= cy1; cy++) {
            int base = cy * gridW;
            for (int cx = cx0; cx <= cx1; cx++) {
                int c = base + cx;
                for (int k = cellStart[c], ke = cellStart[c + 1]; k < ke; k++) {
                    qScratch[qScratchN++] = cellItems[k];
                }
            }
        }
        java.util.Arrays.sort(qScratch, 0, qScratchN);
        statGridCandidates += qScratchN;
        return qScratchN;
    }

    /**
     * v2.43 P0-a: the roster index the main update loop is currently at, so
     * updateUnit() can phase-stagger its idle target acquisition. A plain
     * field rather than a parameter because updateUnit/updateBuilding are
     * called from exactly one place, and because the phase has to be derived
     * from the SAME index the loop is walking -- deriving it from anything
     * else would make the two peers disagree about which units acquire this
     * tick, which is a desync.
     */
    private int curRosterIdx;

    /**
     * v2.43 P0-a: how many ticks the idle-acquire phase is spread over.
     */
    private static final int ACQUIRE_PHASES = 8;

    /**
     * v2.43 P0-a: scan counters, for the desktop assertion only.
     *
     * These are deliberately NOT part of stateHash(): they measure how much
     * work the simulation did, not what it computed, so two peers may legally
     * disagree about them (they will not -- the stagger is index-keyed and the
     * short-circuit is state-keyed -- but they must never be allowed to make
     * a match desync). They exist so the optimisation can be asserted by
     * number instead of by reading the source and hoping.
     *
     * "Queries" counts how many times a caller asked; "scans" counts how many
     * of those fell through to a full roster walk. The whole point of the
     * short-circuit is that the second number stays at zero on a map with no
     * arbiters and no detectors, which is every map this game ships.
     */
    public int statAuraQueries;
    public int statAuraScans;
    public int statAcquireQueries;
    public int statAcquireScans;

    /**
     * v2.43 P0-a: roster size at which idle auto-acquire starts phase-staggering.
     *
     * The stagger trades acquisition latency (up to 8 ticks, ~0.27s at 30Hz)
     * for scan volume, and below this size there is no scan volume worth
     * trading for. Keeping the un-staggered path for small rosters also means
     * a skirmish behaves exactly as it did in v2.42, which is what makes the
     * change reviewable: only big games move.
     */
    private static final int ACQUIRE_STAGGER_MIN = 24;

    public final List<Mineral> minerals = new ArrayList<>();
    public final List<Shot> shots = new ArrayList<>();
    public final List<float[]> effects = new ArrayList<>(); // x,y,life,kind
    /** Sprite-sheet animations (explosions, death sequences). */
    public final List<Anim> anims = new ArrayList<>();

    public int mineralsPlayer = 400;
    public int gasPlayer = 0;
    public int supplyUsed, supplyCap;
    public float time;

    // ---- end-of-game scoreboard (v2.7 batch 7.1). Counted here rather than in
    // the view so the numbers survive a save/load and can be asserted from the
    // desktop harness.
    public int kills;              // enemy units/buildings destroyed
    public int losses;             // own units/buildings lost
    public int mineralsMined;      // total minerals delivered to a command center
    public int gasMined;           // total gas delivered to a refinery
    public int difficulty = 1;        // 0 easy, 1 normal, 2 hard

    /**
     * v2.8: which army the player commands. "terran" keeps the original
     * v2.x behaviour; "zerg" swaps the worker/building keys the economy,
     * production and construction code look for. Stored as a string so a
     * save file stays readable and a future third race needs no new enum.
     */
    public String race = "terran";

    /** True for both worker kinds -- the economy code keys off this. */
    public static boolean isWorkerType(String key) {
        return "scv".equals(key) || "drone".equals(key) || "probe".equals(key);
    }

    public static boolean isWorker(Ent e) {
        return e != null && isWorkerType(e.type.key);
    }

    /** Buildings that accept a returning worker's load. */
    public static boolean isDropOff(String key) {
        return "cc".equals(key) || "hatchery".equals(key)
                || "lair".equals(key) || "hive".equals(key)
                || "nexus".equals(key);
    }

    /** Refinery and its zerg/protoss equivalents; all snap onto a geyser. */
    public static boolean isGasBuilding(String key) {
        return "refinery".equals(key) || "extractor".equals(key)
                || "assim".equals(key);
    }

    /** Supply a finished building contributes. 0 when it provides none. */
    public static int supplyProvided(String key) {
        return supplyProvided(key, 1f);
    }

    /**
     * v2.27: supply per building, scaled by the current cap tier. The tier
     * multiplies what each provider gives so the number of depots a player
     * needs tracks the cap instead of the cap outrunning them -- at the 100
     * tier a depot feeds 20 and a command centre 25.
     */
    public static int supplyProvided(String key, float tier) {
        int base;
        if ("cc".equals(key)) base = 10;
        // A hatchery feeds as much as a command center, so a zerg opening is
        // not supply-starved from the first second; lair/hive are upgrades of
        // the same building and keep the same figure.
        else if ("hatchery".equals(key) || "lair".equals(key)
                || "hive".equals(key)) base = 10;
        else if ("depot".equals(key)) base = 8;
        else if ("over".equals(key)) base = 8;      // overlord carries supply
        // v2.10: the pylon is the protoss supply building. 8, like a depot,
        // because a protoss opening leans on a single pylon for its first
        // zealots and 10 would let the forge line run supply-free.
        else if ("pylon".equals(key)) base = 8;
        else return 0;
        return Math.round(base * tier);
    }
    public volatile float gasBonus = 0f;   // unused placeholder for future

    // commands posted from the UI thread, executed on the game thread
    private final List<Runnable> pendingOrders = new ArrayList<>();

    /** Sound events drained by the view each frame:
     *  {"dead", tiles:int} {"trained", key:String} {"built"} */
    public final List<Object[]> events = new ArrayList<>();

    /** Thread-safe: enqueue a game-state mutation from the UI thread. */
    public void post(Runnable r) {
        synchronized (pendingOrders) {
            pendingOrders.add(r);
        }
    }

    // ------------------------------------------------ v2.16 batch 4: replay
    // The core is already deterministic: one Random(12345) per Game, a fixed
    // 1/30 update step, and no wall-clock reads (time is accumulated dt). So a
    // replay only has to record the player's commands with the tick they were
    // issued on, and re-inject them at the same tick into a fresh Game built
    // from the same map/race/difficulty. Everything else re-simulates.
    //
    // Commands are recorded as text lines ("<tick> <verb> <args...>") in the
    // same spirit as the save format, so a replay stays diffable.
    public int tick;                       // fixed-step simulation counter
    public boolean recording;
    public final java.util.List<String> replayLog = new java.util.ArrayList<>();
    public String mapId = "";
    /**
     * v2.29: the map's meta.txt, set by the view alongside mapId. A mission
     * with "economy": true re-parses it in setMission to restore the resource
     * rows the skirmish clear removed. Null (the desktop harness, an old
     * caller) simply means "no economy restore", which is the old behaviour.
     */
    public String mapMeta;
    public String replayVersion = "2.20";

    // ---- v2.30: local-network lockstep
    /**
     * Non-null while this Game is one peer of a lockstep match. When set, the
     * order path goes through the session instead of the local replay log (see
     * recordCommand) and update() gates on the session being ready for the
     * current turn. Null -- the desktop harness, a replay, an ordinary
     * skirmish -- leaves every existing path byte-for-byte unchanged.
     */
    public Lockstep lockstep;
    /** Which player this peer is; index into the session's canonical order. */
    public int lockstepPlayer;

    /** Append one command at the current tick while recording. */
    public void recordCommand(String cmd) {
        // v2.30: in a lockstep session a command is not appended to the local
        // replay log -- it is submitted to the session, and every player's
        // commands for a turn are applied from the session's canonical order.
        // The local player's own order is no exception, which is why a lockstep
        // order takes effect on the NEXT turn rather than this one. That is the
        // definition of lockstep, not a latency bug: at 30 Hz the wait is one
        // frame (33 ms).
        if (lockstep != null) {
            lockstep.submit(lockstepPlayer, cmd);
            return;
        }
        if (recording && !replayMode) replayLog.add(tick + " " + cmd);
    }

    // ---- v2.19 batch 5: playback
    /** True while a replay is being re-simulated; input orders are ignored. */
    public boolean replayMode;
    /** Parsed replay: {tick, "verb idxs args"} in file order. */
    private final java.util.List<String[]> replayLines = new java.util.ArrayList<>();
    private int replayIdx;

    /**
     * Record one order with the exact entity indices it acted on. Carrying the
     * selection in the command means playback needs no separate "select" rows
     * and cannot drift if the UI selection changes for its own reasons.
     */
    public void recordOrder(String verb, java.util.List<Ent> sel, String args) {
        // v2.30: one builder for the recorded form and the lockstep form, so a
        // lockstep order and a replay row are guaranteed to be the same string.
        String cmd = commandFor(verb, sel, args);
        if (lockstep != null) {
            lockstep.submit(lockstepPlayer, cmd);
            return;
        }
        if (!recording || replayMode) return;
        replayLog.add(tick + " " + cmd);
    }

    /**
     * v2.31: render one order as the command string the replay format and the
     * lockstep wire both use: "verb idx,idx,... args". Carrying the selection
     * as entity indices is what makes a command self-contained -- neither the
     * replay nor the peer needs a separate "select" row, and neither can drift
     * if the UI selection changes for its own reasons.
     */
    public String commandFor(String verb, java.util.List<Ent> sel, String args) {
        StringBuilder sb = new StringBuilder(verb).append(' ');
        if (sel != null) {
            boolean first = true;
            for (Ent e : sel) {
                int i = ents.indexOf(e);
                if (i < 0) continue;
                if (!first) sb.append(',');
                sb.append(i);
                first = false;
            }
        }
        if (args != null && !args.isEmpty()) sb.append(' ').append(args);
        return sb.toString();
    }

    /** Load a serialized replay for playback. Returns success. */
    public boolean loadReplay(String text) {
        replayLines.clear();
        replayIdx = 0;
        if (text == null) return false;
        for (String line : text.split("\n")) {
            line = line.trim();
            if (line.startsWith("cmd ")) line = line.substring(4).trim();
            else if (!line.isEmpty() && Character.isDigit(line.charAt(0))) {
                // "tick verb args" from replayLog
            } else {
                continue;   // header line
            }
            int sp = line.indexOf(' ');
            if (sp <= 0) continue;
            String t = line.substring(0, sp), rest = line.substring(sp + 1).trim();
            try { Integer.parseInt(t); } catch (Exception e) { continue; }
            replayLines.add(new String[]{t, rest});
        }
        replayMode = true;
        return true;
    }

    /** Apply every recorded command scheduled for the current tick. */
    private void injectReplay() {
        String now = String.valueOf(tick);
        while (replayIdx < replayLines.size()
                && replayLines.get(replayIdx)[0].equals(now)) {
            applyCommand(replayLines.get(replayIdx)[1]);
            replayIdx++;
        }
    }

    /** True once the replay has no more commands to inject. */
    public boolean replayFinished() {
        return replayMode && replayIdx >= replayLines.size();
    }

    /** How many replay rows have been injected so far (desktop assertions). */
    public int replayInjected() {
        return replayIdx;
    }

    /** How many replay rows the loaded stream holds. */
    public int replayCount() {
        return replayLines.size();
    }

    /** A selection command, recorded whenever the player changes selection. */
    public void recordSelect(java.util.List<Ent> sel) {
        if (!recording) return;
        StringBuilder sb = new StringBuilder("select");
        for (Ent e : sel) {
            int i = ents.indexOf(e);
            if (i >= 0) sb.append(' ').append(i);
        }
        recordCommand(sb.toString());
    }

    public String replayHeader() {
        return "XJZB-REPLAY-1\nmap " + mapId + " race " + race
                + " difficulty " + difficulty + " version " + replayVersion
                + "\nseed 12345\n";
    }

    public String serializeReplay() {
        StringBuilder sb = new StringBuilder(replayHeader());
        for (String line : replayLog) sb.append("cmd ").append(line).append('\n');
        return sb.toString();
    }

    /**
     * v2.20 batch 5: the one-line blurb the replay browser shows. The header is
     * the same text serializeReplay() writes, so parsing it here keeps the list
     * and the file from ever disagreeing.
     */
    public static String replaySummary(String text) {
        String map = "?", race = "?", diff = "?";
        int cmds = 0, last = 0;
        if (text != null) {
            for (String line : text.split("\\n")) {
                line = line.trim();
                if (line.startsWith("map ")) {
                    String[] tok = line.split(" ");
                    for (int i = 0; i + 1 < tok.length; i++) {
                        if ("map".equals(tok[i])) map = tok[i + 1];
                        else if ("race".equals(tok[i])) race = tok[i + 1];
                        else if ("difficulty".equals(tok[i])) diff = tok[i + 1];
                    }
                } else if (line.startsWith("cmd ")) {
                    cmds++;
                    int sp = line.indexOf(' ', 4);
                    if (sp > 4) {
                        try { last = Integer.parseInt(line.substring(4, sp)); }
                        catch (Exception ignored) { }
                    }
                }
            }
        }
        String raceName = "terran".equals(race) ? "人族"
                : ("zerg".equals(race) ? "虫族"
                : ("protoss".equals(race) ? "星灵" : race));
        String diffName = "0".equals(diff) ? "简单"
                : ("2".equals(diff) ? "困难" : "普通");
        return map + " · " + raceName + " · " + diffName + " · "
                + cmds + " 指令 · " + (last / 30) + " 秒";
    }

    /**
     * Apply one recorded command. The selection is re-established first so a
     * command's `sel` list matches the live `ents` order the same way it did
     * when it was recorded.
     */
    public void applyCommand(String line) {
        String[] p = line.trim().split(" ");
        if (p.length == 0 || p[0].isEmpty()) return;
        String verb = p[0];
        if (verb.equals("select")) {
            for (Ent e : ents) e.selected = false;
            for (int i = 1; i < p.length; i++) {
                int idx = Integer.parseInt(p[i]);
                if (idx >= 0 && idx < ents.size()) ents.get(idx).selected = true;
            }
            return;
        }
        // v2.19 batch 5: the new rows carry their own entity indices as the
        // second field ("move 0,2,5 300 400"). Re-establish that selection so
        // the order hits the same units it did when recorded. A field that is
        // not an index list means an older replay (or a manual probe), which
        // keeps using whatever selection is already live.
        int argBase = 1;
        if (p.length > 1 && isIndexList(p[1])) {
            for (Ent e : ents) e.selected = false;
            for (String tok : p[1].split(",")) {
                if (tok.isEmpty()) continue;
                int idx = Integer.parseInt(tok);
                if (idx >= 0 && idx < ents.size()) ents.get(idx).selected = true;
            }
            argBase = 2;
        }
        java.util.List<Ent> sel = selected();
        switch (verb) {
            case "move":
                orderMove(sel, Float.parseFloat(p[argBase]), Float.parseFloat(p[argBase + 1]),
                        p.length > argBase + 2 && "1".equals(p[argBase + 2]));
                break;
            case "attack":
                orderAttack(sel, entAt(p[argBase]));
                break;
            case "harvest":
                orderHarvest(sel, mineralAt(p[argBase]));
                break;
            case "resume":
                orderResumeBuild(sel, entAt(p[argBase]));
                break;
            case "hold":
                orderHold(sel);
                break;
            case "patrol":
                orderPatrol(sel, Float.parseFloat(p[argBase]), Float.parseFloat(p[argBase + 1]));
                break;
            case "repair":
                orderRepair(sel, entAt(p[argBase]));
                break;
            case "heal":
                orderHeal(sel, entAt(p[argBase]));
                break;
            case "build":
                if (!sel.isEmpty()) tryBuild(sel.get(0), p[argBase],
                        Float.parseFloat(p[argBase + 1]), Float.parseFloat(p[argBase + 2]));
                break;
            case "train":
                if (!sel.isEmpty()) tryTrain(sel.get(0), p[argBase]);
                break;
            case "cancel":
                if (!sel.isEmpty()) cancelQueue(sel.get(0), Integer.parseInt(p[argBase]));
                break;
            case "siege":
                if (!sel.isEmpty()) toggleSiege(sel.get(0));
                break;
            case "cloak":
                // v2.22 batch B: the ghost/wraith personal cloak toggle. An
                // immediate order like siege -- no target, one argument.
                if (!sel.isEmpty()) toggleCloak(sel.get(0));
                break;
            case "mine":
                if (!sel.isEmpty()) placeMine(sel.get(0));
                break;
            case "scan":
                // v2.25: the comsat's scanner sweep. Two floats, like storm.
                if (!sel.isEmpty()) castScan(sel.get(0), Float.parseFloat(p[argBase]),
                        Float.parseFloat(p[argBase + 1]));
                break;
            case "nuke":
                // v2.25: the ghost's nuclear strike, aimed at two floats.
                if (!sel.isEmpty()) callNuke(sel.get(0), Float.parseFloat(p[argBase]),
                        Float.parseFloat(p[argBase + 1]));
                break;
            case "addon":
                // v2.25: attach an add-on to the selected building. One string
                // argument (the add-on key), so the aim is implied by geometry.
                if (!sel.isEmpty()) buildAddon(sel.get(0), p[argBase]);
                break;
            case "merge":
                // v2.26: the templar merge. The pair is the whole selection,
                // so no argument is needed.
                orderMerge(new ArrayList<>(sel), null);
                break;
            case "burrow":
                // v2.26: the burrow toggle, immediate like siege/cloak.
                if (!sel.isEmpty()) toggleBurrow(sel.get(0));
                break;
            case "group":
                groupTap(Integer.parseInt(p[argBase]), p.length > argBase + 1 && "1".equals(p[argBase + 1]));
                break;
            case "storm":
                if (!sel.isEmpty()) castStorm(sel.get(0), Float.parseFloat(p[argBase]),
                        Float.parseFloat(p[argBase + 1]));
                break;
            case "emp":
                if (!sel.isEmpty()) castEmp(sel.get(0), Float.parseFloat(p[argBase]),
                        Float.parseFloat(p[argBase + 1]));
                break;
            case "dswarm":
                if (!sel.isEmpty()) castDswarm(sel.get(0), Float.parseFloat(p[argBase]),
                        Float.parseFloat(p[argBase + 1]));
                break;
            case "ensnare":
                if (!sel.isEmpty()) castEnsnare(sel.get(0), Float.parseFloat(p[argBase]),
                        Float.parseFloat(p[argBase + 1]));
                break;
            case "dweb":
                if (!sel.isEmpty()) castDweb(sel.get(0), Float.parseFloat(p[argBase]),
                        Float.parseFloat(p[argBase + 1]));
                break;
            case "irradiate":
                if (!sel.isEmpty()) castIrradiate(sel.get(0), entAt(p[argBase]));
                break;
            case "yamato":
                if (!sel.isEmpty()) castYamato(sel.get(0), entAt(p[argBase]));
                break;
            case "lockdown":
                if (!sel.isEmpty()) castLockdown(sel.get(0), entAt(p[argBase]));
                break;
            // v2.23 batch A: the transport pair. `load` names the unit (an
            // entity index, like irradiate), `unload` names the drop point
            // (two floats, like storm). Both are recorded by the view so a
            // replay drives the same boarding.
            case "load":
                if (!sel.isEmpty()) {
                    Ent cargo = entAt(p[argBase]);
                    if (cargo != null && loadError(sel.get(0), cargo) == null) {
                        orderLoad(java.util.Collections.singletonList(sel.get(0)), cargo);
                        orderMove(java.util.Collections.singletonList(sel.get(0)),
                                cargo.x, cargo.y, false);
                    }
                }
                break;
            case "unload":
                if (!sel.isEmpty()) unloadAll(sel.get(0), Float.parseFloat(p[argBase]),
                        Float.parseFloat(p[argBase + 1]));
                break;
            default:
                break;      // unknown verb: a newer replay than this build
        }
    }

    /** True when the token is a comma list of entity indices ("0", "0,3,5"). */
    private static boolean isIndexList(String s) {
        if (s == null || s.isEmpty()) return false;
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            if (ch != ',' && (ch < '0' || ch > '9')) return false;
        }
        return true;
    }

    private Ent entAt(String s) {
        int i = Integer.parseInt(s);
        return i >= 0 && i < ents.size() ? ents.get(i) : null;
    }

    private Mineral mineralAt(String s) {
        int i = Integer.parseInt(s);
        return i >= 0 && i < minerals.size() ? minerals.get(i) : null;
    }

    /**
     * A cheap order-sensitive digest of the simulation state. The replay
     * assertion compares this every second: two runs of the same command
     * stream must agree at every sample or determinism has been broken
     * somewhere (a HashMap iteration order, a wall-clock read, ...).
     */
    public long stateHash() {
        long h = 1469598103934665603L;      // FNV-1a
        h = mix(h, mineralsPlayer);
        h = mix(h, gasPlayer);
        h = mix(h, Math.round(time * 1000f));
        h = mix(h, kills * 31 + losses);
        for (Ent e : ents) {
            h = mix(h, e.type.key.hashCode());
            h = mix(h, e.team);
            h = mix(h, Math.round(e.x * 16f));
            h = mix(h, Math.round(e.y * 16f));
            h = mix(h, e.hp);
            h = mix(h, e.shield);
            h = mix(h, e.alive() ? 1 : 0);
        }
        return h;
    }

    private static long mix(long h, long v) {
        h ^= v;
        h *= 1099511628211L;
        return h;
    }

    /**
     * Install a mission: spawn its start units, clear the default skirmish
     * armies and let the mission's objectives decide the result.
     *
     * The stock constructor always lays down a symmetric player/enemy base;
     * a mission wants a scripted board instead, so those entities are removed
     * before the mission's own units are placed.
     */
    public void setMission(Mission m) {
        this.mission = m;
        if (m == null) return;
        ents.clear();
        clearPathQueue();            // v2.43 P0-c
        invalidateAuraCounts();      // v2.43 P0-a
        minerals.clear();
        // v2.29: the skirmish opening spawned a base whose footprint was
        // stamped into `walk`. Clearing the entity list does not clear those
        // tiles, so a mission whose units stand where the skirmish barracks
        // used to be had them boxed in by an invisible wall -- the same defect
        // the old occupyFootprint(clear) had, and it moved the enemy's
        // production numbers by a third (measured: m05's 4-minute count swung
        // 27 vs 38 across runs before this). Restore the pristine terrain.
        System.arraycopy(walk0, 0, walk, 0, walk.length);
        // v2.8: a mission authors its own units, so it also decides the race.
        // Without this a player who picked zerg on the menu would get terran
        // units from m01 plus a zerg build card, which offers hatcheries that
        // no drone can ever build.
        if (m.playerRace != null && !m.playerRace.isEmpty()) race = m.playerRace;
        // v2.29: a mission that asks for the map's economy gets its resource
        // fields back. The clear above is right for a scripted board (the
        // skirmish layout's patches would sit under the mission's own units),
        // but it also left every campaign level with no minerals at all --
        // probe: `minerals.size()==0` on m01/m02/m05, so the briefing's
        // "the workers will mine" could never come true. Opt-in so the five
        // shipped missions keep the exact board they were balanced against.
        if (m.economy && mapMeta != null) {
            for (Object[] u : parseMapUnits(mapMeta)) {
                int kind = (Integer) u[0];
                Mineral mm = new Mineral();
                mm.x = (Float) u[1];
                mm.y = (Float) u[2];
                // Same two figures the skirmish constructor uses for a patch
                // and a geyser, so a mission's economy matches a melee map's.
                mm.amount = kind == 1 ? 1500 : 5000;
                mm.variant = kind == 1 ? (Integer) u[3] : 3;
                minerals.add(mm);
            }
        }
        for (Object[] u : m.startUnits) {
            String key = (String) u[0];
            Type t = TYPES.get(key);
            if (t == null) continue;
            float ux = (Float) u[1], uy = (Float) u[2];
            // v2.29: a mobile start unit that the author put on a blocked
            // minitile is nudged to the nearest walkable one, exactly as
            // Mission.update does for a deferred wave spawn. The maps carry
            // single-tile pits (hunters at 3150,3180 and 3300,3200; thinice at
            // 4570,412) that an offset hand-copied from the base layout lands
            // in, and a unit standing inside a cliff has no path home. A
            // building is left where it is: spawn() snaps it to the tile grid
            // and stamps its footprint, so a silent move would relocate the
            // structure the author actually asked for.
            if (t.tiles == 0) {
                int[] spot = nearestPassMini((int) (ux / 8), (int) (uy / 8), 12);
                if (spot != null) {
                    ux = spot[0] * 8 + 4;
                    uy = spot[1] * 8 + 4;
                }
            }
            spawn(key, (Integer) u[3], ux, uy, true);
        }
        difficulty = m.difficulty;
        for (Game.Ent e : ents) {
            if (e.team == 0) revealAround(e.x, e.y, 12);
        }
    }

    /** Mission start point, reused by the AI when an event has no origin. */
    public float[] findPlayerStart() {
        for (Ent e : ents)
            if (e.team == 0 && ("cc".equals(e.type.key) || "hatchery".equals(e.type.key)
                    || "nexus".equals(e.type.key)))
                return new float[]{e.x, e.y};
        for (Ent e : ents)
            if (e.team == 0) return new float[]{e.x, e.y};
        return new float[]{wPx / 2f, hPx / 2f};
    }

    /** Enemy base centre, or the map centre when the enemy has been wiped. */
    public float[] findEnemyBase() {
        for (Ent e : ents)
            if (e.team == 1 && e.isBuilding() && e.type.key.equals("hatchery"))
                return new float[]{e.x, e.y};
        for (Ent e : ents)
            if (e.team == 1 && e.isBuilding()) return new float[]{e.x, e.y};
        return new float[]{wPx / 2f, hPx / 2f};
    }

    private void runPendingOrders() {
        Runnable[] batch;
        synchronized (pendingOrders) {
            batch = pendingOrders.toArray(new Runnable[0]);
            pendingOrders.clear();
        }
        for (Runnable r : batch) r.run();
    }

    public static class Shot {
        public float x, y, tx, ty;
        public float t;               // elapsed seconds
        public float dur;             // total flight seconds
        public int team;
        public boolean missile;       // draws a smoke trail behind it
        public float smokeTimer;

        /** 0 at the muzzle, 1 on impact. */
        public float prog() {
            return dur > 0 ? Math.min(1f, t / dur) : 1f;
        }
    }

    /**
     * A sprite-sheet effect played once at a world position: unit death
     * animations and the bang explosion series. `frameTime` is fixed so the
     * animation runs at the same speed regardless of frame rate.
     */
    public static class Anim {
        public String key;        // SpriteBank key
        public float x, y;
        public float t;           // elapsed seconds
        public float frameTime;   // seconds per frame
        public int frames;
        public int team;          // 0 player, 1 enemy (picks the _b/_r sheet)
        public float scale = 1f;

        public int frame() {
            int f = (int) (t / frameTime);
            return f >= frames ? frames - 1 : f;
        }

        public boolean done() {
            return t >= frames * frameTime;
        }
    }

    public String status = "";        // "win" / "lose" / ""

    /**
     * v2.7 batch 8: the active scripted mission, or null for a plain
     * skirmish. When set, the mission owns the win/lose decision and the
     * default "destroy every enemy building" rule steps aside.
     */
    public Mission mission;
    private final Random rnd = new Random(12345);

    /** Pristine walkability, so load-state can undo saved buildings' footprints. */
    private final boolean[] walk0;

    // ------------------------------------------------------------ upgrades
    /**
     * v2.7 9.1: three-level weapon/armor upgrades. Costs and effects are the
     * plan's numbers: 100/150/200 minerals, +2 damage and +1 armor per level.
     * They are global (all player units benefit), which matches how the
     * original's infantry upgrades read to a player.
     *
     * v2.11 batch C moved the seller from the engineering bay to the armoury,
     * which is where Brood War actually sells them; the engineering bay keeps
     * its art and becomes a plain prerequisite-free building. The gate itself
     * lives in the command card (GameView draws the two buttons only when an
     * armoury is selected), so this class only owns the purchase.
     */
    public static final int UPGRADE_MAX = 3;
    public static final int[] UPGRADE_COST = {100, 150, 200};
    public static final int UPGRADE_DMG = 2, UPGRADE_ARMOR = 1;

    public int weaponLevel, armorLevel;

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

    /**
     * v2.27: the population cap tier, an index into SUPPLY_TIERS. Separate
     * from weaponLevel/armorLevel because those are one shared axis the plan
     * wants split into per-class lines (v2.28), while this is the growth
     * ladder's own state.
     */
    public int capTier;

    /** The multiplier the current tier applies to every supply provider. */
    public float capTier() {
        int i = capTier < 0 ? 0 : (capTier >= SUPPLY_TIERS.length
                ? SUPPLY_TIERS.length - 1 : capTier);
        return SUPPLY_TIERS[i] / (float) SUPPLY_TIERS[0];
    }

    /** Raise the population ceiling to the next tier. null on success. */
    public String raiseSupplyCap() {
        if (capTier >= SUPPLY_TIERS.length - 1) return "人口上限已到顶";
        int cost = popUpgradeCost(capTier + 1);
        if (mineralsPlayer < cost) return "晶体矿不足";
        mineralsPlayer -= cost;
        capTier++;
        return null;
    }

    /**
     * What the next supply tier costs. Indexed by the tier being bought, so
     * tier 1 (the 100 ceiling) is the only entry today. The price is set so
     * the upgrade is a real decision rather than a formality -- it is roughly
     * a factory plus a depot.
     */
    public static int popUpgradeCost(int tier) {
        return tier <= 1 ? 400 : 800;
    }

    public int upgradeCost(int level) {
        return level >= 0 && level < UPGRADE_MAX ? UPGRADE_COST[level] : -1;
    }

    /**
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
    }

    // --------------------------------------------------------------- stim
    /** Stimpack (v2.7 9.1): pay HP now, fire faster for a while. */
    public static final int STIM_HP_COST = 10;
    public static final float STIM_DURATION = 8f, STIM_COOLDOWN = 15f;
    public static final float STIM_RATE = 1.5f;

    /** null when stim is legal, else a human-readable reason. */
    public String stimError(Ent e) {
        if (e == null || !e.alive() || e.isBuilding()) return "目标无效";
        if (e.stimTime > 0) return "兴奋剂仍在生效";
        if (e.cd > 0 && e.cd > e.type.cooldown * 0.5f) return "冷却中";
        if (e.hp <= STIM_HP_COST) return "生命值过低";
        return null;
    }

    public boolean stim(Ent e) {
        if (stimError(e) != null) return false;
        e.hp -= STIM_HP_COST;
        e.stimTime = STIM_DURATION;
        return true;
    }

    /** Attack cooldown after stim, used by both the unit and the building path. */
    public float effectiveCooldown(Ent e) {
        return e.stimTime > 0 ? e.type.cooldown / STIM_RATE : e.type.cooldown;
    }

    // ------------------------------------------------------- psionic storm
    /**
     * v2.10: the templar's signature spell. A storm is a stationary damage
     * field: anything hostile standing inside it takes a tick of damage four
     * times a second for as long as it lasts. That shape -- rather than a
     * one-shot blast -- is the whole point of the ability, because it punishes
     * clumped units and forces the player to move out of it.
     */
    public static final int STORM_DAMAGE = 8;          // per tick
    public static final float STORM_DURATION = 3.0f;   // seconds
    public static final float STORM_RADIUS = 88f;      // world px
    public static final float STORM_TICK = 0.25f;      // seconds per damage tick
    public static final float STORM_COOLDOWN = 12f;    // per caster

    /** A live psionic storm. Casters may die while it runs; it keeps ticking. */
    public static class Storm {
        public float x, y;
        public float t;              // elapsed
        public float tickTimer;
        public int team;             // the caster's team; hurts the other one

        public boolean done() {
            return t >= STORM_DURATION;
        }
    }

    public final List<Storm> storms = new ArrayList<>();

    /** null when the storm is legal, else a human-readable reason. */
    public String stormError(Ent e) {
        if (e == null || !e.alive() || e.isBuilding()) return "目标无效";
        if (!"templar".equals(e.type.key)) return "该单位无法施放灵能风暴";
        if (e.stormCd > 0) return "灵能风暴冷却中";
        return energyGate(e, COST_STORM);
    }

    /**
     * Cast a storm centred on (tx, ty). Returns false when the caster cannot
     * cast; the caller shows the reason from stormError().
     */
    public boolean castStorm(Ent caster, float tx, float ty) {
        if (stormError(caster) != null) return false;
        Storm s = new Storm();
        s.x = tx;
        s.y = ty;
        s.team = caster.team;
        storms.add(s);
        caster.energy -= COST_STORM;
        caster.stormCd = STORM_COOLDOWN;
        caster.facing = (float) Math.atan2(ty - caster.y, tx - caster.x);
        caster.dir = dirOf(caster.facing);
        // No one-shot Anim here: the view draws the storm itself straight from
        // the psistorm sheet so the effect lives exactly as long as the field
        // does, instead of ending a second after the cast.
        return true;
    }

    /** Control groups 1..N, shared by the view and save/load. */
    public final List<List<Ent>> groups = new ArrayList<>();

    /** Result codes for groupTap(). */
    public static final int GROUP_ASSIGNED = 0, GROUP_RECALLED = 1, GROUP_EMPTY = 2;

    /**
     * Assign the current selection to slot `g` (assign=true) or recall slot `g`
     * into the selection. Pure game logic so it can be regression-tested on the
     * JVM; the view only maps the hold duration to the assign flag and renders
     * the message.
     */
    public int groupTap(int g, boolean assign) {
        while (groups.size() <= g) groups.add(new ArrayList<>());
        List<Ent> grp = groups.get(g);
        if (assign) {
            grp.clear();
            grp.addAll(selected());
            return GROUP_ASSIGNED;
        }
        for (int i = grp.size() - 1; i >= 0; i--)
            if (!grp.get(i).alive()) grp.remove(i);
        if (grp.isEmpty()) return GROUP_EMPTY;
        for (Ent e : ents) e.selected = false;
        for (Ent e : grp) e.selected = true;
        return GROUP_RECALLED;
    }


    /**
     * Ground marker drawn where an order landed: the move-acknowledgement
     * circle (kind 0) or the red "unreachable" cross (kind 1).
     */
    public static class Marker {
        public float x, y;
        public float t;
        public float dur = 0.6f;
        public int kind;              // 0 = move ok, 1 = unreachable
    }

    public final List<Marker> markers = new ArrayList<>();

    public void addMarker(float x, float y, boolean ok) {
        if (markers.size() > 64) markers.remove(0);
        Marker m = new Marker();
        m.x = x;
        m.y = y;
        m.kind = ok ? 0 : 1;
        markers.add(m);
    }

    /**
     * Fading corpse: the last frame of a unit's death sequence held on screen
     * for CORPSE_HOLD while the death anim plays, then fading out.
     */
    public static class Corpse {
        public String key;
        public int team;
        public float x, y;
        public int frame;             // sheet frame to draw
        public float t;
        public static final float HOLD = 0.6f;   // while the death anim runs
        public static final float FADE = 2.0f;   // then fade over this long
        public float dur() { return HOLD + FADE; }
    }

    public final List<Corpse> corpses = new ArrayList<>();

    /** Sound-event cooldown so a firestorm doesn't spam the under-attack alert. */
    private float alertCd;

    // AI economy
    // v2.14: these are public so the desktop assertions can drive the AI into a
    // specific state instead of waiting out a real 60-second wave. The rest of
    // the simulation's tunables (mineralsPlayer, weaponLevel) are public for
    // the same reason, so this is the existing convention, not a new one.
    public int aiMinerals = 350;
    private float aiIncome;
    public float aiWaveTimer = 75f;
    public int aiWave = 0;
    public float aiBuildTimer = 10f;

    // ------------------------------------------------ v2.14 batch 1.6: AI
    /**
     * The AI's race. Skirmish keeps the zerg enemy the earlier batches built
     * (the whole wave table in aiPick is a zerg progression); the field exists
     * so the same brain can drive a terran or protoss opponent, which is what
     * "三族各自 build 顺序" asks for. 0 terran, 1 zerg, 2 protoss.
     */
    public int aiRace = 1;
    /** Set by damage() when an AI building is hit; drives the defence recall. */
    private float aiDefendTimer;
    private float aiDefendX, aiDefendY;
    /** The recall re-paths the army once per alert, not once per frame. */
    private boolean aiDefendIssued;
    /**
     * Units committed when the current wave launched, for the retreat test.
     * Public like aiWave/aiWaveTimer so a desktop assertion can stage a wave
     * that has already taken losses instead of simulating a real one for a
     * minute. 0 means "no wave is out", which also disables the retreat check.
     */
    public int aiWaveStrength;
    /** Throttles the spell-casting pass -- it does not need to run every tick. */
    private float aiSpellTimer;
    /** Index into the AI's structure ladder (see aiBuildOrder). */
    private int aiTechTier;
    private float aiTechTimer = 30f;

    public Game(int wTiles, int hTiles, boolean[] walkMini, List<int[]> starts,
                List<Object[]> mapUnits) {
        this(wTiles, hTiles, walkMini, starts, mapUnits, "terran");
    }

    /**
     * v2.8: race-aware constructor. The opening base is spawned here, so the
     * race has to be known before the base exists -- setting the field after
     * construction would leave a terran base under a zerg flag.
     */
    public Game(int wTiles, int hTiles, boolean[] walkMini, List<int[]> starts,
                List<Object[]> mapUnits, String race) {
        this(wTiles, hTiles, walkMini, null, starts, mapUnits, race);
    }

    /**
     * v2.23 batch C: the full constructor. `elevMini` is the per-minitile
     * ground level (0 low / 1 mid / 2 high), or null for "one flat level" --
     * which is what every caller that predates the elevation layer passes, so
     * they all keep the old behaviour and the miss rule becomes a no-op on an
     * old asset tree.
     */
    public Game(int wTiles, int hTiles, boolean[] walkMini, byte[] elevMini,
                List<int[]> starts, List<Object[]> mapUnits, String race) {
        this.elev = elevMini != null && elevMini.length == wTiles * 4 * hTiles * 4
                ? elevMini.clone() : null;
        if (race != null && !race.isEmpty()) this.race = race;
        this.wTiles = wTiles;
        this.hTiles = hTiles;
        this.wMini = wTiles * 4;
        this.hMini = hTiles * 4;
        this.wPx = wTiles * 32;
        this.hPx = hTiles * 32;
        // Defensive copy: the caller's array is the map's pristine terrain and
        // every building spawned here stamps its footprint into `walk`
        // (occupyFootprint). Holding the caller's reference would leak those
        // footprints into every later Game built from the same map -- a
        // restarted match would begin with phantom blocked tiles where the
        // previous match's base used to stand.
        this.walk = walkMini.clone();
        this.walk0 = walkMini.clone();
        this.fog = new byte[wTiles * hTiles];

        // resources from the map
        for (Object[] u : mapUnits) {
            int kind = (Integer) u[0];
            float x = (Float) u[1], y = (Float) u[2];
            if (kind == 1) {
                Mineral m = new Mineral();
                m.x = x;
                m.y = y;
                m.amount = 1500;
                m.variant = (Integer) u[3];
                minerals.add(m);
            } else if (kind == 2) {
                Mineral m = new Mineral();
                m.x = x;
                m.y = y;
                m.amount = 5000;
                m.variant = 3;   // geyser
                minerals.add(m);
            }
        }

        // player base at starts[0], enemy at starts[1]
        float[] ps = startPx(starts, 0);
        float[] es = startPx(starts, Math.min(1, starts.size() - 1));
        // v2.8/v2.10: the opening differs by race. A zerg player starts with a
        // hatchery, drones and an overlord instead of a command center, SCVs
        // and a barracks; a protoss player starts with a nexus, probes and a
        // pylon (the pylon is what makes the first gateway affordable supply-
        // wise, so it takes the barracks slot). The enemy is always zerg.
        if ("zerg".equals(race)) {
            spawn("hatchery", 0, ps[0], ps[1] - 20, true);
            for (int i = 0; i < 4; i++) {
                spawn("drone", 0, ps[0] - 60 + i * 26, ps[1] + 70, true);
            }
            spawn("over", 0, ps[0] + 90, ps[1] + 60, true);
            spawn("pool", 0, ps[0] + 150, ps[1] + 20, true);
        } else if ("protoss".equals(race)) {
            spawn("nexus", 0, ps[0], ps[1] - 20, true);
            for (int i = 0; i < 4; i++) {
                spawn("probe", 0, ps[0] - 60 + i * 26, ps[1] + 70, true);
            }
            spawn("pylon", 0, ps[0] + 130, ps[1] + 20, true);
        } else {
            spawn("cc", 0, ps[0], ps[1] - 20, true);
            for (int i = 0; i < 4; i++) {
                spawn("scv", 0, ps[0] - 60 + i * 26, ps[1] + 70, true);
            }
            spawn("barracks", 0, ps[0] + 130, ps[1] + 20, true);
        }

        // enemy base: hatchery + defense + workers
        spawn("hatchery", 1, es[0], es[1] - 20, true);
        spawn("pool", 1, es[0] - 150, es[1] + 60, true);
        spawn("sunken", 1, es[0] + 120, es[1] + 80, true);
        for (int i = 0; i < 4; i++) {
            spawn("zergling", 1, es[0] - 70 + i * 24, es[1] + 110, true);
        }
        for (int i = 0; i < 2; i++) {
            spawn("hydra", 1, es[0] + 40 + i * 30, es[1] + 130, true);
        }

        // reveal start areas
        revealAround(ps[0], ps[1], 12);
    }

    private float[] startPx(List<int[]> starts, int i) {
        int[] s = starts.get(i);
        return new float[]{s[0] + 64, s[1] + 64};
    }

    private void revealAround(float px, float py, int rad) {
        int cx = (int) (px / 32), cy = (int) (py / 32);
        for (int y = Math.max(0, cy - rad); y <= Math.min(hTiles - 1, cy + rad); y++)
            for (int x = Math.max(0, cx - rad); x <= Math.min(wTiles - 1, cx + rad); x++)
                fog[y * wTiles + x] = 2;
    }

    public Ent spawn(String typeKey, int team, float x, float y, boolean complete) {
        Type t = TYPES.get(typeKey);
        if (t == null) return null;
        Ent e = new Ent();
        e.type = t;
        e.team = team;
        e.x = clamp(x, 16, wPx - 16);
        e.y = clamp(y, 16, hPx - 16);
        e.hp = complete ? t.hp : 1;
        e.constructing = !complete;
        e.buildProgress = complete ? 1 : 0;
        // v2.10: a unit spawns with its shield already up. An unfinished
        // building starts with none -- the shield comes online with the
        // building, so a half-built pylon is not secretly tanky.
        e.shield = complete ? t.shield : 0;
        // v2.22 batch A: casters come out of the gate at the original's 50
        // energy, regen from there. v2.25: the comsat is the one building with
        // a pool (the scanner sweep), so the old "units only" guard is gone --
        // a building caster fills its pool here like any other.
        if (t.caster) {
            e.maxEnergy = ENERGY_MAX;
            e.energy = ENERGY_SPAWN;
        }
        // v2.26: a fresh carrier starts with a partial hangar (it fills on its
        // own) and a fresh reaver with a full scarab rack, which is the state
        // the original ships it in.
        if (t.hangarCap > 0 && complete) e.interceptors = Math.min(t.hangarCap, 4);
        if (t.ammoCap > 0 && complete) e.ammo = t.ammoCap;
        if (team == 0) {
            // v2.7 9.1: upgrades are global, so anything that joins afterwards
            // must pick up the levels already researched. v2.28: from its own
            // class's lines, not from one army-wide number.
            int ui = classIndex(t.upClass);
            e.dmgBonus = (ui < 0 ? 0 : weaponByClass[ui]) * UPGRADE_DMG;
            e.armorBonus = (ui < 0 ? 0 : armorByClass[ui]) * UPGRADE_ARMOR;
        }
        if (t.tiles > 0) {
            e.x = snapBuilding(e.x, t.tiles);
            e.y = snapBuilding(e.y, t.tiles);
            occupyFootprint(e, true);
            if (team == 0 && complete) revealAround(e.x, e.y, 10);
        }
        ents.add(e);
        invalidateAuraCounts();      // v2.43 P0-a: a new arbiter/detector may exist now
        return e;
    }

    private float snapBuilding(float v, int tiles) {
        int px = ((int) (v / 32) - tiles / 2) * 32 + 16;
        return clamp(px, tiles * 16, wPx - tiles * 16);
    }

    // ------------------------------------------------------------- footprints
    /**
     * Stamp or clear a building's footprint in the minitile walk map.
     *
     * Clearing has to restore from `walk0`, not from `walk` itself: the old
     * `walk[..] = !occupy && walk[..]` reduced to `walk = walk` when occupy was
     * false, so a destroyed building left its tiles permanently blocked. The
     * symptom was subtle and only appeared once the repaired walk map let the
     * AI actually reach and raze the player's barracks -- every later path
     * then routed around an invisible 3x3 hole where the building used to be.
     * Restoring from the pristine map is safe because buildings never overlap.
     */
    private void occupyFootprint(Ent b, boolean occupy) {
        int tiles = b.type.tiles;
        int tx0 = (int) (b.x / 32) - tiles / 2;
        int ty0 = (int) (b.y / 32) - tiles / 2;
        for (int y = ty0; y < ty0 + tiles; y++)
            for (int x = tx0; x < tx0 + tiles; x++) {
                if (x < 0 || y < 0 || x >= wTiles || y >= hTiles) continue;
                // mark all 4x4 minitiles of the tile unwalkable
                for (int my = 0; my < 4; my++)
                    for (int mx = 0; mx < 4; mx++) {
                        int X = x * 4 + mx, Y = y * 4 + my;
                        int idx = Y * wMini + X;
                        walk[idx] = occupy ? false : walk0[idx];
                    }
            }
    }

    // ------------------------------------------------------------- pathfinding
    private static final int[] DX = {1, -1, 0, 0, 1, 1, -1, -1};
    private static final int[] DY = {0, 0, 1, -1, 1, -1, 1, -1};
    private float[] gScore;
    private int[] from;
    private boolean[] closed;
    private int[] heap;
    private int heapN;
    private float[] fScore;
    private int visitToken;
    private int[] visitedToken;

    /**
     * v2.44: A* heuristic weight. 1.0 is plain admissible A*; anything above it
     * is weighted A*, which trades a slightly longer path for far fewer
     * expanded cells.
     *
     * Why this is not a micro-optimisation: the AI sends its whole army across
     * the map to the player's base, and on the larger maps plain A* expands
     * 100k-180k cells on an open field (measured per mission -- bonecanyon
     * 100159, sirocco 119863, riverlethe 178739). That blew past the old
     * 60000 cap, so findPath returned null for two bases that are plainly
     * connected, and the wave stood still at the spawn point. Weighting the
     * heuristic is what makes those searches fit: at 2.0 every mission's
     * base-to-base path costs under 60k, and the path is 2-14% longer, which
     * is invisible in play.
     *
     * PATH_TIE additionally breaks equal-f ties toward the *deeper* node
     * (subtract g). On an open axis-aligned rectangle every cell between start
     * and goal has exactly the same f, so without this the search floods the
     * whole rectangle before touching the goal -- that flood, not the path
     * length, is where the six-figure expansion counts came from.
     */
    private static final float PATH_WEIGHT = 2.0f;
    private static final float PATH_TIE = 0.1f;

    /**
     * v2.44: absolute per-search expansion ceiling. This exists only to stop a
     * genuinely unreachable goal (a sealed pocket) from expanding the entire
     * map; it must be comfortably above the worst real path. Measured worst
     * base-to-base with PATH_WEIGHT is 58623 (sirocco), so 200000 leaves a 3x
     * margin and can only be hit by a goal that truly cannot be reached.
     */
    private static final int PATH_EXPANSION_CAP = 200000;

    /**
     * v2.44: total expansions one tick may spend across every queued path
     * request. Eight full-size searches in a single tick was the old worst
     * case and it is a visible hitch; the cap makes an expensive tick do less
     * work and finish the rest next tick instead.
     */
    private static final int PATH_TICK_EXPANSIONS = 100000;

    /** Expansions still available this tick; refilled in update(). */
    private int pathBudgetLeft = PATH_TICK_EXPANSIONS;

    /**
     * v2.44: how an attack-moving unit that stopped short of its goal retries.
     * A stalled wave used to end its lock and stand there for the rest of the
     * match; now it re-asks for a route every AI_REPATH_DELAY seconds, at most
     * AI_REPATH_MAX times. The bound matters: a goal inside a sealed pocket
     * would otherwise cost one full A* per unit per delay, forever.
     */
    private static final float AI_REPATH_DELAY = 1.5f;
    private static final int AI_REPATH_MAX = 8;

    /** True when the last findPath stopped because the tick budget ran out. */
    private boolean lastPathBudgetHit;

    private void ensurePathBuffers() {
        int n = wMini * hMini;
        if (gScore == null || gScore.length < n) {
            gScore = new float[n];
            from = new int[n];
            closed = new boolean[n];
            heap = new int[n];
            fScore = new float[n];
            visitedToken = new int[n];
            visitToken = 0;
        }
    }

    /**
     * Set by findPath: true when the goal could not be reached exactly and the
     * path ends at the nearest walkable minitile (or fails outright).
     */
    private boolean lastPathApprox;

    /**
     * v2.43 P1: returns the path packed flat as [x0,y0, x1,y1, ...] in minitile
     * coordinates, or null when there is none. The caller owns the array (a
     * fresh one per call), so it can be installed on the unit directly -- there
     * is no intermediate list to copy out of.
     *
     * v2.44: this entry point does NOT draw on the per-tick budget. It is the
     * player's own command path (orderMove / orderAttack / tryBuild all call
     * setPath, which lands here), and a click has to answer on the tick it
     * happens. The AI's massed requests go through findPathBudgeted instead.
     */
    public int[] findPath(int sx, int sy, int gx, int gy) {
        lastPathBudgetHit = false;
        return findPathCapped(sx, sy, gx, gy, PATH_EXPANSION_CAP);
    }

    /**
     * v2.44: the same search, charged against this tick's expansion budget.
     * Returns null and sets lastPathBudgetHit when the budget -- not the map --
     * is what stopped it, so the caller can retry next tick instead of
     * treating a live route as unreachable.
     */
    private int[] findPathBudgeted(int sx, int sy, int gx, int gy) {
        if (pathBudgetLeft <= 0) {
            lastPathBudgetHit = true;
            return null;
        }
        int cap = Math.min(PATH_EXPANSION_CAP, pathBudgetLeft);
        int before = pathExpansions;
        int[] p = findPathCapped(sx, sy, gx, gy, cap);
        pathBudgetLeft -= (pathExpansions - before);
        lastPathBudgetHit = pathExpansions - before >= cap && p == null;
        return p;
    }

    /** Expansions performed by the most recent findPath call. */
    private int pathExpansions;

    private int[] findPathCapped(int sx, int sy, int gx, int gy, int cap) {
        ensurePathBuffers();
        sx = (int) Game.clamp(sx, 0, wMini - 1);
        sy = (int) Game.clamp(sy, 0, hMini - 1);
        lastPathApprox = false;
        if (!passMini(gx, gy)) {
            int[] alt = nearestPassMini(gx, gy, 24);
            if (alt == null) {
                lastPathApprox = true;
                return null;
            }
            gx = alt[0];
            gy = alt[1];
            lastPathApprox = true;
        }
        int n = wMini * hMini;
        visitToken++;
        int start = sy * wMini + sx, goal = gy * wMini + gx;
        heapN = 0;
        gScore[start] = 0;
        from[start] = -1;
        visitedToken[start] = visitToken;
        closed[start] = false;
        push(start, PATH_WEIGHT * heur(sx, sy, gx, gy));
        int expansions = 0;
        int found = -1;
        while (heapN > 0 && expansions < cap) {
            int cur = pop();
            if (closed[cur] && visitedToken[cur] == visitToken) continue;
            closed[cur] = true;
            expansions++;
            if (cur == goal) {
                found = cur;
                break;
            }
            int cx = cur % wMini, cy = cur / wMini;
            for (int d = 0; d < 8; d++) {
                int nx = cx + DX[d], ny = cy + DY[d];
                if (!passMini(nx, ny)) continue;
                if (d >= 4 && (!passMini(cx + DX[d], cy) || !passMini(cx, cy + DY[d]))) continue;
                int ni = ny * wMini + nx;
                if (visitedToken[ni] == visitToken && closed[ni]) continue;
                float step = (d >= 4) ? 1.4142f : 1f;
                float ng = gScore[cur] + step;
                if (visitedToken[ni] != visitToken || ng < gScore[ni]) {
                    visitedToken[ni] = visitToken;
                    closed[ni] = false;
                    gScore[ni] = ng;
                    from[ni] = cur;
                    push(ni, ng + PATH_WEIGHT * heur(nx, ny, gx, gy) - PATH_TIE * ng);
                }
            }
        }
        pathExpansions = expansions;
        if (found < 0) {
            lastPathApprox = true;
            return null;
        }
        // v2.43 P1: walk the chain backwards once to count it, allocate exactly
        // that many nodes, then fill from the tail. The old version appended to
        // an ArrayList (growing it several times) and then reversed it.
        int nodes = 0;
        for (int c = found; c != -1; c = from[c]) {
            nodes++;
            if (c == start) break;
        }
        int[] path = new int[nodes * 2];
        int w = nodes - 1;
        for (int c = found; c != -1; c = from[c]) {
            path[w * 2] = c % wMini;
            path[w * 2 + 1] = c / wMini;
            w--;
            if (c == start) break;
        }
        return path;
    }

    private float heur(int x, int y, int gx, int gy) {
        int dx = Math.abs(x - gx), dy = Math.abs(y - gy);
        return (dx + dy) + (1.4142f - 2f) * Math.min(dx, dy);
    }

    private void push(int i, float f) {
        if (heapN >= heap.length) return;
        heap[heapN] = i;
        fScore[heapN] = f;
        int c = heapN++;
        while (c > 0) {
            int p = (c - 1) / 2;
            if (fScore[p] <= fScore[c]) break;
            int ti = heap[p];
            heap[p] = heap[c];
            heap[c] = ti;
            float tf = fScore[p];
            fScore[p] = fScore[c];
            fScore[c] = tf;
            c = p;
        }
    }

    private int pop() {
        int top = heap[0];
        heapN--;
        if (heapN > 0) {
            heap[0] = heap[heapN];
            fScore[0] = fScore[heapN];
            int c = 0;
            while (true) {
                int l = c * 2 + 1, r = l + 1, m = c;
                if (l < heapN && fScore[l] < fScore[m]) m = l;
                if (r < heapN && fScore[r] < fScore[m]) m = r;
                if (m == c) break;
                int ti = heap[m];
                heap[m] = heap[c];
                heap[c] = ti;
                float tf = fScore[m];
                fScore[m] = fScore[c];
                fScore[c] = tf;
                c = m;
            }
        }
        return top;
    }

    public boolean passMini(int x, int y) {
        return x >= 0 && y >= 0 && x < wMini && y < hMini && walk[y * wMini + x];
    }

    public int[] nearestPassMini(int x, int y, int maxR) {
        for (int r = 1; r <= maxR; r++)
            for (int dy = -r; dy <= r; dy++)
                for (int dx = -r; dx <= r; dx++) {
                    if (Math.max(Math.abs(dx), Math.abs(dy)) != r) continue;
                    if (passMini(x + dx, y + dy)) return new int[]{x + dx, y + dy};
                }
        return null;
    }

    // ----------------------------------------------------------------- orders
    public List<Ent> selected() {
        List<Ent> out = new ArrayList<>();
        for (Ent e : ents)
            if (e.selected && e.alive() && e.team == 0) out.add(e);
        return out;
    }

    /**
     * v2.23 batch C: the ground level at a world point, 0/1/2. The bitmap is
     * one entry per 8 px minitile, the same grid as `walk`, so the lookup is
     * the same two-line conversion. A map with no elevation data answers 0
     * everywhere, which turns the whole miss rule into a no-op instead of a
     * crash on an old asset tree.
     */
    public int elevLevel(float wx, float wy) {
        if (elev == null) return 0;
        int mx = (int) (wx / 8), my = (int) (wy / 8);
        if (mx < 0 || my < 0 || mx >= wMini || my >= hMini) return 0;
        return elev[my * wMini + mx];
    }

    /**
     * v2.23 batch C: does a shot from `from` at `tgt` suffer the low-to-high
     * penalty? Only the up-hill direction is penalised -- shooting down from a
     * cliff is free, and so is a fight on the same level. Melee is exempt: the
     * plan range<64 rule, because a zealot that has walked up the ramp is
     * standing next to its target and the cliff is behind it.
     */
    public boolean elevationPenalty(Ent from, Ent tgt) {
        if (elev == null || from == null || tgt == null) return false;
        if (from.type.range < MELEE_RANGE) return false;
        return elevLevel(tgt.x, tgt.y) > elevLevel(from.x, from.y);
    }

    /**
     * v2.23 batch C: does this shot land? Only the up-hill direction can miss,
     * and only for a ranged weapon. Split out of fire() so the desktop harness
     * can roll it ten thousand times and assert the 53.125% the plan pins,
     * instead of having to stage a real firefight to measure the same number.
     */
    public boolean shotHits(Ent from, Ent tgt) {
        if (!elevationPenalty(from, tgt)) return true;
        return rnd.nextFloat() >= HIGH_MISS_CHANCE;
    }

    // ------------------------------------------------ v2.23 batch A: cargo
    /**
     * null when `carrier` may take `unit` aboard, else a human-readable reason.
     * The rules are the plan's: friendly, a mobile unit, not already loaded,
     * not the carrier itself, and enough free supply slots.
     */
    public String loadError(Ent carrier, Ent unit) {
        if (carrier == null || unit == null) return "目标无效";
        if (carrier.type.cargoCap <= 0) return "该单位无法装载";
        if (!carrier.alive() || carrier.isBuilding()) return "该单位无法装载";
        if (unit.team != carrier.team) return "只能装载我方单位";
        if (!unit.alive() || unit.isBuilding()) return "只能装载单位";
        if (unit == carrier) return "无法装载自身";
        if (unit.cargoOf != null || unit.garrisoned) return "该单位已被装载";
        if (cargoUsed(carrier) + unit.type.supply > carrier.type.cargoCap)
            return "装载空间不足";
        return null;
    }

    /** Supply slots already taken in this carrier. */
    public int cargoUsed(Ent carrier) {
        int n = 0;
        for (Ent c : carrier.cargo) n += c.type.supply;
        return n;
    }

    /** Load one unit. Returns false with loadError() as the explanation. */
    public boolean loadUnit(Ent carrier, Ent unit) {
        if (loadError(carrier, unit) != null) return false;
        unit.cargoOf = carrier;
        unit.selected = false;
        unit.moving = false;
        unit.path = Ent.EMPTY_PATH;
        cancelQueuedPath(unit);   // v2.43 P0-c: a loaded unit has no pending path
        unit.target = null;
        unit.mineTarget = null;
        unit.repairTarget = null;
        unit.healTarget = null;
        carrier.cargo.add(unit);
        return true;
    }

    /**
     * Unload everything a carrier holds. `tx, ty` is the drop point. Each unit
     * is placed on the nearest free minitile by a spiral search, so a full
     * shuttle landing on a narrow ledge spreads out instead of stacking. The
     * plan wording ("no room to unload") is reported when the search fails.
     */
    public boolean unloadAll(Ent carrier, float tx, float ty) {
        if (carrier == null || carrier.cargo.isEmpty()) return false;
        boolean any = false;
        for (Ent u : new ArrayList<>(carrier.cargo)) {
            float[] spot = freeSpotNear(tx, ty, u);
            if (spot == null) continue;
            carrier.cargo.remove(u);
            u.cargoOf = null;
            u.x = spot[0];
            u.y = spot[1];
            u.moving = false;
            u.path = Ent.EMPTY_PATH;
            cancelQueuedPath(u);   // v2.43 P0-c: teleported out; drop any pending path
            any = true;
        }
        return any;
    }

    /** The nearest walkable spot for `u` around (tx, ty), or null. */
    private float[] freeSpotNear(float tx, float ty, Ent u) {
        if (spotFree(tx, ty, u)) return new float[]{tx, ty};
        for (int r = 1; r <= 24; r++) {
            for (int dy = -r; dy <= r; dy++) {
                for (int dx = -r; dx <= r; dx++) {
                    if (Math.max(Math.abs(dx), Math.abs(dy)) != r) continue;
                    float x = clamp(tx + dx * 16, 8, wPx - 8);
                    float y = clamp(ty + dy * 16, 8, hPx - 8);
                    if (spotFree(x, y, u)) return new float[]{x, y};
                }
            }
        }
        return null;
    }

    /** Is (x, y) walkable and clear of buildings and live units? */
    private boolean spotFree(float x, float y, Ent u) {
        if (!passMini((int) (x / 8), (int) (y / 8))) return false;
        for (Ent o : ents) {
            if (o == u || !o.alive() || o.constructing) continue;
            if (o.cargoOf != null || o.garrisoned) continue;
            if (o.isBuilding()) {
                float half = o.type.tiles * 16;
                if (Math.abs(o.x - x) < half + 12 && Math.abs(o.y - y) < half + 12)
                    return false;
            } else if (o.type.flying == u.type.flying) {
                float min = o.type.radius + u.type.radius;
                float dx = o.x - x, dy = o.y - y;
                if (dx * dx + dy * dy < min * min) return false;
            }
        }
        return true;
    }

    /**
     * Player-facing load order: point the transport at a friendly unit. The
     * pickup itself happens in updateLoading once it is close enough, which is
     * what the plan means by "walk over and it collects itself".
     */
    public boolean orderLoad(List<Ent> sel, Ent unit) {
        boolean any = false;
        for (Ent c : sel) {
            if (c.type.cargoCap <= 0) continue;
            if (unit == null || loadError(c, unit) != null) continue;
            c.loadTarget = unit;
            any = true;
        }
        return any;
    }

    /** Player-facing unload order: every selected transport drops its hold. */
    public boolean orderUnload(List<Ent> sel, float wx, float wy) {
        boolean any = false;
        for (Ent c : sel) {
            if (c.type.cargoCap <= 0) continue;
            if (unloadAll(c, wx, wy)) any = true;
        }
        return any;
    }

    /**
     * v2.23 batch A: automatic boarding. A transport told to load a unit walks
     * to it and picks it up on arrival, which is what the plan means by "walk
     * close and it collects itself". Gated on `loadTarget` so a transport only
     * ever collects what it was pointed at: the overlord is a transport too,
     * and a free sweep would have it eating the player base.
     */
    private void updateLoading(Ent carrier) {
        if (carrier.type.cargoCap <= 0 || !carrier.alive()) return;
        Ent want = carrier.loadTarget;
        if (want == null) return;
        if (!want.alive() || want.cargoOf != null || want.garrisoned) {
            carrier.loadTarget = null;
            return;
        }
        if (dist(carrier, want) > LOAD_RANGE) return;
        if (loadError(carrier, want) != null) return;
        loadUnit(carrier, want);
        carrier.loadTarget = null;
    }

    // ------------------------------------------------ v2.23 batch B: bunker
    /** null when `unit` may garrison `bunker`, else a human-readable reason. */
    public String garrisonError(Ent bunker, Ent unit) {
        if (bunker == null || unit == null) return "目标无效";
        if (bunker.type.bunkerCap <= 0) return "该建筑无法驻守";
        if (!bunker.alive() || !bunker.isBuilding()) return "该建筑无法驻守";
        if (bunker.constructing) return "建筑尚未完工";
        if (unit.team != bunker.team) return "只能驻守我方单位";
        if (!unit.alive() || unit.isBuilding()) return "只能驻守步兵";
        if (unit.cargoOf != null || unit.garrisoned) return "该单位已被装载";
        if (unit.type.airOnly || unit.type.flying) return "只有地面步兵可以驻守";
        if (garrisonUsed(bunker) + unit.type.supply > bunker.type.bunkerCap)
            return "驻守空间不足";
        return null;
    }

    public int garrisonUsed(Ent bunker) {
        int n = 0;
        for (Ent g : bunker.cargo) n += g.type.supply;
        return n;
    }

    public boolean garrisonUnit(Ent bunker, Ent unit) {
        if (garrisonError(bunker, unit) != null) return false;
        unit.garrisoned = true;
        unit.bunker = bunker;
        unit.selected = false;
        unit.moving = false;
        unit.path = Ent.EMPTY_PATH;
        cancelQueuedPath(unit);   // v2.43 P0-c: inside a bunker; no pending path
        unit.target = null;
        unit.mineTarget = null;
        unit.repairTarget = null;
        unit.healTarget = null;
        bunker.cargo.add(unit);
        return true;
    }

    /** Empty a bunker, spilling its garrison around it. */
    public boolean ungarrisonAll(Ent bunker) {
        if (bunker == null || bunker.cargo.isEmpty()) return false;
        boolean any = false;
        for (Ent u : new ArrayList<>(bunker.cargo)) {
            float[] spot = freeSpotNear(bunker.x + bunker.type.tiles * 16f + 8,
                    bunker.y, u);
            if (spot == null) spot = freeSpotNear(bunker.x, bunker.y + bunker.type.tiles * 16f + 8, u);
            if (spot == null) continue;
            bunker.cargo.remove(u);
            u.garrisoned = false;
            u.bunker = null;
            u.x = spot[0];
            u.y = spot[1];
            any = true;
        }
        return any;
    }

    public boolean orderGarrison(List<Ent> sel, Ent bunker) {
        boolean any = false;
        for (Ent u : sel) {
            if (garrisonError(bunker, u) == null && garrisonUnit(bunker, u)) any = true;
        }
        return any;
    }

    // ------------------------------------------------- v2.25: Terran add-ons
    /**
     * The world position of a parent building's pad `slot`. The pads are the
     * four 2x2 squares flush against the parent's sides; the parent is a 3x3
     * (96 px) footprint and an add-on a 2x2 (64 px), so slot 0 sits one
     * add-on-width to the +x side, centred on the parent's row. These are the
     * original's own add-on offsets for a 3x3 parent.
     */
    public static float[] addonPad(Ent parent, int slot) {
        float h = parent.type.tiles * 16f;      // parent half-extent, px
        float aw = 32f;                          // add-on half-extent (2 tiles)
        switch (slot) {
            case 1: return new float[]{parent.x - h - aw, parent.y};
            case 2: return new float[]{parent.x, parent.y + h + aw};
            case 3: return new float[]{parent.x, parent.y - h - aw};
            default: return new float[]{parent.x + h + aw, parent.y};
        }
    }

    /** True when `key` is an add-on (built by its parent, not by an SCV). */
    public static boolean isAddon(String key) {
        Type t = TYPES.get(key);
        return t != null && t.addonFor != null && !t.addonFor.isEmpty();
    }

    /** The completed add-on of `key` attached to `parent`, or null. */
    public Ent addonOf(Ent parent, String key) {
        if (parent == null) return null;
        for (Ent e : ents) {
            if (!e.alive() || e.constructing || e.addonParent != parent) continue;
            if (e.type.key.equals(key)) return e;
        }
        return null;
    }

    /** The completed add-on a building needs to open its advanced rows, or null. */
    public Ent addonFor(Ent building) {
        if (building == null || building.type.addonNeeded.isEmpty()) return null;
        return addonOf(building, building.type.addonNeeded);
    }

    /**
     * Why this add-on cannot be attached to `parent` right now, or null. The
     * caller (the command card) offers the build only for a completed parent
     * with a free matching pad, which is the original's rule.
     */
    public String addonError(Ent parent, String key) {
        Type t = TYPES.get(key);
        if (t == null || t.addonFor.isEmpty()) return "该建筑无法建造附件";
        if (parent == null || !parent.alive() || parent.constructing) return "目标无效";
        if (parent.team != 0) return "只能在我方建筑上建造附件";
        if (!parent.type.key.equals(t.addonFor)) return nameOf(t.addonFor) + "才能建造" + t.name;
        if (addonOf(parent, key) != null) return t.name + "已存在";
        // one add-on per pad
        for (Ent e : ents) {
            if (e.alive() && e.addonParent == parent && e.type.addonSlot == t.addonSlot)
                return "该位置已被占用";
        }
        // the pad must be clear. The general building-collision test in
        // canPlace() sits exactly on the pad's boundary (a 3x3 parent and a
        // 2x2 add-on are (3+2)*16 = 80 px apart, and that test uses a strict
        // `<`), so it cannot be relied on here -- an SCV could otherwise drop a
        // depot on the pad and the add-on would then be built on top of it.
        float[] pad = addonPad(parent, t.addonSlot);
        float half = t.tiles * 16f;               // 32 px
        for (Ent e : ents) {
            if (!e.alive() || e == parent) continue;
            float ex = e.isBuilding() ? e.type.tiles * 16f : 8f;
            if (Math.abs(e.x - pad[0]) < half + ex && Math.abs(e.y - pad[1]) < half + ex)
                return "附件位置被占用";
        }
        for (Mineral m : minerals) {
            if (Math.abs(m.x - pad[0]) < half + 26 && Math.abs(m.y - pad[1]) < half + 26)
                return "附件位置被矿物阻挡";
        }
        // and the pad must be on walkable ground
        for (int my = -1; my <= 1; my += 2)
            for (int mx = -1; mx <= 1; mx += 2)
                if (!passMini((int) ((pad[0] + mx * 24) / 8), (int) ((pad[1] + my * 24) / 8)))
                    return "附件位置不可建造";
        if (mineralsPlayer < t.cost) return "晶体矿不足";
        if (gasPlayer < t.gasCost) return "瓦斯不足";
        return null;
    }

    /**
     * Attach an add-on to `parent`, spawning it on the pad and paying for it.
     * The add-on grows like any other Terran structure (an SCV must finish it
     * only in the sense that buildProgress climbs; here it is placed already
     * under construction and self-finishes on the normal building path).
     */
    public Ent buildAddon(Ent parent, String key) {
        if (addonError(parent, key) != null) return null;
        Type t = TYPES.get(key);
        float[] p = addonPad(parent, t.addonSlot);
        mineralsPlayer -= t.cost;
        gasPlayer -= t.gasCost;
        Ent e = spawn(key, 0, p[0], p[1], true);
        if (e != null) {
            e.addonParent = parent;
            // spawn() snaps a 2x2 building to the tile grid, which would pull
            // the add-on 16 px off the pad the parent's geometry defines. The
            // pad IS the position, so re-stamp it after the snap.
            occupyFootprint(e, false);
            e.x = p[0];
            e.y = p[1];
            occupyFootprint(e, true);
            // an add-on is a finished structure the moment it is attached;
            // the original builds it over time, but the pad is the scarce
            // resource here, not the 25 seconds of construction.
            e.constructing = false;
            e.buildProgress = 1f;
            occupyFootprint(e, true);
        }
        return e;
    }

    /**
     * Per-tick add-on upkeep: an add-on whose parent is gone stops working
     * (the original destroys the add-on with the parent). Returning it to the
     * "dead but present" state would leave invisible buildings on the map, so
     * the add-on is destroyed outright -- the plan's "主楼被毁附件停摆".
     */
    private void updateAddons() {
        for (Ent e : ents) {
            if (!e.alive() || e.addonParent == null) continue;
            if (!e.addonParent.alive()) {
                e.hp = 0;
                e.addonParent = null;
            }
        }
    }

    // --------------------------------------------- v2.25: radar scan + nuke
    /** The comsat's scanner sweep: 50 energy, a 12-tile square, 8 seconds. */
    public static final float COST_SCAN = 50f;
    public static final float SCAN_RADIUS = 384f;
    public static final float SCAN_DURATION = 8f;
    /** Nuke: 800 at the centre, falling off to 25% at the 12-tile rim. */
    public static final int NUKE_DAMAGE = 800;
    public static final float NUKE_RADIUS = 384f;
    public static final float NUKE_FALLOFF = 0.25f;
    /** Warning-to-impact delay, and how long a silo takes to build a missile. */
    public static final float NUKE_DELAY = 10f;
    public static final float NUKE_BUILD_TIME = 30f;

    /** An active scanner sweep. The view draws the square; the core reveals fog. */
    public static class Scan {
        public float x, y, t;
        public int team;
    }

    /** A nuclear strike counting down to impact, visible to BOTH players. */
    public static class Nuke {
        public float x, y, t;         // t counts up to NUKE_DELAY
        public int team;
        public Ent silo;              // the silo that is armed while this flies
        public boolean done;
    }

    public final List<Scan> scans = new ArrayList<>();
    public final List<Nuke> nukes = new ArrayList<>();

    /** null when the comsat may sweep now, else a human-readable reason. */
    public String scanError(Ent comsat) {
        if (comsat == null || !comsat.alive() || comsat.constructing)
            return "目标无效";
        if (!"comsat".equals(comsat.type.key)) return "该单位无法扫描";
        if (comsat.addonParent == null || !comsat.addonParent.alive())
            return "雷达站已停摆";
        return energyGate(comsat, COST_SCAN);
    }

    /**
     * Fire a scanner sweep centred on (tx, ty). The sweep is the comsat's own
     * energy pool (it is a caster like any spell unit), reveals the square on
     * the minimap and the main view for SCAN_DURATION seconds, and -- because
     * it is a reveal -- also shows cloaked enemies standing in it.
     */
    public boolean castScan(Ent comsat, float tx, float ty) {
        if (scanError(comsat) != null) return false;
        comsat.energy -= COST_SCAN;
        Scan s = new Scan();
        s.x = tx;
        s.y = ty;
        s.team = comsat.team;
        s.t = SCAN_DURATION;
        scans.add(s);
        revealAround(tx, ty, (int) (SCAN_RADIUS / 32f));
        events.add(new Object[]{"scan", tx, ty});
        return true;
    }

    /** The armed silo owned by `team`, or null. A ghost needs one to strike. */
    public Ent armedSilo(int team) {
        for (Ent e : ents) {
            if (e.alive() && !e.constructing && e.team == team && e.nukeArmed
                    && "nukesilo".equals(e.type.key)) return e;
        }
        return null;
    }

    /** null when the ghost may call a strike now, else a reason. */
    public String nukeError(Ent ghost) {
        if (ghost == null || !ghost.alive() || ghost.isBuilding()) return "目标无效";
        if (!"ghost".equals(ghost.type.key)) return "只有幽灵可以呼叫核弹";
        if (ghost.team != 0) return "只能呼叫我方核弹";
        if (ghost.cargoOf != null || ghost.garrisoned) return "该单位不在场上";
        if (armedSilo(0) == null) return "没有已装填的核弹井";
        return null;
    }

    /**
     * Call a nuclear strike on (tx, ty). The missile falls after NUKE_DELAY
     * seconds, during which the ghost is locked in place -- the original's
     * window for the defender to kill the spotter and cancel the strike, which
     * is the whole drama of the ability. The countdown is visible to both
     * sides (the plan's "敌我都能看到").
     */
    public boolean callNuke(Ent ghost, float tx, float ty) {
        if (nukeError(ghost) != null) return false;
        Ent silo = armedSilo(0);
        silo.nukeArmed = false;          // the missile leaves the silo
        silo.nukeProgress = 0f;
        Nuke n = new Nuke();
        n.x = clamp(tx, 0, wPx);
        n.y = clamp(ty, 0, hPx);
        n.team = 0;
        n.silo = silo;
        nukes.add(n);
        // the spotter is rooted for the countdown
        ghost.nukeLock = NUKE_DELAY;
        ghost.nukeX = n.x;
        ghost.nukeY = n.y;
        events.add(new Object[]{"nuke", n.x, n.y});
        return true;
    }

    private void updateNukes(float dt) {
        // a ghost is rooted while its strike is in the air
        for (Ent e : ents) {
            if (e.nukeLock > 0) e.nukeLock = Math.max(0, e.nukeLock - dt);
        }
        // silos build a missile over time and then sit armed
        for (Ent e : ents) {
            if (!e.alive() || e.constructing || !"nukesilo".equals(e.type.key)) continue;
            if (e.addonParent != null && !e.addonParent.alive()) continue;
            if (e.nukeArmed) continue;
            if (e.nukeProgress <= 0f) e.nukeProgress = 0.0001f;   // auto-arm on first tick
            e.nukeProgress += dt / NUKE_BUILD_TIME;
            if (e.nukeProgress >= 1f) {
                e.nukeProgress = 1f;
                e.nukeArmed = true;
            }
        }
        // countdowns
        for (Nuke n : nukes) {
            if (n.done) continue;
            n.t += dt;
            if (n.t >= NUKE_DELAY) {
                n.done = true;
                splash(n.x, n.y, NUKE_DAMAGE, "explosive", null, NUKE_RADIUS, NUKE_FALLOFF, null);
                for (Ent e : ents) {
                    if (!e.alive()) continue;
                    float dx = e.x - n.x, dy = e.y - n.y;
                    if (dx * dx + dy * dy <= NUKE_RADIUS * NUKE_RADIUS
                            && !e.isBuilding() && e.type.radius < 20) {
                        // the original floors small units: nothing survives the centre
                        damage(e, NUKE_DAMAGE, null, "explosive");
                    }
                }
                playAnim("nukehit", n.x, n.y, animFrames("nukehit"), n.team, 26f, 1f);
            }
        }
        for (int i = nukes.size() - 1; i >= 0; i--)
            if (nukes.get(i).done) nukes.remove(i);
    }

    /** Age the scanner sweeps out, revealing the square on the way. */
    private void updateScans(float dt) {
        for (int i = scans.size() - 1; i >= 0; i--) {
            Scan s = scans.get(i);
            s.t -= dt;
            if (s.t <= 0) { scans.remove(i); continue; }
            revealAround(s.x, s.y, (int) (SCAN_RADIUS / 32f));
        }
    }

    /**
     * Is (x, y) inside a live scanner sweep? The view uses this to draw the
     * bright square, and the cloak layer uses it as a second reveal source --
     * a sweep shows cloaked units in its square even without a detector, which
     * is the whole point of the ability against a dark templar rush.
     */
    public boolean scanReveals(float x, float y, int byTeam) {
        for (Scan s : scans) {
            if (s.team != byTeam) continue;
            float dx = s.x - x, dy = s.y - y;
            if (dx * dx + dy * dy <= SCAN_RADIUS * SCAN_RADIUS) return true;
        }
        return false;
    }

    // ------------------------------------------- v2.26: production fidelity
    // ------------------------------------------- v2.27: growth and scale
    /**
     * The population ceiling. The plan asks for 200 with a headroom check and
     * 100 as the documented fallback if the engine cannot hold it. Measured on
     * the desktop harness with 200 marines against 200 zerglings in sustained
     * combat, a tick cost 10.9 ms -- a third of the 33 ms frame at 30 fps, on a
     * desktop CPU. A phone has roughly a third of that single-core throughput,
     * so 400 entities would not hold frame on the low-end target this game
     * ships to. 100 is the plan's own fallback and the largest tier that stays
     * comfortably inside budget; the tier list below is the growth ladder and
     * the ceiling is just its last entry.
     */
    public static final int[] SUPPLY_TIERS = {40, 100};
    public static final int SUPPLY_CAP = SUPPLY_TIERS[SUPPLY_TIERS.length - 1];

    /** How close two templars have to be to merge. */
    public static final float MERGE_RANGE = 48f;
    /** A carrier holds and launches up to this many interceptors. */
    public static final int HANGAR_CAP = 8;
    /** A reaver carries this many scarabs and reloads them beside a robotics bay. */
    public static final int REAVER_AMMO = 10;
    public static final float REAVER_RELOAD_TIME = 12f;
    /** Interceptors launch at anything inside this range of the carrier. */
    public static final float HANGAR_RANGE = 224f;

    /** The unit a two-unit merge produces, or null when the pair is not mergeable. */
    public static String mergeResult(String key) {
        if ("templar".equals(key)) return "archon";
        if ("dtemplar".equals(key)) return "darchon";
        return null;
    }

    /**
     * Why these two units cannot merge, or null. The original's rule is exact:
     * two of the SAME type, both fully built, both on the field, standing next
     * to each other. Anything looser turns the merge into a free unit printer.
     */
    public String mergeError(List<Ent> pair, String toKey) {
        if (pair == null || pair.size() != 2) return "需要选中两个同类单位";
        Ent a = pair.get(0), b = pair.get(1);
        if (a == null || b == null || !a.alive() || !b.alive()) return "目标无效";
        if (!a.type.key.equals(b.type.key)) return "必须是两个同类单位";
        if (mergeResult(a.type.key) == null) return "该单位无法合体";
        if (toKey != null && !mergeResult(a.type.key).equals(toKey))
            return "该单位无法合体为" + nameOf(toKey);
        if (a.cargoOf != null || b.cargoOf != null || a.garrisoned || b.garrisoned)
            return "该单位不在场上";
        if (a.constructing || b.constructing) return "该单位尚未完成";
        if (dist(a, b) > MERGE_RANGE) return "两个单位距离太远";
        return null;
    }

    /**
     * Merge two templars into one archon. Both are consumed and the archon
     * appears between them with its shield already up, which is the original's
     * "the merge is the birth" behaviour. Returns the new unit, or null.
     */
    public Ent orderMerge(List<Ent> pair, String toKey) {
        if (mergeError(pair, toKey) != null) return null;
        Ent a = pair.get(0), b = pair.get(1);
        String result = toKey != null ? toKey : mergeResult(a.type.key);
        float mx = (a.x + b.x) / 2f, my = (a.y + b.y) / 2f;
        int team = a.team;
        // consume both. Setting hp to 0 lets the ordinary death sweep remove
        // them, so the scoreboard and supply tally stay honest -- a merge is
        // two losses and one gain, exactly as the original counts it.
        a.hp = 0;
        b.hp = 0;
        Ent archon = spawn(result, team, mx, my, true);
        if (archon != null) {
            if (team == 0) archon.selected = false;
            playAnim("pshield", mx, my, animFrames("pshield"), team, 14f, 1f);
        }
        return archon;
    }

    // ---- the zerg burrow: any ground zerg unit may hide ---------------------
    /** True for the zerg ground units the original lets burrow. */
    public static boolean canBurrow(Ent e) {
        if (e == null || !e.alive() || e.isBuilding() || e.type.flying) return false;
        switch (e.type.key) {
            case "zergling": case "hydra": case "drone": case "defiler":
            case "lurker": case "lurker_bur": case "queen": case "ultra":
            case "broodling": case "larva":
                return true;
            default:
                return false;
        }
    }

    public String burrowError(Ent e) {
        if (e == null || !e.alive()) return "目标无效";
        if (!canBurrow(e)) return "该单位无法钻地";
        if (e.burrowed && e.moving) return "移动中无法钻地";
        return null;
    }

    /**
     * Toggle a zerg unit's burrow. A burrowed unit is hidden (isCloakedNow
     * already folds this in) and immobile -- it cannot move, and melee cannot
     * reach it. The original's burrow is a defensive stance, not a second
     * movement mode, so the unit is rooted while down.
     */
    public boolean toggleBurrow(Ent e) {
        if (burrowError(e) != null) return false;
        e.burrowed = !e.burrowed;
        if (e.burrowed) {
            e.moving = false;
            e.path = Ent.EMPTY_PATH;
            cancelQueuedPath(e);   // v2.43 P0-c: rooted while down
            e.target = null;
        }
        events.add(new Object[]{"burrow"});
        return true;
    }

    // ---- the carrier's interceptors -----------------------------------------
    /**
     * Per-tick hangar management. A carrier builds interceptors up to its cap
     * over time (the original builds them at the robotics bay for a cost; here
     * they are free and slow, which keeps the carrier's power gated on time
     * rather than on a second economy). Interceptors launch when an enemy is
     * inside HANGAR_RANGE and dock when nothing is.
     */
    private void updateHangars(float dt) {
        for (Ent e : ents) {
            if (!e.alive() || e.type.hangarCap <= 0) continue;
            if (e.constructing) continue;
            if (e.interceptors < e.type.hangarCap) {
                e.interceptorCd -= dt;
                if (e.interceptorCd <= 0) {
                    e.interceptorCd = 4f;
                    e.interceptors++;
                }
            }
            // launch/recall by threat
            Ent foe = findEnemyInRange(e, HANGAR_RANGE);
            int want = foe != null ? e.interceptors : 0;
            e.launched = want;
        }
    }

    // ---- the reaver's scarab ammo -------------------------------------------
    /**
     * A reaver carries a limited number of scarabs and reloads them only while
     * standing beside the robotics facility that built it -- the original's
     * rule, and the reason a reaver is a siege unit rather than a rifleman.
     */
    private void updateAmmo(float dt) {
        for (Ent e : ents) {
            if (!e.alive() || e.type.ammoCap <= 0) continue;
            if (e.ammo >= e.type.ammoCap) continue;
            Ent bay = null;
            for (Ent b : ents) {
                if (b.alive() && !b.constructing && b.team == e.team
                        && "robotic".equals(b.type.key)) { bay = b; break; }
            }
            if (bay == null || dist(e, bay) > 120f) continue;
            e.ammoCd -= dt;
            if (e.ammoCd <= 0) {
                e.ammoCd = REAVER_RELOAD_TIME / e.type.ammoCap;
                e.ammo++;
            }
        }
    }

    /**
     * v2.23 batch B: a garrisoned unit fires from the bunker. The bunker has no
     * weapon of its own (type.dmg == 0), so without this a full bunker would be
     * a very expensive wall. Range is measured from the bunker, which is what
     * gives the position its reach advantage over the same marines standing in
     * the open.
     */
    private void updateGarrisonFire(Ent bunker) {
        if (bunker.type.bunkerCap <= 0 || bunker.cargo.isEmpty()) return;
        for (Ent u : bunker.cargo) {
            if (!u.alive() || u.type.dmg <= 0) continue;
            if (u.cd > 0) continue;
            Ent tgt = u.target;
            if (tgt == null || !tgt.alive() || tgt.cargoOf != null
                    || tgt.garrisoned
                    || dist(bunker, tgt) > u.type.range + 12) {
                tgt = findEnemyInRangeFrom(bunker.x, bunker.y, u, u.type.range);
                u.target = tgt;
            }
            if (tgt != null && u.cd <= 0) {
                u.cd = effectiveCooldown(u);
                u.facing = (float) Math.atan2(tgt.y - bunker.y, tgt.x - bunker.x);
                fireFrom(u, bunker, tgt);
            }
        }
    }

    /** Load-all-possible sweep for a freshly clicked bunker. */
    public boolean orderGarrisonNear(Ent bunker) {
        if (bunker == null || bunker.type.bunkerCap <= 0) return false;
        boolean any = false;
        for (Ent o : ents) {
            if (o.team != bunker.team || !o.alive() || o.isBuilding()) continue;
            if (o.garrisoned || o.cargoOf != null) continue;
            if (o.type.supply <= 0) continue;
            if (dist(bunker, o) > LOAD_RANGE) continue;
            if (garrisonError(bunker, o) != null) continue;
            if (garrisonUnit(bunker, o)) any = true;
        }
        return any;
    }

    public void orderMove(List<Ent> sel, float wx, float wy, boolean attackMove) {
        int idx = 0;
        boolean anyOrdered = false, anyApprox = false;
        for (Ent e : sel) {
            if (e.isBuilding()) continue;
            // v2.25: a ghost calling a nuclear strike is rooted for the
            // countdown. The original lets the defender kill the spotter to
            // cancel the hit, and a ghost that could walk away would remove
            // that counterplay entirely.
            if (e.nukeLock > 0) continue;
            int ox = (idx % 5) - 2, oy = (idx / 5) - 2;
            idx++;
            setPath(e, wx + ox * 18, wy + oy * 18);
            anyOrdered = true;
            if (lastPathApprox) anyApprox = true;
            e.target = null;
            e.patrolling = false;       // a plain move cancels a patrol loop
            e.repairTarget = null;
            e.holding = false;          // ...and cancels a hold order
            if (attackMove) e.aiTimer = -1;   // marks attack-move
            if (isWorker(e)) {
                e.workerState = Ent.W_IDLE;
                e.mineTarget = null;
            }
        }
        // feedback: every ground order leaves a mark so the tap is echoed
        if (anyOrdered) {
            addMarker(wx, wy, !anyApprox);
            if (anyApprox) events.add(new Object[]{"error", "无法到达该位置"});
        }
    }

    /**
     * v2.14 batch 1.3: Hold Position. The unit stops where it stands and only
     * engages what walks into its own weapon range. It never chases -- that is
     * the one rule that separates this from attack-move -- and it never leaves
     * the spot it was given the order on, so a hold line keeps its shape even
     * when a single zergling runs past it.
     */
    public void orderHold(List<Ent> sel) {
        boolean any = false;
        for (Ent e : sel) {
            if (e.isBuilding()) continue;
            e.holding = true;
            e.holdX = e.x;
            e.holdY = e.y;
            e.moving = false;
            e.path = Ent.EMPTY_PATH;
            // v2.43 P0-c: drop any request still waiting in the budget queue.
            // Hold is an explicit "stop here" -- a queued chase request would
            // otherwise fire a few ticks later and walk the unit off the spot.
            cancelQueuedPath(e);
            e.pathIndex = 0;
            e.goalX = e.x;
            e.goalY = e.y;
            e.target = null;
            e.patrolling = false;
            e.repairTarget = null;
            e.aiTimer = 0;          // holding is not an attack-move
            if (isWorker(e)) {
                e.workerState = Ent.W_IDLE;
                e.mineTarget = null;
            }
            any = true;
        }
        if (any) {
            // reuse the "stop" marker: the order is a stop that keeps shooting
            for (Ent e : sel)
                if (e.alive()) { addMarker(e.x, e.y, true); break; }
        }
    }

    /** Release a hold order (any other order implicitly does this too). */
    public void stopHold(Ent e) {
        e.holding = false;
    }

    public void orderAttack(List<Ent> sel, Ent target) {
        for (Ent e : sel) {
            if (e.isBuilding()) continue;
            e.target = target;
            e.patrolling = false;
            e.repairTarget = null;
            e.holding = false;
            setPath(e, target.x, target.y);
        }
    }

    /**
     * Patrol (v2.5 batch-6): the unit walks to the tapped point, then
     * continuously back and forth between where it started and that point.
     * Endpoints are stored on the Ent so the reversal needs no extra state
     * machine -- see the path-completion hook in update().
     */
    public void orderPatrol(List<Ent> sel, float wx, float wy) {
        boolean any = false;
        for (Ent e : sel) {
            if (e.isBuilding()) continue;
            e.patrolling = true;
            e.patrolAX = e.x;
            e.patrolAY = e.y;
            e.patrolBX = clamp(wx, 8, wPx - 8);
            e.patrolBY = clamp(wy, 8, hPx - 8);
            e.target = null;
            e.repairTarget = null;
            e.holding = false;
            if (isWorker(e)) {
                e.workerState = Ent.W_IDLE;
                e.mineTarget = null;
            }
            setPath(e, e.patrolBX, e.patrolBY);
            any = true;
        }
        if (any) addMarker(wx, wy, true);
    }

    /** Cancel any patrol loop (used by every other order). */
    public void stopPatrol(Ent e) {
        e.patrolling = false;
    }

    /**
     * Repair (v2.5 batch-6): SCVs mend a friendly damaged unit or building.
     * Costs minerals per hit point and is refused when either the target is
     * already whole or the player cannot pay.
     */
    public static final int REPAIR_COST_PER_HP = 1;      // minerals per hp
    public static final float REPAIR_HP_PER_SEC = 6f;    // mend rate

    /** null when the order is legal, else a human-readable reason. */
    public String repairError(Ent target) {
        if (target == null || !target.alive()) return "目标无效";
        if (target.team != 0) return "只能修理我方单位";
        if (target.hp >= target.type.hp) return "目标未受损";
        if (mineralsPlayer <= 0) return "晶体矿不足";
        return null;
    }

    public boolean orderRepair(List<Ent> sel, Ent target) {
        if (repairError(target) != null) return false;
        boolean any = false;
        for (Ent e : sel) {
            if (!isWorker(e)) continue;
            e.repairTarget = target;
            e.target = null;
            e.patrolling = false;
            e.workerState = Ent.W_IDLE;
            e.mineTarget = null;
            setPath(e, target.x, target.y);
            any = true;
        }
        return any;
    }

    // ------------------------------------------- v2.17 resume construction
    public String resumeBuildError(Ent target) {
        if (target == null || !target.alive()) return "目标无效";
        if (!target.isBuilding() || !target.constructing) return "该建筑未在建造";
        if (target.team != 0) return "只能继续建造我方建筑";
        return null;
    }

    public boolean orderResumeBuild(List<Ent> sel, Ent target) {
        if (resumeBuildError(target) != null) return false;
        boolean any = false;
        for (Ent e : sel) {
            if (!isWorker(e)) continue;
            e.target = target;
            e.repairTarget = null;
            e.healTarget = null;
            e.mineTarget = null;
            e.patrolling = false;
            e.holding = false;
            e.workerState = Ent.W_IDLE;
            setPath(e, target.x, target.y);
            any = true;
        }
        return any;
    }

    /**
     * v2.44 gas fix: a geyser is harvestable only through a COMPLETED gas
     * building sitting on it. Before, tapping the geyser directly sent a
     * worker to mine gas nobody could deliver (nearestDropOff(gas) finds no
     * building, the load vanished and the worker went idle), and tapping the
     * REFINERY itself selected the building instead of ever reaching here.
     * GameView now routes a worker tap on the gas building to its geyser and
     * this gate keeps the pre-completion window honest.
     */
    public boolean gasHarvestable(Mineral m) {
        if (m == null) return false;
        if (m.variant < 3) return m.amount > 0;
        return m.amount > 0 && m.refinery != null && m.refinery.alive()
                && !m.refinery.constructing && m.refinery.buildProgress >= 1f;
    }

    public void orderHarvest(List<Ent> sel, Mineral m) {
        if (!gasHarvestable(m)) return;
        for (Ent e : sel) {
            if (!isWorker(e)) continue;
            e.mineTarget = m;
            e.workerState = Ent.W_TO_MINE;
            setPath(e, m.x, m.y);
        }
    }

    // ------------------------------------------------- v2.11 medic (batch C)
    /**
     * The medic's Heal, which the plan asks to reuse the repair machinery for.
     * It is the same shape as repairError/orderRepair with two deliberate
     * differences, both straight out of BroodUnits.doc:
     *   - it costs nothing (the manual's only price is time: 1 energy per 2 hp,
     *     and this game has no energy pool, so it is simply free), and
     *   - it only works on organic ground units. Protoss are not organic in the
     *     original's sense and neither are buildings, which is exactly why the
     *     ability is interesting: it heals marines and zerglings, not tanks.
     */
    public static final float HEAL_HP_PER_SEC = 8f;

    /**
     * True for the units a medic may heal: living tissue, on the ground.
     * This is deliberately a positive list rather than "everything except the
     * protoss". The manual's word is *organic*, and the terran half of the
     * roster is mostly machinery -- an early draft of this method healed
     * siege tanks, which is the one thing a medic famously cannot do.
     */
    public static boolean isBiological(Ent e) {
        if (e == null || e.isBuilding() || e.type.flying) return false;
        String k = e.type.key;
        // Terran: the infantry rows only. The vulture, the siege tank, every
        // aircraft and the SCV are machines -- which is exactly why the SCV's
        // repair is a separate, ore-paying order instead of a heal.
        if ("marine".equals(k) || "firebat".equals(k)
                || "ghost".equals(k) || "medic".equals(k)) return true;
        // Zerg ground rows are all living tissue. Spider mines are not on this
        // list (they are machinery, and nobody can target one anyway).
        if ("zergling".equals(k) || "hydra".equals(k) || "drone".equals(k)
                || "ultra".equals(k) || "defiler".equals(k)
                || "queen".equals(k) || "lurker".equals(k)
                || "lurker_bur".equals(k) || "broodling".equals(k)) return true;
        // Protoss, and anything a later batch adds without thinking about it,
        // is not healable. Failing closed is the safe direction here.
        return false;
    }

    /** null when the heal order is legal, else a human-readable reason. */
    public String healError(Ent target) {
        if (target == null || !target.alive()) return "目标无效";
        if (target.team != 0) return "只能治疗我方单位";
        if (!isBiological(target)) return "只能治疗生物单位";
        if (target.hp >= target.type.hp) return "目标未受损";
        return null;
    }

    public boolean orderHeal(List<Ent> sel, Ent target) {
        if (healError(target) != null) return false;
        boolean any = false;
        for (Ent e : sel) {
            if (!"medic".equals(e.type.key)) continue;
            e.healTarget = target;
            e.target = null;
            e.patrolling = false;
            e.repairTarget = null;
            setPath(e, target.x, target.y);
            any = true;
        }
        return any;
    }

    // --------------------------------------------- v2.11 defiler (batch B)
    /**
     * Dark Swarm and Ensnare. Both are area effects that outlive the caster,
     * so they follow the psionic storm's design exactly: a plain data object
     * on a list the view draws, and a per-caster cooldown instead of an energy
     * cost. Dark Swarm is the interesting one -- it makes everything inside it
     * immune to *ranged* fire, so it is a hard counter to the tanks and
     * dragoons that otherwise decide every fight.
     */
    public static final float DSWARM_DURATION = 10f;
    public static final float DSWARM_RADIUS = 96f;
    public static final float DSWARM_COOLDOWN = 20f;
    public static final float ENSNARE_DURATION = 8f;
    public static final float ENSNARE_RADIUS = 88f;
    public static final float ENSNARE_COOLDOWN = 16f;
    public static final float ENSNARE_SLOW = 0.5f;     // speed multiplier

    /** A live Dark Swarm cloud. */
    public static class Dswarm {
        public float x, y, t;
        public int team;
        public boolean done() { return t >= DSWARM_DURATION; }
    }

    /** A live Ensnare field. */
    public static class Ensnare {
        public float x, y, t;
        public int team;
        public boolean done() { return t >= ENSNARE_DURATION; }
    }

    /**
     * v2.14 batch 1.5: Disruption Web. The corsair's field, modelled on Dark
     * Swarm because the original's is mechanically the same idea -- anything
     * standing inside cannot use a RANGED weapon. Two deliberate differences:
     * it is team-filtered (it is a placed field, not a physical blast, and the
     * original does not friendly-fire it), and it blocks the shooter rather
     * than the target, so a unit under a web cannot shoot out of it either.
     */
    public static class Dweb {
        public float x, y, t;
        public int team;
        public boolean done() { return t >= DWEB_DURATION; }
    }

    public final List<Dswarm> dswarms = new ArrayList<>();
    public final List<Ensnare> ensnares = new ArrayList<>();
    public final List<Dweb> dwebs = new ArrayList<>();

    /** True when (x, y) sits under a friendly-to-e the swarm cloud. */
    public boolean underDswarm(float x, float y) {
        for (Dswarm d : dswarms) {
            float dx = x - d.x, dy = y - d.y;
            if (dx * dx + dy * dy <= DSWARM_RADIUS * DSWARM_RADIUS) return true;
        }
        return false;
    }

    /** True when (x, y) is caught by any ensnare field. */
    public boolean underEnsnare(float x, float y) {
        for (Ensnare s : ensnares) {
            float dx = x - s.x, dy = y - s.y;
            if (dx * dx + dy * dy <= ENSNARE_RADIUS * ENSNARE_RADIUS) return true;
        }
        return false;
    }

    /**
     * v2.14 batch 1.5: team-aware swarm test. A cloud shields the units of the
     * side that laid it -- which is what makes "swarm up, then charge" a plan
     * rather than a coin flip, and what the AI has to respect when it decides
     * whether a storm is worth casting.
     */
    public boolean underDswarmFor(float x, float y, int team) {
        for (Dswarm d : dswarms) {
            if (d.team != team) continue;
            float dx = x - d.x, dy = y - d.y;
            if (dx * dx + dy * dy <= DSWARM_RADIUS * DSWARM_RADIUS) return true;
        }
        return false;
    }

    /**
     * True when (x, y) is inside ANY disruption web. Deliberately not
     * team-filtered: the original's web silences whoever stands in it,
     * including the corsair's own army, and that is what makes placing it a
     * decision rather than a free win button.
     */
    public boolean underDweb(float x, float y) {
        for (Dweb w : dwebs) {
            float dx = x - w.x, dy = y - w.y;
            if (dx * dx + dy * dy <= DWEB_RADIUS * DWEB_RADIUS) return true;
        }
        return false;
    }

    public String dswarmError(Ent e) {
        if (e == null || !e.alive() || e.isBuilding()) return "目标无效";
        if (!"defiler".equals(e.type.key)) return "该单位无法施放黑暗蜂群";
        if (e.dswarmCd > 0) return "黑暗蜂群冷却中";
        return energyGate(e, COST_DSWARM);
    }

    public boolean castDswarm(Ent caster, float tx, float ty) {
        if (dswarmError(caster) != null) return false;
        Dswarm d = new Dswarm();
        d.x = tx;
        d.y = ty;
        d.team = caster.team;
        dswarms.add(d);
        caster.energy -= COST_DSWARM;
        caster.dswarmCd = DSWARM_COOLDOWN;
        caster.facing = (float) Math.atan2(ty - caster.y, tx - caster.x);
        caster.dir = dirOf(caster.facing);
        return true;
    }

    public String ensnareError(Ent e) {
        if (e == null || !e.alive() || e.isBuilding()) return "目标无效";
        if (!"defiler".equals(e.type.key)) return "该单位无法施放诱捕";
        if (e.ensnareCd > 0) return "诱捕冷却中";
        return energyGate(e, COST_ENSNARE);
    }

    public boolean castEnsnare(Ent caster, float tx, float ty) {
        if (ensnareError(caster) != null) return false;
        Ensnare s = new Ensnare();
        s.x = tx;
        s.y = ty;
        s.team = caster.team;
        ensnares.add(s);
        caster.energy -= COST_ENSNARE;
        caster.ensnareCd = ENSNARE_COOLDOWN;
        caster.facing = (float) Math.atan2(ty - caster.y, tx - caster.x);
        caster.dir = dirOf(caster.facing);
        return true;
    }

    // ------------------------------------------- v2.11 spider mine (batch C)
    /**
     * PlaceMine, the vulture's ability. The mine is an ordinary entity with
     * speed 0 that sits where it was dropped; updateUnit gives it the trip
     * wire. It is deliberately free and on a cooldown, not an energy cost,
     * for the same reason the other spells are.
     */
    public static final float MINE_COOLDOWN = 12f;
    public static final float MINE_ARM_TIME = 0.5f;
    public static final float MINE_TRIGGER_RANGE = 48f;

    public String mineError(Ent e) {
        if (e == null || !e.alive() || e.isBuilding()) return "目标无效";
        if (!"vulture".equals(e.type.key)) return "该单位无法埋设蜘蛛雷";
        if (e.cd > 0) return "蜘蛛雷冷却中";
        return null;
    }

    public boolean placeMine(Ent vulture) {
        if (mineError(vulture) != null) return false;
        // Drop it just behind the vulture so it does not immediately trip on
        // whatever the vulture is driving toward.
        float mx = vulture.x - (float) Math.cos(vulture.facing) * 20f;
        float my = vulture.y - (float) Math.sin(vulture.facing) * 20f;
        Ent m = spawn("spider", vulture.team, clamp(mx, 8, wPx - 8),
                clamp(my, 8, hPx - 8), true);
        if (m == null) return false;
        m.facing = vulture.facing;
        m.dir = vulture.dir;
        vulture.cd = MINE_COOLDOWN;
        return true;
    }

    // ------------------------------------- v2.14 batch 1.5: five new spells
    /**
     * EMP, Irradiate, Yamato, Lockdown and Disruption Web. Each follows the
     * shape the v2.10/v2.11 spells already use: an `xxxError` gate returning a
     * Chinese reason (or null), and a `castXxx` returning whether it fired.
     * No energy cost, cooldowns only, for the same reason the earlier spells
     * are free -- there is no energy bar to spend.
     *
     * EMP_SHIELD_DAMAGE is the original's 200: enough to strip every protoss
     * unit's shield outright except an archon (350) or a nexus (300), which
     * keep a sliver. That is what makes EMP the hard counter to a protoss
     * deathball rather than just another nuke.
     */
    public static final float EMP_RADIUS = 96f;
    public static final float EMP_COOLDOWN = 24f;
    public static final int EMP_SHIELD_DAMAGE = 200;

    public static final float IRRADIATE_DURATION = 12f;
    public static final float IRRADIATE_TICK = 0.5f;
    public static final int IRRADIATE_DAMAGE = 4;
    public static final float IRRADIATE_COOLDOWN = 20f;

    public static final int YAMATO_DAMAGE = 260;
    public static final float YAMATO_COOLDOWN = 30f;

    public static final float LOCKDOWN_DURATION = 8f;
    public static final float LOCKDOWN_COOLDOWN = 20f;

    public static final float DWEB_DURATION = 12f;
    public static final float DWEB_RADIUS = 96f;
    public static final float DWEB_COOLDOWN = 22f;

    /** Spell reach. Kept in one place so the AI can ask "is it in range". */
    public static final float SPELL_RANGE = 224f;

    /**
     * v2.14 batch 1.5: mechanical means "not biological and not a building".
     * The positive `isBiological` list already enumerates the fleshy units, so
     * protoss and terran vehicles fall out of it naturally -- which is exactly
     * the set Lockdown is allowed to freeze.
     */
    public static boolean isMechanical(Ent e) {
        return e != null && e.alive() && !e.isBuilding() && !isBiological(e);
    }

    public String empError(Ent e) {
        if (e == null || !e.alive() || e.isBuilding()) return "目标无效";
        if (!"vessel".equals(e.type.key)) return "该单位无法施放电磁脉冲";
        if (e.empCd > 0) return "电磁脉冲冷却中";
        return energyGate(e, COST_EMP);
    }

    /**
     * EMP Shockwave. Strips shields in a radius and does nothing to hp, which
     * is why it is the answer to a shielded army and a wasted cast against
     * zerg. Deliberately hits BOTH teams -- the original does, and that is
     * what makes aiming it a decision rather than a free button.
     */
    public boolean castEmp(Ent caster, float tx, float ty) {
        if (empError(caster) != null) return false;
        for (Ent o : ents) {
            if (!o.alive() || o.type.shield <= 0) continue;
            float dx = o.x - tx, dy = o.y - ty;
            if (dx * dx + dy * dy > EMP_RADIUS * EMP_RADIUS) continue;
            int before = o.shield;
            o.shield = Math.max(0, o.shield - EMP_SHIELD_DAMAGE);
            o.shieldDelay = SHIELD_DELAY;
            if (o.shield != before) {
                effects.add(new float[]{o.x, o.y, 0.4f, 0});
                alertIfPlayer(o);
            }
        }
        caster.energy -= COST_EMP;
        caster.empCd = EMP_COOLDOWN;
        caster.facing = (float) Math.atan2(ty - caster.y, tx - caster.x);
        caster.dir = dirOf(caster.facing);
        effects.add(new float[]{tx, ty, 0.6f, 0});
        playAnim("emp", tx, ty, animFrames("emp"), caster.team, 40f, 1f);
        return true;
    }

    public String irradiateError(Ent e, Ent target) {
        if (e == null || !e.alive() || e.isBuilding()) return "目标无效";
        if (!"vessel".equals(e.type.key)) return "该单位无法施放辐射";
        if (e.empCd > 0) return "辐射冷却中";
        if (energyGate(e, COST_IRRADIATE) != null) return "能量不足";
        if (target == null || !target.alive()) return "需要选择一个目标";
        if (!isBiological(target)) return "辐射只能作用于生物单位";
        float dx = target.x - e.x, dy = target.y - e.y;
        if (dx * dx + dy * dy > SPELL_RANGE * SPELL_RANGE) return "目标超出施法范围";
        return null;
    }

    /**
     * Irradiate. A damage-over-time that rides the VICTIM, so unlike a storm
     * it cannot be walked out of -- the unit just bleeds wherever it runs,
     * which is what makes it the right answer to a fast unit that would
     * otherwise escape. Biological targets only.
     */
    public boolean castIrradiate(Ent caster, Ent target) {
        if (irradiateError(caster, target) != null) return false;
        target.irradiateTime = IRRADIATE_DURATION;
        target.irradiateTick = 0f;
        caster.energy -= COST_IRRADIATE;
        caster.empCd = IRRADIATE_COOLDOWN;
        caster.facing = (float) Math.atan2(target.y - caster.y, target.x - caster.x);
        caster.dir = dirOf(caster.facing);
        effects.add(new float[]{target.x, target.y, 0.5f, 0});
        playAnim("ehamed", target.x, target.y, animFrames("ehamed"), caster.team, 26f, 1f);
        return true;
    }

    public String yamatoError(Ent e, Ent target) {
        if (e == null || !e.alive() || e.isBuilding()) return "目标无效";
        if (!"battlecruiser".equals(e.type.key)) return "该单位无法施放大和炮";
        if (e.yamatoCd > 0) return "大和炮冷却中";
        if (energyGate(e, COST_YAMATO) != null) return "能量不足";
        if (target == null || !target.alive()) return "需要选择一个目标";
        float dx = target.x - e.x, dy = target.y - e.y;
        if (dx * dx + dy * dy > SPELL_RANGE * SPELL_RANGE) return "目标超出施法范围";
        return null;
    }

    /**
     * Yamato Gun. One 260-damage shot on a long cooldown -- enough to delete a
     * tank or a sunken colony outright, which is the point: the battlecruiser's
     * ordinary laser is weak for its cost, and this is what the cost buys.
     */
    public boolean castYamato(Ent caster, Ent target) {
        if (yamatoError(caster, target) != null) return false;
        caster.energy -= COST_YAMATO;
        caster.yamatoCd = YAMATO_COOLDOWN;
        caster.facing = (float) Math.atan2(target.y - caster.y, target.x - caster.x);
        caster.dir = dirOf(caster.facing);
        // The bolt is a projectile so the target has a beat to move; damage is
        // typed normal, because Yamato is not a splash weapon.
        Shot s = new Shot();
        s.x = caster.x;
        s.y = caster.y - 6;
        s.tx = target.x;
        s.ty = target.y;
        s.dur = Math.max(0.08f, dist(caster, target) / 700f);
        s.t = 0;
        s.team = caster.team;
        s.missile = true;
        shots.add(s);
        pendingShots.add(new Object[]{s, target, YAMATO_DAMAGE, "normal", 0f, 0.5f, caster,
                "plasma"});
        playAnim("b_blastcan", caster.x, caster.y - 6, animFrames("b_blastcan"),
                caster.team, 30f, 1f);
        return true;
    }

    public String lockdownError(Ent e, Ent target) {
        if (e == null || !e.alive() || e.isBuilding()) return "目标无效";
        if (!"ghost".equals(e.type.key)) return "该单位无法施放锁定";
        if (e.lockdownCd > 0) return "锁定冷却中";
        if (energyGate(e, COST_LOCKDOWN) != null) return "能量不足";
        if (target == null || !target.alive()) return "需要选择一个目标";
        if (!isMechanical(target)) return "锁定只能作用于机械单位";
        float dx = target.x - e.x, dy = target.y - e.y;
        if (dx * dx + dy * dy > SPELL_RANGE * SPELL_RANGE) return "目标超出施法范围";
        return null;
    }

    /**
     * Lockdown. The target is frozen in place for eight seconds -- it cannot
     * move and cannot shoot, but it can still be shot. Mechanical only, which
     * is why it is the ghost's answer to a tank line and useless against
     * zerglings.
     */
    public boolean castLockdown(Ent caster, Ent target) {
        if (lockdownError(caster, target) != null) return false;
        target.lockdownTime = LOCKDOWN_DURATION;
        target.target = null;
        target.moving = false;
        target.path = Ent.EMPTY_PATH;
        cancelQueuedPath(target);   // v2.43 P0-c: frozen; no pending path may fire
        caster.energy -= COST_LOCKDOWN;
        caster.lockdownCd = LOCKDOWN_COOLDOWN;
        caster.facing = (float) Math.atan2(target.y - caster.y, target.x - caster.x);
        caster.dir = dirOf(caster.facing);
        effects.add(new float[]{target.x, target.y, 0.5f, 0});
        // The plan named no asset for lockdown; elect02 is the blue electric
        // crackle of a unit being shocked, which is what the spell is.
        playAnim("elect02", target.x, target.y, animFrames("elect02"), caster.team, 26f, 1f);
        return true;
    }

    public String dwebError(Ent e) {
        if (e == null || !e.alive() || e.isBuilding()) return "目标无效";
        if (!"corsair".equals(e.type.key)) return "该单位无法施放干扰网";
        if (e.dwebCd > 0) return "干扰网冷却中";
        return energyGate(e, COST_DWEB);
    }

    /**
     * Disruption Web. Anything standing inside loses its ranged weapon for the
     * duration -- and, like the original, the web does NOT check teams, so the
     * corsair's own army is silenced too. That is the whole tactical shape of
     * the spell: you place it on the enemy's tanks and then fight inside it
     * with melee, and if your own dragoons are caught in it they are just as
     * useless.
     */
    public boolean castDweb(Ent caster, float tx, float ty) {
        if (dwebError(caster) != null) return false;
        Dweb w = new Dweb();
        w.x = tx;
        w.y = ty;
        w.t = 0;
        w.team = caster.team;
        dwebs.add(w);
        caster.energy -= COST_DWEB;
        caster.dwebCd = DWEB_COOLDOWN;
        caster.facing = (float) Math.atan2(ty - caster.y, tx - caster.x);
        caster.dir = dirOf(caster.facing);
        playAnim("dweb", tx, ty, animFrames("dweb"), caster.team, 40f, 1f);
        return true;
    }

    public void setPath(Ent e, float wx, float wy) {
        e.goalX = clamp(wx, 8, wPx - 8);
        e.goalY = clamp(wy, 8, hPx - 8);
        // v2.43 P0-c: a synchronous request supersedes whatever is waiting in
        // the budget queue -- the caller is about to install a fresher path.
        e.pathGen = 0;
        int[] p = findPath((int) (e.x / 8), (int) (e.y / 8),
                (int) (e.goalX / 8), (int) (e.goalY / 8));
        e.path = p != null ? p : Ent.EMPTY_PATH;
        if (p != null) {
            e.pathIndex = Math.min(PATH_START_SKIP, (p.length >> 1) - 1);
        }
        e.moving = true;
    }

    // ------------------------------------------------------- path budget queue
    /**
     * v2.43 P0-c: how many A* searches one tick may run for paths that were
     * asked for by the simulation itself (chase, hold return, harvest, patrol
     * reversal, the AI wave). An AI wave hands the same destination to every
     * attacker in one tick, which used to mean one A* per attacker inside a
     * single frame -- the measured 100 ms-plus spike. Spreading them over
     * ceil(n / PATH_BUDGET) ticks flattens the spike and leaves the total work
     * unchanged.
     *
     * <p>Player orders do NOT go through this queue: orderMove/orderAttack/...
     * and tryBuild call setPath directly, so a click still resolves in the tick
     * it was made and still reports "无法到达该位置" immediately.
     *
     * <p>Determinism: FIFO in, fixed budget per tick, both peers running the
     * same code in the same order. The queue holds Ent references and the
     * roster order of the enqueueing loops is itself deterministic, so the two
     * machines pop the identical unit on the identical tick.
     */
    private static final int PATH_BUDGET = 8;

    /**
     * v2.44 pathing fix: how many leading waypoints of a fresh path to skip.
     *
     * findPath returns the start cell as node 0 (Game.java, "walk the chain
     * backwards"), so skipping exactly one node is the standard "don't walk to
     * the cell you are already standing in" optimisation and nothing more.
     *
     * This used to be a bare `Math.min(3, ...)`, which skipped THREE nodes --
     * 24 world px, since a minitile is 8 px. Two consequences, both visible in
     * play:
     *   - For any path of 4 nodes or fewer (any order 32 px away or closer) the
     *     clamp collapsed to N-1, i.e. the entire path was discarded and the
     *     unit walked straight at the goal. Since path following is a plain
     *     straight-line interpolation that never consults passMini, a short
     *     move next to a cliff, water or a building walked THROUGH it.
     *   - For longer paths the first 24 px of the detour A* had just computed
     *     were thrown away, so a unit whose obstacle was immediately beside it
     *     set off in the wrong direction and jammed against the wall.
     * Nothing in the codebase depended on the start being pre-skipped, and the
     * constant had no name or comment, so this was never a deliberate
     * lookahead -- it was a magic number that broke short-range pathing.
     */
    private static final int PATH_START_SKIP = 1;

    /** Units with a path request waiting, oldest first. Slots are appended
     *  once per unit and skipped if the unit cancelled or was served first. */
    private final List<Ent> pathQueue = new ArrayList<>();
    private int pathQueueHead;

    public int statPathQueued;
    public int statPathDrains;

    /** v2.44: queued requests postponed because the tick's expansion budget ran
     *  out. Nonzero means long AI routes are being spread over several ticks
     *  (which is the intended behaviour), not that they were refused. */
    public int statPathDeferred;

    /**
     * Ask for a path to be computed on a later tick, at the fixed budget.
     * Unlike setPath this does not touch the unit's current path: it keeps
     * walking what it has until the search runs, which is what keeps a crowd
     * from freezing mid-stride when the queue is deep.
     */
    public void queuePath(Ent e, float wx, float wy) {
        if (e == null) return;
        e.goalX = clamp(wx, 8, wPx - 8);
        e.goalY = clamp(wy, 8, hPx - 8);
        e.moving = true;
        if (e.pathGen != 0) return;      // already waiting: goal refreshed in place
        e.pathGen = ++pathGenSeq;
        pathQueue.add(e);
        statPathQueued++;
    }

    /** Drop every pending request. Used when the roster is replaced wholesale
     *  (mission start, save load), where the queued units no longer exist.
     *  v2.44: also clears each queued unit's pathGen. The two current callers
     *  wipe the roster right after, so this is belt-and-braces -- but a stale
     *  pathGen with an empty queue is a unit whose `moving` can never be
     *  cleared, which is a hang, not a slowdown. */
    private void clearPathQueue() {
        for (int i = pathQueueHead; i < pathQueue.size(); i++) {
            Ent e = pathQueue.get(i);
            if (e != null) e.pathGen = 0;
        }
        pathQueue.clear();
        pathQueueHead = 0;
    }

    /** Drop a unit's pending request. The queue slot goes stale and is skipped. */
    public void cancelQueuedPath(Ent e) {
        if (e != null) e.pathGen = 0;
    }

    private int pathGenSeq;

    /**
     * Run at most `PATH_BUDGET` queued searches. Called once per tick from a
     * fixed point in update(), so the work is spread identically on both peers.
     *
     * v2.44: the searches go through findPathBudgeted, so a tick also has a
     * ceiling on total expanded cells (PATH_TICK_EXPANSIONS). A request that
     * runs out of budget is left AT THE HEAD of the queue with its pathGen
     * intact rather than being handed an empty path -- otherwise a long
     * cross-map AI order would be silently reported as "no route" and the unit
     * would stand still, which is exactly the bug this release fixes. The
     * deferral is deterministic (same queue order, same budget on both peers),
     * so lockstep is unaffected.
     */
    private void drainPathQueue() {
        statPathDrains++;
        if (pathQueueHead >= pathQueue.size()) {
            if (!pathQueue.isEmpty()) pathQueue.clear();
            pathQueueHead = 0;
            return;
        }
        int served = 0;
        while (pathQueueHead < pathQueue.size() && served < PATH_BUDGET) {
            Ent e = pathQueue.get(pathQueueHead);
            if (e == null || e.pathGen == 0) {
                pathQueueHead++;                         // cancelled or served
                continue;
            }
            // A unit that died while queued: nothing to path. Skipping it does
            // not consume budget, so the tick still serves up to PATH_BUDGET
            // live units -- `alive()` is deterministic, so both peers agree.
            if (!e.alive()) {
                e.pathGen = 0;
                pathQueueHead++;
                continue;
            }
            int[] p = findPathBudgeted((int) (e.x / 8), (int) (e.y / 8),
                    (int) (e.goalX / 8), (int) (e.goalY / 8));
            if (p == null && lastPathBudgetHit) {
                statPathDeferred++;
                break;                                   // retry next tick
            }
            e.pathGen = 0;
            pathQueueHead++;
            e.path = p != null ? p : Ent.EMPTY_PATH;
            if (p != null) {
                e.pathIndex = Math.min(PATH_START_SKIP, (p.length >> 1) - 1);
            }
            // Same tail as setPath. Re-asserted here because the unit may have
            // finished its old path (which clears `moving`) while this request
            // was still waiting -- without this it would receive the path and
            // then stand there until something else set `moving` again.
            e.moving = true;
            served++;
        }
        // Keep the backing array from growing without bound over a long match.
        if (pathQueueHead > 256 && pathQueueHead * 2 > pathQueue.size()) {
            pathQueue.subList(0, pathQueueHead).clear();
            pathQueueHead = 0;
        }
    }

    public boolean hasFreeGeyserNear(float x, float y) {
        for (Mineral m : minerals) {
            if (m.variant < 3 || m.refinery != null) continue;
            float dx = m.x - x, dy = m.y - y;
            if (dx * dx + dy * dy < 80 * 80) return true;
        }
        return false;
    }

    public boolean canPlace(String key, float x, float y) {
        Type t = TYPES.get(key);
        int tx0 = (int) (x / 32) - t.tiles / 2;
        int ty0 = (int) (y / 32) - t.tiles / 2;
        for (int by = ty0; by < ty0 + t.tiles; by++)
            for (int bx = tx0; bx < tx0 + t.tiles; bx++)
                for (int my = 0; my < 4; my++)
                    for (int mx = 0; mx < 4; mx++)
                        if (!passMini(bx * 4 + mx, by * 4 + my)) return false;
        // keep clear of other buildings
        for (Ent e : ents) {
            if (!e.alive() || !e.isBuilding()) continue;
            if (Math.abs(e.x - x) < (e.type.tiles + t.tiles) * 16
                    && Math.abs(e.y - y) < (e.type.tiles + t.tiles) * 16)
                return false;
        }
        // keep clear of ground units
        for (Ent e : ents) {
            if (!e.alive() || e.isBuilding() || e.type.flying) continue;
            if (Math.abs(e.x - x) < t.tiles * 16 + 6
                    && Math.abs(e.y - y) < t.tiles * 16 + 6)
                return false;
        }
        // minerals (a refinery is allowed on its geyser)
        for (Mineral m : minerals) {
            if (isGasBuilding(key) && m.variant >= 3) continue;
            if (Math.abs(m.x - x) < t.tiles * 16 + 26
                    && Math.abs(m.y - y) < t.tiles * 16 + 26)
                return false;
        }
        return true;
    }

    /**
     * Why a building cannot be placed here, or null if it can. The view calls
     * this before posting tryBuild so the player gets a reason, not just a beep.
     */
    public String buildError(String key, float x, float y) {
        Type t = TYPES.get(key);
        if (t == null) return null;
        if (mineralsPlayer < t.cost) return "晶体矿不足";
        if (gasPlayer < t.gasCost) return "瓦斯不足";
        if (isGasBuilding(key) && !hasFreeGeyserNear(x, y))
            return nameOf(key) + "必须建在气矿上";
        if (!canPlace(key, x, y)) return "无法在此建造";
        return null;
    }

    /**
     * Why a training order cannot be queued, or null if it can.
     */
    public String trainError(String key) {
        Type t = TYPES.get(key);
        if (t == null) return null;
        // v2.7 9.1: Type.requires existed since v2 but was never checked, so
        // "firebat needs a barracks" was documentation, not a rule. Enforcing
        // it is what makes the new academy gate real.
        if (t.requires != null && !t.requires.isEmpty() && !hasBuilding(0, t.requires))
            return "需要" + nameOf(t.requires);
        // v2.25: the add-on gate, checked AFTER the building requirement so the
        // more fundamental reason is the one reported -- a battlecruiser with
        // neither a science facility nor a physics lab should say "需要科学设施",
        // not "需要物理实验室". Only the rows the original closes this way carry
        // addonNeeded (the dropship and valkyrie behind a control tower, the
        // battlecruiser behind a physics lab). The check looks for the add-on
        // itself, wherever it stands -- an add-on is useless without its parent
        // anyway, so requiring them to be adjacent would only add a way for a
        // legal base to be refused.
        if (t.addonNeeded != null && !t.addonNeeded.isEmpty()
                && !hasBuilding(0, t.addonNeeded))
            return "需要" + nameOf(t.addonNeeded);
        if (mineralsPlayer < t.cost) return "晶体矿不足";
        if (gasPlayer < t.gasCost) return "瓦斯不足";
        if (t.supply > 0 && supplyUsed + t.supply > supplyCap) return "人口已达上限";
        return null;
    }

    /** Does `team` own a completed building of this key? */
    public boolean hasBuilding(int team, String key) {
        for (Ent e : ents)
            if (e.alive() && e.team == team && !e.constructing
                    && e.type.key.equals(key)) return true;
        return false;
    }

    /** The first completed building of this key owned by `team`, or null. */
    public Ent firstBuilding(int team, String key) {
        for (Ent e : ents)
            if (e.alive() && e.team == team && !e.constructing
                    && e.type.key.equals(key)) return e;
        return null;
    }

    /** Display name of a type key, falling back to the key itself. */
    public static String nameOf(String key) {
        Type t = TYPES.get(key);
        return t == null ? key : t.name;
    }

    /** Cancel the queue entry at `index` and refund its cost. */
    public boolean cancelQueue(Ent building, int index) {
        if (building == null || index < 0 || index >= building.queue.size()) return false;
        Type t = TYPES.get(building.queue.get(index));
        building.queue.remove(index);
        if (index == 0) building.queueProgress = 0;
        mineralsPlayer += t.cost;
        gasPlayer += t.gasCost;
        return true;
    }

    public boolean tryBuild(Ent scv, String key, float x, float y) {
        Type t = TYPES.get(key);
        if (mineralsPlayer < t.cost || gasPlayer < t.gasCost) return false;
        Mineral geyser = null;
        if (isGasBuilding(key)) {
            // must sit on a free geyser
            float bd = 80 * 80;
            for (Mineral m : minerals) {
                if (m.variant < 3 || m.amount <= 0 || m.refinery != null) continue;
                float d = (m.x - x) * (m.x - x) + (m.y - y) * (m.y - y);
                if (d < bd) {
                    bd = d;
                    geyser = m;
                }
            }
            if (geyser == null) return false;
            x = geyser.x;
            y = geyser.y;
        }
        if (!canPlace(key, x, y)) return false;
        mineralsPlayer -= t.cost;
        gasPlayer -= t.gasCost;
        Ent b = spawn(key, 0, x, y, false);
        b.constructing = true;
        if (geyser != null) {
            geyser.refinery = b;
            b.geyser = geyser;
        }
        // v2.17: protoss and zerg structures self-build once placed. The probe/
        // drone is free the instant the structure is dropped (the structure
        // grows on its own in updateProduction); only terran keeps the SCV
        // tethered to the site.
        b.selfBuilding = !"terran".equals(race);
        if (b.selfBuilding) {
            scv.workerState = Ent.W_IDLE;
            scv.target = null;
        } else {
            setPath(scv, x, y);
            scv.workerState = Ent.W_IDLE;
            scv.target = b;
        }
        return true;
    }

    public boolean tryTrain(Ent building, String key) {
        Type t = TYPES.get(key);
        if (mineralsPlayer < t.cost || gasPlayer < t.gasCost) return false;
        if (supplyUsed + t.supply > supplyCap && t.supply > 0) return false;
        if (building.queue.size() >= 5) return false;
        mineralsPlayer -= t.cost;
        gasPlayer -= t.gasCost;
        building.queue.add(key);
        return true;
    }

    /**
     * Siege tank morph, and -- since v2.11 -- the lurker's burrow, which is the
     * same operation with a different name. The two share this method because
     * the mechanism is identical (swap to the paired type, stop, keep hp) and
     * the only difference is the art. Returns false when not applicable.
     */
    public boolean toggleSiege(Ent tank) {
        if (tank == null || !tank.alive() || tank.type.siegesTo == null
                || tank.moving || tank.constructing) return false;
        String fromKey = tank.type.key;
        Type t = TYPES.get(tank.type.siegesTo);
        tank.type = t;
        // v2.43 P0-a: a morph swaps the type out from under the unit, and the
        // arbiter/detector counts are keyed off the type. None of the current
        // morph pairs touches those two flags, so this is belt-and-braces --
        // but a future pair that did would silently break the short-circuit,
        // and a stale-LOW count hides a real aura.
        invalidateAuraCounts();
        tank.hp = Math.min(tank.hp, t.hp);
        tank.moving = false;
        tank.path = Ent.EMPTY_PATH;
        cancelQueuedPath(tank);   // v2.43 P0-c: a morph cancels the pending move
        tank.dir = dirOf(tank.facing);
        // v2.22 batch C: the lurker's burrow/unburrow has its own sound; the
        // tank's siege transform keeps its in-place clang (no event).
        if (fromKey.equals("lurker") || fromKey.equals("lurker_bur"))
            events.add(new Object[]{"burrow"});
        return true;
    }

    /** True when the unit has a paired form (siege tank, lurker). */
    public static boolean canMorph(Ent e) {
        return e != null && e.alive() && e.type.siegesTo != null;
    }

    // ------------------------------------------- v2.22: energy pool + cloak
    /**
     * The energy pool (batch A) and the cloak layer (batch B) ship together
     * because cloak is an energy customer: the toggle costs 25 up front and
     * sips 1/s, which is what keeps a wraith from hiding over your base all
     * game. Prices are the original's; only the regen rate is a tuning knob.
     */
    public static final float ENERGY_MAX = 200f;
    public static final float ENERGY_SPAWN = 50f;
    public static final float ENERGY_REGEN = 0.8f;
    public static final float CLOAK_COST = 25f;
    public static final float CLOAK_DRAIN = 1f;
    /** Spell prices, the manual's numbers. Healing is free (medic rule). */
    public static final float COST_STORM = 75f;
    public static final float COST_EMP = 100f;
    public static final float COST_DSWARM = 100f;
    public static final float COST_ENSNARE = 75f;
    public static final float COST_DWEB = 100f;
    public static final float COST_IRRADIATE = 75f;
    public static final float COST_LOCKDOWN = 100f;
    public static final float COST_YAMATO = 150f;

    /**
     * Cloak field radius: the arbiter hides friends within 9 tiles of itself,
     * and a detector reveals cloaked units within the same 9-tile reach. One
     * radius for both keeps the mental model simple; the original's numbers
     * differ by a tile in places.
     */
    public static final float CLOAK_RADIUS = 288f;

    // ------------------------------ v2.23 batch A/B: cargo + bunker
    /**
     * Transport capacity in supply slots. 8 is the original figure the plan
     * pins, and it is measured in `type.supply` rather than unit count -- so a
     * shuttle holds 8 marines or 4 tanks, which is the rule the original uses
     * and the reason the field is not just "8 units".
     */
    public static final int CARGO_CAP = 8;
    /**
     * Bunker garrison slots, also in supply: four marines, or two firebats at
     * two slots each. The plan original figure ("4 infantry slots") is
     * exactly this reading, and the split falls out for free.
     */
    public static final int BUNKER_CAP = 4;

    /**
     * How far a transport can reach to pick up a unit when the player clicks
     * a load order, and how close a unit has to be for the automatic sweep to
     * board it. Generous, because the alternative is a player watching a
     * shuttle sit next to a marine and never load it.
     */
    public static final float LOAD_RANGE = 96f;

    // ------------------------------ v2.23 batch C: elevation
    /**
     * The original low-ground-to-high-ground hit chance: a ranged shot fired
     * from below at a target standing on a cliff lands about half the time
     * (the published figure is 53.125%; the plan pins it as a constant).
     * High ground shoots at full accuracy, and same-level shots are
     * unaffected, so this is the only number the rule needs.
     */
    public static final float HIGH_MISS_CHANCE = 0.53125f;
    /** Range below which a shot is melee and ignores elevation entirely. */
    public static final float MELEE_RANGE = 64f;

    /** Energy price of a spell action key, or -1 when it is not a spell. */
    public static float spellEnergyCost(String action) {
        switch (action) {
            case "storm": return COST_STORM;
            case "emp": return COST_EMP;
            case "dswarm": return COST_DSWARM;
            case "ensnare": return COST_ENSNARE;
            case "dweb": return COST_DWEB;
            case "irradiate": return COST_IRRADIATE;
            case "lockdown": return COST_LOCKDOWN;
            case "yamato": return COST_YAMATO;
            default: return -1f;
        }
    }

    /**
     * One gate for the command card's spell cells: is this action castable by
     * this caster right now? Wrong caster, cooldown and pool are all checked
     * here so the cell can gray itself for any of the three reasons. Returns
     * null when ready. (The castXxx error functions stay authoritative for the
     * actual cast -- this is the same ruleset restated for rendering.)
     */
    public String spellGate(Ent caster, String action) {
        if (caster == null || !caster.alive()) return "目标无效";
        float cost = spellEnergyCost(action);
        if (cost < 0) return "该单位无法施放";
        switch (action) {
            case "storm":
                if (!"templar".equals(caster.type.key)) return "该单位无法施放灵能风暴";
                if (caster.stormCd > 0) return "灵能风暴冷却中";
                break;
            case "emp":
                if (!"vessel".equals(caster.type.key)) return "该单位无法施放电磁脉冲";
                if (caster.empCd > 0) return "电磁脉冲冷却中";
                break;
            case "irradiate":
                if (!"vessel".equals(caster.type.key)) return "该单位无法施放辐射";
                if (caster.empCd > 0) return "辐射冷却中";
                break;
            case "dswarm":
                if (!"defiler".equals(caster.type.key)) return "该单位无法施放黑暗蜂群";
                if (caster.dswarmCd > 0) return "黑暗蜂群冷却中";
                break;
            case "ensnare":
                if (!"defiler".equals(caster.type.key)) return "该单位无法施放诱捕";
                if (caster.ensnareCd > 0) return "诱捕冷却中";
                break;
            case "dweb":
                if (!"corsair".equals(caster.type.key)) return "该单位无法施放干扰网";
                if (caster.dwebCd > 0) return "干扰网冷却中";
                break;
            case "yamato":
                if (!"battlecruiser".equals(caster.type.key)) return "该单位无法施放大和炮";
                if (caster.yamatoCd > 0) return "大和炮冷却中";
                break;
            case "lockdown":
                if (!"ghost".equals(caster.type.key)) return "该单位无法施放锁定";
                if (caster.lockdownCd > 0) return "锁定冷却中";
                break;
            default:
                return "该单位无法施放";
        }
        return energyGate(caster, cost);
    }

    /**
     * Net cloak state of a live unit: permanent types, the personal toggle,
     * the burrowed lurker, or standing inside a friendly arbiter's aura. The
     * arbiter never hides itself -- the original's rule, and it avoids the
     * circular "who cloaks the cloaker" question.
     */
    public boolean isCloakedNow(Ent e) {
        if (e == null || !e.alive()) return false;
        if (e.type.cloak == 1 || e.cloakOn || isBurrowed(e)) return true;
        // v2.43 P0-a: no live arbiter on e's team means the aura loop below
        // cannot possibly find one -- and that is every game until arbiters
        // exist, so this is the whole cost of the scan in practice.
        // v2.43 P0-b: when there IS one, walk the arbiters the count already
        // proved exist instead of the whole roster. Same roster order, same
        // gates, same first match -- just a shorter list to walk.
        ensureAuraCounts();
        int team = e.team == 1 ? 1 : 0;
        statAuraQueries++;
        if (arbCount[team] == 0) return false;
        statAuraScans++;
        for (int i = 0, n = arbListN; i < n; i++) {
            Ent a = arbList[i];
            if (a == e || a.team != e.team || !a.alive() || a.constructing) continue;
            if (dist(e, a) <= CLOAK_RADIUS) return true;
        }
        return false;
    }

    /** Can `byTeam`'s detectors see the point (x, y)? */
    public boolean detectorNear(float x, float y, int byTeam) {
        // v2.43 P0-a: same short-circuit as isCloakedNow -- with no detector
        // built anywhere on that side, the roster walk cannot return true.
        // v2.43 P0-b: and when there is one, walk only the detectors.
        ensureAuraCounts();
        int team = byTeam == 1 ? 1 : 0;
        statAuraQueries++;
        if (detCount[team] == 0) return false;
        statAuraScans++;
        for (int i = 0, n = detListN; i < n; i++) {
            Ent d = detList[i];
            if (d.team != byTeam || !d.alive() || d.constructing) continue;
            float dx = d.x - x, dy = d.y - y;
            if (dx * dx + dy * dy <= CLOAK_RADIUS * CLOAK_RADIUS) return true;
        }
        return false;
    }

    /**
     * Per-tick cloak settlement. Runs right after updateFog so targeting,
     * drawing and tapping all read `cloakActive`/`spotted` flags from this
     * tick instead of rescanning the roster per candidate -- the naive form
     * was O(units x units x arbiters) in the acquire path.
     */
    private void updateCloak() {
        for (Ent e : ents) {
            if (!e.alive()) continue;
            e.cloakActive = isCloakedNow(e);
            // v2.25: a scanner sweep reveals cloaked units inside its square
            // even with no detector present -- the comsat's reason to exist
            // against a dark templar rush.
            e.spotted = e.cloakActive && (detectorNear(e.x, e.y, 1 - e.team)
                    || scanReveals(e.x, e.y, 1 - e.team));
        }
    }

    /** The view's enemy-visibility hook: a cloaked enemy shows only when spotted. */
    public boolean enemyRevealed(Ent e) {
        return !e.cloakActive || e.spotted;
    }

    public String cloakError(Ent e) {
        if (e == null || !e.alive() || e.isBuilding()) return "目标无效";
        if (e.type.cloak != 2) return "该单位无法隐形";
        if (e.cloakOn) return null;          // dropping the cloak is free
        if (e.energy < CLOAK_COST) return "能量不足";
        return null;
    }

    /** Personal cloak toggle (ghost, wraith). Returns false with cloakError(). */
    public boolean toggleCloak(Ent e) {
        if (cloakError(e) != null) return false;
        e.cloakOn = !e.cloakOn;
        if (e.cloakOn) e.energy -= CLOAK_COST;
        return true;
    }

    /** Shared spell gate: the pool must exist and hold the price. */
    private String energyGate(Ent e, float cost) {
        if (e.maxEnergy <= 0) return "该单位没有能量";
        if (e.energy < cost) return "能量不足";
        return null;
    }

    // ------------------------------------------------------------------- tick
    public void update(float dt) {
        runPendingOrders();
        if (replayMode) injectReplay();   // v2.19 batch 5: playback injection
        // v2.30: a lockstep peer only advances once every player has reported
        // for this turn. A slow peer therefore freezes this one instead of
        // letting it run ahead -- that freeze is the entire point, because a
        // machine that runs ahead is a machine that has already diverged.
        if (lockstep != null) {
            if (!lockstep.ready()) {
                // v2.34: remember that this turn has been waiting, so a peer
                // that never comes back can be declared gone instead of both
                // machines sitting on the same turn forever. A frame that does
                // release resets the count (see Lockstep.release).
                lockstep.noteStall();
                return;
            }
            for (Lockstep.Cmd c : lockstep.release()) applyCommand(c.cmd);
        }
        resolveShots();
        if (!status.isEmpty()) return;
        tick++;
        time += dt;
        // v2.44: refill the pathfinding expansion budget for this tick. It is
        // refilled here, before any search can run, so every peer starts each
        // tick with the same allowance and the deferral decisions match.
        pathBudgetLeft = PATH_TICK_EXPANSIONS;
        // v2.43 P0-b: one O(N) rebuild per tick, here, so every query in the
        // body below reads a grid built from a single consistent roster
        // snapshot. Anything that spawns later in the tick invalidates it (see
        // invalidateAuraCounts), and the next query rebuilds lazily -- so a
        // wave tick pays two rebuilds instead of one, which is still O(N) and
        // not the O(N^2) it replaced.
        rebuildSpatial();
        aiUpdate(dt);
        updateFog();
        // v2.43 P0-a: rebuild the arbiter/detector counts once per tick, right
        // before the only consumer (updateCloak). One O(N) pass here replaces
        // the two N x N scans updateCloak used to run on every map.
        rebuildAuraCounts();
        // v2.22 batch B: settle the cloak layer once per tick. Every consumer
        // (targeting, drawing, tapping) reads the flags this sets.
        updateCloak();
        updateEconomy(dt);
        updateProduction(dt);
        // v2.25: add-ons, the scanner sweep and the nuclear countdown.
        updateAddons();
        updateScans(dt);
        updateNukes(dt);
        // v2.26: carrier hangars, reaver scarab racks, and the spawn
        // assignment for anything that needs one.
        updateHangars(dt);
        updateAmmo(dt);

        // v2.43 P0-c: spend this tick's pathfinding budget. Placed here, after
        // aiUpdate (whose wave hands one destination to the whole attacking
        // army) and after updateEconomy, so those requests are served starting
        // the same tick -- and before the unit loop, so anything updateUnit
        // queues waits for the next tick. Both peers run this at the same point
        // in the same order, which is all the determinism the queue needs.
        drainPathQueue();

        // v2.43 P0-a: an indexed loop, not a for-each, because updateUnit()
        // phase-staggers its idle target acquisition off curRosterIdx. The
        // index is the unit's position in the roster, which both peers agree
        // on, so the phase assignment is identical on both machines.
        for (int ei = 0, en = ents.size(); ei < en; ei++) {
            Ent e = ents.get(ei);
            curRosterIdx = ei;
            if (!e.alive()) continue;
            // v2.23: a unit riding in a transport is off the field entirely --
            // it does not move, shoot, light fog or regen energy, and the only
            // thing that can happen to it is the carrier dying. A garrisoned
            // unit is the exception: it still shoots (updateGarrisonFire), so
            // it keeps its cooldown clock and skips the rest.
            if (e.cargoOf != null) continue;
            e.cd -= dt;
            if (e.garrisoned) continue;
            if (e.stimTime > 0) e.stimTime = Math.max(0, e.stimTime - dt);
            if (e.stormCd > 0) e.stormCd = Math.max(0, e.stormCd - dt);
            if (e.dswarmCd > 0) e.dswarmCd = Math.max(0, e.dswarmCd - dt);
            if (e.ensnareCd > 0) e.ensnareCd = Math.max(0, e.ensnareCd - dt);
            // v2.14 batch 1.5: the four new spell timers.
            if (e.empCd > 0) e.empCd = Math.max(0, e.empCd - dt);
            if (e.yamatoCd > 0) e.yamatoCd = Math.max(0, e.yamatoCd - dt);
            if (e.lockdownCd > 0) e.lockdownCd = Math.max(0, e.lockdownCd - dt);
            if (e.dwebCd > 0) e.dwebCd = Math.max(0, e.dwebCd - dt);
            if (e.dwebTime > 0) e.dwebTime = Math.max(0, e.dwebTime - dt);
            e.flashTime = Math.max(0, e.flashTime - dt);
            // v2.22 batch A: the energy pool refills -- but an active personal
            // cloak SUSPENDS regen and drains instead. Letting both run on the
            // same tick made the net drain 0.2/s and a wraith could hide for
            // the whole match; the drain replacing the regen keeps the pool
            // meaningful. Out of energy, the unit decloaks (the original's
            // rule -- it does not starve).
            if (e.maxEnergy > 0) {
                if (e.cloakOn) {
                    e.energy -= CLOAK_DRAIN * dt;
                    if (e.energy <= 0) {
                        e.energy = 0;
                        e.cloakOn = false;
                    }
                } else {
                    e.energy = Math.min(e.maxEnergy, e.energy + ENERGY_REGEN * dt);
                }
            }
            if (e.constructing) continue;

            // v2.10 shield regen. The delay is what makes a shield different
            // from extra hp: it only comes back if the unit breaks contact.
            if (e.type.shield > 0) {
                if (e.shieldDelay > 0) {
                    e.shieldDelay = Math.max(0, e.shieldDelay - dt);
                } else if (e.shield < e.type.shield) {
                    e.shieldCarry += SHIELD_REGEN * dt;
                    int whole = (int) e.shieldCarry;
                    if (whole > 0) {
                        e.shieldCarry -= whole;
                        e.shield = Math.min(e.type.shield, e.shield + whole);
                    }
                }
            }

            if (e.isBuilding()) {
                updateBuilding(e, dt);
            } else {
                updateUnit(e, dt);
            }
        }

        // v2.23 batch A/B: the transport pickup sweep and the bunker firing
        // pass. Both live outside the main loop because a garrisoned unit is
        // skipped by it (see above) and a loading unit has to be caught the
        // moment its carrier walks into range.
        for (Ent e : ents) {
            if (!e.alive()) continue;
            if (e.type.cargoCap > 0) updateLoading(e);
            if (e.type.bunkerCap > 0) updateGarrisonFire(e);
        }

        // shots / effects lifetimes
        if (alertCd > 0) alertCd -= dt;
        updateStorms(dt);
        // v2.14 batch 1.5: Irradiate's damage-over-time rides the same clock
        // shape as a storm, but on the victim rather than on a field, so it
        // follows the unit around and cannot be walked out of.
        updateIrradiate(dt);
        // v2.11: the defiler's two fields age exactly like a storm does.
        for (int i = dswarms.size() - 1; i >= 0; i--) {
            Dswarm d = dswarms.get(i);
            d.t += dt;
            if (d.done()) dswarms.remove(i);
        }
        for (int i = ensnares.size() - 1; i >= 0; i--) {
            Ensnare s = ensnares.get(i);
            s.t += dt;
            if (s.done()) ensnares.remove(i);
        }
        // v2.14 batch 1.5: the disruption web ages like the other two fields.
        for (int i = dwebs.size() - 1; i >= 0; i--) {
            Dweb w = dwebs.get(i);
            w.t += dt;
            if (w.done()) dwebs.remove(i);
        }
        for (int i = shots.size() - 1; i >= 0; i--) {
            Shot s = shots.get(i);
            s.t += dt;
            if (s.missile) {
                s.smokeTimer -= dt;
                if (s.smokeTimer <= 0) {
                    s.smokeTimer = 0.05f;
                    playAnim("smoke", s.x, s.y, animFrames("smoke"), s.team, 14f, 0.4f);
                }
            }
            if (s.t >= s.dur) shots.remove(i);
        }
        for (int i = effects.size() - 1; i >= 0; i--) {
            float[] fx = effects.get(i);
            fx[2] -= dt;
            if (fx[2] <= 0) effects.remove(i);
        }
        for (int i = anims.size() - 1; i >= 0; i--) {
            Anim a = anims.get(i);
            a.t += dt;
            if (a.done()) anims.remove(i);
        }
        for (int i = markers.size() - 1; i >= 0; i--) {
            Marker m = markers.get(i);
            m.t += dt;
            if (m.t >= m.dur) markers.remove(i);
        }
        for (int i = corpses.size() - 1; i >= 0; i--) {
            Corpse c = corpses.get(i);
            c.t += dt;
            if (c.t >= c.dur()) corpses.remove(i);
        }

        // remove dead
        for (int i = ents.size() - 1; i >= 0; i--) {
            Ent e = ents.get(i);
            if (!e.alive()) {
                // v2.23: a transport or bunker goes down with everyone aboard.
                // The occupants are killed here rather than left orphaned, so
                // the scoreboard and the supply tally both stay honest; the
                // loop below then removes them on the same pass.
                if (!e.cargo.isEmpty()) {
                    for (Ent c : e.cargo) {
                        c.cargoOf = null;
                        c.garrisoned = false;
                        c.bunker = null;
                        c.hp = 0;
                        if (c.team == 0) losses++; else kills++;
                    }
                    e.cargo.clear();
                }
                if (e.isBuilding()) {
                    occupyFootprint(e, false);
                    if (e.geyser != null && e.geyser.refinery == e)
                        e.geyser.refinery = null;
                }
                spawnDeathFx(e);
                events.add(new Object[]{"dead", e.type.tiles, e.type.key});
                if (e.team == 0) losses++;
                else kills++;
                ents.remove(i);
                invalidateAuraCounts();      // v2.43 P0-a: a dead arbiter/detector is gone
            }
        }

        // v2.7 batch 8: a mission owns the result when one is loaded
        if (mission != null && mission.active()) {
            mission.update(this, dt);
            if (mission.finished) {
                status = mission.victory ? "win" : "lose";
            }
            return;
        }

        // win / lose
        boolean playerBuilding = false, enemyBuilding = false, playerAny = false;
        for (Ent e : ents) {
            if (e.team == 0) playerAny = true;
            if (e.isBuilding() && e.team == 0 && !e.constructing) playerBuilding = true;
            if (e.isBuilding() && e.team == 1) enemyBuilding = true;
        }
        if (!enemyBuilding) status = "win";
        else if (!playerAny) status = "lose";
    }

    private void updateFog() {
        // decay visible to explored
        for (int i = 0; i < fog.length; i++)
            if (fog[i] == 2) fog[i] = 1;
        for (Ent e : ents) {
            if (e.team != 0 || !e.alive()) continue;
            if (offField(e)) continue;    // v2.23: cargo lights no fog
            int rad = e.isBuilding() ? 9 : 7;
            revealAround(e.x, e.y, rad);
        }
    }

    private void updateEconomy(float dt) {
        supplyUsed = 0;
        supplyCap = 0;
        for (Ent e : ents) {
            if (!e.alive() || e.constructing) continue;
            // v2.23: a loaded or garrisoned unit still costs its supply, which
            // is the original rule -- the slot is occupied for as long as the
            // unit exists, wherever it is sitting. This loop is therefore left
            // deliberately unaware of cargo, and the field interactions that
            // need to skip off-field units do so themselves.
            if (e.team == 0) {
                supplyUsed += e.type.supply;
                // v2.8: supply comes from the race's own buildings; an
                // overlord is a unit but carries supply like a depot.
                // v2.27: scaled by the current cap tier, so a depot keeps
                // paying for itself as the cap grows.
                supplyCap += supplyProvided(e.type.key, capTier());
            }
        }
        // v2.27: the ceiling is the CURRENT tier, not the global maximum. The
        // research buys the right to build past the old cap; it does not hand
        // the player 100 supply the moment it is researched.
        supplyCap = Math.min(supplyCap, SUPPLY_TIERS[capTier < 0 ? 0
                : (capTier >= SUPPLY_TIERS.length ? SUPPLY_TIERS.length - 1 : capTier)]);

        // player AI: auto-harvest idle workers
        for (Ent e : ents) {
            if (!e.alive() || e.team != 0 || e.constructing) continue;
            if (!isWorker(e)) continue;
            if (e.workerState == Ent.W_IDLE && !e.moving && e.target == null) {
                // v2.44 gas fix: a finished refinery staffs itself first -- up
                // to GAS_WORKERS workers on its geyser, exactly like the
                // original pulling workers onto a completed gas building. The
                // v2.44 mining-side fix (haulingGas derived from the patch)
                // made geyser loads deliverable, but nothing ever SENT a
                // worker to a geyser: nearestMineral skips variant>=3, so
                // auto-harvest kept every worker on crystals and gasPlayer
                // never moved. Both gates below require a COMPLETED building:
                // a geyser under a still-raising refinery is not minable yet.
                Mineral gas = gasNeedingStaff();
                Mineral m = gas != null ? gas : nearestMineral(e);
                if (m != null) {
                    e.mineTarget = m;
                    e.workerState = Ent.W_TO_MINE;
                    // v2.43 P0-c: simulation-side request, so it goes through
                    // the budget queue (see queuePath). A freshly built worker
                    // standing next to a patch still starts on the next tick.
                    queuePath(e, m.x, m.y);
                }
            }
        }
    }

    /** Workers one finished gas building keeps on its geyser (the original's
     * soft cap; every further idle worker goes to crystals). */
    private static final int GAS_WORKERS = 3;

    /**
     * v2.44 gas fix: the first geyser (roster order, deterministic) whose
     * refinery is finished and carries fewer than GAS_WORKERS assigned
     * workers, or null. Assignment is counted from live worker state, so a
     * worker that loses its target (refinery destroyed, patch depleted)
     * frees its slot automatically.
     */
    private Mineral gasNeedingStaff() {
        for (int ei = 0, en = ents.size(); ei < en; ei++) {
            Ent b = ents.get(ei);
            if (!b.alive() || b.team != 0 || b.constructing) continue;
            if (!isGasBuilding(b.type.key) || b.geyser == null) continue;
            if (b.geyser.amount <= 0) continue;
            int staff = 0;
            for (int oi = 0; oi < en; oi++) {
                Ent o = ents.get(oi);
                if (o == b || !o.alive() || o.team != 0 || !isWorker(o)) continue;
                if (o.mineTarget == b.geyser
                        && (o.workerState == Ent.W_TO_MINE
                            || o.workerState == Ent.W_MINING
                            || o.workerState == Ent.W_TO_RETURN)) {
                    staff++;
                }
            }
            if (staff < GAS_WORKERS) return b.geyser;
        }
        return null;
    }

    private Mineral mineralOfRefinery(Ent ref) {
        if (ref.geyser != null) return ref.geyser;
        for (Mineral m : minerals)
            if (m.refinery == ref) return m;
        return null;
    }

    private Mineral nearestMineral(Ent e) {
        Mineral best = null;
        float bd = 1e9f;
        for (Mineral m : minerals) {
            if (m.amount <= 0) continue;
            // v2.44 gas fix: a geyser (variant 3) is not directly minable. The
            // auto-harvest pass below used to hand idle workers the nearest
            // "mineral", which could be a geyser, and the worker would then mine
            // it and deliver the load as MINERALS (see the haulingGas fix in
            // updateUnit). Skipping geysers here restores the original's rule:
            // gas needs a refinery, and the only way to staff one is to tap it.
            if (m.variant >= 3) continue;
            float d = (m.x - e.x) * (m.x - e.x) + (m.y - e.y) * (m.y - e.y);
            if (d < bd) {
                bd = d;
                best = m;
            }
        }
        return best;
    }

    private void updateProduction(float dt) {
        // v2.43 P1: an indexed loop, not a for-each, because a completed queue
        // item spawns a unit and spawn() appends to ents. The old
        // CopyOnWriteArrayList hid this -- its iterator walked a stale snapshot,
        // so a unit trained this tick was silently skipped until the next one --
        // and on an ArrayList the same append throws
        // ConcurrentModificationException. Snapshotting the bound restores the
        // old snapshot semantics exactly: the roster prefix that existed at the
        // top of the tick is the roster this tick processes.
        for (int ei = 0, en = ents.size(); ei < en; ei++) {
            Ent e = ents.get(ei);
            if (!e.alive() || !e.isBuilding()) continue;
            // v2.17: protoss and zerg structures grow on their own after
            // placement (see Ent.selfBuilding); terran sites stay on the
            // worker tether handled in updateUnit.
            if (e.constructing) {
                if (e.selfBuilding && e.buildProgress < 1f) {
                    e.buildProgress = Math.min(1f, e.buildProgress + dt / e.type.buildTime);
                    if (e.buildProgress >= 1f) {
                        e.constructing = false;
                        e.hp = e.type.hp;
                        e.shield = e.type.shield;
                        if (e.team == 0) {
                            revealAround(e.x, e.y, 10);
                            events.add(new Object[]{"built", e.x, e.y});
                        }
                    }
                }
                continue;
            }
            // construction progress
            if (e.buildProgress < 1f) {
                e.buildProgress = Math.min(1f, e.buildProgress + dt / e.type.buildTime);
                continue;
            }
            if (e.team == 1) continue;    // enemy trains via AI spawner
            if (!e.queue.isEmpty()) {
                e.queueProgress += dt;
                String key = e.queue.get(0);
                Type t = TYPES.get(key);
                if (e.queueProgress >= t.buildTime) {
                    e.queueProgress = 0;
                    e.queue.remove(0);
                    float rx = e.rallyX >= 0 ? e.rallyX : e.x;
                    float ry = e.rallyY >= 0 ? e.rallyY : e.y + e.type.tiles * 16 + 20;
                    Ent u = spawn(key, e.team, rx, ry, true);
                    if (isWorkerType(key)) {
                        u.workerState = Ent.W_IDLE;
                    }
                    if (e.team == 0) events.add(new Object[]{"trained", key});
                }
            }
        }
    }

    private void updateBuilding(Ent e, float dt) {
        // turret defense
        if (e.type.dmg > 0) {
            Ent tgt = e.target;
            if (tgt == null || !tgt.alive() || dist(e, tgt) > e.type.range + 12) {
                tgt = findEnemyInRange(e, e.type.range);
                e.target = tgt;
            }
            if (tgt != null && e.cd <= 0) {
                e.cd = effectiveCooldown(e);
                e.facing = (float) Math.atan2(tgt.y - e.y, tgt.x - e.x);
                fire(e, tgt);
            }
        }
    }

    private void updateUnit(Ent e, float dt) {
        // worker: mining blocks; the trips themselves use the shared movement below
        if (isWorker(e) && e.workerState == Ent.W_MINING) {
            e.animTime -= dt;
            e.moving = false;
            // v2.43 P0-c: mining is a settled state -- drop anything the budget
            // queue is still holding for this worker, or the request would fire
            // a tick later and walk it off the patch it just reached.
            cancelQueuedPath(e);
            Mineral m = e.mineTarget;
            if (m == null || m.amount <= 0) {
                e.mineTarget = null;
                e.workerState = Ent.W_IDLE;
                return;
            }
            if (e.animTime <= 0) {
                int take = Math.min(8, m.amount);
                m.amount -= take;
                e.carrying = take;
                // v2.44 gas fix: derive the load's kind from the patch actually
                // mined, every trip. `haulingGas` used to be assigned false in
                // exactly one place (the "no depot" branch below) and never set
                // true anywhere, so every load -- including one taken off a
                // geyser -- was delivered as minerals and gasPlayer never moved.
                // Deriving it here rather than at order time means a worker that
                // is re-tasked mid-trip still delivers the right resource, and a
                // destroyed refinery cannot leave a stale true behind.
                e.haulingGas = m.variant >= 3;
                e.workerState = Ent.W_TO_RETURN;
                Ent depot = nearestDropOff(e, e.haulingGas);
                // v2.43 P0-c: simulation-side, so budgeted.
                if (depot != null) queuePath(e, depot.x, depot.y + depot.type.tiles * 14 + 4);
                else e.workerState = Ent.W_IDLE;
            }
            return;
        }
        if (isWorker(e) && e.workerState == Ent.W_TO_RETURN) {
            Ent depot = nearestDropOff(e, e.haulingGas);
            if (depot == null) {
                e.workerState = Ent.W_IDLE;
                e.mineTarget = null;
                e.haulingGas = false;
            } else if (dist(e, depot) < depot.type.tiles * 16 + 16) {
                effects.add(new float[]{e.x, e.y, 0.3f, e.haulingGas ? 2 : 0});
                if (e.haulingGas) gasPlayer += e.carrying;
                else mineralsPlayer += e.carrying;
                if (e.haulingGas) gasMined += e.carrying;
                else mineralsMined += e.carrying;
                e.carrying = 0;
                e.workerState = Ent.W_TO_MINE;
                Mineral m = e.mineTarget;
                if (m != null && m.amount > 0) {
                    // v2.43 P0-c: simulation-side, so budgeted.
                    queuePath(e, m.x, m.y);
                } else {
                    e.mineTarget = null;
                    e.workerState = Ent.W_IDLE;
                }
                return;
            }
        }
        // repair work (v2.5 batch-6): an SCV standing next to a damaged friendly
        // unit/building mends it, paying minerals per hit point. Cancels itself
        // when the target is whole, dies, or the player runs dry.
        if (e.repairTarget != null) {
            Ent rt = e.repairTarget;
            boolean ok = rt.alive() && rt.team == e.team
                    && rt.hp < rt.type.hp && mineralsPlayer > 0
                    && isWorker(e);
            if (!ok) {
                e.repairTarget = null;
            } else {
                float d = dist(e, rt);
                if (d < rt.type.tiles * 16 + 28 + rt.type.radius) {
                    e.moving = false;
                    e.path = Ent.EMPTY_PATH;
                    cancelQueuedPath(e);   // v2.43 P0-c: arrived; drop any pending request
                    float mend = Math.min(REPAIR_HP_PER_SEC * dt,
                            rt.type.hp - rt.hp);
                    int cost = (int) Math.ceil(mend * REPAIR_COST_PER_HP);
                    if (cost > mineralsPlayer) {
                        // spend what is left, mend proportionally
                        mend = mineralsPlayer / (float) REPAIR_COST_PER_HP;
                        cost = mineralsPlayer;
                    }
                    if (mend > 0f && cost > 0) {
                        mineralsPlayer -= cost;
                        rt.hp = Math.min(rt.type.hp, rt.hp + (int) Math.max(1f, mend));
                    }
                    if (rt.hp >= rt.type.hp) e.repairTarget = null;
                    return;
                }
                // v2.43 P0-c: simulation-side, so budgeted.
                queuePath(e, rt.x, rt.y);
            }
        }

        // heal work (v2.11 batch C): a medic standing next to a damaged organic
        // friendly mends it for free. Same shape as the repair block above --
        // walk into range, then mend -- but the two conditions that make a
        // medic a medic rather than a cheap SCV are the target filter (living
        // tissue only) and the absence of a mineral price.
        if (e.healTarget != null) {
            Ent ht = e.healTarget;
            boolean ok = ht.alive() && ht.team == e.team && ht.hp < ht.type.hp
                    && isBiological(ht) && "medic".equals(e.type.key);
            if (!ok) {
                e.healTarget = null;
            } else {
                float d = dist(e, ht);
                if (d < ht.type.radius + 40) {
                    e.moving = false;
                    e.path = Ent.EMPTY_PATH;
                    cancelQueuedPath(e);   // v2.43 P0-c: arrived; drop any pending request
                    float mend = Math.min(HEAL_HP_PER_SEC * dt, ht.type.hp - ht.hp);
                    if (mend > 0f) {
                        ht.hp = Math.min(ht.type.hp, ht.hp + (int) Math.max(1f, mend));
                        // The heal beam is a repeating effect, not a one-shot:
                        // BroodUnits.doc describes a channel, so it re-fires
                        // while the medic is working.
                        if (e.flashTime <= 0) {
                            playAnim("heal", ht.x, ht.y, animFrames("heal"),
                                    e.team, 14f, 0.8f);
                            e.flashTime = 0.55f;
                            // v2.22 batch C: the beam gets the medic's voice
                            // line; the view throttles overlapping medics.
                            events.add(new Object[]{"heal"});
                        }
                    }
                    if (ht.hp >= ht.type.hp) e.healTarget = null;
                    return;
                }
                // v2.43 P0-c: simulation-side, so budgeted.
                queuePath(e, ht.x, ht.y);
            }
        }

        // spider mine (v2.11 batch C): a mine is an ordinary entity with zero
        // speed, so this is where it lives. It arms for a moment (so it cannot
        // detonate on the vulture that just dropped it) and then blows up on
        // the first enemy that walks into range. It is consumed on firing --
        // the original's mines are one-shot.
        if ("spider".equals(e.type.key)) {
            if (e.armTime < MINE_ARM_TIME) {
                e.armTime += dt;
                return;
            }
            Ent victim = findEnemyInRange(e, MINE_TRIGGER_RANGE);
            if (victim != null) {
                // splash: everything hostile within the blast radius, not just
                // the trip wire's target, so a mine can catch a whole squad.
                float r2 = MINE_TRIGGER_RANGE * MINE_TRIGGER_RANGE;
                for (Ent o : ents) {
                    if (o.team == e.team || !o.alive() || o.constructing) continue;
                    float dx = o.x - e.x, dy = o.y - e.y;
                    if (dx * dx + dy * dy > r2) continue;
                    damage(o, e.type.dmg, e);
                }
                playAnim("bang_m", e.x, e.y, animFrames("bang_m"), e.team, 14f, 1f);
                effects.add(new float[]{e.x, e.y, 0.4f, 1});
                e.hp = 0;
                return;
            }
            return;
        }

        // construction work (terran SCV tether; protoss/zerg sites self-build
        // in updateProduction, so their worker never carries this order)
        if (e.target != null && e.target.constructing && e.target.team == e.team
                && !e.target.selfBuilding && isWorker(e)) {
            float d = dist(e, e.target);
            if (d < e.target.type.tiles * 16 + 24) {
                e.moving = false;
                e.target.buildProgress = Math.min(1f,
                        e.target.buildProgress + dt / (e.target.type.buildTime * 0.7f));
                if (e.target.buildProgress >= 1f) {
                    e.target.constructing = false;
                    e.target.hp = e.target.type.hp;
                    // v2.10: the shield comes online with the building.
                    e.target.shield = e.target.type.shield;
                    if (e.target.team == 0) {
                        revealAround(e.target.x, e.target.y, 10);
                        events.add(new Object[]{"built", e.target.x, e.target.y});
                    }
                    e.target = null;
                }
                return;
            }
            // v2.43 P0-c: simulation-side, so budgeted.
            queuePath(e, e.target.x, e.target.y);
        }

        // combat
        Ent tgt = e.target;
        if (tgt != null && (!tgt.alive() || (tgt.team == e.team && !tgt.constructing))) {
            if (tgt.team == e.team) {
                e.target = null;    // construction done
            } else {
                e.target = null;
            }
        }
        boolean attackMove = e.aiTimer < 0;
        if (e.aiTimer > 0) {
            e.aiTimer -= dt;
            if (e.aiTimer <= 0) e.aiTimer = 0;
        }
        // v2.44: the re-path throttle for a stalled attack-mover (see the
        // "nothing in sight" branch). Ticked here, with the other per-unit
        // timers, so it is advanced exactly once per unit per tick.
        if (e.aiRepathCd > 0) {
            e.aiRepathCd -= dt;
            if (e.aiRepathCd < 0) e.aiRepathCd = 0;
        }
        // v2.14 batch 1.5: a locked-down mechanical unit is frozen solid -- it
        // neither moves nor fires for the duration, and it drops whatever it
        // was shooting at. The order it had is remembered only in the sense
        // that it resumes acquiring once the lock lifts.
        if (e.lockdownTime > 0) {
            e.lockdownTime -= dt;
            if (e.lockdownTime <= 0) e.lockdownTime = 0;
            e.target = null;
            e.moving = false;
            cancelQueuedPath(e);   // v2.43 P0-c: frozen; no pending path may fire
            e.cd = Math.max(e.cd, 0.1f);
            return;
        }
        if (e.target == null && !e.moving && !attackMove) {
            // idle auto-acquire. v2.14 batch 1.3: a holding unit uses its exact
            // weapon range (no +30 grace) because it must not commit to a
            // target it would then have to walk toward -- if the target is
            // outside the range, there is no legal response but to stand still.
            //
            // v2.44: this used to be `e.team == 0`, i.e. only the player's
            // units ever looked around. The effect on the enemy was severe: an
            // AI unit whose attack-move lock had ended (see below) simply stood
            // there while it was shot to pieces -- measured in-game, two idle
            // zerglings were killed by four marines without ever returning
            // fire. An idle unit of either team now acquires, which is also
            // what makes an AI base defend itself.
            //
            // v2.43 P0-a: this scan is spread over ACQUIRE_PHASES ticks, keyed
            // off the unit's roster index. An idle army was paying one full
            // roster scan per idle unit per tick for an answer that does not
            // change at 30Hz; now each idle unit re-checks every 8th tick. The
            // index is the unit's slot in `ents`, which both lockstep peers
            // compute identically, so the phase is deterministic -- the one
            // rule this whole pass must not break. A unit that is ordered to
            // attack-move skips the stagger entirely (below), so orders still
            // acquire on the tick they are issued.
            //
            // The stagger only engages once the roster is big enough for the
            // scan to be worth spreading (ACQUIRE_STAGGER_MIN). Below that the
            // old every-tick behaviour is kept, which costs nothing and keeps
            // small skirmishes and the unit tests byte-identical to v2.42.
            // ents.size() is shared state, so the threshold itself is
            // deterministic.
            if (ents.size() < ACQUIRE_STAGGER_MIN
                    || (curRosterIdx & (ACQUIRE_PHASES - 1)) == (tick & (ACQUIRE_PHASES - 1))) {
                statAcquireScans++;
                float acq = e.holding ? e.type.range : e.type.range + 30;
                Ent en = findEnemyInRange(e, acq);
                if (en != null) e.target = en;
            }
            statAcquireQueries++;
        }
        if (e.target == null && attackMove) {
            Ent en = findEnemyInRange(e, 420);
            if (en != null) {
                e.target = en;
                // v2.43 P0-c: budgeted -- an attack-move order given to a whole
                // army used to fire one A* per unit in the issuing tick.
                queuePath(e, en.x, en.y);
            }
        }
        if (e.target != null && e.target.alive()
                // v2.44 regression fix: a friendly CONSTRUCTING building in
                // e.target is a builder's tether, never a combat target. The
                // v2.44 change of the range test to the target's EDGE widened
                // "in range" past the tether's own catch radius (72px), so a
                // terran worker walking to a site stopped at ~94px, opened fire
                // on the site it was building and killed it (hp starts at 1).
                // The tether block above handles approach and build; combat
                // must not see this target at all.
                && !(e.target.constructing && e.target.team == e.team)) {
            // v2.44: measured to the target's EDGE (reachDist), not its centre.
            // Against a building the centre is unreachable -- its footprint is
            // not walkable -- so the old centre-to-centre test put every melee
            // unit permanently out of range and melee could not damage
            // structures at all. See reachDist.
            float d = reachDist(e, e.target);
            if (d <= e.type.range + e.target.type.radius) {
                e.moving = false;
                e.path = Ent.EMPTY_PATH;
                // v2.43 P0-c: in range and stopping to fire. Any request still
                // waiting in the budget queue is now stale -- without this the
                // unit would walk off again the moment it was served.
                cancelQueuedPath(e);
                e.facing = (float) Math.atan2(e.target.y - e.y, e.target.x - e.x);
                e.dir = dirOf(e.facing);
                if (e.cd <= 0) {
                    e.cd = effectiveCooldown(e);
                    fire(e, e.target);
                }
                return;
            }
            // v2.14 batch 1.3: out of range. A holding unit drops the target
            // instead of closing -- this is the rule that keeps a hold line
            // from collapsing into a chase, and it is what makes Hold differ
            // from Attack-Move in play rather than only in the button art.
            if (e.holding) {
                e.target = null;
            } else if (!e.moving || e.pathIndex >= e.pathLen()) {
                // v2.43 P0-c: budgeted. Note this is also the point where a unit
                // whose old path just ran out asks for a fresh one, so the
                // queued request must not be dropped by the "path finished"
                // branch above -- it is what keeps a chase from stalling.
                queuePath(e, e.target.x, e.target.y);
            }
        } else if (attackMove && !e.moving && e.target == null) {
            // v2.44: this used to end the attack-move lock outright
            // (`e.aiTimer = 1`), and that is how an AI wave died: its path
            // failed or ran out short of the player's base, the lock ended, and
            // the unit then stood at the spot for the rest of the match --
            // permanently, because a non-attack-moving AI unit had no way to
            // re-acquire a target either (see the idle-acquire gate above).
            //
            // Now the unit re-asks for a route to its own goal, throttled so a
            // genuinely unreachable goal does not cost one A* per tick, and
            // bounded so it cannot spin forever. Only a unit that has actually
            // arrived (or has given up) ends its lock.
            float gdx = e.goalX - e.x, gdy = e.goalY - e.y;
            if (gdx * gdx + gdy * gdy <= 48 * 48 || e.aiRepathTries >= AI_REPATH_MAX) {
                e.aiTimer = 1;   // arrived, or out of patience: end the lock
            } else if (e.aiRepathCd <= 0) {
                e.aiRepathCd = AI_REPATH_DELAY;
                e.aiRepathTries++;
                // v2.43 P0-c: budgeted. Re-issuing here is what keeps an AI
                // wave walking instead of freezing at its spawn point.
                queuePath(e, e.goalX, e.goalY);
            }
        }

        // v2.14 batch 1.3: drift back onto the hold spot. A holding unit is
        // never displaced by its own orders, but the separation pass below can
        // shove it aside when friendlies pile up. Walking back is legal here
        // because it is a return, not a chase: the target must be null, so
        // this can never pull a unit toward an enemy.
        if (e.holding && e.target == null && !e.moving) {
            float hdx = e.holdX - e.x, hdy = e.holdY - e.y;
            // v2.43 P0-c: budgeted -- a shoved hold line walks back a tick later.
            if (hdx * hdx + hdy * hdy > 100f) queuePath(e, e.holdX, e.holdY);
        }

        // follow path
        if (e.moving) {
            if (e.pathIndex >= e.pathLen()) {
                // v2.43 P0-c: an empty path with a request still waiting in the
                // budget queue is "not arrived yet", not "arrived". Clearing
                // `moving` here would make the unit read as idle for the one or
                // two ticks until the search runs -- which would end an AI
                // wave's attack-move (see the aiTimer branch above) and drop a
                // worker back to W_IDLE before it ever started walking.
                if (e.pathGen == 0) {
                    e.moving = false;
                    reversePatrolIfDone(e);
                }
            } else {
                int ni = e.pathIndex * 2;
                float nx = e.path[ni] * 8 + 4, ny = e.path[ni + 1] * 8 + 4;
                float dx = nx - e.x, dy = ny - e.y;
                float d = (float) Math.sqrt(dx * dx + dy * dy);
                float step = e.type.speed * dt;
                // v2.11 ensnare: the defiler's second field glues everything
                // inside it to the ground, halving movement. Applied at the
                // step rather than by rewriting type.speed so it lifts the
                // instant the field expires.
                if (underEnsnare(e.x, e.y)) step *= ENSNARE_SLOW;
                if (d < Math.max(4, step)) {
                    e.pathIndex++;
                    if (e.pathIndex >= e.pathLen()) {
                        e.moving = false;
                        if (isWorker(e) && e.mineTarget != null
                                && e.workerState == Ent.W_TO_MINE) {
                            e.workerState = Ent.W_MINING;
                            e.animTime = 1.1f;
                        } else {
                            reversePatrolIfDone(e);
                        }
                    }
                } else {
                    // v2.44 pathing fix: path following is a straight-line
                    // interpolation, so this is the only place that can stop a
                    // unit from walking through terrain -- there is no collider
                    // for a cliff or water tile, only for buildings. It used to
                    // step blindly. Combined with the start-skip bug above, a
                    // unit ordered a short move beside a cliff walked straight
                    // through it and ended up on ground it could never reach.
                    // Flying units ignore terrain, as they do everywhere else.
                    float tx = e.x + dx / d * step, ty = e.y + dy / d * step;
                    if (e.type.flying || passMini((int) (tx / 8), (int) (ty / 8))) {
                        e.x = tx;
                        e.y = ty;
                        e.facing = (float) Math.atan2(dy, dx);
                        e.dir = dirOf(e.facing);
                        e.animTime += dt;
                    } else {
                        // Blocked. Drop the path so the next AI tick or order
                        // asks for a fresh one instead of grinding into the
                        // wall forever. `pathGen` is left alone: a request that
                        // is already in the budget queue is still valid.
                        e.path = Ent.EMPTY_PATH;
                        e.moving = e.pathGen != 0;
                    }
                }
            }
        }

        // separation
        // batch-D regression: a crowd of workers standing on a waypoint used to
        // push exactly as hard as the path step pulled, so the unit stopped dead
        // with moving=true, the waypoint never got inside the arrival radius and
        // the path index never advanced. Four SCVs froze at (126,328) for 200 s
        // and mining stalled at 432 minerals while a lone SCV mined normally.
        // Accumulate the push, and while the unit is actually pathing cap it
        // below the per-frame step so it can never fully cancel progress.
        // v2.43 P0-b: only the cells within reach of the largest possible
        // neighbour can contribute, and gatherNear hands them back in roster
        // order so this accumulates the identical float sum as the full scan.
        float pushX = 0f, pushY = 0f;
        int nearN = gatherNear(e.x, e.y, e.type.radius + maxUnitRadius());
        for (int ni = 0; ni < nearN; ni++) {
            Ent o = ents.get(qScratch[ni]);
            if (o == e || !o.alive() || o.isBuilding() || o.type.flying != e.type.flying) continue;
            float dx = e.x - o.x, dy = e.y - o.y;
            float d2 = dx * dx + dy * dy;
            float min = e.type.radius + o.type.radius;
            if (d2 < min * min && d2 > 0.01f) {
                float d = (float) Math.sqrt(d2);
                float push = (min - d) * 0.4f;
                pushX += dx / d * push;
                pushY += dy / d * push;
            }
        }
        if (e.moving) {
            float pm = (float) Math.sqrt(pushX * pushX + pushY * pushY);
            float cap = Math.max(0.5f, e.type.speed * dt * 0.5f);
            if (pm > cap) {
                pushX *= cap / pm;
                pushY *= cap / pm;
            }
        }
        e.x += pushX;
        e.y += pushY;
        // building collision
        // v2.43 P0-b: buildings never move, so the per-cell buckets cannot be
        // trusted to hold them for a query centred on a unit that has just been
        // pushed -- use the flat roster-ordered building list instead. It is
        // short (a handful per side), so this is still far cheaper than the
        // full roster walk, and it cannot miss a building for being one cell
        // too far from where the unit now stands.
        //
        // v2.44 pathing fix: the collider used to be a square centred on the
        // entity centre (half + radius*0.5). Two mismatches with the walkable
        // grid made it a unit trap: the radius margin let the push zone reach
        // past the footprint, and -- worse -- the blocked FOOTPRINT is anchored
        // to the tile grid (canPlace: tx0 = x/32 - tiles/2), so for a building
        // whose centre sits mid-tile the true blocked box is shifted up to half
        // a tile from the collider. A corridor running through the difference
        // (a worker walking home under a hatchery) hit a fixed point where the
        // 2.2px path step and the push cancelled and the unit stood still
        // forever with moving=true. The box below is canPlace's exact footprint,
        // so the collider, the placement check and A* all agree: every corridor
        // the pather can route through is one the unit can actually walk.
        for (int bi = 0; bi < bldListN; bi++) {
            Ent o = bldList[bi];
            if (o == e || !o.alive() || o.type.flying) continue;
            float x0 = ((int) (o.x / 32) - o.type.tiles / 2) * 32f;
            float y0 = ((int) (o.y / 32) - o.type.tiles / 2) * 32f;
            float dx0 = e.x - x0, dx1 = x0 + o.type.tiles * 32f - e.x;
            float dy0 = e.y - y0, dy1 = y0 + o.type.tiles * 32f - e.y;
            if (dx0 > 0 && dx1 > 0 && dy0 > 0 && dy1 > 0) {
                float mx = Math.min(dx0, dx1), my = Math.min(dy0, dy1);
                if (mx < my) e.x += (dx0 < dx1 ? -mx : mx);
                else e.y += (dy0 < dy1 ? -my : my);
            }
        }
        e.x = clamp(e.x, 8, wPx - 8);
        e.y = clamp(e.y, 8, hPx - 8);
    }


    private Ent nearestPlayerBuilding(Ent e, String key) {
        Ent best = null;
        float bd = 1e9f;
        // v2.43 P0-b: dropList is already "live, completed, team-0 buildings in
        // roster order", which is this loop's filter minus the key test.
        ensureSpatial();
        for (int di = 0; di < dropListN; di++) {
            Ent o = dropList[di];
            if (!o.alive() || !o.type.key.equals(key)) continue;
            float d = dist(e, o);
            if (d < bd) {
                bd = d;
                best = o;
            }
        }
        return best;
    }

    /**
     * v2.8: where a loaded worker delivers. Gas goes to a refinery/extractor,
     * minerals to a town hall -- cc for terran, hatchery/lair/hive for zerg.
     * Keeping this in one place is what let the mining code stay race-neutral.
     */
    private Ent nearestDropOff(Ent e, boolean gas) {
        Ent best = null;
        float bd = 1e9f;
        // v2.43 P0-b: a "nearest" helper is a global question, so the grid
        // cannot answer it by looking at the caller's own cell. rebuildSpatial
        // collects the qualifying buildings once per tick into dropList, in
        // roster order, which reproduces this loop's exact candidate sequence
        // (and therefore its first-strictly-closer tie-break) without walking
        // the roster.
        ensureSpatial();
        for (int di = 0; di < dropListN; di++) {
            Ent o = dropList[di];
            // the list already guarantees team 0, completed and a building; the
            // liveness re-check stays because a structure can be destroyed
            // during the tick that built the list (splash, then the sweep).
            if (!o.alive()) continue;
            String k = o.type.key;
            boolean ok = gas ? isGasBuilding(k) : isDropOff(k);
            if (!ok) continue;
            float d = dist(e, o);
            if (d < bd) {
                bd = d;
                best = o;
            }
        }
        return best;
    }

    /**
     * Explosion + death sequence for a unit that just died. Units with a real
     * death GRP play it; everything else gets a bang scaled to its footprint.
     */
    private void spawnDeathFx(Ent e) {
        // bang_l is already 252 px wide, which covers a 4x4 building footprint,
        // so buildings use their sheet at native size and units scale down.
        float scale = e.isBuilding() ? 1f : 0.55f;
        String bang = bangFor(e.type.tiles);
        playAnim(bang, e.x, e.y, animFrames(bang), e.team, 22f, scale);
        String death = deathAnimFor(e.type.key);
        if (death != null) {
            playAnim(death, e.x, e.y, animFrames(death), e.team, 14f, 1f);
            // corpse: the death sequence's last frame, held then faded out
            Corpse c = new Corpse();
            c.key = death;
            c.team = e.team;
            c.x = e.x;
            c.y = e.y;
            c.frame = animFrames(death) - 1;
            if (corpses.size() > 48) corpses.remove(0);
            corpses.add(c);
        }
        effects.add(new float[]{e.x, e.y, 0.7f, 1});
    }

    private void fire(Ent e, Ent tgt) {
        fireFrom(e, e, tgt);
    }

    /**
     * v2.23: fire with an explicit origin. For every ordinary unit `src` is
     * the shooter itself and this is exactly the old fire(). A garrisoned unit
     * passes its bunker, so the muzzle flash, the elevation test and the
     * projectile all measure from the bunker while the damage and the team
     * still belong to the unit inside.
     *
     * v2.23 batch C adds the elevation miss here rather than in damage():
     * this is the one place a ranged shot is decided, so a low-to-high shot is
     * rolled once, before the muzzle flash, and a miss costs the shot without
     * any impact effect. Splash is deliberately not re-rolled (it resolves on
     * the primary hit, in resolveShots).
     */
    private void fireFrom(Ent e, Ent src, Ent tgt) {
        e.flashTime = 0.12f;
        // v2.11 dark swarm: a cloud of spores swallows ranged fire. Anything
        // standing under its own team's swarm simply cannot be shot at from a
        // distance -- the shot is spent and nothing happens. Melee (range < 64)
        // is unaffected, which is the entire counter-play: the swarm turns a
        // tank line into a liability and forces you to walk in and hit things.
        // Checked before the muzzle flash so a blocked shot does not even
        // appear to leave the barrel.
        if (e.type.range >= 64 && underDswarm(tgt.x, tgt.y)) {
            return;
        }
        // v2.14 batch 1.5: disruption web silences the SHOOTER, not the target
        // -- a unit standing in a web cannot use a ranged weapon at all, not
        // even to shoot out of it. Note this test is not team-filtered, so a
        // corsair that drops a web on its own dragoons disarms them too; that
        // friendly-fire is the original's behaviour and the reason the spell
        // is a placement puzzle rather than a free button.
        if (e.type.range >= 64 && underDweb(e.x, e.y)) {
            return;
        }
        // v2.26: a reaver with an empty rack cannot fire. The reload only
        // happens beside the robotics facility (updateAmmo), which is what
        // forces the reaver to shuttle home between volleys.
        if (e.type.ammoCap > 0) {
            if (e.ammo <= 0) return;
            e.ammo--;
        }
        // real muzzle-flash sprite, sized by weapon weight
        int gun = damageOf(e, tgt);
        String fl = gun >= 30 ? "flsh_l" : gun >= 15 ? "flsh_m" : "flsh_s";
        float mx = src.x + (float) Math.cos(e.facing) * (e.type.radius + 4),
                my = src.y + (float) Math.sin(e.facing) * (e.type.radius + 4);
        playAnim(fl, mx, my, animFrames(fl), e.team, 22f, 0.9f);
        // v2.23 batch C: low ground shooting up at a cliff. The roll happens
        // after the flash so the player sees the shot leave the barrel, and a
        // miss simply ends here -- no projectile, no impact, no damage.
        if (!shotHits(src, tgt)) return;

        boolean missile = e.type.key.equals("tank") || e.type.key.equals("stank")
                || e.type.key.equals("vulture") || e.type.key.equals("turret")
                || (e.type.dmgAir >= 0 && tgt.type.flying);
        int dmg = gun;
        // v2.8: instant-hit weapons. Both workers melee, the ghost's rifle is
        // hitscan; everything else lobs a projectile that lands on arrival.
        // v2.10: the protoss melee castes join the instant list. Zealot and
        // dark templar both swing at range 14, and a psi blade that has to
        // fly across the screen as a projectile would look wrong; the dragoon
        // deliberately stays a projectile, which is what makes its `b_dragbull`
        // bolt the visual difference between the two gateway units.
        // v2.11: `melee` names the same property on the new zerg rows (ultra,
        // broodling) instead of extending this string comparison every batch.
        if (e.type.melee || e.type.key.equals("firebat") || e.type.key.equals("zergling")
                || e.type.key.equals("scv") || e.type.key.equals("drone")
                || e.type.key.equals("ghost") || e.type.key.equals("probe")
                || e.type.key.equals("zealot") || e.type.key.equals("dtemplar")) {
            // instant hit
            damage(tgt, dmg, e);
            // v2.14 batch 1.2: the firebat's short cone is an instant-hit splash.
            // Everything else in this list has splashR == 0, so this is a no-op
            // for them and does not need its own branch.
            if (e.type.splashR > 0) {
                splash(tgt.x, tgt.y, dmg, e.type.dmgType, e, e.type.splashR,
                        e.type.splashFalloff, tgt);
                playAnim("bang_s", tgt.x, tgt.y, animFrames("bang_s"), e.team, 14f, 0.9f);
            }
        } else {
            Shot s = new Shot();
            s.x = src.x;
            s.y = src.y - 6;
            s.tx = tgt.x;
            s.ty = tgt.y;
            s.dur = Math.max(0.08f, dist(src, tgt) / 700f);
            s.t = 0;
            s.team = e.team;
            s.missile = missile;
            s.smokeTimer = 0;
            shots.add(s);
            // damage is applied on arrival (the old code applied it instantly,
            // which let shells kill through cover and pre-empted the impact fx)
            // v2.14 batch 1.2: the splash geometry travels with the shell, so a
            // target that walks away from the impact point still takes the
            // smaller edge damage rather than the full hit.
            pendingShots.add(new Object[]{s, tgt, dmg, e.type.dmgType,
                    e.type.splashR, e.type.splashFalloff, e});
        }
        alertIfPlayer(tgt);
    }

    /** Shots whose damage lands when the projectile arrives. */
    private final List<Object[]> pendingShots = new ArrayList<>();

    /**
     * v2.10: tick every live psionic storm. Damage lands on the storm's own
     * clock (STORM_TICK), not on the caster's attack cooldown, so a storm
     * keeps hurting after the templar dies or walks away.
     */
    private void updateStorms(float dt) {
        for (int i = storms.size() - 1; i >= 0; i--) {
            Storm s = storms.get(i);
            s.t += dt;
            s.tickTimer += dt;
            while (s.tickTimer >= STORM_TICK) {
                s.tickTimer -= STORM_TICK;
                for (Ent e : ents) {
                    if (!e.alive() || e.team == s.team) continue;
                    if (offField(e)) continue;    // v2.23: storms cannot reach cargo
                    float dx = e.x - s.x, dy = e.y - s.y;
                    if (dx * dx + dy * dy <= STORM_RADIUS * STORM_RADIUS) {
                        // v2.14 batch 1.6: mechanism-respecting AI, applied to
                        // the rule rather than to the AI. A unit standing under
                        // its OWN dark swarm is shielded from the storm too --
                        // the swarm eats area spells as well as bullets, which
                        // is the whole reason "swarm up, then charge" works and
                        // why an AI that ignores it just wastes its storms.
                        if (underDswarmFor(e.x, e.y, e.team)) continue;
                        damage(e, STORM_DAMAGE, null, "normal");
                        alertIfPlayer(e);
                    }
                }
            }
            if (s.done()) storms.remove(i);
        }
    }

    /**
     * v2.14 batch 1.5: Irradiate. Unlike a storm this is not a field, it is a
     * property of the victim: the unit keeps bleeding hp wherever it walks for
     * the duration, which is what makes it the right answer to a clump of
     * zerglings (it spreads nothing, but the target cannot outrun it).
     */
    private void updateIrradiate(float dt) {
        for (Ent e : ents) {
            if (!e.alive() || e.irradiateTime <= 0) continue;
            if (offField(e)) continue;    // v2.23: the burn pauses in a transport
            e.irradiateTime -= dt;
            e.irradiateTick += dt;
            while (e.irradiateTick >= IRRADIATE_TICK) {
                e.irradiateTick -= IRRADIATE_TICK;
                damage(e, IRRADIATE_DAMAGE, null, "normal");
                alertIfPlayer(e);
                if (!e.alive()) break;
            }
            if (e.irradiateTime <= 0) e.irradiateTime = 0;
        }
    }

    private void resolveShots() {
        for (int i = pendingShots.size() - 1; i >= 0; i--) {
            Object[] p = pendingShots.get(i);
            Shot s = (Shot) p[0];
            if (s.t < s.dur) continue;
            Ent tgt = (Ent) p[1];
            int dmg = (Integer) p[2];
            String dt = p.length > 3 ? (String) p[3] : null;
            float sr = p.length > 4 ? (Float) p[4] : 0f;
            float sf = p.length > 5 ? (Float) p[5] : 0.5f;
            Ent src = p.length > 6 ? (Ent) p[6] : null;
            String impact = p.length > 7 ? (String) p[7] : null;
            pendingShots.remove(i);
            if (tgt != null && tgt.alive()) {
                damage(tgt, dmg, src, dt);
                effects.add(new float[]{tgt.x, tgt.y, 0.25f, 0});
                playAnim("hit", tgt.x, tgt.y, animFrames("hit"), tgt.team, 20f, 0.8f);
                alertIfPlayer(tgt);
            }
            // v2.14 batch 1.2: splash resolves at the IMPACT POINT, not on the
            // target, so a shell that lands where the squad used to stand still
            // catches whoever is left there.
            if (sr > 0 && tgt != null) {
                splash(tgt.x, tgt.y, dmg, dt, src, sr, sf, tgt);
                String bang = sr >= 48f ? "bang_l" : "bang_m";
                playAnim(bang, tgt.x, tgt.y, animFrames(bang), s.team, 16f, 1f);
            }
            // v2.14 batch 1.5: a shot may carry its own impact effect, which is
            // how Yamato Gun gets the plasma fireball on arrival instead of the
            // generic `hit` spark. It plays at the impact point either way, so
            // a bolt that kills its target still shows where it landed.
            if (impact != null && tgt != null) {
                playAnim(impact, tgt.x, tgt.y, animFrames(impact), s.team, 24f, 1.4f);
            }
        }
    }

    /**
     * v2.14 batch 1.2: area damage. Deliberately does NOT filter by team -- the
     * original's splash hits friendly units too, and that rule is the entire
     * reason "zerglings hugging a tank" is a real tactic rather than a
     * formality. The shooter itself is excluded (its own shell does not
     * damage it) and `primary` is skipped because it already took full damage.
     * Damage falls off linearly from the centre to `falloff` at the rim.
     */
    public void splash(float x, float y, int dmg, String dmgType, Ent from,
                       float radius, float falloff, Ent primary) {
        if (radius <= 0) return;
        float r2 = radius * radius;
        // v2.43 P0-b: same candidates, same order. gatherNear returns roster
        // indices ascending, so damage lands on the same units in the same
        // sequence -- which matters because each hit mutates hp and can kill,
        // and the roster walk used to apply those in roster order.
        int hitN = gatherNear(x, y, radius);
        for (int hi = 0; hi < hitN; hi++) {
            Ent o = ents.get(qScratch[hi]);
            if (o == primary || o == from || !o.alive() || o.constructing) continue;
            if (offField(o)) continue;    // v2.23: splash cannot reach cargo
            float dx = o.x - x, dy = o.y - y;
            float d2 = dx * dx + dy * dy;
            if (d2 > r2) continue;
            float d = (float) Math.sqrt(d2);
            float mul = falloff + (1f - falloff) * (1f - d / radius);
            int hit = (int) (dmg * mul);
            if (hit < 1) hit = 1;
            damage(o, hit, from, dmgType);
        }
    }

    /** Player-owned things under fire raise the minimap alert (rate limited). */
    private void alertIfPlayer(Ent tgt) {
        if (tgt == null || tgt.team != 0 || alertCd > 0) return;
        alertCd = 2.5f;
        events.add(new Object[]{"alert", tgt.x, tgt.y});
    }

    /**
     * v2.14 batch 1.6: the AI's own alarm. A hit on an AI STRUCTURE records
     * where it happened so the next aiUpdate can call the army home; a hit on
     * an AI unit only matters if the army is already committed, in which case
     * the retreat test in aiUpdate notices the losses anyway. Kept separate
     * from alertIfPlayer because the two sides react differently -- the player
     * gets a minimap ping, the AI gets a recall order.
     */
    private void alertIfAi(Ent tgt) {
        if (tgt == null || tgt.team != 1 || !tgt.isBuilding()) return;
        // A fresh alert (or a new location) re-arms the recall; repeated hits on
        // the same building just extend the window rather than re-pathing the
        // whole army every frame.
        if (aiDefendTimer <= 0) aiDefendIssued = false;
        aiDefendTimer = 6f;
        aiDefendX = tgt.x;
        aiDefendY = tgt.y;
    }

    /**
     * v2.7 9.2: flat armor reduction, floored at 1 damage. The floor is what
     * keeps the model from deadlocking -- without it a high-armor target could
     * become literally unkillable by a cheap attacker and stall the game.
     */
    public int applyArmor(Ent tgt, int dmg) {
        int eff = dmg - (tgt.type.armor + tgt.armorBonus);
        return eff < 1 ? 1 : eff;
    }

    /**
     * v2.14 batch 1.1: the original's damage-type x unit-size counter triangle.
     * The published table is
     *     normal     1.00 / 1.00 / 1.00
     *     explosive  1.00 / 0.75 / 0.50
     *     concussive 1.00 / 0.50 / 0.25
     * over small / medium / large. This is what makes "a tank one-shots a
     * swarm of zerglings, but a zergling can barely scratch the tank" fall out
     * of the rules instead of being hand-tuned into each unit's damage number.
     * Applied BEFORE armor, so the floor-at-1 in applyArmor still protects a
     * cheap attacker from being literally useless.
     */
    public static float typeMultiplier(String dmgType, String size) {
        if (dmgType == null || size == null) return 1f;
        boolean small = "small".equals(size), large = "large".equals(size);
        if ("explosive".equals(dmgType)) {
            if (large) return 1.0f;
            return small ? 0.5f : 0.75f;
        }
        if ("concussive".equals(dmgType)) {
            if (large) return 0.25f;
            return small ? 1.0f : 0.5f;
        }
        return 1.0f;
    }

    /** Damage after the type/size counter table, before armor. */
    public int typedDamage(int dmg, String dmgType, String size) {
        float mul = typeMultiplier(dmgType, size);
        int out = (int) (dmg * mul);
        return out < 1 ? 1 : out;
    }

    /** Weapon damage after this unit's upgrades (v2.7 9.1). */
    public int damageOf(Ent e) {
        return e.type.dmg + e.dmgBonus;
    }

    /**
     * v2.23 batch B: the dual-weapon axis pick. A goliath carries an air
     * missile (20) over its ground autocannon (12); every other type leaves
     * dmgAir at -1 and this collapses to damageOf. The upgrade bonus is added
     * to whichever axis is chosen, so a weapon upgrade helps both guns.
     */
    public int damageOf(Ent e, Ent tgt) {
        if (tgt != null && tgt.type.flying && e.type.dmgAir >= 0)
            return e.type.dmgAir + e.dmgBonus;
        return damageOf(e);
    }

    /**
     * The single damage entry point: shields absorb first, then hp. Public so
     * the desktop harness can assert the shield split without having to stage a
     * real firefight (same reason applyArmor and stim are public).
     */
    public void damage(Ent tgt, int dmg, Ent from) {
        damage(tgt, dmg, from, from != null ? from.type.dmgType : null);
    }

    /**
     * v2.14 batch 1.1: the type-aware overload. `dmgType` is passed explicitly
     * whenever the source is not a unit's own weapon -- splash, storms,
     * irradiate and EMP all arrive with `from == null`, and inferring "normal"
     * there would silently drop the counter triangle for exactly the weapons
     * (tank, firebat, valkyrie, devourer) the triangle exists to fix.
     */
    public void damage(Ent tgt, int dmg, Ent from, String dmgType) {
        // v2.23: a unit inside a transport or bunker cannot be hit by anything
        // short of the carrier dying -- that rule lives in the death cascade.
        if (offField(tgt)) return;
        int eff = applyArmor(tgt, typedDamage(dmg, dmgType, tgt.type.size));
        // v2.10: the shield eats the hit before hp does. Armor is applied once,
        // to the whole hit, rather than separately to the shield and the hp --
        // the original does split it, but with a single flat armor value the
        // split only changes rounding, and one reduction is far easier to
        // reason about when tuning.
        // The regen clock is restarted by any damage at all, including damage
        // that lands once the shield is already stripped: otherwise a unit
        // under sustained fire would quietly recharge between shots, which is
        // the exact thing the delay exists to prevent.
        if (tgt.type.shield > 0) tgt.shieldDelay = SHIELD_DELAY;
        if (tgt.shield > 0) {
            int absorbed = Math.min(tgt.shield, eff);
            tgt.shield -= absorbed;
            eff -= absorbed;
        }
        tgt.hp -= eff;
        if (!tgt.alive()) {
            effects.add(new float[]{tgt.x, tgt.y, 0.25f, 0});
        }
        alertIfPlayer(tgt);
        alertIfAi(tgt);
    }

    /**
     * v2.10 shield tuning. The original is ~50 shield points per 10 seconds;
     * scaled to this game's pace (units move at ~60-120 px/s and a fight is
     * over in seconds, not minutes) that is far too slow to ever matter, so
     * regen is much faster and the delay is what carries the cost: three
     * seconds of not being shot at buys back SHIELD_REGEN points per second.
     */
    public static final float SHIELD_DELAY = 3.0f;
    public static final float SHIELD_REGEN = 8.0f;   // points per second

    public float dist(Ent a, Ent b) {
        float dx = a.x - b.x, dy = a.y - b.y;
        return (float) Math.sqrt(dx * dx + dy * dy);
    }

    /**
     * v2.44: centre-to-centre distance, less the target's body. Melee could not
     * damage a building before this existed.
     *
     * A building's footprint is carved out of the walk grid (occupyFootprint),
     * so a melee unit walks up to the nearest walkable minitile and stops --
     * measured 68.1px from a barracks centre. The old in-range test was
     * `d <= e.type.range + e.target.type.radius`, i.e. 34px for a zergling and
     * 38px for a zealot, so a melee unit could never satisfy it: four
     * zerglings chewed on a barracks for twenty seconds and did exactly zero
     * damage, while the same four killed an SCV normally.
     *
     * The fix is to measure to the target's edge rather than its centre. For a
     * 3x3 barracks (tiles=3) that subtracts 48px, which brings the standoff
     * inside melee reach. Ranged units are unaffected in practice -- their
     * range is large enough that either measure hits -- but the same formula
     * now also gives them the correct answer when shooting a big building from
     * just outside its footprint.
     */
    public float reachDist(Ent a, Ent b) {
        float d = dist(a, b);
        if (b.type.tiles <= 0) return d;
        return Math.max(0f, d - b.type.tiles * 16f);
    }

    /**
     * Patrol turnaround (v2.5 batch-6): called whenever a unit finishes its
     * path. A patrolling unit immediately heads for its other endpoint, which
     * makes the loop self-sustaining with no extra state.
     */
    private void reversePatrolIfDone(Ent e) {
        if (!e.patrolling || e.target != null) return;
        float dx = e.patrolBX - e.x, dy = e.patrolBY - e.y;
        boolean atB = dx * dx + dy * dy < 40 * 40;
        float nx = atB ? e.patrolAX : e.patrolBX;
        float ny = atB ? e.patrolAY : e.patrolBY;
        // v2.43 P0-c: budgeted. A patrol reversal happens once per leg, so the
        // one-tick delay is invisible, and it keeps a large patrol group from
        // turning around with one A* per unit in the same frame.
        queuePath(e, nx, ny);
    }

    /**
     * v2.11: is this entity underground? The burrowed lurker is a separate
     * type (lurker_bur) rather than a flag on the mobile one, so the test is
     * just its key -- but it is asked in enough places (targeting, drawing,
     * the "can I shoot that" rules) that it earns a named helper.
     */
    public static boolean isBurrowed(Ent e) {
        // v2.26: the lurker's burrow is a TYPE (lurker_bur, the siege-morph
        // pair), while every other zerg ground unit burrows with the
        // `burrowed` flag. Both answer here so targeting, drawing and the
        // "can I shoot that" rules stay in one place.
        return e != null && ("lurker_bur".equals(e.type.key) || e.burrowed);
    }

    /**
     * v2.23: is this unit off the field -- riding in a transport or garrisoned
     * in a bunker? Every field interaction (targeting, splash, storms, fog,
     * picking, the AI helpers) tests this and skips the unit, which is what
     * makes "loaded" mean the same thing to the whole simulation instead of to
     * just the renderer.
     */
    public static boolean offField(Ent e) {
        return e != null && (e.cargoOf != null || e.garrisoned);
    }

    public Ent findEnemyInRange(Ent e, float range) {
        return findEnemyInRangeFrom(e.x, e.y, e, range);
    }

    /**
     * v2.23 batch B: the same search measured from an arbitrary point. A
     * garrisoned unit sits off the field inside its bunker, so its range has
     * to be measured from the bunker -- and rather than special-case the whole
     * acquisition block, the origin is simply passed in. `e` still supplies
     * the team and the weapon-layer rules.
     */
    public Ent findEnemyInRangeFrom(float ox, float oy, Ent e, float range) {
        Ent best = null;
        float bd = range * range;
        // v2.43 P0-b: only cells that can hold something within `range`. The
        // tie-break is "first strictly closer wins", so the candidate order has
        // to stay roster order -- gatherNear guarantees exactly that, which
        // keeps the pick identical to the old full walk (and therefore
        // identical on both lockstep peers).
        int candN = gatherNear(ox, oy, range);
        for (int ci = 0; ci < candN; ci++) {
            Ent o = ents.get(qScratch[ci]);
            if (o.team == e.team || !o.alive() || o.constructing) continue;
            // v2.23: a unit inside a transport or a bunker is off the field and
            // cannot be shot at. A garrisoned unit is a separate flag from
            // cargoOf because it still shoots back (see updateGarrisonFire).
            if (o.cargoOf != null || o.garrisoned) continue;
            // v2.22 batch B: a cloaked enemy is not a target until one of the
            // observer's team's detectors reveals it. This one gate covers
            // every auto-acquire path -- idle acquire, attack-move, turret
            // defence, spider mines and the AI's wave logic -- because they
            // all come through here.
            if (o.cloakActive && !o.spotted) continue;
            if (o.type.flying && e.type.range < 64) continue;  // melee can't hit flyers
            // v2.11: the two layer restrictions. A valkyrie or devourer simply
            // has no air-to-ground weapon, and a lurker's spines never leave
            // the ground, so each side of the pair is invisible to the other.
            if (e.type.airOnly && !o.type.flying) continue;
            if (e.type.groundOnly && o.type.flying) continue;
            // v2.11: a burrowed lurker cannot be reached by melee -- the whole
            // point of burrowing. Ranged units still hit it (its spines stick
            // out), which is what keeps it from being invulnerable.
            if (isBurrowed(o) && e.type.range < 64) continue;
            float dx = o.x - ox, dy = o.y - oy;
            float d2 = dx * dx + dy * dy;
            if (d2 < bd) {
                bd = d2;
                best = o;
            }
        }
        return best;
    }

    public static int dirOf(float facing) {
        // sprite dirs: 0 = east, clockwise (SC convention); facing radians CCW
        float deg = (float) Math.toDegrees(-facing);
        if (deg < 0) deg += 360;
        int dir = Math.round(deg / 22.5f) & 15;
        return dir;
    }

    public static float clamp(float v, float a, float b) {
        return v < a ? a : (v > b ? b : v);
    }

    // -------------------------------------------------------------------- AI

    /**
     * v2.10 batch A item 7: which unit the skirmish AI queues next, given the
     * clock, the wave counter and a 0..99 roll. Split out of aiUpdate so the
     * desktop harness can assert the protoss mix without staging a twenty
     * minute match (the AI is the only place the three races meet).
     *
     * Before 90 s it is pure zergling, and the protoss band only opens from
     * wave 2: a zealot rush at minute two would be unwinnable on a fresh base.
     * The AI owns no protoss buildings and spawns these from its hatchery --
     * a deliberate cheat of the same kind as its free income, because the
     * point is the matchup, not an AI economy simulation.
     *
     * v2.11 batch B widens the zerg band with the units the batch just added,
     * gated on wave so the early game stays readable: the lurker (a ground
     * siege unit that punishes clumped marines) opens at wave 3, and the
     * ultralisk / guardian / devourer heavies only at wave 4, which in a
     * skirmish is several minutes in.
     */
    public static String aiPick(float time, int aiWave, int roll) {
        if (time < 90) return "zergling";
        // The wave-4 zerg heavies must be tested *before* the protoss band.
        // The protoss slots own rolls 70..99 outright, so putting the ultralisk
        // / guardian / devourer above them (as the first draft did) left all
        // three unreachable at any roll -- the batch A assertion still passed,
        // which is exactly why this ordering needs its own assertion below.
        if (aiWave >= 4) {
            if (roll < 22) return "zergling";
            if (roll < 38) return "hydra";
            if (roll < 48) return "muta";
            if (roll < 58) return "lurker";
            if (roll < 64) return "ultra";
            if (roll < 68) return "guardian";
            if (roll < 70) return "devourer";
        }
        if (aiWave >= 2 && roll >= 70)
            return roll < 78 ? "zealot" : roll < 86 ? "dragoon" : "scout";
        if (aiWave >= 3 && roll >= 62 && roll < 74) return "lurker";
        if (roll < 55) return "zergling";
        if (roll < 85) return "hydra";
        return "muta";
    }

    /**
     * v2.14 batch 1.6: is the AI currently pulling its army home because one of
     * its structures was hit? Public so the desktop assertion can ask the
     * question directly instead of inferring it from unit paths -- "did the
     * army turn around" is a weaker and much flakier statement than "did the
     * alarm fire", and the alarm is the thing that was added.
     */
    public boolean aiIsDefending() {
        return aiDefendTimer > 0;
    }

    private void aiUpdate(float dt) {
        aiMinerals += aiIncome * dt;
        aiIncome = 0;
        int workers = 0, combat = 0;
        Ent hatchery = null;
        for (Ent e : ents) {
            if (e.team != 1 || !e.alive()) continue;
            if (e.type.key.equals("drone")) workers++;
            if (e.isBuilding() && e.type.key.equals("hatchery")) hatchery = e;
            if (!e.isBuilding()) combat++;
        }
        // income: pretend drones mine (difficulty scaling). v2.7 9.3: a mission
        // board has no placeholder drones -- the scripted start units are all
        // combat -- so the worker term is zero and the AI would starve. Give a
        // mission enemy a base income instead, scaled by difficulty.
        float mul = difficulty == 0 ? 0.6f : difficulty == 1 ? 1f : 1.5f;
        aiIncome = workers * 11f * mul;
        if (mission != null) aiIncome += 90f * mul;

        // build army periodically
        aiBuildTimer -= dt;
        int queueCap = difficulty == 0 ? 2 : difficulty == 1 ? 3 : 4;
        if (aiBuildTimer <= 0 && hatchery != null && hatchery.queue.size() < queueCap) {
            aiBuildTimer = difficulty == 0 ? 8f : difficulty == 1 ? 6f : 4.5f;
            String pick;
            int roll = rnd.nextInt(100);
            if (mission != null && !mission.aiWaves.isEmpty()) {
                // v2.7 9.3: a mission dictates its own wave composition, so the
                // progression is authored (lings -> hydras -> mixed) instead of
                // the skirmish random weighting.
                String[] plan = mission.aiWaves.get(
                        Math.min(mission.aiWaves.size() - 1, aiWave));
                pick = plan[roll % plan.length];
            } else {
                pick = aiPick(time, aiWave, roll);
            }
            Type t = TYPES.get(pick);
            int cost = pick.equals("zergling") ? 50 : t.cost;
            if (aiMinerals >= cost) {
                aiMinerals -= cost;
                hatchery.queue.add(pick);
            }
        }

        // attack waves
        aiWaveTimer -= dt;
        if (aiWaveTimer <= 20f && aiWaveTimer + dt > 20f && hatchery != null) {
            // v2.7 9.3: 20 s heads-up before a wave, so an incoming push is
            // announced rather than only noticed once the base is on fire.
            events.add(new Object[]{"mission_msg", "警报:虫群接近"});
            events.add(new Object[]{"alert", hatchery.x, hatchery.y});
        }
        if (aiWaveTimer <= 0 && hatchery != null) {
            aiWave++;
            aiWaveTimer = (difficulty == 0 ? 85f : difficulty == 1 ? 62f : 45f) + aiWave * 4f;
            int attackers = 0;
            float[] target = findPlayerStart();
            for (Ent e : ents) {
                if (e.team == 1 && !e.isBuilding() && e.alive()
                        && !offField(e)
                        && !e.type.key.equals("drone")) {
                    e.target = null;
                    // v2.43 P0-c: THE spike this whole pass exists for. One
                    // wave hands the same destination to every attacker, so
                    // this used to be one A* per attacker inside a single
                    // frame. Queued, it drains PATH_BUDGET per tick.
                    queuePath(e, target[0], target[1]);
                    e.aiTimer = -1;   // attack-move
                    e.waveUnit = true;
                    attackers++;
                }
            }
            // v2.14 batch 1.6: remember how big the push was, so the retreat
            // test below can measure it against what is still standing. Only
            // WAVE-TAGGED units count towards it -- the AI keeps producing
            // units at home, and if those counted too the army would never look
            // like it had shrunk and the AI would never retreat.
            aiWaveStrength = attackers;
        }

        // v2.14 batch 1.6: defence recall. A hit on an AI structure (see
        // alertIfAi) pulls the standing army home for a few seconds. It only
        // fires while the wave is NOT already marching -- once the army is
        // committed, turning it around on every stray shot would mean it never
        // arrives anywhere.
        if (aiDefendTimer > 0) {
            aiDefendTimer -= dt;
            if (!aiDefendIssued) {
                aiDefendIssued = true;
                for (Ent e : ents) {
                    if (e.team != 1 || e.isBuilding() || !e.alive()) continue;
                    if (e.type.key.equals("drone")) continue;
                    if (e.aiTimer < 0) continue;   // already attack-moving
                    // v2.43 P0-c: budgeted -- recall also commands the whole
                    // standing army at once.
                    queuePath(e, aiDefendX, aiDefendY);
                    e.target = null;
                }
            }
            if (aiDefendTimer <= 0) aiDefendIssued = false;
        }

        // v2.14 batch 1.6: retreat. If the committed wave has lost more than
        // 60% of its strength, break off and rebuild instead of feeding the
        // rest of it in one unit at a time. This is what stops a losing AI from
        // trickling to its death, and it is the behaviour the plan's assertion
        // names.
        //
        // The baseline is the count taken when the wave launched and it is NOT
        // refreshed while the wave is out: re-baselining every frame would make
        // the ratio always 100% and the AI would never notice its losses. It is
        // cleared on retreat and re-armed by the next launch.
        if (aiWaveStrength > 0) {
            int left = 0;
            for (Ent e : ents) {
                if (e.team == 1 && e.waveUnit && e.alive()) left++;
            }
            if (left * 10 < aiWaveStrength * 4) {   // lost > 60%
                aiWaveStrength = 0;
                aiWaveTimer = Math.max(aiWaveTimer, 25f);
                for (Ent e : ents) {
                    if (e.team != 1 || e.isBuilding() || !e.alive()) continue;
                    if (!e.waveUnit) continue;
                    e.waveUnit = false;
                    e.aiTimer = 0;
                    e.target = null;
                    if (hatchery != null) {
                        // v2.43 P0-c: budgeted -- the retreating wave all turns
                        // for home in the same tick.
                        queuePath(e, hatchery.x + rnd.nextInt(120) - 60,
                                hatchery.y + 110);
                    }
                }
                if (hatchery != null) {
                    events.add(new Object[]{"alert", hatchery.x, hatchery.y});
                }
            }
        }

        // v2.14 batch 1.6: the AI casts. Throttled to twice a second because
        // target selection scans every entity and the decision does not change
        // that fast. The whole point of this pass is that the AI must respect
        // its own mechanics -- it will not storm its own swarm, will not cast a
        // biological-only spell at a machine, and will not waste EMP on a race
        // with no shields.
        aiSpellTimer -= dt;
        if (aiSpellTimer <= 0) {
            aiSpellTimer = 0.5f;
            aiCastSpells();
        }

        // v2.14 batch 1.6: walk this race's structure ladder.
        aiBuildStructures(dt);

        // drain hatchery queue into units
        if (hatchery != null && hatchery.buildProgress >= 1 && !hatchery.queue.isEmpty()) {
            // v2.7 9.5: difficulty scales the drain as well as the queue, or the
            // per-unit buildTime caps every tier at the same output.
            float speed = difficulty == 0 ? 0.75f : difficulty == 1 ? 1f : 1.4f;
            hatchery.queueProgress += dt * speed;
            if (hatchery.queueProgress >= TYPES.get(hatchery.queue.get(0)).buildTime) {
                String key = hatchery.queue.remove(0);
                hatchery.queueProgress = 0;
                Ent u = spawn(key, 1, hatchery.x, hatchery.y + 90, true);
                // v2.7 9.3: the enemy upgrades on a fixed ladder by difficulty
                // so a hard AI keeps pace with a player who is teching up.
                //
                // v2.44: both the altitude nudge and the gather order moved
                // INSIDE this null check. spawn() returns null when the unit
                // cannot be placed (supply blocked, footprint occupied), and
                // these two lines used to sit outside it -- so any blocked
                // spawn threw a NullPointerException from inside the game loop.
                if (u != null) {
                    // v2.28: the AI's ladder is per class like the player's, so
                    // a hard AI's hydralisks and mutalisks no longer share one
                    // number. (The AI is zerg, so its lines are melee/ranged/
                    // carapace in the original; here they map onto the same
                    // three tags.)
                    int tier = difficulty == 0 ? 0 : difficulty == 1 ? 1 : 2;
                    u.dmgBonus = tier * 2;
                    u.armorBonus = tier;
                    if (u.type.flying) u.y -= 40;
                    // idle army gathers near base
                    setPath(u, hatchery.x + rnd.nextInt(160) - 80,
                            hatchery.y + 120 + rnd.nextInt(60));
                }
            }
        }
    }



    private void updateAIFrame(float dt) {
        // unused
    }

    // ------------------------------------- v2.14 batch 1.6: AI spell casting
    /**
     * The AI's spell pass. It walks its own casters and, for each, asks the
     * same error gate the player's command card uses -- which is the point:
     * the AI cannot do anything a player could not, and any rule added to a
     * castXxx gate is respected by the AI for free.
     *
     * The one place it needs an extra judgement is target selection, and there
     * the AI has to respect the MECHANICS, not just the legality: it will not
     * drop a storm on ground its own swarm is covering (the swarm eats the
     * storm, so the cast is simply wasted), and it will not fire a
     * biological-only spell into a mechanical target.
     */
    private void aiCastSpells() {
        for (Ent e : ents) {
            if (e.team != 1 || !e.alive() || e.isBuilding()) continue;
            if (offField(e)) continue;    // v2.23: cargo does not cast
            String k = e.type.key;
            if (k.equals("templar")) {
                if (e.stormCd > 0) continue;
                float[] spot = bestEnemyCluster(e, 3, SPELL_RANGE);
                if (spot == null) continue;
                // Respect our own swarm: a storm under a cloud we laid does
                // nothing, so hold the cast rather than burn the cooldown.
                if (underDswarmFor(spot[0], spot[1], 1)) continue;
                castStorm(e, spot[0], spot[1]);
            } else if (k.equals("defiler")) {
                if (e.dswarmCd > 0) continue;
                // Swarm goes on our OWN army, just ahead of it.
                float[] me = ownArmyCentre(e);
                if (me == null) continue;
                castDswarm(e, me[0], me[1]);
            } else if (k.equals("vessel")) {
                // EMP only pays against shields; skip it entirely against zerg.
                if (e.empCd <= 0) {
                    float[] spot = bestEnemyCluster(e, 2, SPELL_RANGE);
                    if (spot != null && anyShieldNear(spot[0], spot[1], EMP_RADIUS)) {
                        castEmp(e, spot[0], spot[1]);
                        continue;
                    }
                }
                // Irradiate wants the fattest biological target it can reach.
                if (e.empCd <= 0) {
                    Ent bio = bestBiologicalInRange(e, SPELL_RANGE);
                    if (bio != null) castIrradiate(e, bio);
                }
            } else if (k.equals("battlecruiser")) {
                if (e.yamatoCd > 0) continue;
                Ent hard = toughestEnemyInRange(e, SPELL_RANGE);
                if (hard != null) castYamato(e, hard);
            } else if (k.equals("ghost")) {
                if (e.lockdownCd > 0) continue;
                Ent mech = bestMechanicalInRange(e, SPELL_RANGE);
                if (mech != null) castLockdown(e, mech);
            } else if (k.equals("corsair")) {
                if (e.dwebCd > 0) continue;
                // The web is a placement puzzle: drop it on the enemy's ranged
                // blob. It silences our own units too, so only worth it when
                // there is a cluster to catch.
                float[] spot = bestEnemyCluster(e, 3, SPELL_RANGE);
                if (spot != null) castDweb(e, spot[0], spot[1]);
            }

            // v2.23 batch 0: the personal cloak. The ghost and the wraith were
            // already gated on their energy pool, but nothing ever spent it on
            // hiding -- the AI only ever locked down. Cloaking when an enemy is
            // in weapon range and the pool can afford it (with 40 held back, so
            // a cloak never eats the last of the energy a spell needs) is what
            // makes an AI ghost read as a ghost. It is deliberately a separate
            // branch from the spell above: a ghost may want to do both, and the
            // cast pass should not have to choose.
            if ((k.equals("ghost") || k.equals("wraith")) && !e.cloakOn
                    && e.energy >= CLOAK_COST + 40f) {
                Ent near = findEnemyInRange(e, e.type.range + 40f);
                if (near != null) toggleCloak(e);
            }
        }
    }

    /**
     * The densest enemy clump within `range` of `e`, as {x, y}, or null when
     * fewer than `min` enemies are inside the spell's radius anywhere near.
     * This is deliberately the same "count them, then aim at the middle"
     * heuristic a player uses, not an optimiser.
     */
    private float[] bestEnemyCluster(Ent e, int min, float range) {
        float[] best = null;
        int bestCount = min - 1;
        for (Ent o : ents) {
            if (o.team == e.team || !o.alive() || o.constructing) continue;
            if (offField(o)) continue;    // v2.23
            if (o.cloakActive && !o.spotted) continue;   // v2.22: AI cannot see cloak
            if (dist(e, o) > range) continue;
            int count = 0;
            float sx = 0, sy = 0;
            for (Ent p : ents) {
                if (p.team == e.team || !p.alive() || p.constructing) continue;
                if (offField(p)) continue;    // v2.23
                if (p.cloakActive && !p.spotted) continue;   // v2.22
                float dx = p.x - o.x, dy = p.y - o.y;
                if (dx * dx + dy * dy <= STORM_RADIUS * STORM_RADIUS) {
                    count++;
                    sx += p.x;
                    sy += p.y;
                }
            }
            if (count > bestCount) {
                bestCount = count;
                best = new float[]{sx / count, sy / count};
            }
        }
        return best;
    }

    /** Centre of mass of the AI's own mobile army, or null if it has none. */
    private float[] ownArmyCentre(Ent around) {
        float sx = 0, sy = 0;
        int n = 0;
        for (Ent o : ents) {
            if (o.team != 1 || !o.alive() || o.isBuilding() || o.constructing) continue;
            if (offField(o)) continue;    // v2.23
            if (o.type.key.equals("drone") || o.type.key.equals("defiler")) continue;
            if (dist(around, o) > 260f) continue;
            sx += o.x;
            sy += o.y;
            n++;
        }
        if (n == 0) return null;
        return new float[]{sx / n, sy / n};
    }

    private boolean anyShieldNear(float x, float y, float r) {
        for (Ent o : ents) {
            if (!o.alive() || o.type.shield <= 0 || o.shield <= 0) continue;
            if (offField(o)) continue;    // v2.23
            float dx = o.x - x, dy = o.y - y;
            if (dx * dx + dy * dy <= r * r) return true;
        }
        return false;
    }

    private Ent bestBiologicalInRange(Ent e, float range) {
        Ent best = null;
        int bestHp = -1;
        for (Ent o : ents) {
            if (o.team == e.team || !o.alive() || o.constructing) continue;
            if (offField(o)) continue;    // v2.23
            if (o.cloakActive && !o.spotted) continue;   // v2.22: AI cannot see cloak
            if (!isBiological(o)) continue;
            if (dist(e, o) > range) continue;
            if (o.hp > bestHp) {
                bestHp = o.hp;
                best = o;
            }
        }
        return best;
    }

    private Ent bestMechanicalInRange(Ent e, float range) {
        Ent best = null;
        int bestHp = -1;
        for (Ent o : ents) {
            if (o.team == e.team || !o.alive() || o.constructing) continue;
            if (offField(o)) continue;    // v2.23
            if (o.cloakActive && !o.spotted) continue;   // v2.22: AI cannot see cloak
            if (!isMechanical(o)) continue;
            if (dist(e, o) > range) continue;
            if (o.hp > bestHp) {
                bestHp = o.hp;
                best = o;
            }
        }
        return best;
    }

    private Ent toughestEnemyInRange(Ent e, float range) {
        Ent best = null;
        int bestHp = -1;
        for (Ent o : ents) {
            if (o.team == e.team || !o.alive() || o.constructing) continue;
            if (offField(o)) continue;    // v2.23
            if (o.cloakActive && !o.spotted) continue;   // v2.22: AI cannot see cloak
            if (dist(e, o) > range) continue;
            if (o.hp + o.shield > bestHp) {
                bestHp = o.hp + o.shield;
                best = o;
            }
        }
        return best;
    }

    // ------------------------------------- v2.14 batch 1.6: AI build orders
    /**
     * Each race's structure ladder, in the order the AI builds them. The three
     * lists are deliberately different shapes, not the same list renamed: the
     * zerg ladder is short and defensive (pool, sunken, spire), the terran one
     * is the longest tech chain in the game (barracks -> factory -> starport ->
     * science facility), and the protoss one has to start with a pylon because
     * everything else needs the supply.
     */
    public static String[] aiBuildOrder(int race) {
        if (race == 0) {
            return new String[]{"barracks", "academy", "factory", "starport",
                    "sciencefac", "armory", "turret"};
        }
        if (race == 2) {
            return new String[]{"pylon", "gateway", "gencore", "citadel",
                    "archives", "robotic", "stargate", "beacon", "photon"};
        }
        return new String[]{"pool", "sunken", "spire", "hydraden"};
    }

    /**
     * The AI's builder. It does not walk a worker to a site the way a player
     * does -- it places the structure directly and pays for it out of
     * aiMinerals, which is the same shortcut the wave spawner already takes.
     * The interesting part is the LADDER: it walks its race's list in order,
     * one structure at a time, and only advances the index when the placement
     * succeeds.
     */
    private void aiBuildStructures(float dt) {
        if (aiTechTier >= aiBuildOrder(aiRace).length) return;
        aiTechTimer -= dt;
        if (aiTechTimer > 0) return;
        String[] ladder = aiBuildOrder(aiRace);
        String key = ladder[aiTechTier];
        Type t = TYPES.get(key);
        if (t == null) {
            aiTechTier++;
            return;
        }
        if (aiMinerals < t.cost) {
            aiTechTimer = 5f;
            return;
        }
        // Anchor the new structure on the AI base and spiral outward until a
        // spot passes canPlace, so a crowded base does not stall the ladder.
        float[] base = findEnemyBase();
        if (base == null) return;
        for (int ring = 1; ring <= 6; ring++) {
            for (int i = 0; i < 8; i++) {
                double ang = i * Math.PI / 4;
                float x = clamp(base[0] + (float) Math.cos(ang) * ring * 90f, 40, wPx - 40);
                float y = clamp(base[1] + (float) Math.sin(ang) * ring * 90f, 40, hPx - 40);
                if (!canPlace(key, x, y)) continue;
                aiMinerals -= t.cost;
                Ent b = spawn(key, 1, x, y, true);
                if (b != null) {
                    aiTechTier++;
                    aiTechTimer = 12f;
                    return;
                }
            }
        }
        aiTechTimer = 4f;
    }

    /** Map loader data: kind 1 = mineral (with variant), 2 = geyser. */
    public static List<Object[]> parseMapUnits(String metaText) {
        List<Object[]> out = new ArrayList<>();
        for (String line : metaText.split("\n")) {
            line = line.trim();
            if (!line.startsWith("unit=")) continue;
            String[] p = line.substring(5).split(",");
            int u = Integer.parseInt(p[0]);
            float x = Float.parseFloat(p[1]);
            float y = Float.parseFloat(p[2]);
            Object[] row = u == 1
                    ? new Object[]{1, x, y, Integer.parseInt(p.length > 5 ? p[5] : "0")}
                    : new Object[]{2, x, y, 0};
            out.add(row);
        }
        return out;
    }

    public static List<int[]> parseStarts(String metaText) {
        List<int[]> out = new ArrayList<>();
        for (String line : metaText.split("\n")) {
            line = line.trim();
            if (!line.startsWith("start=")) continue;
            String[] p = line.substring(6).split(",");
            out.add(new int[]{Integer.parseInt(p[0]), Integer.parseInt(p[1])});
        }
        return out;
    }

    // ----------------------------------------------------------- save / load
    // Line-based text so a save stays diffable and survives repack hiccups.
    // References between entities (attack target, mine target, refinery) are
    // stored as list indices and resolved on load.

    public String serialize() {
        StringBuilder sb = new StringBuilder(1 << 16);
        sb.append("XJZB-SAVE-1\n");
        sb.append("state ").append(mineralsPlayer).append(' ').append(gasPlayer)
                .append(' ').append(time).append(' ').append(difficulty)
                .append(' ').append(aiMinerals).append(' ').append(aiWaveTimer)
                .append(' ').append(aiWave).append(' ').append(aiBuildTimer)
                .append(' ').append(kills).append(' ').append(losses)
                .append(' ').append(mineralsMined).append(' ').append(gasMined)
                .append(' ').append(weaponLevel).append(' ').append(armorLevel)
                .append(' ').append(race)
                .append(' ').append(capTier)
                // v2.28: the per-class upgrade levels, one token per line
                // ("w0,w1,w2;a0,a1,a2"). Appended last so a v2.27 save still
                // loads (it stops at capTier and keeps the arrays at 0).
                .append(' ').append(joinInts(weaponByClass))
                .append(' ').append(joinInts(armorByClass))
                .append('\n');
        sb.append("fog ");
        for (byte b : fog) {
            sb.append(Character.forDigit((b >> 4) & 15, 16));
            sb.append(Character.forDigit(b & 15, 16));
        }
        sb.append('\n');
        for (Ent e : ents) {
            sb.append("e ").append(e.type.key).append(' ').append(e.team)
                    .append(' ').append(e.x).append(' ').append(e.y)
                    .append(' ').append(e.hp).append(' ').append(e.cd)
                    .append(' ').append(e.facing).append(' ').append(e.dir)
                    .append(' ').append(e.selected ? 1 : 0)
                    .append(' ').append(e.moving ? 1 : 0)
                    .append(' ').append(e.goalX).append(' ').append(e.goalY)
                    .append(' ').append(e.workerState).append(' ').append(e.carrying)
                    .append(' ').append(e.haulingGas ? 1 : 0)
                    .append(' ').append(e.queue.isEmpty() ? "-" : join(e.queue, ";"))
                    .append(' ').append(e.queueProgress)
                    .append(' ').append(e.rallyX).append(' ').append(e.rallyY)
                    .append(' ').append(e.buildProgress)
                    .append(' ').append(e.constructing ? 1 : 0)
                    .append(' ').append(e.aiTimer).append(' ').append(e.flashTime)
                    .append(' ').append(e.patrolling ? 1 : 0)
                    .append(' ').append(e.patrolAX).append(' ').append(e.patrolAY)
                    .append(' ').append(e.patrolBX).append(' ').append(e.patrolBY)
                    .append(' ').append(indexOf(ents, e.target))
                    .append(' ').append(indexOfMineral(e.mineTarget))
                    .append(' ').append(e.stimTime)
                    .append(' ').append(e.dmgBonus).append(' ').append(e.armorBonus)
                    // v2.10: shield state. Appended last so a v2.9 save still
                    // parses (the reader length-checks each new field).
                    .append(' ').append(e.shield).append(' ').append(e.shieldDelay)
                    .append(' ').append(e.stormCd)
                    // v2.23: the cargo / garrison links. Both are stored as
                    // entity indices, like target and mineTarget, so a save
                    // round-trips a loaded shuttle and a full bunker exactly.
                    .append(' ').append(indexOf(ents, e.cargoOf))
                    .append(' ').append(indexOf(ents, e.bunker))
                    .append('\n');
        }
        for (Mineral m : minerals) {
            sb.append("m ").append(m.x).append(' ').append(m.y).append(' ')
                    .append(m.amount).append(' ').append(m.variant).append(' ')
                    .append(indexOf(ents, m.refinery)).append('\n');
        }
        return sb.toString();
    }

    /** Restore a saved state into this (same-map) instance. Returns success. */
    public boolean deserialize(String s) {
        if (s == null || !s.startsWith("XJZB-SAVE-1")) return false;
        try {
            // undo any footprint a saved building will re-occupy
            System.arraycopy(walk0, 0, walk, 0, walk.length);
            java.util.Arrays.fill(fog, (byte) 0);
            ents.clear();
            clearPathQueue();            // v2.43 P0-c
            invalidateAuraCounts();      // v2.43 P0-a
            minerals.clear();
            markers.clear();
            corpses.clear();
            anims.clear();
            effects.clear();
            shots.clear();
            storms.clear();
            groups.clear();

            List<Ent> loaded = new ArrayList<>();
            List<int[]> entRefs = new ArrayList<>();      // target, mine per ent
            List<int[]> minRefs = new ArrayList<>();      // refinery per mineral
            List<int[]> cargoRefs = new ArrayList<>();    // v2.23: carrier, bunker
            for (String raw : s.split("\n")) {
                String line = raw.trim();
                if (line.isEmpty()) continue;
                String[] p = line.split(" ");
                switch (p[0]) {
                    case "state":
                        mineralsPlayer = Integer.parseInt(p[1]);
                        gasPlayer = Integer.parseInt(p[2]);
                        time = Float.parseFloat(p[3]);
                        difficulty = Integer.parseInt(p[4]);
                        aiMinerals = Integer.parseInt(p[5]);
                        aiWaveTimer = Float.parseFloat(p[6]);
                        aiWave = Integer.parseInt(p[7]);
                        aiBuildTimer = Float.parseFloat(p[8]);
                        // v2.7: scoreboard counters. Older saves stop at p[8];
                        // default them so a v2.6 save still loads.
                        if (p.length > 9) {
                            kills = Integer.parseInt(p[9]);
                            losses = Integer.parseInt(p[10]);
                            mineralsMined = Integer.parseInt(p[11]);
                            gasMined = Integer.parseInt(p[12]);
                        }
                        if (p.length > 13) {
                            weaponLevel = Integer.parseInt(p[13]);
                            armorLevel = Integer.parseInt(p[14]);
                        }
                        // v2.8: race travels with the save. A v2.7 save has no
                        // p[15], so it keeps the constructor default (terran).
                        if (p.length > 15) race = p[15];
                        // v2.27: the supply tier. Older saves stop at p[15]
                        // and keep tier 0 (the original 40 ceiling).
                        if (p.length > 16) capTier = Integer.parseInt(p[16]);
                        // v2.28: the per-class levels. A v2.27 save stops at
                        // p[16] and keeps every line at 0.
                        if (p.length > 17) parseInts(p[17], weaponByClass);
                        if (p.length > 18) parseInts(p[18], armorByClass);
                        status = "";
                        break;
                    case "fog": {
                        String hx = p[1];
                        for (int i = 0; i < fog.length && 2 * i + 1 < hx.length(); i++)
                            fog[i] = (byte) ((Character.digit(hx.charAt(2 * i), 16) << 4)
                                    | Character.digit(hx.charAt(2 * i + 1), 16));
                        break;
                    }
                    case "e": {
                        Ent e = new Ent();
                        e.type = TYPES.get(p[1]);
                        if (e.type == null) return false;
                        e.team = Integer.parseInt(p[2]);
                        e.x = Float.parseFloat(p[3]);
                        e.y = Float.parseFloat(p[4]);
                        e.hp = Integer.parseInt(p[5]);
                        e.cd = Float.parseFloat(p[6]);
                        e.facing = Float.parseFloat(p[7]);
                        e.dir = Integer.parseInt(p[8]);
                        e.selected = "1".equals(p[9]);
                        e.moving = "1".equals(p[10]);
                        e.goalX = Float.parseFloat(p[11]);
                        e.goalY = Float.parseFloat(p[12]);
                        e.workerState = Integer.parseInt(p[13]);
                        e.carrying = Integer.parseInt(p[14]);
                        e.haulingGas = "1".equals(p[15]);
                        if (!p[16].equals("-"))
                            e.queue.addAll(Arrays.asList(p[16].split(";")));
                        e.queueProgress = Float.parseFloat(p[17]);
                        e.rallyX = Float.parseFloat(p[18]);
                        e.rallyY = Float.parseFloat(p[19]);
                        e.buildProgress = Float.parseFloat(p[20]);
                        e.constructing = "1".equals(p[21]);
                        e.aiTimer = Float.parseFloat(p[22]);
                        e.flashTime = Float.parseFloat(p[23]);
                        e.patrolling = "1".equals(p[24]);
                        e.patrolAX = Float.parseFloat(p[25]);
                        e.patrolAY = Float.parseFloat(p[26]);
                        e.patrolBX = Float.parseFloat(p[27]);
                        e.patrolBY = Float.parseFloat(p[28]);
                        entRefs.add(new int[]{Integer.parseInt(p[29]),
                                Integer.parseInt(p[30])});
                        if (p.length > 31) {
                            e.stimTime = Float.parseFloat(p[31]);
                            e.dmgBonus = Integer.parseInt(p[32]);
                            e.armorBonus = Integer.parseInt(p[33]);
                        }
                        // v2.10: shield state. A pre-v2.10 save has no such
                        // column, and a protoss unit loaded from one must not
                        // come back shield-less forever (regen would top it up
                        // anyway, but only after three seconds of being shot
                        // at), so a missing column means "spawn with a full
                        // shield" rather than "spawn with none".
                        if (p.length > 35) {
                            e.shield = Integer.parseInt(p[34]);
                            e.shieldDelay = Float.parseFloat(p[35]);
                        } else {
                            e.shield = e.type.shield;
                        }
                        // v2.10: storm cooldown rides behind the shield pair.
                        // A missing column means "ready to cast", which is what
                        // a templar that was saved mid-cooldown would otherwise
                        // silently lose.
                        if (p.length > 36) e.stormCd = Float.parseFloat(p[36]);
                        // v2.23: the cargo / garrison links. A pre-v2.23 save
                        // has neither column, and a missing one means "on the
                        // field", which is what every older unit was.
                        if (p.length > 38)
                            cargoRefs.add(new int[]{Integer.parseInt(p[37]),
                                    Integer.parseInt(p[38])});
                        else
                            cargoRefs.add(new int[]{-1, -1});
                        // v2.17: selfBuilding is a pure function of the race and
                        // the entity kind, so it is recomputed rather than saved
                        // (a v2.16 save needs no new column).
                        e.selfBuilding = e.isBuilding() && !"terran".equals(race);
                        loaded.add(e);
                        if (e.isBuilding()) occupyFootprint(e, true);
                        break;
                    }
                    case "m": {
                        Mineral m = new Mineral();
                        m.x = Float.parseFloat(p[1]);
                        m.y = Float.parseFloat(p[2]);
                        m.amount = Integer.parseInt(p[3]);
                        m.variant = Integer.parseInt(p[4]);
                        minRefs.add(new int[]{Integer.parseInt(p[5])});
                        minerals.add(m);
                        break;
                    }
                    default:
                        break;      // unknown row: skip forward-compatibly
                }
            }
            ents.addAll(loaded);
            invalidateAuraCounts();      // v2.43 P0-a
            for (int i = 0; i < loaded.size(); i++) {
                Ent e = loaded.get(i);
                int t = entRefs.get(i)[0];
                e.target = (t >= 0 && t < loaded.size()) ? loaded.get(t) : null;
                int mi = entRefs.get(i)[1];
                e.mineTarget = (mi >= 0 && mi < minerals.size()) ? minerals.get(mi) : null;
                if (e.moving) setPath(e, e.goalX, e.goalY);
            }
            // v2.23: rebuild the carrier / bunker relations and the cargo
            // lists they point into. Done after every entity exists, which is
            // why it cannot ride the parse loop above.
            for (int i = 0; i < loaded.size(); i++) {
                int ci = cargoRefs.get(i)[0];
                int bi = cargoRefs.get(i)[1];
                Ent e = loaded.get(i);
                if (ci >= 0 && ci < loaded.size()) {
                    e.cargoOf = loaded.get(ci);
                    e.cargoOf.cargo.add(e);
                }
                if (bi >= 0 && bi < loaded.size()) {
                    e.bunker = loaded.get(bi);
                    e.garrisoned = true;
                    e.bunker.cargo.add(e);
                }
            }
            for (int i = 0; i < minerals.size(); i++) {
                int r = minRefs.get(i)[0];
                minerals.get(i).refinery =
                        (r >= 0 && r < loaded.size()) ? loaded.get(r) : null;
            }
            return true;
        } catch (Exception ex) {
            return false;      // a corrupt save must never crash the game thread
        }
    }

    private static String join(List<String> parts, String sep) {
        StringBuilder sb = new StringBuilder();
        for (String s : parts) {
            if (sb.length() > 0) sb.append(sep);
            sb.append(s);
        }
        return sb.toString();
    }

    private static int indexOf(List<Ent> list, Ent e) {
        if (e == null) return -1;
        for (int i = 0; i < list.size(); i++) if (list.get(i) == e) return i;
        return -1;
    }

    private int indexOfMineral(Mineral m) {
        if (m == null) return -1;
        for (int i = 0; i < minerals.size(); i++) if (minerals.get(i) == m) return i;
        return -1;
    }
}
