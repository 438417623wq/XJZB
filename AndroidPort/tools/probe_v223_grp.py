import sys
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import sc_archive, grp as grpm
ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(ROOT + r"\StarDat.mpq")
for path in [r"unit\terran\goliath.grp", r"unit\terran\dropship.grp"]:
    d, g = SD.read_with_gaps(path)
    frames, mw, mh = grpm.decode_grp(d, g)
    print("== %s frames=%d %dx%d" % (path, len(frames), mw, mh))
    n = len(frames)
    for b in range((n + 16) // 17):
        cnt = []
        for f in frames[b * 17:b * 17 + 17]:
            cnt.append(sum(1 for v in f["px"] if v))
        print("   block %2d: %s" % (b, cnt))
