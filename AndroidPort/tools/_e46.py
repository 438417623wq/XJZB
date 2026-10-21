# Final batch-C evidence: crop the terran build page-2 command card.
import os
from PIL import Image

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
im = Image.open(os.path.join(OUT, "_e45_build2.png")).convert("RGB")
card = im.crop((2560, 900, 2992, 1230))
card = card.resize((card.width * 2, card.height * 2), Image.LANCZOS)
card.save(os.path.join(OUT, "_e46_terran_page2.png"))
print("wrote", card.size)
