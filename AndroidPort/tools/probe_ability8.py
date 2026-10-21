import sc_archive, grp as grpm
from PIL import Image, ImageDraw
import pipeline_sprites as ps
ar = ps.PT
if not ar.has(r"unit\cmdbtns\cmdicons.grp"):
    ar = ps.SD
d, g = ar.read_with_gaps(r"unit\cmdbtns\cmdicons.grp")
frames, mw, mh = grpm.decode_grp(d, g)
idxs = list(range(255, 330))
cell = 34; cols = 8; scale = 3; lab = 16
rows = (len(idxs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * cell * scale, rows * (cell * scale + lab)), (30, 30, 40))
dr = ImageDraw.Draw(sheet)
for i, idx in enumerate(idxs):
    if idx >= len(frames): continue
    im = ps.frame_image(frames[idx], ps.BASE_PAL)
    x = (i % cols) * cell * scale; y = (i // cols) * (cell * scale + lab)
    big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    sheet.paste(big, (x + 2, y + 2), big)
    dr.text((x + 2, y + cell * scale + 2), str(idx), fill=(255, 240, 120))
sheet.save("out/probe_ability_255_330.png")
print("saved", sheet.size)
