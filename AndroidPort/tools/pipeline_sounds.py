"""Extract a usable sound set + menu background from the MPQs.

WAVs in this repack are stored raw but truncated (the RIFF header still claims
the original size); we rewrite the chunk sizes to the actual payload so
SoundPool can play them.
"""
import os
import struct
import sc_archive

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\app\app\src\main\assets")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))


def parse_tbl(data):
    n, = struct.unpack_from("<H", data, 0)
    offs = struct.unpack_from("<%dH" % n, data, 2)
    out = []
    for i in range(n):
        end = data.find(b"\0", offs[i])
        out.append(data[offs[i]:end].decode("latin1"))
    return out


sfx = parse_tbl(SD.read("arr\\sfxdata.tbl"))
# BrooDat carries the Brood War / zerg unit voices in its own table, so the
# lookup has to span both archives. (Reading only StarDat is why every zerg
# and siege-tank line used to miss and fall back to building sounds.)
for _extra in (BD.read("arr\\sfxdata.tbl"),):
    for _n in parse_tbl(_extra):
        if _n.lower() not in {s.lower() for s in sfx}:
            sfx.append(_n)
sfx_lower = {s.lower(): s for s in sfx}


def find(name_frag):
    hits = [s for s in sfx if name_frag.lower() in s.lower()]
    return hits[0] if hits else None


def grab(tbl_name, out_name, max_bytes=400000):
    # A few BrooDat table entries are stored with the first character of the
    # directory eaten ("orsair\\PCoRdy00.wav", "ARCHON\\PDaRdy00.WAV"), so the
    # table lookup cannot reach them. Passing a path that already starts with
    # "sound" skips the table entirely and reads the MPQ directly.
    if tbl_name.lower().startswith("sound"):
        real = tbl_name
        mpq = real.replace("\\", "/")
    else:
        real = sfx_lower.get(tbl_name.lower())
        if not real:
            print("MISS tbl", tbl_name)
            return False
        mpq = "sound/" + real.replace("\\", "/")
    for ar in (SD, BD):
        if ar.has(mpq):
            try:
                d, gaps = ar.read_with_gaps(mpq)
            except Exception as ex:
                print("FAIL", tbl_name, ex)
                return False
            if len(d) < 44 or d[:4] != b"RIFF":
                print("BAD", tbl_name, len(d), d[:4])
                return False
            d = d[:max_bytes]
            # rewrite RIFF sizes to the actual payload
            d = d[:4] + struct.pack("<I", len(d) - 8) + d[8:]
            # fix the data chunk size as well (last chunk in file)
            i = d.find(b"data")
            if i >= 0:
                d = d[:i + 4] + struct.pack("<I", len(d) - i - 8) + d[i + 8:]
            os.makedirs(os.path.join(OUT, "sounds"), exist_ok=True)
            with open(os.path.join(OUT, "sounds", out_name + ".wav"), "wb") as fp:
                fp.write(d)
            print("ok %-14s <- %s (%d bytes)" % (out_name, real, len(d)))
            return True
    print("MISS mpq", mpq)
    return False


