"""Find music in the MPQs by enumerating the block table.

StarDat has no (listfile), and sfxdata.tbl has no music entries. But the block
table lists every file's (offset, csize, fsize, flags) regardless of name, so a
big unnamed block whose first bytes are "RIFF" is a WAV -- and in SC1 the only
multi-hundred-KB WAVs are the music tracks. Names are recovered by probing a
dictionary of plausible track names against the hash table.
"""
import os
import struct
import sc_archive

ROOT = r"F:\KF\XJZB"


def riff_probe(ar):
    """Return [(block_index, fsize, csize, flags, starts_with_RIFF)]."""
    out = []
    fp = ar.fp
    for i, (o, cs, fs, flags, rel) in enumerate(ar.block_table):
        if fs < 20000:                      # music is large; skip sfx-sized
            continue
        fp.seek(o)
        head = fp.read(4)
        out.append((i, fs, cs, flags, head == b"RIFF"))
    return out


def probe_names(ar, names):
    """Map block index -> name for the dictionary we can guess."""
    found = {}
    for n in names:
        bi = ar.find(n)
        if bi is not None:
            found[bi] = n
    return found


TRACKS = ["title", "ttitle", "ztitle", "radio", "radiofree", "terran1", "terran2",
          "terran3", "terran4", "zerg1", "zerg2", "zerg3", "zerg4", "protoss1",
          "protoss2", "protoss3", "protoss4", "ttheme1", "ztheme1", "ptheme1",
          "tvictory", "zvictory", "pvictory", "tdefeat", "zdefeat", "pdefeat",
          "brief", "tbrief", "zbrief", "pbrief", "game1", "tgam", "zgam", "pgam",
          "tmusic", "zmusic", "pmusic", "music"]
DIRS = ["sound\\music\\", "music\\", "sound\\", "sound\\music\\themes\\",
        "arr\\", "glue\\music\\", ""]


def candidates():
    out = set()
    for t in TRACKS:
        for d in DIRS:
            out.add(d + t + ".wav")
            out.add(d + t.upper() + ".WAV")
            out.add(d + t.capitalize() + ".wav")
    return sorted(out)


for label, fname in (("StarDat", "StarDat.mpq"), ("BrooDat", "BrooDat.mpq"),
                     ("patch_rt", "patch_rt.mpq")):
    ar = sc_archive.Archive(os.path.join(ROOT, fname))
    big = riff_probe(ar)
    named = probe_names(ar, candidates())
    named.update({bi: n for bi, n in probe_names(ar, candidates()).items()})
    # also mark every name we already know from extracted tables
    try:
        import pipeline_sounds as ps
        for n in ps.sfx:
            bi = ar.find("sound/" + n.replace("\\", "/"))
            if bi is not None:
                named[bi] = n
    except Exception:
        pass
    print("=== %s: %d blocks, %d >=20KB, %d RIFF ===" %
          (label, len(ar.block_table), len(big), sum(1 for b in big if b[4])))
    for bi, fs, cs, flags, riff in big:
        tag = named.get(bi, "???")
        print("  blk%-5d size=%-8d csize=%-8d flags=0x%04x RIFF=%-5s %s"
              % (bi, fs, cs, flags, riff, tag))
