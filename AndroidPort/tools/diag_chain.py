"""Render megatile 64 under 4 chain interpretations at 4x zoom."""
import sc_archive
from gapio import GapReader
from PIL import Image, ImageDraw

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
TS = "platform"


def load(TS):
    def rd(n):
        return SD.read_with_gaps("tileset\\%s.%s" % (TS, n))
    wpe, _ = rd("wpe")
    if len(wpe) < 1024:
        wpe += bytes(1024 - len(wpe))
    pal = [(wpe[i * 4 + 2], wpe[i * 4 + 1], wpe[i * 4]) for i in range(256)]
    cv5, g0 = rd("cv5")
    vx4, g2 = rd("vx4")
    vr4, g3 = rd("vr4")
    gc, gv, gr = GapReader(cv5, g0 or []), GapReader(vx4, g2 or []), GapReader(vr4, g3 or [])
    n_mega = len(cv5) // 52
    megas = [[gc.u16(m * 52 + k * 2) for k in range(16)] for m in range(n_mega)]
    vx4_flat = [gv.u16(i * 2) for i in range(len(vx4) // 2)]
    pixels = [bytearray(gr.bytes_at(m * 64, 64)) for m in range(len(vr4) // 64)]
    return pal, megas, vx4_flat, pixels


pal, megas, vx4_flat, pixels = load(TS)
mi = 64
Z = 4
img = Image.new("RGB", (4 * (32 * Z + 8), 32 * Z + 12), (20, 20, 20))
dr = ImageDraw.Draw(img)


def draw_mega(vi, subtiles):
    """subtiles: list of 16 (vr4_index, flip)."""
    ox0 = vi * (32 * Z + 8)
    for k in range(16):
        vri, flip = subtiles[k]
        mini = pixels[vri] if vri < len(pixels) else bytes(64)
        mx = (k % 4) * 8
        my = (k // 4) * 8
        for yy in range(8):
            for xx in range(8):
                sx = (7 - xx) if flip else xx
                v = mini[yy * 8 + sx]
                for dy in range(Z):
                    for dx in range(Z):
                        img.putpixel((ox0 + (mx + xx) * Z + dx, (my + yy) * Z + dy), pal[v])


variants = []
# (a) cv5[k] -> vx4 entry -> vr4
variants.append([(vx4_flat[megas[mi][k]] & 0x7FFF, (vx4_flat[megas[mi][k]] >> 15) & 1) for k in range(16)])
# (b) cv5[k] -> vr4 directly
variants.append([(megas[mi][k] & 0x7FFF, (megas[mi][k] >> 15) & 1) for k in range(16)])
# (c) cv5[0]+k -> vx4 -> vr4
variants.append([(vx4_flat[megas[mi][0] + k] & 0x7FFF, (vx4_flat[megas[mi][0] + k] >> 15) & 1) for k in range(16)])
# (d) cv5[0]*16+k -> vr4
variants.append([((megas[mi][0] * 16 + k) & 0x7FFF, 0) for k in range(16)])

for vi, subtiles in enumerate(variants):
    draw_mega(vi, subtiles)
    dr.text((vi * (32 * Z + 8) + 4, 32 * Z + 1), "abcd"[vi], fill=(255, 0, 0))

img.save(r"F:\KF\XJZB\AndroidPort\tools\out\chain_variants.png")
print("done: a=cv5>vx4>vr4 b=cv5>vr4 c=cv5base+k>vx4 d=base*16+k>vr4")
