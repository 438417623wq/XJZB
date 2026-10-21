import sc_archive, grp as grpm
ROOT = r"F:\KF\XJZB"
cands = [r"unit\thingy\NukeTarg.grp", r"unit\thingy\NukeBeam.grp", r"unit\thingy\NukeHit.grp",
         r"unit\thingy\nuketarg.grp", r"unit\thingy\nukebeam.grp", r"unit\thingy\nukehit.grp"]
for mpq in ("StarDat.mpq", "BrooDat.mpq", "patch_rt.mpq"):
    A = sc_archive.Archive(ROOT + "\\" + mpq)
    for n in cands:
        try:
            if A.has(n):
                data, gaps = A.read_with_gaps(n)
                fr, mw, mh = grpm.decode_grp(data, gaps)
                print("%-16s %-28s frames=%d max=%dx%d" % (mpq, n, len(fr), mw, mh))
        except Exception as e:
            pass
    A.close()
