"""Probe BrooDat for BW tilesets and find units.pal."""
import sc_archive

BD = sc_archive.Archive(r"F:\KF\XJZB\BrooDat.mpq")
SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
PT = sc_archive.Archive(r"F:\KF\XJZB\patch_rt.mpq")

tss = ["ashworld", "badlands", "desert", "ice", "jungle", "platform", "installation", "twilight"]
for ts in tss:
    for ext in ["cv5", "vf4", "vx4", "vr4", "wpe", "pal"]:
        p = "tileset\\%s.%s" % (ts, ext)
        for tag, ar in (("BD", BD), ("SD", SD), ("PT", PT)):
            if ar.has(p):
                print("FOUND %-3s %s" % (tag, p))
                break

# units palette hunting
cands = []
for d in ["tileset", "", "tileset\\jungle", "game", "arr", "rez", "unit"]:
    for n in ["units.pal", "unit.pal", "pal_units.pal", "tileset.pal", "tunit.pal", "gpal.pal"]:
        cands.append((d + "\\" if d else "") + n)
for p in cands:
    for tag, ar in (("BD", BD), ("SD", SD), ("PT", PT)):
        if ar.has(p):
            print("FOUND %-3s %s" % (tag, p))
            break

# list what tileset files exist in BD by scanning hash table names? try listing via block scan
# instead: check a couple of known SC files
for p in ["tileset\\ashworld.cv5", "tileset\\twilight.wpe", "tileset\\desert.vr4",
          "tileset\\ice.vx4", "tileset\\installation.vr4", "tileset\\jungle.units.pal"]:
    print(p, BD.has(p), SD.has(p), PT.has(p))
