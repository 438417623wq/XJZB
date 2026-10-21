"""Shrink the shipped assets in place.

The pipelines emit PNG (source of truth); this step rewrites the shipped copies
so the APK stays small:

  * every PNG -> lossless WEBP (terrain chunks drop to ~12% of their PNG size
    because the terrain is 8bpp-paletted content; zero quality loss),
  * every walk.bin -> walk.gz (~1.6 MB -> ~60 KB over 9 maps),
  * every elev.bin -> elev.bin.gz (the v2.23 elevation bitmap, same trick).

The loaders try .webp/.gz first and fall back to .png/.bin, so re-running a
pipeline never breaks the app -- it just ships slightly bigger until this runs.
"""
import gzip
import os
import sys
from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"

# Pillow's WEBP encoder switched its default lossless effort at method 4. On
# some images -- the plasma.grp fireball sheet is the one that bit us -- the
# bitstreams it emits at method 4/5/6 make TwelveMonkeys' WEBP reader throw
# "ArrayIndexOutOfBoundsException: Coordinate out of bounds!", i.e. the sheet
# silently fails to load on the desktop harness and in any ImageIO-based tool.
# Pillow itself reads them back fine, which is why this went unnoticed: the
# PNG was gone and the WEBP existed, so nothing looked wrong until an
# ImageIO consumer tried to decode it. method=3 costs +1.2% across the whole
# 362-sheet set and every one of them decodes. Do not raise this without
# re-running tools/ProbeAllWebp.java over the whole asset tree.
WEBP_METHOD = 3


# v2.16 batch 3.3: an optional lossy terrain mode. The plan asked for
# "地形块用有损 webp q80, minimap 保持无损" on the theory that the terrain is
# photographic enough to compress 3-5x. Measured on the shipped hunters
# terrain set, q80 saves only 1.30x and moves pixels by up to 72/255 -- well
# past "肉眼不可辨" -- while q85 saves 1.0x. So the honest default stays
# lossless, and the lossy path is opt-in via --terrain-quality so the
# comparison the plan's acceptance criteria ask for can still be run. A
# minimap is always lossless regardless.
TERRAIN_QUALITY = None


def _save_webp(im, out, lossless):
    if lossless:
        im.save(out, "WEBP", lossless=True, method=WEBP_METHOD)
    else:
        im.save(out, "WEBP", lossless=False, quality=TERRAIN_QUALITY,
                method=WEBP_METHOD)


def png_to_webp(path):
    im = Image.open(path)
    out = path[:-4] + ".webp"
    # terrain chunks are c_<x>_<y>.png; everything else (minimap, sprites)
    # stays lossless even in --terrain-quality mode.
    is_terrain = os.path.basename(path).startswith("c_")
    _save_webp(im, out, lossless=not (is_terrain and TERRAIN_QUALITY))
    os.remove(path)
    return os.path.getsize(out), im.mode


def bin_to_gz(path):
    out = path + ".gz"
    with open(path, "rb") as f:
        data = f.read()
    with open(out, "wb") as f:
        with gzip.GzipFile(fileobj=f, mode="wb", mtime=0) as g:
            g.write(data)
    os.remove(path)
    return os.path.getsize(out), len(data)


def main():
    before = after = 0
    n_png = n_bin = 0
    for root, _dirs, files in os.walk(ASSETS):
        for f in sorted(files):
            p = os.path.join(root, f)
            before += os.path.getsize(p)
            if f.endswith(".png"):
                sz, _ = png_to_webp(p)
                after += sz
                n_png += 1
            elif f in ("walk.bin", "elev.bin", "void.bin"):
                # v2.42: void.bin (1 byte per tile, marks the deep off-map sea
                # the bake leaves black) rides the same gzip path as the walk
                # and elevation bitmaps. The loader and the [v242] assertion
                # both accept the raw name too, so a missed slim only costs size.
                sz, _ = bin_to_gz(p)
                after += sz
                n_bin += 1
            else:
                after += os.path.getsize(p)
    print("converted %d png -> lossless webp, %d bin -> gz"
          % (n_png, n_bin))
    print("assets %.2f MB -> %.2f MB  (%.0f%%)" % (before / 1e6, after / 1e6,
                                                   100.0 * after / max(1, before)))


if __name__ == "__main__":
    for i, a in enumerate(sys.argv):
        if a == "--terrain-quality" and i + 1 < len(sys.argv):
            TERRAIN_QUALITY = int(sys.argv[i + 1])
        elif a.startswith("--terrain-quality="):
            TERRAIN_QUALITY = int(a.split("=", 1)[1])
    if "--yes" not in sys.argv:
        print("dry run only; pass --yes to rewrite"
              + (" (terrain quality %d)" % TERRAIN_QUALITY if TERRAIN_QUALITY
                 else " (lossless)"))
        sys.exit(0)
    main()
    if TERRAIN_QUALITY:
        print("terrain chunks written lossy q%d; minimaps/sprites lossless"
              % TERRAIN_QUALITY)
