"""Check offset-table sanity across many GRPs to isolate the corruption."""
import struct
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")

names = ["unit\\terran\\marine.grp", "unit\\terran\\SCV.grp", "unit\\terran\\firebat.grp",
         "unit\\terran\\Vulture.grp", "unit\\terran\\tank.grp", "unit\\terran\\control.grp",
         "unit\\terran\\Depot.grp", "unit\\terran\\TBarrack.grp", "unit\\terran\\factory.grp",
         "unit\\terran\\refinery.grp", "unit\\terran\\missile.grp", "unit\\terran\\PillBox.grp",
         "unit\\terran\\goliath.grp", "unit\\terran\\wessel.grp", "unit\\terran\\dropship.grp",
         "unit\\terran\\BattleCr.grp", "unit\\terran\\starport.grp", "unit\\terran\\Academy.grp",
         "unit\\zerg\\zergling.grp", "unit\\zerg\\hydra.grp", "unit\\zerg\\mutalid.grp",
         "unit\\zerg\\overlord.grp", "unit\\zerg\\hatchery.grp", "unit\\zerg\\drone.grp",
         "unit\\zerg\\larva.grp", "unit\\zerg\\egg.grp", "unit\\zerg\\ultra.grp",
         "unit\\neutral\\min01.grp", "unit\\neutral\\min02.grp", "unit\\neutral\\min03.grp",
         "unit\\neutral\\Geyser.grp", "unit\\cmdbtns\\cmdicons.grp"]

for n in names:
    try:
        d = SD.read(n)
    except Exception as e:
        print("%-36s READ FAIL %s" % (n, e))
        continue
    fc, mw, mh = struct.unpack_from("<HHH", d, 0)
    exp0 = 6 + fc * 4
    ok = None
    if fc * 4 + 6 <= len(d):
        offs = struct.unpack_from("<%dI" % min(fc, 8), d, 6)
        ok = (offs[0] == exp0) and all(offs[i] <= offs[i + 1] for i in range(len(offs) - 1))
    print("%-36s frames=%3d %3dx%-3d size=%6d tableOK=%s first=%s" % (
        n, fc, mw, mh, len(d), ok, offs[:3] if ok is not None else "-"))
