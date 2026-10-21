package com.xjzb.rts;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import com.xjzb.rts.core.Handshake;
import com.xjzb.rts.core.LanBeacon;
import com.xjzb.rts.core.Lobby;
import com.xjzb.rts.net.LanDiscovery;
import com.xjzb.rts.net.LanHost;
import com.xjzb.rts.net.LanJoin;
import com.xjzb.rts.net.NetSession;
import com.xjzb.rts.net.TcpLink;

import java.util.ArrayList;
import java.util.List;

/**
 * v2.37: the LAN lobby -- host a room, or find one and join it.
 *
 * Deliberately plain Android views rather than a custom surface: everything
 * interesting (who may join, when the match may start, what the handshake
 * rejects) lives in core/ and is asserted on the desktop, so this screen is
 * only a view over those rules and a place to put the numbers. The three
 * failure paths a player actually hits -- no wifi, nothing found, version
 * mismatch -- each get their own sentence instead of a generic "failed".
 */
public class LobbyActivity extends Activity {

    /** Room capacity: 2 for a duel, which is what the lockstep path is proven on. */
    private static final int CAPACITY = 2;

    private Lobby lobby;
    private LanDiscovery discovery;
    private LanHost host;
    private final List<LanBeacon> rooms = new ArrayList<>();
    private LanBeacon joining;
    private LanJoin.Result joined;

    private TextView status;
    private LinearLayout roomList;
    private LinearLayout seatList;
    private Button startBtn;

