"""Account for every large block in StarDat/BrooDat by name.

Builds the biggest name dictionary we have (sfx table, tilesets, images.tbl GRP
paths, UI art, tables, maps) and reports which >=300KB blocks remain unnamed --
those are the only candidates for music.
"""
import os
import struct
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))


def parse_tbl(data):
    n, = struct.unpack_from("<H", data, 0)
    offs = struct.unpack_from("<%dH" % n, data, 2)
    return [data[offs[i]:data.find(b"\0", offs[i])].decode("latin1") for i in range(n)]


def build_names():
    names = []
    # sounds
    try:
        import pipeline_sounds as ps
        for n in ps.sfx:
            names.append("sound/" + n.replace("\\", "/"))
    except Exception:
        pass
    # tilesets
    for ts in ("badlands", "platform", "install", "ashworld", "jungle",
               "desert", "ice", "twilight"):
        for ext in ("wpe", "cv5", "vx4", "vr4", "vf4"):
            names.append("tileset/%s.%s" % (ts, ext))
            names.append("tileset/%s-nc.%s" % (ts, ext))
    # images.tbl GRP paths (both archives)
    for src in ("images_tbl.txt",):
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), src)
        if os.path.exists(p):
            for l in open(p, encoding="utf8", errors="ignore"):
                l = l.strip()
                if l:
                    names.append("unit/" + l.replace("\\", "/"))
    try:
        for ar in (SD, BD):
            names += [l.replace("\\", "/") for l in parse_tbl(ar.read("arr/images.tbl"))]
    except Exception:
        pass
    # known art / tables / maps
    names += ["unit/wirefram/wirefram.grp", "unit/cmdbtns/cmdicons.grp",
              "glue/title/Title.pcx", "rez/stat_txt.tbl", "arr/sfxdata.tbl",
              "arr/images.tbl", "arr/units.dat", "arr/flingy.dat",
              "arr/orders.dat", "arr/techdata.tbl", "arr/upgrade.dat",
              "arr/weapons.dat", "arr/mapdata.tbl", "rez/gluAll.tbl",
              "rezzoo/stat_tbl.tbl", "arr/portdata.tbl", "arr/sprites.tbl"]
    for d in ("glue/ScorePd", "glue/Console", "glue/Briefing", "glue/Expcampaign"):
        for f in ("TProt.pcx", "TZerg.pcx", "TTerr.pcx", "Prot.pcx", "Zerg.pcx",
                  "Terr.pcx", "ScoreBack.pcx", "tConsole.pcx", "zConsole.pcx",
                  "pConsole.pcx"):
            names.append("%s/%s" % (d, f))
    for m in ("(4)Blood Bath", "(2)Bottleneck", "(2)Boxer", "(8)The Hunters",
              "(4)Dark Crystal", "(2)River Crossing", "(3)Three Kingdoms",
              "(2)The Small Divide", "(4)Cyclone", "(2)Volcanis"):
        names.append("maps/%s.scm" % m)
        names.append("maps/%s.scx" % m)
    # BrooDat listfile
    lf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "listfile_BrooDat.txt")
    if os.path.exists(lf):
        for l in open(lf, encoding="utf8", errors="ignore"):
            l = l.strip()
            if l:
                names.append(l.replace("\\", "/"))
    return [n for n in names if n]


for label, ar in (("StarDat", SD), ("BrooDat", BD)):
    bi2name = {}
    for n in build_names():
        bi = ar.find(n)
        if bi is not None:
            bi2name[bi] = n
    big = sorted(((fs, cs, i, flags) for i, (o, cs, fs, flags, rel)
                  in enumerate(ar.block_table) if fs >= 300000), reverse=True)
    print("=== %s: %d blocks, %d named, %d >=300KB ==="
          % (label, len(ar.block_table), len(bi2name), len(big)))
    for fs, cs, i, flags in big:
        n = bi2name.get(i)
        enc = "enc" if flags & sc_archive.FLAG_ENCRYPTED else "   "
        print("  blk%-5d fsize=%-8d csize=%-8d %s %s" % (i, fs, cs, enc, n or "???"))
