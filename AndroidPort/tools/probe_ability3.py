import sc_archive, grp as grpm
from PIL import Image, ImageDraw
import pipeline_sprites as ps
ar = ps.PT
if not ar.has(r"unit\cmdbtns\cmdicons.grp"):
    ar = ps.SD
d, g = ar.read_with_gaps(r"unit\cmdbtns\cmdicons.grp")
frames, mw, mh = grpm.decode_grp(d, g)

idxs = list(range(238, 300))
cell = 34
cols = 5
rows = (len(idxs) + cols - 1) // cols
scale = 4
lab = 22
sheet = Image.new("RGB", (cols * cell * scale, rows * (cell * scale + lab)), (18, 18, 24))
dr = ImageDraw.Draw(sheet)
for i, idx in enumerate(idxs):
    if idx >= len(frames):
        continue
    im = ps.frame_image(frames[idx], ps.BASE_PAL)
    x = (i % cols) * cell * scale
    y = (i // cols) * (cell * scale + lab)
    big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    sheet.paste(big, (x + 2, y + 2), big)
    dr.text((x + 2, y + cell * scale + 2), "f%d" % idx, fill=(255, 240, 120))
sheet.save("out/probe_ability_big.png")
print("saved", sheet.size)
