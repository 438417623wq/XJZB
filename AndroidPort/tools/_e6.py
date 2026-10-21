"""Batch E probe 6: decode the expansion-campaign race SMKs (candidate emblems)."""
import os, sys
import cv2
from PIL import Image, ImageDraw

sys.path.insert(0, ".")
import sc_archive

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

FILES = [
    r"glue\Expcampaign\XTerr.SMK",
    r"glue\Expcampaign\XTerrOn.SMK",
    r"glue\Expcampaign\XZerg.SMK",
    r"glue\Expcampaign\XZergOn.SMK",
    r"glue\Expcampaign\XProt.SMK",
    r"glue\Expcampaign\XProtOn.SMK",
    r"glue\Expcampaign\Disk.SMK",
]
tiles = []
for p in FILES:
    ar = SD if SD.has(p) else (BD if BD.has(p) else None)
    if ar is None:
        print("%-34s MISS" % p)
        continue
    d, _ = ar.read_with_gaps(p)
    tmp = os.path.join(OUT, "_e6_tmp.smk")
    with open(tmp, "wb") as f:
        f.write(d)
    cap = cv2.VideoCapture(tmp)
    frames = []
    while True:
        ok, fr = cap.read()
        if not ok or fr is None:
            break
        frames.append(fr)
        if len(frames) >= 3:
            break
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    os.remove(tmp)
    name = os.path.basename(p).replace(".SMK", "")
    print("%-34s frames=%d (got %d)" % (p, n, len(frames)))
    for i, fr in enumerate(frames):
        rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(rgb)
        im.save(os.path.join(OUT, "_e6_%s_%d.png" % (name, i)))
        tiles.append(("%s#%d" % (name, i), im))

if tiles:
    H = 260
    W = 0
    scaled = []
    for k, im in tiles:
        sc = min(1.0, H / im.height)
        s = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.NEAREST)
        scaled.append((k, s))
        W += s.width + 6
    sheet = Image.new("RGB", (W + 6, H + 18), (24, 24, 32))
    dr = ImageDraw.Draw(sheet)
    x = 6
    for k, s in scaled:
        sheet.paste(s, (x, 16))
        dr.text((x, 3), k, fill=(240, 220, 120))
        x += s.width + 6
    sp = os.path.join(OUT, "_e6_sheet.png")
    sheet.save(sp)
    print("sheet ->", sp)
