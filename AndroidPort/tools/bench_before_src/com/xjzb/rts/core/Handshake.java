package com.xjzb.rts.core;

/**
 * v2.32: the opening handshake. Before a single turn is played, both machines
 * must agree on what they are about to play. A mismatch that is discovered
 * after the match starts is a desync with no explanation; a mismatch refused
 * up front is a sentence the player can act on.
 *
 * Three fields are fatal, and each is fatal for a specific reason:
 *
 *  - version  -- two builds can simulate differently, so their command streams
 *                are not the same language;
 *  - map      -- two different maps means two different simulations from turn
 *                zero;
 *  - players  -- the turn gate needs the same N on both sides, or one machine
 *                waits for a report that the other never sends;
 *  - seed     -- the AI's random sequence is seeded, so a different seed is a
 *                different enemy even with identical orders.
 *
 * race and difficulty are carried for the record and a mismatch is a warning,
 * not a refusal: the race already reaches Game through the map/mission path, and
 * a player who picked a different difficulty is making a choice, not a bug.
 */
public final class Handshake {

    public String version = "";
    public String map = "";
    public int players = 2;
    public long seed = 12345L;
    public String race = "terran";
    public int difficulty = 1;

    public Handshake() {
    }

    public Handshake(String version, String map, int players, long seed,
                     String race, int difficulty) {
        this.version = version;
        this.map = map;
        this.players = players;
        this.seed = seed;
        this.race = race;
        this.difficulty = difficulty;
    }

    /** Wire form: "H version <v> map <m> players <n> seed <s> race <r> diff <d>". */
    public String encode() {
        return "H version " + version + " map " + map + " players " + players
                + " seed " + seed + " race " + race + " difficulty " + difficulty;
    }

    /**
     * Parse a handshake line. Tolerant like the rest of the wire format: a
     * malformed line yields null, and an unknown token is skipped so a future
     * build can add a field without breaking an older peer.
     */
    public static Handshake decode(String line) {
        if (line == null) return null;
        String s = line.trim();
        if (!s.startsWith("H ")) return null;
        String[] t = s.substring(2).split(" ");
        Handshake h = new Handshake();
        try {
            for (int i = 0; i + 1 < t.length; i += 2) {
                String k = t[i], v = t[i + 1];
                if (k.equals("version")) h.version = v;
                else if (k.equals("map")) h.map = v;
                else if (k.equals("players")) h.players = Integer.parseInt(v);
                else if (k.equals("seed")) h.seed = Long.parseLong(v);
                else if (k.equals("race")) h.race = v;
                else if (k.equals("difficulty")) h.difficulty = Integer.parseInt(v);
            }
        } catch (NumberFormatException e) {
            return null;
        }
        return h;
    }

    /**
     * Compare a peer's handshake against mine. Returns null when the match may
     * start, otherwise a message naming the field that disagreed -- naming it is
     * the whole point, because "could not connect" tells the player nothing.
     */
    public String reject(Handshake peer) {
        if (peer == null) return "握手数据无法解析";
        if (!version.equals(peer.version))
            return "版本不一致:本机 " + version + ",对面 " + peer.version;
        if (!map.equals(peer.map))
            return "地图不一致:本机 " + map + ",对面 " + peer.map;
        if (players != peer.players)
            return "人数不一致:本机 " + players + ",对面 " + peer.players;
        if (seed != peer.seed)
            return "随机种子不一致:本机 " + seed + ",对面 " + peer.seed;
        return null;
    }

    /** A non-fatal difference worth showing, or null. */
    public String warn(Handshake peer) {
        if (peer == null) return null;
        if (!race.equals(peer.race)) return "族不同:" + race + " vs " + peer.race;
        if (difficulty != peer.difficulty)
            return "难度不同:" + difficulty + " vs " + peer.difficulty;
        return null;
    }
}