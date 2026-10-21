import sc_archive, grp as grpm
from PIL import Image, ImageDraw
import pipeline_sprites as ps

ar = ps.PT
if not ar.has(r"unit\cmdbtns\cmdicons.grp"):
    ar = ps.SD
d, g = ar.read_with_gaps(r"unit\cmdbtns\cmdicons.grp")
frames, mw, mh = grpm.decode_grp(d, g)
print("frames", len(frames))

idxs = list(range(238, 276))
cell = 40
cols = 8
rows = (len(idxs) + cols - 1) // cols
scale = 3
sheet = Image.new("RGB", (cols * cell * scale, rows * (cell + 12) * scale), (20, 20, 28))
dr = ImageDraw.Draw(sheet)
for i, idx in enumerate(idxs):
    if idx >= len(frames):
        continue
    im = ps.frame_image(frames[idx], ps.BASE_PAL)
    x = (i % cols) * cell * scale
    y = (i // cols) * (cell + 12) * scale
    big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    sheet.paste(big, (x + 4, y + 4), big)
    dr.text((x + 4, y + (cell * scale) + 2), str(idx), fill=(255, 230, 120))
sheet.save("out/probe_ability_238_275.png")
print("saved")
