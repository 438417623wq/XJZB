"""Batch E probe 5: pull SMK first frames out with OpenCV (bundled ffmpeg)."""
import os, sys
import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, ".")
import sc_archive

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

# our playable roster -> retail portrait group
PAIRS = [
    ("medic",      r"portrait\tmedic\TMEfid00.smk"),
    ("lurker",     r"portrait\ZLurker\ZLuFid00.smk"),
    ("devourer",   r"portrait\ZDevour\ZDvFid00.smk"),
    ("valkyrie",   r"portrait\tBomber\TBmFid00.smk"),
    ("corsair",    r"portrait\PCORSAIR\PCsFid00.smk"),
    ("darkarchon", r"portrait\pDarchon\PDaFid00.smk"),
    ("_sam",       r"portrait\tSam\Tsmfid00.smk"),
    ("_razagal",   r"portrait\PRaz\PRzFid00.smk"),
]

os.makedirs(OUT, exist_ok=True)
tiles = []
for key, p in PAIRS:
    ar = SD if SD.has(p) else (BD if BD.has(p) else None)
    if ar is None:
        print("%-12s MISS" % key)
        continue
    d, _ = ar.read_with_gaps(p)
    tmp = os.path.join(OUT, "_e5_tmp.smk")
    with open(tmp, "wb") as f:
        f.write(d)
    cap = cv2.VideoCapture(tmp)
    ok, fr = cap.read()
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    os.remove(tmp)
    if not ok or fr is None:
        print("%-12s DECODE FAIL" % key)
        continue
    rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
    im = Image.fromarray(rgb)
    png = os.path.join(OUT, "_e5_%s.png" % key)
    im.save(png)
    print("%-12s %-34s %dx%d frames=%d -> %s" % (key, p, im.width, im.height, n, os.path.basename(png)))
    tiles.append((key, im))

if tiles:
    Z = 3
    cell = 64 * Z
    pad = 18
    sheet = Image.new("RGB", (cell * len(tiles), cell + pad), (24, 24, 32))
    dr = ImageDraw.Draw(sheet)
    for i, (k, im) in enumerate(tiles):
        big = im.resize((im.width * Z, im.height * Z), Image.NEAREST)
        ox = i * cell + (cell - big.width) // 2
        oy = pad + (cell - big.height) // 2
        sheet.paste(big, (ox, oy))
        dr.text((i * cell + 4, 3), k, fill=(240, 220, 120))
    sp = os.path.join(OUT, "_e5_sheet.png")
    sheet.save(sp)
    print("sheet ->", sp)