WANT = [
    ("Misc\\TBldgPlc.wav", "build"),
    ("Misc\\ExploSm.wav", "explo_sm"),
    ("Misc\\ExploMed.wav", "explo_md"),
    ("Misc\\ExploLrg.wav", "explo_lg"),
    ("Misc\\PError.wav", "error"),
    ("Misc\\Button.wav", "click"),
    # the radio-transmission beep: StarCraft's generic incoming-message tone,
    # used here for the "under attack" minimap alert
    ("Misc\\Transmission.wav", "alert"),
    ("Terran\\MARINE\\TMaRdy00.wav", "marine_ready"),
    ("Terran\\MARINE\\TMaWht00.wav", "marine_what"),
    ("Terran\\MARINE\\TMaPss00.wav", "marine_ack"),
    ("Terran\\MARINE\\TMaDth00.wav", "marine_die"),
    ("Terran\\SCV\\TSCRdy00.wav", "scv_ready"),
    ("Terran\\SCV\\TSCWht00.wav", "scv_what"),
    ("Terran\\SCV\\TSCPss00.wav", "scv_ack"),
    ("Terran\\SCV\\TSCDth00.wav", "scv_die"),
    ("Terran\\FIREBAT\\TFBRdy00.wav", "firebat_ready"),
    ("Terran\\FIREBAT\\TFBWht00.wav", "firebat_what"),
    ("Terran\\FIREBAT\\TFBPss00.wav", "firebat_ack"),
    ("Terran\\FIREBAT\\TFBDth00.wav", "firebat_die"),
    ("Terran\\VULTURE\\TVuRdy00.wav", "vulture_ready"),
    ("Terran\\VULTURE\\TVuWht00.wav", "vulture_what"),
    ("Terran\\VULTURE\\TVuPss00.wav", "vulture_ack"),
    ("Terran\\TANK\\TTaRdy00.wav", "tank_ready"),
    ("Terran\\TANK\\TTaWht00.wav", "tank_what"),
    ("Terran\\TANK\\TTaPss00.wav", "tank_ack"),
    ("Terran\\TANK\\TTaDth00.wav", "tank_die"),
    # Zerg voices: the units are playable-as-enemy and used to fall back to
    # building sounds because these were never extracted.
    ("Zerg\\Zergling\\ZZeRdy00.wav", "zergling_ready"),
    ("Zerg\\Zergling\\ZZeWht00.wav", "zergling_what"),
    ("Zerg\\Zergling\\ZZePss00.wav", "zergling_ack"),
    ("Zerg\\Zergling\\ZZeDth00.wav", "zergling_die"),
    ("Zerg\\Hydra\\ZHyRdy00.wav", "hydra_ready"),
    ("Zerg\\Hydra\\ZHyWht00.wav", "hydra_what"),
    ("Zerg\\Hydra\\ZHyPss00.wav", "hydra_ack"),
    ("Zerg\\Hydra\\ZHyDth00.wav", "hydra_die"),
    ("Zerg\\Mutalid\\ZMuRdy00.wav", "muta_ready"),
    ("Zerg\\Mutalid\\ZMuWht00.wav", "muta_what"),
    ("Zerg\\Mutalid\\ZMuPss00.wav", "muta_ack"),
    ("Zerg\\Mutalid\\ZMuDth00.wav", "muta_die"),
    ("Zerg\\Drone\\ZDrRdy00.wav", "drone_ready"),
    ("Zerg\\Drone\\ZDrErr00.wav", "zerg_error"),
    # --- Protoss (v2.10). Names are the real sfx-table spellings; the table is
    # not case-consistent (SCOUT\\PScRdy00 vs Scout\\PScWht00) so each entry is
    # quoted as it appears in arr\\sfxdata.tbl.
    ("Protoss\\PROBE\\PPrRdy00.WAV", "probe_ready"),
    ("Protoss\\PROBE\\PPrWht00.WAV", "probe_what"),
    ("Protoss\\PROBE\\PPrYes00.WAV", "probe_ack"),
    ("Protoss\\PROBE\\PPrDth00.WAV", "probe_die"),
    ("Protoss\\ZEALOT\\PZeRdy00.WAV", "zealot_ready"),
    ("Protoss\\ZEALOT\\PZeWht00.WAV", "zealot_what"),
    ("Protoss\\ZEALOT\\PZeYes00.WAV", "zealot_ack"),
    ("Protoss\\ZEALOT\\PZeDth00.WAV", "zealot_die"),
    ("Protoss\\DRAGOON\\PDrRdy00.WAV", "dragoon_ready"),
    ("Protoss\\DRAGOON\\PDrWht00.WAV", "dragoon_what"),
    ("Protoss\\DRAGOON\\PDrYes00.WAV", "dragoon_ack"),
    ("Protoss\\DRAGOON\\PDrDth00.WAV", "dragoon_die"),
    ("Protoss\\TEMPLAR\\PTeRdy00.WAV", "templar_ready"),
    ("Protoss\\TEMPLAR\\PTeWht00.WAV", "templar_what"),
    ("Protoss\\TEMPLAR\\PTeYes00.WAV", "templar_ack"),
    ("Protoss\\TEMPLAR\\PTeDth00.WAV", "templar_die"),
    ("Protoss\\DARKTEMPLAR\\PDTRdy00.WAV", "dtemplar_ready"),
    ("Protoss\\DARKTEMPLAR\\PDTWht00.WAV", "dtemplar_what"),
    ("Protoss\\DARKTEMPLAR\\PDTYes00.WAV", "dtemplar_ack"),
    ("Protoss\\DARKTEMPLAR\\PDTDth00.WAV", "dtemplar_die"),
    ("Protoss\\ARCHON\\PArRdy00.WAV", "archon_ready"),
    ("Protoss\\ARCHON\\PArWht00.WAV", "archon_what"),
    ("Protoss\\ARCHON\\PArYes00.WAV", "archon_ack"),
    ("Protoss\\ARCHON\\PArDth00.WAV", "archon_die"),
    ("Protoss\\Scout\\PScRdy00.WAV", "scout_ready"),
    ("Protoss\\Scout\\PScWht00.WAV", "scout_what"),
    ("Protoss\\Scout\\PScYes00.WAV", "scout_ack"),
    ("Protoss\\Scout\\PScDth00.WAV", "scout_die"),
    ("Protoss\\Carrier\\PCaRdy00.WAV", "carrier_ready"),
    ("Protoss\\Carrier\\PCaWht00.WAV", "carrier_what"),
    ("Protoss\\Carrier\\PCaYes00.WAV", "carrier_ack"),
    ("Protoss\\Carrier\\PCaDth00.WAV", "carrier_die"),
    ("Protoss\\SHUTTLE\\PShRdy00.WAV", "shuttle_ready"),
    ("Protoss\\SHUTTLE\\PShWht00.WAV", "shuttle_what"),
    ("Protoss\\SHUTTLE\\PShYes00.WAV", "shuttle_ack"),
    ("Protoss\\SHUTTLE\\PShDth00.WAV", "shuttle_die"),
    ("Protoss\\ARBITER\\PAbRdy00.WAV", "arbiter_ready"),
    ("Protoss\\ARBITER\\PAbWht00.WAV", "arbiter_what"),
    ("Protoss\\ARBITER\\PAbYes00.WAV", "arbiter_ack"),
    ("Protoss\\ARBITER\\PAbDth00.WAV", "arbiter_die"),
    ("Protoss\\TRILOBYTE\\PTrRdy00.WAV", "reaver_ready"),
    ("Protoss\\TRILOBYTE\\PTrWht00.WAV", "reaver_what"),
    ("Protoss\\TRILOBYTE\\PTrYes00.WAV", "reaver_ack"),
    ("Protoss\\TRILOBYTE\\PTrDth00.WAV", "reaver_die"),
    ("Protoss\\Witness\\PWiRdy00.WAV", "observer_ready"),
    ("Protoss\\Witness\\PWiWht00.WAV", "observer_what"),
    ("Protoss\\Witness\\PWiYes00.WAV", "observer_ack"),
    ("Protoss\\Witness\\PWiDth00.WAV", "observer_die"),
    # Direct paths: the BrooDat table has these two groups truncated, so the
    # table lookup can never reach them.
    ("sound\\protoss\\corsair\\pcordy00.wav", "corsair_ready"),
    ("sound\\protoss\\corsair\\pcowht00.wav", "corsair_what"),
    ("sound\\protoss\\corsair\\pcoyes00.wav", "corsair_ack"),
    ("sound\\protoss\\corsair\\pcopss00.wav", "corsair_die"),
    ("sound\\protoss\\darchon\\pdardy00.wav", "darchon_ready"),
    ("sound\\protoss\\darchon\\pdawht00.wav", "darchon_what"),
    ("sound\\protoss\\darchon\\pdayes00.wav", "darchon_ack"),
    # Protoss advisor: replaces the terran "not enough minerals" line when a
    # Protoss race is selected.
    ("Protoss\\Advisor\\PAdErr00.WAV", "protoss_error"),
    # --- v2.12 batch E: the "glue" (front-end) interface sounds. These live in
    # a separate group of arr\sfxdata.tbl whose names are spelled
    # "glue\<name>.wav" (the table's own prefix, not a path we chose) and the
    # MPQ stores them under sound/glue/. The plan asked for ui_click and
    # ui_swishin/out by those names, but the retail files are bnetclick /
    # swishin / swishout; the output names below are the ones GameView plays.
    # mousedown2 is the 15 KB front-end click -- bnetclick is the same idea at
    # 200 KB, which is not worth the APK budget for a button press.
    ("glue\\mousedown2.wav", "ui_click"),
    ("glue\\mouseover.wav", "ui_hover"),
    ("glue\\swishin.wav", "ui_swishin"),
    ("glue\\swishout.wav", "ui_swishout"),
    ("glue\\countdown.wav", "ui_countdown"),
    ("glue\\scorefill.wav", "ui_scorefill"),
    ("glue\\scorefillend.wav", "ui_scoreend"),
]
for tbl_name, out_name in WANT:
    grab(tbl_name, out_name)


