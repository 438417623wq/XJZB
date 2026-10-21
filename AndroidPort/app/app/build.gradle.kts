plugins {
    id("com.android.application")
}

android {
    namespace = "com.xjzb.rts"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.xjzb.rts"
        minSdk = 21
        targetSdk = 34
        // v2.42: the divide void-tile black blob (and 39 sibling maps) re-render
        // as neighbour terrain, the chunk pipeline got the bilinear /
        // unconditional-bleed / keep-alive hardening plus an on-device render
        // diagnostic, and the bottom HUD gained the control-group block as a
        // seventh widget with a slim, content-hugging info panel.
        // See v2.42方案-滑动黑条根治与底部HUD重构.md.
        //
        // v2.43: match-performance pass. The camera became a per-frame snapshot
        // (which is also what actually fixed the v2.42 black bar), the roster
        // stopped being a CopyOnWriteArrayList, paths stopped being a list of
        // int[2], per-frame Rect allocations are gone, the aura / auto-acquire
        // scans are short-circuited and staggered, the neighbour queries go
        // through a uniform spatial grid, pathfinding is budgeted, the frame
        // loop aligns to 16 ms, and the world loops cull to the viewport.
        // See v2.43方案-对局性能优化.md.
        versionCode = 44
        versionName = "2.44"
    }

    // Self-signed release key for personal sideloading. The keystore lives in
    // signing/xjzb-release.jks (outside the module); regenerate it with
    // tools/new_keystore.ps1 if lost -- a new key means an uninstall is needed
    // before the next install, because Android refuses a signature change.
    signingConfigs {
        create("release") {
            storeFile = file("../../signing/xjzb-release.jks")
            storePassword = "xjzb2026"
            keyAlias = "xjzb"
            keyPassword = "xjzb2026"
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("release")
        }
    }

    // This machine has no lint-gradle in the offline cache, so the release
    // vital lint gate cannot run. Lint is advisory here anyway.
    lint {
        checkReleaseBuilds = false
        abortOnError = false
    }

    // Pure Java, no AndroidX: keeps the build fully offline-capable.
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    // v2.37: the LAN handshake has to agree on a version string, and the one in
    // this file is the only place it is defined. Generating BuildConfig lets the
    // lobby read it instead of a second copy that can drift out of sync -- a
    // drifted version is a handshake that rejects a perfectly good peer.
    buildFeatures {
        buildConfig = true
    }

    sourceSets {
        getByName("main") {
            assets.srcDirs("src/main/assets")
        }
    }
}
