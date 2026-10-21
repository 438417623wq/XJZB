"""Try vr4/vx4 decoding variants on a few megatiles to find the right one."""
import os
from PIL import Image
import sc_archive
from pipeline_maps import build_tileset

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))


def build_variants(ts_name):
    def rd(name):
        for ar in (SD,):
            if ar.has(name):
                return ar.read_with_gaps(name)
        return None, None

    wpe, _ = rd("tileset\\%s.wpe" % ts_name)
    if len(wpe) < 1024:
        wpe += bytes(1024 - len(wpe))
    pal_bgr = [(wpe[i * 4 + 2], wpe[i * 4 + 1], wpe[i * 4]) for i in range(256)]
    pal_rgb = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]
    vx4, g2 = rd("tileset\\%s.vx4" % ts_name)
    vr4, g3 = rd("tileset\\%s.vr4" % ts_name)
    from gapio import GapReader
    gv = GapReader(vx4, g2 or [])
    gr = GapReader(vr4, g3 or [])
    return pal_bgr, pal_rgb, gv, gr, len(vx4) // 32, len(vr4) // 32


pal_bgr, pal_rgb, gv, gr, n_mega, n_mini = build_variants("jungle")
print("jungle: megas=%d minis=%d" % (n_mega, n_mini))


def mega_pixels(gv, gr, mi, nib_hi_first, idx_mask):
    out = []
    for k in range(16):
        v = gv.u16(mi * 32 + k * 2)
        flip = (v >> 15) & 1
        idx = v & idx_mask
        px = bytearray(64)
        for b in range(32):
            byte = gr.byte(idx * 32 + b)
            if nib_hi_first:
                px[b * 2] = (byte >> 4) & 0x0F
                px[b * 2 + 1] = byte & 0x0F
            else:
                px[b * 2] = byte & 0x0F
                px[b * 2 + 1] = (byte >> 4) & 0x0F
        out.append((px, flip))
    return out


cols = 8
rows = 6
TW = 32
img = Image.new("RGB", (cols * TW, rows * TW * 4), (0, 0, 0))
variants = [
    ("lo-nib BGR idx0x7FFF", pal_bgr, False, 0x7FFF),
    ("hi-nib BGR idx0x7FFF", pal_bgr, True, 0x7FFF),
    ("lo-nib RGB idx0x7FFF", pal_rgb, False, 0x7FFF),
    ("hi-nib RGB idx0x7FFF", pal_rgb, True, 0x7FFF),
]
for vi, (tag, pal, hi, mask) in enumerate(variants):
    for t in range(cols):
        mi = 1 + t
        mp = mega_pixels(gv, gr, mi, hi, mask)
        for k in range(16):
            px, flip = mp[k]
            mx = (k % 4) * 8
            my = (k // 4) * 8
            for yy in range(8):
                for xx in range(8):
                    c = pal[px[yy * 8 + (7 - xx if flip else xx)]]
                    img.putpixel((t * TW + mx + xx, vi * TW + my + yy), c)
img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
img.save(r"F:\KF\XJZB\AndroidPort\tools\out\tile_variants.png")
print("OK -> tile_variants.png")
