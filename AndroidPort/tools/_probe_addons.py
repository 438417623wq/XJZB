import sc_archive
ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(ROOT + r"\StarDat.mpq")
BD = sc_archive.Archive(ROOT + r"\BrooDat.mpq")
names = [r"unit\terran\Comsat.grp", r"unit\terran\ComsatSt.grp", r"unit\terran\silo.grp",
         r"unit\terran\NukeSilo.grp", r"unit\terran\NucleSilo.grp",
         r"unit\terran\Covert.grp", r"unit\terran\CovertOp.grp",
         r"unit\terran\Physics.grp", r"unit\terran\PhysicsLab.grp",
         r"unit\terran\Control.grp", r"unit\terran\ControlTower.grp",
         r"unit\terran\Machine.grp", r"unit\terran\MachShop.grp",
         r"unit\terran\addon.grp",
         r"unit\terran\ComsatSt.grp"]
for n in names:
    got = []
    for tag, A in (("SD", SD), ("BD", BD)):
        try:
            if A.has(n): got.append(tag)
        except Exception as e:
            pass
    print(("FOUND " + ",".join(got) + "  " if got else "no     ") + n)
SD.close(); BD.close()
