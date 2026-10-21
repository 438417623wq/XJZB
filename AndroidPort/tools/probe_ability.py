import sc_archive, grp as grpm
from PIL import Image
import pipeline_sprites as ps

ROOT = r"F:\KF\XJZB"
for name, ar in (("PT", ps.PT), ("SD", ps.SD), ("BD", ps.BD)):
    if ar.has(r"unit\cmdbtns\cmdicons.grp"):
        d, g = ar.read_with_gaps(r"unit\cmdbtns\cmdicons.grp")
        frames, mw, mh = grpm.decode_grp(d, g)
        print(name, len(frames), mw, mh)
        break

idxs = list(range(232, 250))
cell = 36
cols = 6
rows = (len(idxs) + cols - 1) // cols
sheet = Image.new("RGBA", (cols * cell, rows * cell), (30, 30, 40, 255))
for i, idx in enumerate(idxs):
    if idx >= len(frames):
        continue
    im = ps.frame_image(frames[idx], ps.BASE_PAL)
    x = (i % cols) * cell
    y = (i // cols) * cell
    sheet.paste(im, (x + 2, y + 2))
sheet = sheet.resize((cols * cell * 4, rows * cell * 4), Image.NEAREST)
sheet.save("out/probe_ability_icons.png")
print("saved", idxs)
