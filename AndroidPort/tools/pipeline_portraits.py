"""Batch E (v2.12/v2.13): decode the SMK unit portraits to first-frame stills.

The plan expected a hand-written SMK decoder (400-600 lines); OpenCV ships an
ffmpeg-backed Smacker decoder, so this is a thin wrapper instead.

Smacker headers in this repack are the standard 104-byte layout, but the
*block offsets* are not stored in the header at all -- frames follow the header
as dword FrameSizes[Frames] + byte FrameTypes[Frames] + HuffmanTrees. That is
why nothing here reads offsets; cv2 handles all of it.

v2.13: expanded from the six Brood War-only portraits to the full roster.
The authoritative name source is arr/portdata.tbl (the game's own portrait
table); its strings are truncated by the repack's byte gaps, so several
directory names need completion variants. MPQ lookup is case-insensitive
("TMaRine" == "tmarine"). Campaign-cast dirs (pArtanis, tSam, UFlag9..12)
are still excluded -- only what a unit id owns goes in the list.
"""
import os
import shutil
import struct
import tempfile

import cv2
import numpy as np
from PIL import Image

import sc_archive

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\app\app\src\main\assets")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

# game type key -> candidate MPQ paths (first hit wins; classic in StarDat,
# Brood War additions in BrooDat)
PORTRAITS = [
    # --- Brood War (BrooDat only), wired since v2.12
    ("medic",      ["portrait\\tmedic\\TMEfid00.smk"]),
    ("lurker",     ["portrait\\ZLurker\\ZLuFid00.smk"]),
    ("devourer",   ["portrait\\ZDevour\\ZDvFid00.smk"]),
    ("valkyrie",   ["portrait\\tBomber\\TBmFid00.smk"]),
    ("corsair",    ["portrait\\PCORSAIR\\PCsFid00.smk"]),
    ("darchon",    ["portrait\\pDarchon\\PDaFid00.smk"]),
    # --- classic roster (StarDat), from portdata.tbl entries 0-111
    ("marine",     ["portrait\\tmarine\\TMaFid00.smk"]),
    ("ghost",      ["portrait\\tghost\\TGhFid00.smk"]),
    ("firebat",    ["portrait\\tfirebat\\TFbFid00.smk"]),
    ("vulture",    ["portrait\\tvulture\\TVuFid00.smk"]),
    ("goliath",    ["portrait\\tgoliath\\TGoFid00.smk"]),
    ("tank",       ["portrait\\ttank\\TTaFid00.smk"]),
    ("scv",        ["portrait\\tSCV\\TSCFid00.smk"]),
    ("wraith",     ["portrait\\tphoenix\\TPhFid00.smk"]),
    ("vessel",     ["portrait\\tvessel\\TVeFid00.smk"]),
    ("dropship",   ["portrait\\tdropshi\\TDrFid00.smk",
                    "portrait\\tdropship\\TDrFid00.smk"]),
    ("battlecruiser", ["portrait\\tbattlec\\TBaFid00.smk",
                       "portrait\\tbattlecr\\TBaFid00.smk",
                       "portrait\\tbattlecruiser\\TBaFid00.smk"]),
    ("zergling",   ["portrait\\ZZergl\\ZZeFid00.smk",
                    "portrait\\ZZergling\\ZZeFid00.smk"]),
    ("hydra",      ["portrait\\ZHydra\\ZHyFid00.smk"]),
    ("ultra",      ["portrait\\ZUltra\\ZUlFid00.smk"]),
    ("drone",      ["portrait\\ZDrone\\ZDrFid00.smk"]),
    ("over",       ["portrait\\ZOver\\ZOvFid00.smk"]),
    ("muta",       ["portrait\\ZMutalid\\ZMuFid00.smk"]),
    ("guardian",   ["portrait\\ZGuard\\ZGuFid00.smk",
                    "portrait\\ZGuardian\\ZGuFid00.smk"]),
    ("queen",      ["portrait\\ZQueen\\ZQuFid00.smk"]),
    ("defiler",    ["portrait\\ZDefiler\\ZDeFid00.smk"]),
    ("probe",      ["portrait\\PProbe\\PPrFid00.smk"]),
    ("zealot",     ["portrait\\PZealot\\PZeFid00.smk"]),
    ("dragoon",    ["portrait\\PDragoon\\PDrFid00.smk"]),
    ("templar",    ["portrait\\PTemplar\\PTeFid00.smk"]),
    ("dtemplar",   ["portrait\\UDTemplar\\UDTFid00.smk"]),
    ("archon",     ["portrait\\parchon\\PArFid00.smk"]),
    ("shuttle",    ["portrait\\pshuttle\\PShFid00.smk"]),
    ("scout",      ["portrait\\PScout\\PScFid00.smk"]),
    ("arbiter",    ["portrait\\PArbiter\\PAbFid00.smk"]),
    ("carrier",    ["portrait\\pcarrier\\PCaFid00.smk"]),
    ("reaver",     ["portrait\\PTrilo\\PTrFid00.smk"]),
    ("observer",   ["portrait\\PWitness\\PWiFid00.smk"]),
]

# The first frame is usually the "mouth closed, eyes forward" neutral pose,
# which is exactly what a console portrait wants.
FRAME = 0


def decode_smk(data, frame=0):
    """Return (H, W, 3) RGB ndarray for one frame of a Smacker file."""
    fd, tmp = tempfile.mkstemp(suffix=".smk")
    os.close(fd)
    try:
        with open(tmp, "wb") as f:
            f.write(data)
        cap = cv2.VideoCapture(tmp)
        if not cap.isOpened():
            return None, 0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        got = None
        i = 0
        while True:
            ok, fr = cap.read()
            if not ok:
                break
            if i == frame:
                got = fr
                break
            i += 1
        cap.release()
        return got, total
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def main():
    dst = os.path.join(OUT, "ui", "portrait")
    os.makedirs(dst, exist_ok=True)
    sheet = []
    for key, paths in PORTRAITS:
        mpq_hit = None
        for cand in paths:
            mpq = cand.replace("\\", "/")
            for ar in (SD, BD):
                if ar.has(mpq):
                    mpq_hit = (ar, mpq)
                    break
            if mpq_hit:
                break
        if not mpq_hit:
            print("MISS", key, paths[0])
            continue
        ar, mpq = mpq_hit
        data = ar.read(mpq)
        # sanity-check the signature so a repack surprise is loud, not silent
        sig = data[:4]
        w, h, nf = struct.unpack_from("<III", data, 4)
        frame, total = decode_smk(data, FRAME)
        if frame is None:
            print("DECODE FAIL", key, len(data), sig)
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(rgb)
        out = os.path.join(dst, "portrait_%s.png" % key)
        im.save(out)
        print("%-13s %-24s hdr=%s %dx%d f=%d -> %s"
              % (key, mpq, sig.decode("latin1"), w, h, nf, os.path.basename(out)))
        sheet.append((key, im))

    if sheet:
        Z = 3
        cw = max(im.width for _, im in sheet) * Z
        ch = max(im.height for _, im in sheet) * Z
        page = Image.new("RGB", (cw * len(sheet), ch), (16, 16, 20))
        for i, (key, im) in enumerate(sheet):
            page.paste(im.resize((im.width * Z, im.height * Z), Image.NEAREST),
                       (i * cw, 0))
        page.save(os.path.join(ROOT, r"AndroidPort\tools\out\_portraits_sheet.png"))
        print("sheet", page.size)


if __name__ == "__main__":
    main()
