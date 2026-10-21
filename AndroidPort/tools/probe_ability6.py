import sc_archive, grp as grpm
from PIL import Image, ImageDraw
import pipeline_sprites as ps
ar = ps.PT
if not ar.has(r"unit\cmdbtns\cmdicons.grp"):
    ar = ps.SD
d, g = ar.read_with_gaps(r"unit\cmdbtns\cmdicons.grp")
frames, mw, mh = grpm.decode_grp(d, g)
idxs = [232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247]
cell = 36; cols = 4; scale = 9; lab = 26
rows = (len(idxs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * cell * scale, rows * (cell * scale + lab)), (40, 40, 52))
dr = ImageDraw.Draw(sheet)
for i, idx in enumerate(idxs):
    im = ps.frame_image(frames[idx], ps.BASE_PAL)
    x = (i % cols) * cell * scale; y = (i // cols) * (cell * scale + lab)
    big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    sheet.paste(big, (x + 6, y + 6), big)
    dr.text((x + 6, y + cell * scale + 4), "f%d" % idx, fill=(255, 240, 120))
sheet.save("out/probe_ability_hi.png")
print("saved", sheet.size)
