"""v2.44: decode-faithful PNG mirror of the sprite sheets for the desktop
harness.

The shipped sheets are lossless (VP8L) WEBP. Android's libwebp decodes their
alpha correctly, but the TwelveMonkeys imageio-webp 3.11.0 plugin on the
harness classpath does NOT: every sheet comes back opaque with its background
filled by garbage RGB -- which is exactly the peach/navy/cyan "blocks" the
_evidence crops show behind every unit. Every art audit that ran on the
harness between v2.23 and v2.43 was therefore looking at a decoding artifact,
not at the shipped art.

This script converts assets/sprites/*.webp to PNG once (PIL reads VP8L alpha
correctly) into tools/harness_sprites/. GameDesktop / HudPreview prefer the
mirror when it exists, so harness renders show the real sheets; the APK still
ships the WEBP untouched.

Usage: python make_harness_sprites.py [--check]
  --check  no writing; exit 1 when any sheet is missing/stale in the mirror
"""
import os
import sys

from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
OUT = r"F:\KF\XJZB\AndroidPort\tools\harness_sprites"


def main(check=False):
    os.makedirs(OUT, exist_ok=True)
    n_ok = n_new = n_stale = 0
    for f in sorted(os.listdir(ASSETS)):
        if not f.endswith(".webp"):
            continue
        src = os.path.join(ASSETS, f)
        dst = os.path.join(OUT, f[:-5] + ".png")
        if check:
            if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
                print("stale:", f)
                n_stale += 1
            else:
                n_ok += 1
            continue
        if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
            n_ok += 1
            continue
        im = Image.open(src)
        im.save(dst)
        n_new += 1
    mode = "check" if check else "build"
    print("%s: ok=%d new=%d stale=%d total_webp=%d"
          % (mode, n_ok, n_new, n_stale,
             sum(1 for f in os.listdir(ASSETS) if f.endswith(".webp"))))
    return 1 if check and n_stale else 0


if __name__ == "__main__":
    sys.exit(main(check="--check" in sys.argv))
