import sc_archive
ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(ROOT + r"\StarDat.mpq")
cands = []
for base in ["Covert", "CovertOp", "CovertOps", "CoverOps", "Machine", "MachShop", "MachineShop",
             "MachineSh", "ControlTower", "CtrlTower", "Tower", "PhysicsLab", "PhysLab",
             "Nuke", "Nuclear", "Silo", "Comsat", "ComSat"]:
    for suf in [".grp", "s.grp", "St.grp", "Lab.grp", "Shop.grp", "Ops.grp", "Tower.grp"]:
        cands.append("unit\\terran\\" + base + suf)
found = []
for n in sorted(set(cands)):
    try:
        if SD.has(n):
            found.append(n)
    except Exception:
        pass
print("FOUND:")
for f in found:
    print("  " + f)
print("total", len(found), "of", len(set(cands)))
SD.close()
