"""Score-screen asset pipeline (v2.7 batch 7.1).

Decodes the original end-of-game score panel chrome out of StarDat.mpq into
Android assets:

    ui/score/pmain.png      640x480 panel background (pMain.pcx)
    ui/score/pinset.png     588x37  title inset strip (pInset.pcx)
    ui/score/scorebox.png   96x30   per-row score box (scorebox.pcx)
    ui/score/untab.png      93x4    tab underline (untab.pcx)
    ui/score/iscore.png     iScore.grp repacked to an 8-column icon grid

PCX notes, both inherited from the v2.2 title-screen fix and re-verified here:
  * xmin/ymin live at header offsets 4/6, xmax/ymax at 8/10 -- reading the
    maxima from 8/10 and subtracting the minima from 12/14 yields 0x0.
  * the 768-byte palette at the tail is R,G,B and the pixel stream holds
    palette *indices*; indexing the palette by pixel position produces noise.
  * every ScorePd file carries its own tail palette, so no external WPE is
    needed for the chrome.

GRP note: iScore.grp holds 54 small glyphs on a 256x100 cell (the original
blits them one at a time, not as a sheet), so they are repacked into one
8-column grid the app can index. GRP pixels are palette indices; they are
resolved through the same WPE ramp the sprites use, with index 255 transparent.
"""
import os
import struct

from PIL import Image

import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\app\app\src\main\assets", "ui", "score")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))

_wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [( _wpe[i * 4], _wpe[i * 4 + 1], _wpe[i * 4 + 2]) for i in range(256)]


def pcx_decode(data):
    """PCX 8bpp RLE -> (palette indices, palette, w, h). See module docstring."""
    if data[0:1] != b"\x0a" or data[1] != 5:
        return None
    xmin, ymin, xmax, ymax = struct.unpack_from("<HHHH", data, 4)
    w = xmax - xmin + 1
    h = ymax - ymin + 1
    if w <= 0 or h <= 0 or w > 4096 or h > 4096:
        return None
    pal = data[-768:]
    px = bytearray()
    i = 128
    end = len(data) - 768
    while len(px) < w * h and i < end:
        b = data[i]
        i += 1
        if b & 0xC0 == 0xC0:
            cnt = b & 0x3F
            if i >= end:
                break
            v = data[i]
            i += 1
            px.extend(bytes([v]) * cnt)
        else:
            px.append(b)
    if len(px) < w * h:
        # this repack drops bytes mid-stream; pad so the panel still renders
        px.extend(bytes(w * h - len(px)))
    return bytes(px[:w * h]), pal, w, h


def write_pcx(name, out):
    data, _ = SD.read_with_gaps(name)
    r = pcx_decode(data)
    if r is None:
        print("  %-14s SKIP (not a 8bpp PCX)" % out)
        return False
    px, pal, w, h = r
    lut = [(pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2]) for i in range(256)]
    im = Image.new("RGBA", (w, h))
    im.putdata([lut[v] + (255,) for v in px])
    im.save(os.path.join(OUT, out))
    print("  %-14s %dx%d" % (out, w, h))
    return True


def frame_rgba(f):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    px = im.load()
    src = f["px"]
    for y in range(f["h"]):
        base = y * f["w"]
        for x in range(f["w"]):
            v = src[base + x]
            if v != 255:
                px[x, y] = PAL[v] + (255,)
    return im


def extract_icons():
    """iScore.grp -> one grid PNG with the transparent background preserved."""
    data, gaps = SD.read_with_gaps("glue\\ScorePd\\iScore.grp")
    frames, _mw, _mh = grpm.decode_grp(data, gaps)
    cols = 8
    rows = (len(frames) + cols - 1) // cols
    cell = max(max(f["w"] for f in frames), max(f["h"] for f in frames))
    sheet = Image.new("RGBA", (cols * cell, rows * cell), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        cellim = frame_rgba(f)
        sheet.paste(cellim, ((i % cols) * cell, (i // cols) * cell), cellim)
    sheet.save(os.path.join(OUT, "iscore.png"))
    print("  %-14s %d frames, cell=%d, grid=%dx%d"
          % ("iscore.png", len(frames), cell, cols, rows))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("ScorePd chrome:")
    write_pcx("glue\\ScorePd\\pMain.pcx", "pmain.png")
    write_pcx("glue\\ScorePd\\pInset.pcx", "pinset.png")
    write_pcx("glue\\ScorePd\\scorebox.pcx", "scorebox.png")
    write_pcx("glue\\ScorePd\\untab.pcx", "untab.png")
    print("score icons:")
    extract_icons()