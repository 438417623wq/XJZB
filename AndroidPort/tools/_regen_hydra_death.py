"""v2.44: regenerate ONLY the death_hydra sheet + its manifest rows.

pipeline_sprites.py now points death_hydra at block 12 (frames 204..220, the
real red death burst measured by _hydrablocks.py) instead of the trailing
partial block 17 (289..296 -- blank filler, meanRGB ~(1.9,1.9,2.1)); running
the full pipeline would rewrite every sheet, and the asset diff should stay
one file per fix. This driver calls the pipeline's own add_anim for the one
key, then patches manifest.txt / manifest.json rows in place.

The two new PNGs are left in place for slim_assets.py to convert (png_to_webp
deletes the .png after writing the .webp, exactly like a full run).
"""
import json
import os
import sys

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_sprites as ps

KEY = "death_hydra"
PATH, FIRST = ps.ANIMS[KEY]

rows = [ln.rstrip("\n") for ln in open(os.path.join(ps.SPR, "manifest.txt"),
                                       encoding="utf8")]
meta = json.load(open(os.path.join(ps.SPR, "manifest.json"), encoding="utf8"))

new_rows = []
for r in rows:
    if r.split(",")[0] == KEY:
        new_rows.append(("DEATH_HYDRA", None))   # marker, replaced below
    else:
        new_rows.append(r)
# add_anim appends its own row and writes the sheets; drop the marker first
rows = [r for r in new_rows if r != ("DEATH_HYDRA", None)]
rows_out = list(rows)
entry = ps.add_anim(KEY, PATH, FIRST, rows_out, meta["units"],
                    count=ps.ANIM_COUNTS.get(KEY), stride=ps.ANIM_STRIDES.get(KEY, 1))
if entry is None:
    raise SystemExit("add_anim failed")

with open(os.path.join(ps.SPR, "manifest.txt"), "w", encoding="utf8") as fp:
    fp.write("\n".join(rows_out) + "\n")
with open(os.path.join(ps.SPR, "manifest.json"), "w", encoding="utf8") as fp:
    json.dump(meta, fp, ensure_ascii=False, indent=1)
print("manifest rows:", len(rows_out))