    private String version() {
        return BuildConfig.VERSION_NAME;
    }

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        lobby = new Lobby(CAPACITY);
        discovery = new LanDiscovery();
        setContentView(buildUi());
        discovery.listen(version(), beacon -> runOnUiThread(() -> addRoom(beacon)));
        refresh();
    }

    // ------------------------------------------------------------------ ui

    private View buildUi() {
        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);
        col.setBackgroundColor(Color.rgb(8, 12, 20));
        col.setPadding(40, 40, 40, 40);

        TextView title = new TextView(this);
        title.setText("局域网对战");
        title.setTextSize(24);
        title.setTextColor(Color.rgb(255, 210, 110));
        col.addView(title);

        status = new TextView(this);
        status.setTextSize(13);
        status.setTextColor(Color.rgb(150, 175, 205));
        status.setPadding(0, 12, 0, 12);
        col.addView(status);

        Button hostBtn = new Button(this);
        hostBtn.setText("开 房");
        hostBtn.setOnClickListener(v -> startHosting());
        col.addView(hostBtn);

        TextView seatsTitle = new TextView(this);
        seatsTitle.setText("座位");
        seatsTitle.setTextColor(Color.rgb(200, 215, 235));
        col.addView(seatsTitle);

        seatList = new LinearLayout(this);
        seatList.setOrientation(LinearLayout.VERTICAL);
        col.addView(seatList);

        startBtn = new Button(this);
        startBtn.setText("开始对战");
        startBtn.setOnClickListener(v -> startMatch());
        col.addView(startBtn);

        TextView roomsTitle = new TextView(this);
        roomsTitle.setText("附近的房间");
        roomsTitle.setTextColor(Color.rgb(200, 215, 235));
        roomsTitle.setPadding(0, 20, 0, 0);
        col.addView(roomsTitle);

        roomList = new LinearLayout(this);
        roomList.setOrientation(LinearLayout.VERTICAL);
        ScrollView sc = new ScrollView(this);
        sc.addView(roomList);
        col.addView(sc, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        return col;
    }

    /** The whole screen is derived, so one call after any state change suffices. */
    private void refresh() {
        seatList.removeAllViews();
        for (int i = 0; i < CAPACITY; i++) {
            Lobby.Slot s = lobby.slots.get(i);
            TextView t = new TextView(this);
            t.setText((i + 1) + " 号位:" + (s.connected
                    ? s.name + (s.ready ? "(已准备)" : "(未准备)") : "空"));
            t.setTextColor(s.connected ? Color.rgb(225, 238, 255)
                    : Color.rgb(110, 125, 145));
            t.setPadding(0, 6, 0, 6);
            seatList.addView(t);
        }
        String why = lobby.blockedReason();
        startBtn.setEnabled(why == null);
        startBtn.setText(why == null ? "开始对战" : "开始对战(" + why + ")");

        roomList.removeAllViews();
        if (rooms.isEmpty()) {
            TextView t = new TextView(this);
            t.setText(host == null ? "正在搜索…(需要与对方在同一 WiFi)"
                    : "正在广播房间,等待对方加入…");
            t.setTextColor(Color.rgb(120, 150, 180));
            roomList.addView(t);
        }
        for (LanBeacon r : rooms) {
            Button btn = new Button(this);
            btn.setText(r.host + " · " + r.map + " · " + r.players + "人");
            btn.setEnabled(joining == null);
            btn.setOnClickListener(v -> joinRoom(r));
            roomList.addView(btn);
        }
    }

    private void addRoom(LanBeacon b) {
        for (LanBeacon r : rooms) {
            if (r.host.equals(b.host) && r.port == b.port) {
                // same room, refreshed beacon: keep the entry current
                r.map = b.map;
                r.players = b.players;
                r.seed = b.seed;
                r.difficulty = b.difficulty;
                return;
            }
        }
        rooms.add(b);
        refresh();
    }

    // ------------------------------------------------------------- hosting

    private void startHosting() {
        if (host != null) return;
        final LanBeacon mine = new LanBeacon(android.os.Build.MODEL, "bloodbath",
                2, 0, version(), System.nanoTime(), 1);
        host = new LanHost(lobby, new LanHost.Room() {
            @Override
            public LanBeacon beacon() {
                return mine;
            }

            @Override
            public String version() {
                return version();
            }
        });
        int port = host.start(new LanHost.Callback() {
            @Override
            public void onConnected(LanHost.Connected c) {
                NetSession.Config cfg = new NetSession.Config();
                cfg.host = true;
                cfg.localPlayer = 0;
                cfg.map = mine.map;
                cfg.players = mine.players;
                cfg.seed = mine.seed;
                cfg.difficulty = mine.difficulty;
                cfg.race = "terran";
                NetSession.install(cfg, c.link, c.peer);
                runOnUiThread(() -> {
                    status.setText("对方已加入,可以开始");
                    refresh();
                });
            }

            @Override
            public void onError(String message) {
                runOnUiThread(() -> {
                    status.setText(message);
                    refresh();
                });
            }
        });
        if (port <= 0) {
            status.setText("无法开房:端口不可用");
            host = null;
            return;
        }
        // announce on a timer so a joiner who arrives late still sees the room
        final android.os.Handler h = new android.os.Handler();
        Runnable beat = new Runnable() {
            @Override
            public void run() {
                if (host == null) return;
                LanDiscovery.broadcast(mine);
                h.postDelayed(this, 1000);
            }
        };
        h.post(beat);
        status.setText("已开房(端口 " + port + "),等待对方加入…");
        refresh();
    }

    // ------------------------------------------------------------- joining

    private void joinRoom(LanBeacon b) {
        joining = b;
        status.setText("正在连接 " + b.host + "…");
        refresh();
        LanJoin.connect(b, version(), "terran", r -> runOnUiThread(() -> {
            joining = null;
            if (!r.ok()) {
                // a version mismatch arrives here as the host's own sentence
                status.setText(r.error == null ? "连接失败" : r.error);
                refresh();
                return;
            }
            joined = r;
            NetSession.Config cfg = new NetSession.Config();
            cfg.host = false;
            cfg.localPlayer = 1;
            cfg.map = b.map;
            cfg.players = b.players;
            cfg.seed = b.seed;
            cfg.difficulty = b.difficulty;
            cfg.race = "terran";
            NetSession.install(cfg, r.link, r.peer);
            // The joiner's local roster: the host (which it just handshook
            // with) plus itself, both ready, so the start button is live here
            // too. Filling only its own seat leaves this view at "1/2".
            lobby.joinAsGuest(b.host, "我");
            status.setText("已连接,开始对战");
            refresh();
        }));
    }

    private void startMatch() {
        if (lobby.start()) {
            NetSession.Config cfg = NetSession.config();
            Intent it = new Intent(this, GameActivity.class);
            it.putExtra("map", cfg == null ? "bloodbath" : cfg.map);
            it.putExtra("difficulty", cfg == null ? 1 : cfg.difficulty);
            it.putExtra("race", cfg == null ? "terran" : cfg.race);
            it.putExtra("lan", true);
            startActivity(it);
            finish();
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (discovery != null) discovery.stop();
        if (host != null) host.stop();
        if (joined == null) NetSession.clear();
    }
}