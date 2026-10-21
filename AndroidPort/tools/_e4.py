"""Batch E probe 4: SMK header census for campaign race logos + portraits."""
import os, sys, struct
sys.path.insert(0, ".")
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

FILES = [
    "glue\\Expcampaign\\XTerr.SMK",
    "glue\\Expcampaign\\XZerg.SMK",
    "glue\\Expcampaign\\XProt.SMK",
    "glue\\Expcampaign\\XTerrOn.SMK",
    "glue\\Expcampaign\\XZergOn.SMK",
    "glue\\Expcampaign\\XProtOn.SMK",
    "glue\\Expcampaign\\Disk.SMK",
    "portrait\\tmedic\\TMEfid00.smk",
    "portrait\\ZLurker\\ZLuFid00.smk",
    "portrait\\ZDevour\\ZDvFid00.smk",
    "portrait\\tBomber\\TBmFid00.smk",
    "portrait\\PCORSAIR\\PCsFid00.smk",
    "portrait\\pDarchon\\PDaFid00.smk",
    "portrait\\tSam\\Tsmfid00.smk",
    "portrait\\PRaz\\PRzFid00.smk",
    "portrait\\tmedic\\TMEtlk00.smk",
]
for p in FILES:
    ar = SD if SD.has(p) else (BD if BD.has(p) else None)
    if ar is None:
        print("%-34s MISS" % p)
        continue
    d, gaps = ar.read_with_gaps(p)
    if d[:4] not in (b"SMK2", b"SMK4"):
        print("%-34s not smk: %s" % (p, d[:8].hex(" ")))
        continue
    w, h, nf, delay, flags = struct.unpack_from("<IIIIi", d, 4)[:4] + (0,)
    w, h, nf, delay = struct.unpack_from("<IIII", d, 4)
    flags, = struct.unpack_from("<i", d, 20)
    aud = struct.unpack_from("<7I", d, 24)
    trees, mmap, mclr, full, typ, audtot, unused = struct.unpack_from("<7I", d, 52)
    toff, moff, coff, foff, tyoff = struct.unpack_from("<5I", d, 80)
    aoff = struct.unpack_from("<7I", d, 100)
    print("%-34s %s %dx%d f=%d delay=%d flags=0x%x size=%d" %
          (p, d[:4].decode(), w, h, nf, delay, flags & 0xffffffff, len(d)))
    print("      trees=%d mmap=%d mclr=%d full=%d type=%d audtot=%d" %
          (trees, mmap, mclr, full, typ, audtot))
    print("      offs trees=%d mmap=%d mclr=%d full=%d type=%d aud=%s" %
          (toff, moff, coff, foff, tyoff, aoff))
    print("      hdr_end_guess: bytes 128..143 = %s" % d[128:144].hex(" "))
    # find where the tree block plausibly starts: first offset after header
    for name, o in (("trees", toff), ("mmap", moff), ("mclr", coff),
                    ("full", foff), ("type", tyoff)):
        if 0 < o < len(d):
            print("      %-5s @%d first 24: %s" % (name, o, d[o:o + 24].hex(" ")))
        else:
            print("      %-5s @%d OUT OF RANGE" % (name, o))
    print()