# ---------------------------------------------------------------- title art
def pcx_decode(data):
    """Minimal PCX 256-color decoder -> (pixels, palette, w, h).

    The 128-byte header holds xmin/ymin at offsets 4/6 and xmax/ymax at 8/10.
    The old code read the maxima from 8/10 and subtracted the minima read from
    12/14, which produced 0x0 for this file.
    """
    if data[0:1] != b"\x0a" or data[1] != 5:
        return None
    xmin, ymin, xmax, ymax = struct.unpack_from("<HHHH", data, 4)
    w = xmax - xmin + 1
    h = ymax - ymin + 1
    if w <= 0 or h <= 0 or w > 4096 or h > 4096:
        return None
    pal = data[-768:]
    px = bytearray()
    i = 128
    while len(px) < w * h and i < len(data) - 768:
        b = data[i]
        i += 1
        if b & 0xC0 == 0xC0:
            cnt = b & 0x3F
            if i >= len(data) - 768:
                break
            v = data[i]
            i += 1
            px.extend(bytes([v]) * cnt)
        else:
            px.append(b)
    if len(px) < w * h:
        # the repack dropped bytes mid-stream; pad so the image still renders
        px.extend(bytes(w * h - len(px)))
    return bytes(px[:w * h]), pal, w, h


try:
    from PIL import Image
    for ar in (SD, BD):
        if ar.has("glue\\title\\Title.pcx"):
            data, gaps = ar.read_with_gaps("glue\\title\\Title.pcx")
            r = pcx_decode(data)
            if r:
                px, pal, w, h = r
                # PCX stores the palette as R,G,B and the pixels are palette
                # indices. The old code indexed the palette by pixel POSITION
                # ((y*w+x)*3) instead of by pixel VALUE, which produced noise.
                lut = [(pal[i * 3], pal[i * 3 + 1], pal[i * 3 + 2]) for i in range(256)]
                img = Image.new("RGB", (w, h))
                img.putdata([lut[v] for v in px[:w * h]])
                img.save(os.path.join(OUT, "ui", "title.png"))
                print("title.png", w, "x", h)
            else:
                print("title pcx decode failed")
            break
    else:
        print("no Title.pcx")
except Exception as ex:
    import traceback
    traceback.print_exc()
    print("title FAIL", ex)
