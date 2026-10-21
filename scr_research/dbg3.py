import sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"F:\KF\XJZB\AndroidPort\assets_src\maps\(1)Enslavers01.chk"
b = open(p,"rb").read()
print("at 17542:", b[17542:17590])
print("hex:", b[17542:17590].hex(" "))
# find all 4-char ascii tags followed by plausible sizes anywhere
import re
for m in re.finditer(rb"(?=[A-Z][A-Z0-9 ]{2}[A-Z0-9 ])([A-Z][A-Z0-9 ]{3})", b):
    pass
# instead: search known tags
for t in [b"UNID", b"MTXM", b"DD2 ", b"TILE", b"ISOM", b"THG2", b"MASK", b"STR ", b"UPRP", b"MRGN", b"TRIG", b"MBRF", b"SPRP", b"FORC", b"WAV ", b"UNIS", b"UPGS", b"TECS", b"SWNM", b"IVE2", b"UNIx", b"UPGx", b"TECx", b"STRx", b"COLR", b"CRGB", b"PUNI", b"UPGR", b"PTEC", b"UNIT", b"VER ", b"IVER", b"VCOD", b"IOWN", b"OWNR", b"ERA ", b"DIM ", b"SIDE", b"TYPE"]:
    idx = b.find(t)
    print(f"{t!r:8s} first at {idx}")
