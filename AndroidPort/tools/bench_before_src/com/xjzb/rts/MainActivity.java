package com.xjzb.rts;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AbsListView;
import android.widget.BaseAdapter;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;

import java.io.InputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

/** Main menu: title art, difficulty, map selection. */
public class MainActivity extends Activity {

    public static class MapInfo {
        String id, name;
        int w, h;
        /** v2.16 batch 3.2: skirmish group (skirmish/ladder/bw/fun/island). */
        String group = "skirmish";
        /** v2.23 batch A: true when the starts sit on separate landmasses. */
        boolean island;
    }

    /** v2.16 batch 3.2: sticky group header label per index.txt group id. */
    private static String groupLabel(String g) {
        if ("ladder".equals(g)) return "天梯经典";
        if ("bw".equals(g)) return "BW 瓦片集";
        if ("fun".equals(g)) return "休闲遭遇战";
        if ("island".equals(g)) return "空投图";
        return "其他";
    }

    private int difficulty = 1;
    private TextView[] diffButtons;
    /** v2.8: "terran" or "zerg"; v2.10 adds "protoss". Sent to GameActivity. */
    private String race = "terran";
    private TextView[] raceButtons;
    /** v2.12 batch E: colour swatch in front of each race label. */
    private View[] raceSwatches;
    /** v2.10: ids in the same order as the race row's labels. */
    private static final String[] RACE_IDS = {"terran", "zerg", "protoss"};
    /**
     * v2.12 batch E: each race's own retail score-panel accent (measured by
     * tools/_e15.py / _e16.py). This is the stand-in for the Battle.net race
     * emblems, which StarDat+BrooDat simply do not contain.
     */
    private static final int[] RACE_ACCENT = {
            Color.rgb(244, 108, 0),     // terran  ScoreTv body
            Color.rgb(172, 244, 108),   // zerg    ScoreZd body
            Color.rgb(226, 60, 50),     // protoss ScorePv maroon, lifted to read on dark
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        FrameLayout root = new FrameLayout(this);

        Bitmap bg = null;
        for (String ext : new String[]{".webp", ".png"}) {
            try (InputStream in = getAssets().open("ui/title" + ext)) {
                bg = BitmapFactory.decodeStream(in);
                break;
            } catch (Exception ignored) {
            }
        }
        if (bg != null) {
            ImageView bgView = new ImageView(this);
            bgView.setImageBitmap(bg);
            bgView.setScaleType(ImageView.ScaleType.CENTER_CROP);
            root.addView(bgView, new FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        } else {
            root.setBackgroundColor(Color.rgb(6, 8, 14));
        }
        View scrim = new View(this);
        scrim.setBackgroundColor(Color.argb(120, 4, 6, 14));
        root.addView(scrim, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        LinearLayout col = new LinearLayout(this);
        col.setOrientation(LinearLayout.VERTICAL);
        col.setGravity(Gravity.CENTER_HORIZONTAL);
        root.addView(col, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        TextView title = new TextView(this);
        title.setText("星 际 争 霸");
        title.setTextSize(40);
        title.setTextColor(Color.rgb(255, 210, 90));
        title.setShadowLayer(6, 0, 0, Color.rgb(180, 80, 20));
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, 70, 0, 4);
        col.addView(title, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView sub = new TextView(this);
        sub.setText("安卓原生机 · 母巢之战");
        sub.setTextSize(15);
        sub.setTextColor(Color.rgb(190, 205, 230));
        sub.setGravity(Gravity.CENTER);
        sub.setPadding(0, 0, 0, 30);
        col.addView(sub, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        LinearLayout diffRow = new LinearLayout(this);
        diffRow.setGravity(Gravity.CENTER);
        diffRow.setPadding(0, 8, 0, 20);
        String[] names = {"简单", "普通", "困难"};
        diffButtons = new TextView[3];
        for (int i = 0; i < 3; i++) {
            final int d = i;
            TextView b = new TextView(this);
            b.setText(names[i]);
            b.setTextSize(15);
            b.setPadding(36, 14, 36, 14);
            b.setGravity(Gravity.CENTER);
            b.setOnClickListener(v -> {
                difficulty = d;
                restyleDiff();
            });
            diffRow.addView(b);
            diffButtons[i] = b;
        }
        restyleDiff();
        col.addView(diffRow, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        // v2.8: race chooser, directly under the difficulty row.
        // v2.10 batch A: protoss joins the row now that the type table, the
        // build menu and the shield system are all in place.
        //
        // v2.12 batch E: the plan asked for Battle.net race emblems out of
        // glue\Battle.net\icons\icons.pcx. That file is a Battle.net button
        // sprite sheet, not an emblem set, and a full sweep of every glue\ and
        // portrait\ asset (see tools/_e14.py, tools/_e17.py) found no
        // terran/zerg/protoss emblem art anywhere in StarDat+BrooDat. Rather
        // than invent one, each race gets the accent its own retail score
        // panel uses -- measured, not guessed:
        //   terran  ScoreTv body rgb(244,108,0)   orange
        //   zerg    ScoreZd body rgb(172,244,108) green
        //   protoss ScorePv accent rgb(128,0,0)   maroon, lifted for legibility
        LinearLayout raceRow = new LinearLayout(this);
        raceRow.setGravity(Gravity.CENTER);
        raceRow.setPadding(0, 0, 0, 20);
        String[] raceNames = {"人类", "虫族", "星灵"};
        raceButtons = new TextView[raceNames.length];
        raceSwatches = new View[raceNames.length];
        int sw = (int) (10 * getResources().getDisplayMetrics().density);
        for (int i = 0; i < raceNames.length; i++) {
            final String r = RACE_IDS[i];
            LinearLayout cell = new LinearLayout(this);
            cell.setGravity(Gravity.CENTER_VERTICAL);
            View dot = new View(this);
            LinearLayout.LayoutParams dlp = new LinearLayout.LayoutParams(sw, sw);
            dlp.rightMargin = sw / 2;
            cell.addView(dot, dlp);
            TextView b = new TextView(this);
            b.setText(raceNames[i]);
            b.setTextSize(15);
            b.setPadding(0, 14, 30, 14);
            b.setGravity(Gravity.CENTER);
            cell.setOnClickListener(v -> {
                race = r;
                restyleRace();
            });
            cell.setPadding(30, 0, 0, 0);
            // v2.15: the cell's height used to ride on the TextView alone,
            // which made a real-finger tap land beside the row on dense
            // screens; the platform minimum touch target is 48dp.
            cell.setMinimumHeight((int) (48 * getResources().getDisplayMetrics().density));
            raceRow.addView(cell);
            raceButtons[i] = b;
            raceSwatches[i] = dot;
            cell.addView(b);
        }
        restyleRace();
        col.addView(raceRow, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        loadCampaign();
        List<MapInfo> maps = loadMaps();
        List<String[]> missions = loadMissions();

        // v2.37: local-network play gets its own button rather than a fourth
        // tab. The lobby is a different screen with its own lifetime (it holds
        // sockets), so a tab that tears it down on every switch would be worse
        // than a plain button next to the map picker.
        TextView lanBtn = new TextView(this);
        lanBtn.setText("局域网对战");
        lanBtn.setTextSize(15);
        lanBtn.setGravity(Gravity.CENTER);
        lanBtn.setPadding(0, 16, 0, 16);
        GradientDrawable lanBg = new GradientDrawable();
        lanBg.setColor(Color.argb(210, 16, 30, 48));
        lanBg.setCornerRadius(12);
        lanBg.setStroke(2, Color.argb(150, 110, 180, 230));
        lanBtn.setBackground(lanBg);
        lanBtn.setTextColor(Color.rgb(200, 235, 255));
        lanBtn.setOnClickListener(v ->
                startActivity(new Intent(MainActivity.this, LobbyActivity.class)));
        col.addView(lanBtn, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        // v2.7 7.3: a two-tab chooser. The campaign tab is the new home for the
        // mission list; the skirmish tab keeps the original free map picker.
        LinearLayout tabs = new LinearLayout(this);
        tabs.setGravity(Gravity.CENTER);
        tabs.setPadding(0, 0, 0, 10);
        // v2.20 batch 5: three tabs now (战役 / 遭遇战 / 回放), so the old
        // boolean pair became an index into this row.
        final int[] tab = {0};
        String[] tabNames = {"战 役", "遭遇战", "回  放"};
        final TextView[] tabViews = new TextView[tabNames.length];
        for (int i = 0; i < tabNames.length; i++) {
            TextView t = new TextView(this);
            t.setText(tabNames[i]);
            t.setTextSize(15);
            t.setPadding(40, 12, 40, 12);
            tabs.addView(t);
            tabViews[i] = t;
        }
        col.addView(tabs, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        ListView list = new ListView(this);
        list.setDividerHeight(2);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f);
        lp.setMargins(120, 0, 120, 0);
        col.addView(list, lp);

        final BaseAdapter campaignAdapter = new BaseAdapter() {
            @Override
            public int getCount() {
                return missions.size();
            }

            @Override
            public Object getItem(int i) {
                return missions.get(i);
            }

            @Override
            public long getItemId(int i) {
                return i;
            }

            @Override
            public View getView(int i, View convertView, ViewGroup parent) {
                String[] m = missions.get(i);
                boolean unlocked = i <= campaignProgress;
                LinearLayout row = new LinearLayout(MainActivity.this);
                row.setOrientation(LinearLayout.HORIZONTAL);
                row.setGravity(Gravity.CENTER_VERTICAL);
                row.setPadding(20, 16, 20, 16);
                GradientDrawable bgd = new GradientDrawable();
                bgd.setColor(Color.argb(unlocked ? 200 : 150, 14, 20, 32));
                bgd.setCornerRadius(14);
                bgd.setStroke(2, unlocked ? Color.argb(140, 190, 150, 60)
                        : Color.argb(90, 90, 110, 130));
                row.setBackground(bgd);

                ImageView thumb = new ImageView(MainActivity.this);
                Bitmap mini = minimap(m[2]);
                if (mini != null) thumb.setImageBitmap(mini);
                thumb.setScaleType(ImageView.ScaleType.FIT_CENTER);
                thumb.setBackgroundColor(Color.argb(160, 6, 10, 18));
                row.addView(thumb, new LinearLayout.LayoutParams(
                        (int) (56 * getResources().getDisplayMetrics().density),
                        (int) (56 * getResources().getDisplayMetrics().density)));

                LinearLayout c2 = new LinearLayout(MainActivity.this);
                c2.setOrientation(LinearLayout.VERTICAL);
                c2.setPadding((int) (14 * getResources().getDisplayMetrics().density), 0, 0, 0);
                TextView name = new TextView(MainActivity.this);
                name.setText(unlocked ? m[1] : "??? (未解锁)");
                name.setTextSize(17);
                name.setTextColor(unlocked ? Color.rgb(225, 238, 255) : Color.rgb(120, 135, 155));
                c2.addView(name);
                TextView info = new TextView(MainActivity.this);
                info.setText(unlocked ? ("地图:" + m[2]) : "通关上一关后解锁");
                info.setTextSize(11);
                info.setTextColor(Color.rgb(120, 150, 180));
                c2.addView(info);
                row.addView(c2);

                final int idx = i;
                row.setOnClickListener(v -> {
                    if (idx > campaignProgress) return;
                    Intent it = new Intent(MainActivity.this, GameActivity.class);
                    it.putExtra("mission", missions.get(idx)[0]);
                    it.putExtra("difficulty", difficulty);
                    it.putExtra("race", race);
                    startActivity(it);
                });
                row.setLayoutParams(new AbsListView.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
                return row;
            }
        };
        final BaseAdapter mapAdapter = new BaseAdapter() {
            @Override
            public int getCount() {
                return maps.size();
            }

            @Override
            public Object getItem(int i) {
                return maps.get(i);
            }

            @Override
            public long getItemId(int i) {
                return i;
            }

            @Override
            public View getView(int i, View convertView, ViewGroup parent) {
                MapInfo m = maps.get(i);
                // v2.16 batch 3.2: a sticky group header. The plan asks for a
                // separator row at each group boundary rather than a third
                // tab level, so the campaign/skirmish frame stays as-is. The
                // header is a normal row (full width, no tap) that reads as a
                // band above the group's first map.
                boolean newGroup = i == 0
                        || !m.group.equals(maps.get(i - 1).group);
                LinearLayout wrap = new LinearLayout(MainActivity.this);
                wrap.setOrientation(LinearLayout.VERTICAL);
                wrap.setLayoutParams(new AbsListView.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
                if (newGroup) {
                    TextView head = new TextView(MainActivity.this);
                    head.setText(groupLabel(m.group));
                    head.setTextSize(14);
                    head.setTextColor(Color.rgb(255, 210, 110));
                    head.setPadding(24, 18, 24, 8);
                    head.setBackgroundColor(Color.argb(150, 30, 22, 8));
                    wrap.addView(head, new LinearLayout.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
                }
                LinearLayout row = new LinearLayout(MainActivity.this);
                row.setOrientation(LinearLayout.HORIZONTAL);
                row.setGravity(Gravity.CENTER_VERTICAL);
                row.setPadding(20, 16, 20, 16);
                GradientDrawable bgd = new GradientDrawable();
                bgd.setColor(Color.argb(190, 14, 20, 32));
                bgd.setCornerRadius(14);
                bgd.setStroke(2, Color.argb(120, 90, 140, 190));
                row.setBackground(bgd);

                // v2.7 7.3: the map's own minimap is already extracted next to
                // its terrain, so the picker shows the real layout instead of
                // only a name. Missing art degrades to a blank tile, not a gap.
                ImageView thumb = new ImageView(MainActivity.this);
                Bitmap mini = minimap(m.id);
                if (mini != null) thumb.setImageBitmap(mini);
                thumb.setScaleType(ImageView.ScaleType.FIT_CENTER);
                thumb.setBackgroundColor(Color.argb(160, 6, 10, 18));
                row.addView(thumb, new LinearLayout.LayoutParams(
                        (int) (56 * getResources().getDisplayMetrics().density),
                        (int) (56 * getResources().getDisplayMetrics().density)));

                LinearLayout col2 = new LinearLayout(MainActivity.this);
                col2.setOrientation(LinearLayout.VERTICAL);
                col2.setPadding((int) (14 * getResources().getDisplayMetrics().density), 0, 0, 0);
                TextView name = new TextView(MainActivity.this);
                name.setText(m.name);
                name.setTextSize(18);
                name.setTextColor(Color.rgb(225, 238, 255));
                col2.addView(name);
                TextView info = new TextView(MainActivity.this);
                // v2.23 batch A: an airlift map carries a badge, so the
                // "starts on separate islands" maps read as a feature rather
                // than as a map that will strand the player.
                info.setText(m.id + " · " + m.w + "×" + m.h
                        + (m.island ? "  ·  空投图" : ""));
                info.setTextSize(11);
                info.setTextColor(m.island ? Color.rgb(255, 200, 120)
                        : Color.rgb(120, 150, 180));
                col2.addView(info);
                row.addView(col2);
                row.setOnClickListener(v -> {
                    Intent it = new Intent(MainActivity.this, GameActivity.class);
                    it.putExtra("map", m.id);
                    it.putExtra("difficulty", difficulty);
                    it.putExtra("race", race);
                    startActivity(it);
                });
                wrap.addView(row, new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
                return wrap;
            }
        };

        // v2.20 batch 5: the replay browser. Asset replays ship in
        // assets/replays/index.txt; the player's own saved replays live in the
        // app's files dir as replay_<mapId>.txt, so the list has two sources.
        final BaseAdapter replayAdapter = new BaseAdapter() {
            @Override
            public int getCount() {
                return replays.size();
            }

            @Override
            public Object getItem(int i) {
                return replays.get(i);
            }

            @Override
            public long getItemId(int i) {
                return i;
            }

            @Override
            public View getView(int i, View convertView, ViewGroup parent) {
                ReplayInfo r = replays.get(i);
                LinearLayout row = new LinearLayout(MainActivity.this);
                row.setOrientation(LinearLayout.HORIZONTAL);
                row.setGravity(Gravity.CENTER_VERTICAL);
                row.setPadding(20, 16, 20, 16);
                GradientDrawable bgd = new GradientDrawable();
                bgd.setColor(Color.argb(190, 14, 20, 32));
                bgd.setCornerRadius(14);
                bgd.setStroke(2, Color.argb(120, 90, 140, 190));
                row.setBackground(bgd);

                ImageView thumb = new ImageView(MainActivity.this);
                Bitmap mini = minimap(r.map);
                if (mini != null) thumb.setImageBitmap(mini);
                thumb.setScaleType(ImageView.ScaleType.FIT_CENTER);
                thumb.setBackgroundColor(Color.argb(160, 6, 10, 18));
                row.addView(thumb, new LinearLayout.LayoutParams(
                        (int) (56 * getResources().getDisplayMetrics().density),
                        (int) (56 * getResources().getDisplayMetrics().density)));

                LinearLayout c2 = new LinearLayout(MainActivity.this);
                c2.setOrientation(LinearLayout.VERTICAL);
                c2.setPadding((int) (14 * getResources().getDisplayMetrics().density), 0, 0, 0);
                TextView name = new TextView(MainActivity.this);
                name.setText(r.title);
                name.setTextSize(17);
                name.setTextColor(Color.rgb(225, 238, 255));
                c2.addView(name);
                TextView info = new TextView(MainActivity.this);
                info.setText(r.summary);
                info.setTextSize(11);
                info.setTextColor(Color.rgb(120, 150, 180));
                c2.addView(info);
                row.addView(c2);

                row.setOnClickListener(v -> {
                    Intent it = new Intent(MainActivity.this, GameActivity.class);
                    it.putExtra("replay", r.name);
                    it.putExtra("map", r.map);
                    it.putExtra("difficulty", difficulty);
                    it.putExtra("race", race);
                    startActivity(it);
                });
                return row;
            }
        };

        list.setAdapter(campaignAdapter);
        final Runnable restyleTabs = () -> {
            for (int i = 0; i < tabViews.length; i++) {
                tabViews[i].setTextColor(i == tab[0] ? Color.rgb(255, 210, 110)
                        : Color.rgb(150, 170, 195));
            }
        };
        restyleTabs.run();
        for (int i = 0; i < tabViews.length; i++) {
            final int which = i;
            tabViews[i].setOnClickListener(v -> {
                tab[0] = which;
                restyleTabs.run();
                if (which == 0) list.setAdapter(campaignAdapter);
                else if (which == 1) list.setAdapter(mapAdapter);
                else {
                    replays.clear();
                    replays.addAll(loadReplays());
                    list.setAdapter(replayAdapter);
                }
            });
        }

        TextView hint = new TextView(this);
        hint.setText("拖框选兵 · 点地移动 · 双指缩放 · 点小地图导航");
        hint.setTextSize(11);
        hint.setTextColor(Color.rgb(160, 175, 200));
        hint.setGravity(Gravity.CENTER);
        hint.setPadding(0, 16, 0, 24);
        col.addView(hint, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        setContentView(root);
    }

    @Override
    protected void onResume() {
        super.onResume();
        // a finished mission may have unlocked the next one
        int before = campaignProgress;
        loadCampaign();
        if (campaignProgress != before) recreate();
    }

    private void restyleDiff() {
        for (int i = 0; i < diffButtons.length; i++) {
            GradientDrawable g = new GradientDrawable();
            g.setCornerRadius(20);
            if (i == difficulty) {
                g.setColor(Color.argb(220, 190, 130, 30));
                g.setStroke(2, Color.rgb(255, 210, 110));
                diffButtons[i].setTextColor(Color.WHITE);
            } else {
                g.setColor(Color.argb(140, 20, 28, 44));
                g.setStroke(2, Color.argb(110, 100, 130, 160));
                diffButtons[i].setTextColor(Color.rgb(150, 170, 195));
            }
            diffButtons[i].setBackground(g);
        }
    }

    // ---- v2.8: race picker styling, mirrors restyleDiff's selected state
    private void restyleRace() {
        for (int i = 0; i < raceButtons.length; i++) {
            // v2.10: three buttons now, so the old "(i == 0) == terran" trick
            // no longer identifies the selected one -- compare ids directly.
            boolean on = RACE_IDS[i].equals(race);
            // v2.12 batch E: the swatch is the race's own accent, dimmed when
            // the row is not the selected one.
            GradientDrawable dot = new GradientDrawable();
            dot.setShape(GradientDrawable.OVAL);
            dot.setColor(on ? RACE_ACCENT[i]
                    : (RACE_ACCENT[i] & 0x00FFFFFF) | 0x66000000);
            dot.setStroke(1, on ? Color.WHITE : Color.argb(120, 120, 140, 165));
            raceSwatches[i].setBackground(dot);

            GradientDrawable g = new GradientDrawable();
            g.setCornerRadius(20);
            if (on) {
                g.setColor(Color.argb(220, 150, 40, 130));
                g.setStroke(2, Color.rgb(240, 150, 230));
                raceButtons[i].setTextColor(Color.WHITE);
            } else {
                g.setColor(Color.argb(140, 20, 28, 44));
                g.setStroke(2, Color.argb(110, 100, 130, 160));
                raceButtons[i].setTextColor(Color.rgb(150, 170, 195));
            }
            raceButtons[i].setBackground(g);
        }
    }

    // ---- v2.7 batch 8: campaign progress
    /** Missions unlocked so far; a win on mission n unlocks n+1. */
    private int campaignProgress;
    private static final String CAMPAIGN_PREFS = "xjzb_campaign";

    private void loadCampaign() {
        campaignProgress = getSharedPreferences(CAMPAIGN_PREFS, MODE_PRIVATE)
                .getInt("progress", 0);
    }

    private void saveCampaign() {
        getSharedPreferences(CAMPAIGN_PREFS, MODE_PRIVATE)
                .edit().putInt("progress", campaignProgress).apply();
    }

    /** Mission index rows: "id|name|map". */
    private List<String[]> loadMissions() {
        List<String[]> out = new ArrayList<>();
        try (InputStream in = getAssets().open("missions/index.txt");
             BufferedReader r = new BufferedReader(new InputStreamReader(in, "UTF-8"))) {
            String line;
            while ((line = r.readLine()) != null) {
                String[] p = line.trim().split("\\|");
                if (p.length < 3) continue;
                out.add(p);
            }
        } catch (Exception ignored) {
        }
        return out;
    }

    /** v2.20 batch 5: the replay tab's rows, filled when the tab is opened. */
    private final List<ReplayInfo> replays = new ArrayList<>();

    /** Cached minimap thumbnails, keyed by map id. */
    private final java.util.HashMap<String, Bitmap> minimaps = new java.util.HashMap<>();

    /** The map's extracted minimap, or null when it is not in the asset set. */
    private Bitmap minimap(String id) {
        if (minimaps.containsKey(id)) return minimaps.get(id);
        Bitmap b = null;
        for (String ext : new String[]{".webp", ".png"}) {
            try (InputStream in = getAssets().open("maps/" + id + "/minimap" + ext)) {
                b = BitmapFactory.decodeStream(in);
                break;
            } catch (Exception ignored) {
            }
        }
        minimaps.put(id, b);
        return b;
    }

    // ---- v2.20 batch 5: the replay browser

    /** One row of the replay tab: the asset name, its map and its one-liner. */
    public static class ReplayInfo {
        String name;        // assets/replays/<name>.txt
        String map = "bloodbath";
        String title;
        String summary;
        boolean local;
    }

    /**
     * The replays to list: the shipped demos first, then whatever the player
     * saved from a match (replay_<mapId>.txt in the app's files dir). A local
     * save with the same name as a shipped one shadows it -- the player's own
     * match is the more interesting one.
     */
    private List<ReplayInfo> loadReplays() {
        List<ReplayInfo> out = new ArrayList<>();
        java.util.LinkedHashMap<String, ReplayInfo> byName = new java.util.LinkedHashMap<>();
        try (InputStream in = getAssets().open("replays/index.txt");
             BufferedReader r = new BufferedReader(new InputStreamReader(in, "UTF-8"))) {
            String line;
            while ((line = r.readLine()) != null) {
                String[] p = line.trim().split("\\|");
                if (p.length < 3) continue;
                ReplayInfo ri = new ReplayInfo();
                ri.name = p[0];
                ri.map = p[1];
                ri.title = p[2];
                String text = readAssetText("replays/" + ri.name + ".txt");
                ri.summary = text == null ? "回放缺失" : com.xjzb.rts.core.Game.replaySummary(text);
                byName.put(ri.name, ri);
            }
        } catch (Exception ignored) {
        }
        // local saves
        java.io.File dir = getFilesDir();
        java.io.File[] files = dir == null ? null : dir.listFiles();
        if (files != null) {
            for (java.io.File f : files) {
                String n = f.getName();
                if (!n.startsWith("replay_") || !n.endsWith(".txt")) continue;
                ReplayInfo ri = new ReplayInfo();
                ri.name = n;
                ri.local = true;
                ri.map = n.substring("replay_".length(), n.length() - 4);
                ri.title = "我的回放 · " + ri.map;
                String text = readFileText(f);
                ri.summary = text == null ? "读取失败" : com.xjzb.rts.core.Game.replaySummary(text);
                byName.put(ri.name, ri);
            }
        }
        out.addAll(byName.values());
        return out;
    }

    private String readAssetText(String path) {
        try (InputStream in = getAssets().open(path);
             BufferedReader r = new BufferedReader(new InputStreamReader(in, "UTF-8"))) {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = r.readLine()) != null) sb.append(line).append('\n');
            return sb.toString();
        } catch (Exception e) {
            return null;
        }
    }

    private static String readFileText(java.io.File f) {
        try (BufferedReader r = new BufferedReader(new InputStreamReader(
                new java.io.FileInputStream(f), "UTF-8"))) {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = r.readLine()) != null) sb.append(line).append('\n');
            return sb.toString();
        } catch (Exception e) {
            return null;
        }
    }

    private List<MapInfo> loadMaps() {
        List<MapInfo> out = new ArrayList<>();
        try (InputStream in = getAssets().open("maps/index.txt");
             BufferedReader r = new BufferedReader(new InputStreamReader(in, "UTF-8"))) {
            String line;
            while ((line = r.readLine()) != null) {
                String[] p = line.trim().split("\\|");
                if (p.length < 4) continue;
                MapInfo m = new MapInfo();
                m.id = p[0];
                m.name = p[1];
                m.w = Integer.parseInt(p[2]);
                m.h = Integer.parseInt(p[3]);
                // v2.16 batch 3.2: the group column is new; a pre-v2.16
                // index.txt has only four fields and falls back to skirmish.
                if (p.length >= 5 && p[4] != null && !p[4].isEmpty()) m.group = p[4];
                // v2.23 batch A: the sixth column marks an airlift map; a
                // pre-v2.23 index has only five fields and stays non-island.
                if (p.length >= 6) m.island = "1".equals(p[5].trim());
                out.add(m);
            }
        } catch (Exception ignored) {
        }
        return out;
    }
}
