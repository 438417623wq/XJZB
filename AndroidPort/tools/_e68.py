# v2.12 final evidence sheet: settings sheet "返回" fix + terran build page 2.
import os
from PIL import Image, ImageDraw

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"


def crop(name, box):
    im = Image.open(os.path.join(OUT, name)).convert("RGB")
    return im.crop(box)


# settings overlay (before) -> pause menu (after) : proves set:back now routes
a = crop("_e61_settings.png", (1150, 60, 2100, 1000))
b = crop("_e62_after_back.png", (1150, 60, 2100, 1000))
# terran build page 2
c = crop("_e67_page2.png", (2560, 900, 2992, 1230))
c = c.resize((c.width * 2, c.height * 2), Image.NEAREST)

w = a.width + b.width + 40
h = max(a.height, b.height) + 34 + c.height + 20
sheet = Image.new("RGB", (w, h), (18, 20, 26))
d = ImageDraw.Draw(sheet)
sheet.paste(a, (0, 30))
sheet.paste(b, (a.width + 40, 30))
d.text((6, 8), "settings open (before)", fill=(255, 235, 80))
d.text((a.width + 46, 8), "after tapping 返回 -> pause menu", fill=(255, 235, 80))
sheet.paste(c, (0, a.height + 50))
d.text((6, a.height + 34), "terran build page 2 (星港/军械库/科学设施/返回)", fill=(120, 255, 160))
sheet.save(os.path.join(OUT, "_e68_final_evidence.png"))
print("wrote", sheet.size)
