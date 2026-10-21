import sc_archive, grp as grpm
from PIL import Image, ImageDraw
import pipeline_sprites as ps
ar = ps.PT
if not ar.has(r"unit\cmdbtns\cmdicons.grp"):
    ar = ps.SD
d, g = ar.read_with_gaps(r"unit\cmdbtns\cmdicons.grp")
frames, mw, mh = grpm.decode_grp(d, g)
idxs = list(range(238, 256))
cell = 36; cols = 3; scale = 12; lab = 30
rows = (len(idxs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * cell * scale, rows * (cell * scale + lab)), (40, 40, 52))
dr = ImageDraw.Draw(sheet)
for i, idx in enumerate(idxs):
    im = ps.frame_image(frames[idx], ps.BASE_PAL)
    x = (i % cols) * cell * scale; y = (i // cols) * (cell * scale + lab)
    big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    sheet.paste(big, (x + 8, y + 8), big)
    dr.text((x + 8, y + cell * scale + 6), "f%d" % idx, fill=(255, 240, 120))
sheet.save("out/probe_ability_hi2.png")
print("saved", sheet.size)
