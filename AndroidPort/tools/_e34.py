# Final batch-E evidence: the six SMK first-frame portraits as rendered by the
# real device, cropped from the selection panel of each tap screenshot.
import os
from PIL import Image, ImageDraw

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
PANEL = (470, 930, 1010, 1160)          # portrait + name + hp block, device px
PORTRAIT = PANEL                        # keep the whole panel: art + name proves identity
ITEMS = [
    ("medic",    "_e33_medic.png"),
    ("lurker",   "sweep\\t420.png"),
    ("devourer", "sweep\\t590.png"),
    ("valkyrie", "sweep\\t720.png"),
    ("corsair",  "sweep\\t150.png"),
    ("darchon",  "sweep\\t990.png"),
]
W, H = PORTRAIT[2] - PORTRAIT[0], PORTRAIT[3] - PORTRAIT[1]
sheet = Image.new("RGB", (len(ITEMS) * W, H + 22), (16, 16, 22))
d = ImageDraw.Draw(sheet)
ok = []
for i, (name, rel) in enumerate(ITEMS):
    p = os.path.join(OUT, rel)
    if not os.path.exists(p):
        print("MISSING", rel); continue
    crop = Image.open(p).convert("RGB").crop(PORTRAIT)
    sheet.paste(crop, (i * W, 22))
    d.text((i * W + 4, 5), name, fill=(255, 220, 90))
    ok.append(name)
sheet = sheet
sheet.save(os.path.join(OUT, "_e34_portraits.png"))
print("confirmed on device:", ok)
print("wrote _e34_portraits.png", sheet.size)
