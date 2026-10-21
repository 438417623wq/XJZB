package com.xjzb.rts.core;

/**
 * v2.33: the broadcast a host puts on the LAN so a joiner can find it.
 *
 * The payload is one line of text, framed exactly like the command stream
 * (see LockstepStream): a newline-terminated UTF-8 line. Reusing the framing is
 * not laziness -- it means a capture of discovery traffic and a capture of the
 * match read the same way, and a beacon can be logged or diffed like a replay.
 *
 * Filtering is by IGNORING, never by erroring. The broadcast domain will carry
 * other people's rooms, older builds and plain unrelated UDP traffic, so
 * anything that is not a well-formed beacon of this version is simply not a
 * room. A parser that threw here would take the lobby down every time a
 * colleague's phone joined the wifi.
 */
public final class LanBeacon {

    /** Protocol tag. A beacon without it is not ours, whatever else it says. */
    public static final String TAG = "XJZB-LAN-1";

    public String host = "";
    public String map = "";
    public int players = 2;
    public int port = 0;
    public String version = "";
    public long seed = 12345L;
    public int difficulty = 1;

    public LanBeacon() {
    }

    public LanBeacon(String host, String map, int players, int port,
                     String version, long seed, int difficulty) {
        this.host = host;
        this.map = map;
        this.players = players;
        this.port = port;
        this.version = version;
        this.seed = seed;
        this.difficulty = difficulty;
    }

    public String encode() {
        return TAG + " host " + host + " map " + map + " players " + players
                + " port " + port + " version " + version + " seed " + seed
                + " difficulty " + difficulty;
    }

    /**
     * Parse one beacon line. Returns null for anything that is not a beacon of
     * this build -- wrong tag, missing fields, unparseable numbers. Never
     * throws: the caller is a listener on a shared network.
     */
    public static LanBeacon decode(String line) {
        if (line == null) return null;
        String s = line.trim();
        if (!s.startsWith(TAG + " ")) return null;
        String[] t = s.substring(TAG.length() + 1).split(" ");
        LanBeacon b = new LanBeacon();
        boolean sawHost = false;
        try {
            for (int i = 0; i + 1 < t.length; i += 2) {
                String k = t[i], v = t[i + 1];
                if (k.equals("host")) { b.host = v; sawHost = true; }
                else if (k.equals("map")) b.map = v;
                else if (k.equals("players")) b.players = Integer.parseInt(v);
                else if (k.equals("port")) b.port = Integer.parseInt(v);
                else if (k.equals("version")) b.version = v;
                else if (k.equals("seed")) b.seed = Long.parseLong(v);
                else if (k.equals("difficulty")) b.difficulty = Integer.parseInt(v);
            }
        } catch (NumberFormatException e) {
            return null;
        }
        // A beacon with no host or no map is not a joinable room.
        if (!sawHost || b.host.isEmpty() || b.map.isEmpty()) return null;
        return b;
    }

    /**
     * Is this beacon a room THIS build can join? Version equality is the only
     * hard rule: two builds can simulate differently, so a mismatched room is
     * not a room, it is a trap.
     */
    public boolean joinable(String myVersion) {
        return version != null && version.equals(myVersion) && port > 0
                && players >= 2 && !map.isEmpty();
    }

    /** The handshake this beacon implies, for the joiner to check on connect. */
    public Handshake handshake(String race) {
        return new Handshake(version, map, players, seed, race, difficulty);
    }
}