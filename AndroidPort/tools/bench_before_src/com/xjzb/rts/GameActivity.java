package com.xjzb.rts;

import android.app.Activity;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;

/** Fullscreen game host. */
public class GameActivity extends Activity {

    private GameView view;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        // v2.23 batch C #3: FLAG_FULLSCREEN is gone. Some ROMs read it as a
        // request to keep clear of the notch / navigation area and inset the
        // window anyway, which showed up as a black band along an edge. The
        // immersive-sticky flags below (LAYOUT_FULLSCREEN + HIDE_NAVIGATION +
        // IMMERSIVE_STICKY) already take the whole screen on every API level
        // we ship to, so the extra legacy flag only ever hurt.
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        // v2.21 #1: the notch. With the default cutout mode a landscape window
        // is inset from the camera pill, so the whole game surface sat ~60dp
        // from the screen's left edge and the system black behind it read as a
        // permanent "black edge" no matter where the camera was. SHORT_EDGES
        // lets the window draw under the cutout like every other fullscreen
        // game; the pill itself may overlap the map's edge pixel, which is the
        // trade every portrait-camera phone makes.
        if (Build.VERSION.SDK_INT >= 28) {
            WindowManager.LayoutParams lp = getWindow().getAttributes();
            lp.layoutInDisplayCutoutMode = WindowManager.LayoutParams
                    .LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
            getWindow().setAttributes(lp);
        }
        // v2.21 #1: FLAG_FULLSCREEN alone leaves the gesture nav bar resident
        // (a black strip across the console's bottom). Immersive sticky hides
        // it and keeps it hidden after swipes.
        hideSystemBars();
        String map = getIntent().getStringExtra("map");
        if (map == null || map.isEmpty()) map = "bloodbath";
        int diff = getIntent().getIntExtra("difficulty", 1);
        // v2.8: the race picked on the main menu. Absent means terran, so an
        // older launch path (or a saved intent) keeps working unchanged.
        String race = getIntent().getStringExtra("race");
        if (race == null || race.isEmpty()) race = "terran";

        // v2.7 batch 8: a campaign launch carries a mission id instead of a
        // bare map. The mission names its own map, so the two paths converge
        // once the JSON is loaded.
        // v2.19 batch 5: a replay launch re-simulates the recorded orders.
        String replay = getIntent().getStringExtra("replay");
        String missionId = getIntent().getStringExtra("mission");
        if (replay != null) {
            // v2.20 batch 5: a replay can be a shipped demo (assets/replays/)
            // or one the player saved from a match (files dir, replay_*.txt).
            String rjson = GameView.readAsset(this, "replays/" + replay + ".txt");
            if (rjson == null || rjson.isEmpty()) {
                rjson = GameView.readLocalReplay(this, replay);
            }
            String mjson = missionId == null || missionId.isEmpty() ? null
                    : GameView.readAsset(this, "missions/" + missionId + ".json");
            view = new GameView(this, map, diff, mjson, race, rjson);
        } else if (missionId != null && !missionId.isEmpty()) {
            String json = GameView.readAsset(this, "missions/" + missionId + ".json");
            com.xjzb.rts.core.Mission m = com.xjzb.rts.core.Mission.parse(json);
            view = new GameView(this, m != null && !m.map.isEmpty() ? m.map : map,
                    diff, json, race);
        } else {
            view = new GameView(this, map, diff, null, race);
        }
        setContentView(view);
    }

    @Override
    protected void onResume() {
        super.onResume();
        hideSystemBars();
    }

    private void hideSystemBars() {
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    }
}
