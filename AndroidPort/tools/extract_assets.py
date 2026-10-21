"""Master asset extractor: pull StarCraft art out of the archives for the port.

Produces, under AndroidPort/assets_src/:
    sprites/<name>.png     -- decoded GRP sprite sheets (one PNG per frame row)
    palettes/units.pal     -- 256-colour RGB palette
    maps/<name>.chk        -- scenario.chk extracted from each .scm/.scx
    sounds/<name>.wav      -- stored WAV effects
    manifest.json          -- index of everything produced
"""

import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image  # noqa: E402
from sc_archive import Archive, MPQError  # noqa: E402

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\assets_src"

GRP_NAMES = []          # filled from listfile
PALETTE = None


# --------------------------------------------------------------------- GRP

def grp_frames(data):
    if len(data) < 6:
        return None
    frames, w, h = struct.unpack_from("<HHH", data, 0)
    if not (0 < frames < 4000) or not (0 < w <= 512) or not (0 < h <= 512):
        return None
    if 6 + frames * 8 > len(data):
        return None
    out = []
    for i in range(frames):
        x, y, fw, fh, off = struct.unpack_from("<BBBBI", data, 6 + i * 8)
        if off >= len(data):
            return None
        out.append((x, y, fw + 1, fh + 1, off))
    return (frames, w, h, out)


def decode_frame(data, fr, pal):
    """Decode one GRP frame to its own small RGBA image.

    Frame header gives the frame's own width/height plus its (x, y) offset
    within the unit's bounding box; the caller composites it there.
    """
    x, y, w, h, off = fr
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    p = off
    row = 0
    prev = None
    while row < h and p < len(data):
        lt = data[p]
        p += 1
        if lt == 0:                     # skip N transparent rows
            if p >= len(data):
                break
            row += data[p]
            p += 1
            prev = None
        elif lt == 2:                   # duplicate previous row
            if prev:
                for i in range(w):
                    px[i, row] = prev[i]
            row += 1
        else:                           # literal row
            cur = [(0, 0, 0, 0)] * w
            col = 0
            while col < w and p < len(data):
                code = data[p]
                p += 1
                if code & 0x80:         # transparent run
                    col += code & 0x7F
                else:                   # run of code+1 palette indices
                    for _ in range(code + 1):
                        if p >= len(data) or col >= w:
                            break
                        cur[col] = pal[data[p]]
                        p += 1
                        col += 1
            px_row = [cur[i] for i in range(w)]
            for i in range(w):
                px[i, row] = px_row[i]
            prev = px_row
            row += 1
    return img


def make_sheet(data, gi, pal, max_frames=64, cols=8):
    """Composite frames into a grid of bounding-box-sized cells."""
    frames, w, h, frs = gi
    n = min(frames, max_frames)
    rows = (n + cols - 1) // cols
    sheet = Image.new("RGBA", (w * cols, h * rows), (0, 0, 0, 0))
    for i in range(n):
        fr = frs[i]
        img = decode_frame(data, fr, pal)
        # place the frame at its offset inside the bounding box cell
        cell_x = (i % cols) * w + fr[0]
        cell_y = (i // cols) * h + fr[1]
        sheet.paste(img, (cell_x, cell_y), img)
    return sheet, n


# ----------------------------------------------------------------- palette

def palette_from_pcx(data):
    """A PCX file ends with 0x0C followed by 256 RGB triples."""
    if len(data) < 769:
        return None
    if data[-769] != 0x0C:
        return None
    pal = []
    base = len(data) - 768
    for i in range(256):
        r, g, b = data[base + i * 3: base + i * 3 + 3]
        pal.append((r, g, b, 255))
    return pal


def main():
    for sub in ("sprites", "palettes", "maps", "sounds"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    manifest = {"sprites": [], "maps": [], "sounds": [], "palette": None}

    # ---------------------------------------------------------- palette
    pal = None
    with Archive(os.path.join(ROOT, "BrooDat.mpq")) as a:
        lf = [n for n in a.read("(listfile)").decode("latin-1")
              .replace("\r", "\n").split("\n") if n.strip()]
        pcx = [n for n in lf if n.lower().endswith(".pcx")]
        for n in pcx:
            try:
                d = a.read(n)
            except Exception:
                continue
            p = palette_from_pcx(d)
            if p:
                pal = p
                manifest["palette"] = n
                with open(os.path.join(OUT, "palettes", "units.pal"), "wb") as fh:
                    fh.write(bytes(v for c in p for v in c[:3]))
                print("palette from %s" % n)
                break

    if pal is None:
        pal = [(i, i, i, 255) for i in range(256)]
        print("WARNING: no palette found, using grayscale")

    # ---------------------------------------------------------- sprites
    with Archive(os.path.join(ROOT, "BrooDat.mpq")) as a:
        lf = [n for n in a.read("(listfile)").decode("latin-1")
              .replace("\r", "\n").split("\n") if n.strip()]
        grps = [n for n in lf if n.lower().endswith(".grp")]
        ok = 0
        for n in grps:
            bi = a.find(n)
            if bi is None:
                continue
            try:
                d = a.read_block(bi, n.split("\\")[-1])
            except Exception:
                continue
            gi = grp_frames(d)
            if not gi:
                continue
            try:
                sheet, nf = make_sheet(d, gi, pal)
            except Exception:
                continue
            safe = n.replace("\\", "__").replace(".grp", "")
            path = os.path.join(OUT, "sprites", safe + ".png")
            sheet.save(path)
            manifest["sprites"].append({
                "name": n, "file": os.path.relpath(path, OUT).replace("\\", "/"),
                "frames": gi[0], "w": gi[1], "h": gi[2], "sheetFrames": nf,
            })
            ok += 1
        print("sprites exported: %d" % ok)

    # ------------------------------------------------------------- maps
    maps_dir = os.path.join(ROOT, "maps")
    from sc_archive import Archive as A2
    n_maps = 0
    for r, _d, files in os.walk(maps_dir):
        for f in files:
            if not f.lower().endswith((".scm", ".scx")):
                continue
            src = os.path.join(r, f)
            try:
                with A2(src) as am:
                    data = am.read("staredit\\scenario.chk")
            except Exception:
                try:
                    with A2(src) as am:
                        bi = am.find("scenario.chk")
                        data = am.read_block(bi, "scenario.chk") if bi is not None else None
                except Exception:
                    data = None
            if data and data[:4] == b"VER ":
                safe = os.path.splitext(f)[0]
                dst = os.path.join(OUT, "maps", safe + ".chk")
                with open(dst, "wb") as fh:
                    fh.write(data)
                manifest["maps"].append({"name": f, "chk": os.path.relpath(dst, OUT).replace("\\", "/"),
                                         "size": len(data)})
                n_maps += 1
    print("maps exported: %d" % n_maps)

    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    print("\nTOTAL  sprites=%d maps=%d" % (len(manifest["sprites"]), len(manifest["maps"])))


if __name__ == "__main__":
    main()
