"""Quantify sector losses across all assets we need."""
import struct
import sc_archive
from pkware import explode

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
BD = sc_archive.Archive(r"F:\KF\XJZB\BrooDat.mpq")

GRPS = ["unit\\terran\\marine.grp", "unit\\terran\\SCV.grp", "unit\\terran\\firebat.grp",
        "unit\\terran\\Vulture.grp", "unit\\terran\\tank.grp", "unit\\terran\\stank.grp",
        "unit\\terran\\goliath.grp", "unit\\terran\\wessel.grp", "unit\\terran\\dropship.grp",
        "unit\\terran\\BattleCr.grp", "unit\\terran\\control.grp", "unit\\terran\\Depot.grp",
        "unit\\terran\\TBarrack.grp", "unit\\terran\\refinery.grp", "unit\\terran\\factory.grp",
        "unit\\terran\\missile.grp", "unit\\terran\\PillBox.grp", "unit\\terran\\Academy.grp",
        "unit\\terran\\starport.grp", "unit\\zerg\\zergling.grp", "unit\\zerg\\hydra.grp",
        "unit\\zerg\\mutalid.grp", "unit\\zerg\\overlord.grp", "unit\\zerg\\hatchery.grp",
        "unit\\zerg\\drone.grp", "unit\\zerg\\larva.grp", "unit\\zerg\\egg.grp",
        "unit\\zerg\\ultra.grp", "unit\\zerg\\Snakey.grp", "unit\\zerg\\Lair.grp",
        "unit\\zerg\\Hive.grp", "unit\\zerg\\spire.grp",
        "unit\\neutral\\min01.grp", "unit\\neutral\\min02.grp", "unit\\neutral\\min03.grp",
        "unit\\neutral\\Geyser.grp", "unit\\cmdbtns\\cmdicons.grp"]
TERRAIN = []
for ts in ["badlands", "platform", "jungle", "ashworld", "desert", "ice", "twilight"]:
    for ext in ["cv5", "vf4", "vx4", "vr4", "wpe"]:
        TERRAIN.append("tileset\\%s.%s" % (ts, ext))


def analyze(ar, name):
    bi = ar.find(name)
    if bi is None:
        return None
    o, cs, fs, flags, rel = ar.block_table[bi]
    key = sc_archive.hash_string(name.split("\\")[-1], sc_archive.HASH_FILE_KEY)
    key = ((key + rel) ^ fs) & 0xFFFFFFFF
    ar.fp.seek(o)
    raw = ar.fp.read(cs)
    num = (fs + ar.sector_size - 1) // ar.sector_size
    tbl = ar._try_sector_table(raw, key, flags, num, ar.sector_size)
    if not tbl:
        # single-sector file
        sec = raw
        if flags & 0x00010000:
            sec = sc_archive.decrypt(sec, key)
        try:
            out = sc_archive.decompress_sector(sec, fs)
            return (fs, len(out), [])
        except Exception:
            return None
    losses = []
    pos = 0
    for i in range(num):
        sec = raw[tbl[i]:tbl[i + 1]]
        if flags & 0x00010000:
            sec = sc_archive.decrypt(sec, (key + i) & 0xFFFFFFFF)
        want = min(ar.sector_size, fs - pos)
        try:
            out = sc_archive.decompress_sector(sec, want)
        except Exception:
            out = b""
        # natural length: explode uncapped when pkware
        if (flags & 0x00000200) and (sec[0] & 0x08 if sec else False):
            try:
                nat = len(explode(sec[1:], None))
            except Exception:
                nat = len(out)
        else:
            nat = len(out)
        if nat != want:
            losses.append((pos + nat, want - nat))
        pos += nat
    return (fs, pos, losses)


print("=== GRPs ===")
tot_bad = 0
for n in GRPS:
    for tag, ar in (("SD", SD), ("BD", BD)):
        r = analyze(ar, n)
        if r:
            fs, got, losses = r
            if losses:
                tot_bad += 1
                print("%-36s fs=%6d got=%6d losses=%s" % (n, fs, got, losses))
            break
print("GRPs with losses: %d / %d" % (tot_bad, len(GRPS)))

print("=== terrain ===")
tb = 0
for n in TERRAIN:
    for tag, ar in (("SD", SD), ("BD", BD)):
        r = analyze(ar, n)
        if r:
            fs, got, losses = r
            if losses:
                tb += 1
                print("%-28s fs=%6d got=%6d losses=%s" % (n, fs, got, losses))
            break
print("terrain files with losses: %d / %d" % (tb, len(TERRAIN)))
