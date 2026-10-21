"""v2.9 asset-expansion pipeline: extract everything the game will need next
but which v2.8 never pulled out of the MPQs.

Output: AndroidPort/extracted/expand/
    units/<name>.png       unit contact sheet (direction block 0 + attack block)
    buildings/<name>.png   building/neutral contact sheet (all frames)
    effects/<name>.png     effect contact sheet (all frames)
    doodads/<name>.png     tileset decoration contact sheet (all frames)
    icons/<name>.png       one PNG per cmdicons frame (units.dat-id rule)
    icons/_grid_<a>_<b>.png  numbered grids for eyeballing
    sounds/<name>.wav      UI glue sounds + Brood War unit voices
    raw_grp/<name>.grp     the raw (gap-stripped) GRP bytes, for re-processing
    report.txt             one line per item: status, archive, frames, size

Why staging and not straight into assets/: SpriteBank decodes every manifest
row at startup, so unreferenced sheets would tax low-end phones. The v2.9
plan wires these in batch by batch; this file only proves they exist and are
decodable.

Palette note: WPE entries are R,G,B,0 (v2.4) -- NOT back-to-front.
"""
import os
import struct

from PIL import Image, ImageDraw

import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\extracted\expand")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
BASE_PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]


def load_grp(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps), (data, gaps), ar
    return None, None, None


def frame_image(f):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    px = im.load()
    src = f["px"]
    for y in range(f["h"]):
        base = y * f["w"]
        for x in range(f["w"]):
            v = src[base + x]
            if v != 255:
                px[x, y] = BASE_PAL[v] + (255,)
    return im


def render_sheet(frames, use, cols, pad=2, label_frame=True):
    """Contact sheet of the chosen frames, with frame indices drawn underneath."""
    if not use:
        return None
    mw = max(frames[i]["w"] for i in use)
    mh = max(frames[i]["h"] for i in use)
    rows = (len(use) + cols - 1) // cols
    cell_w, cell_h = mw + pad * 2, mh + pad * 2 + (8 if label_frame else 0)
    img = Image.new("RGBA", (cols * cell_w, rows * cell_h), (24, 28, 38, 255))
    d = ImageDraw.Draw(img)
    for k, fi in enumerate(use):
        f = frames[fi]
        im = frame_image(f)
        ox = (k % cols) * cell_w + pad
        oy = (k // cols) * cell_h + pad
        img.paste(im, (ox, oy), im)
        if label_frame:
            d.text((ox, oy + mh + 1), str(fi), fill=(180, 200, 220, 255))
    return img


def save_grp_raw(path, name):
    """Keep the raw bytes so a future fix never needs the MPQ hunt again."""
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, _ = ar.read_with_gaps(path)
            d = os.path.join(OUT, "raw_grp")
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, name + ".grp"), "wb") as fp:
                fp.write(data)
            return True
    return False


REPORT = []


def extract(kind, name, path, use_mode="all", cols=8):
    """kind: units | buildings | effects | doodads.
    use_mode: 'all' frames, or ('blocks', [block indices]) for 17-dir units."""
    grp, raw, ar = load_grp(path)
    frames, mw, mh = grp if grp else (None, None, None)
    tag = "MISS"
    img = None
    note = ""
    if frames is None:
        note = "no archive has " + path
    else:
        tag = {"SD": "StarDat", "BD": "BrooDat", "PT": "patch"}.get(
            os.path.basename(ar.path)[:2].upper(), ar.path)
        n = len(frames)
        if use_mode == "all":
            use = list(range(n))
        else:
            use = []
            for b in use_mode[1]:
                use += [b * 17 + dd for dd in range(17) if b * 17 + dd < n]
            use = use or list(range(min(n, 17)))
        img = render_sheet(frames, use, cols)
        note = "%d frames" % n
        save_grp_raw(path, name)
    d = os.path.join(OUT, kind)
    os.makedirs(d, exist_ok=True)
    if img is not None:
        img.save(os.path.join(d, name + ".png"))
    REPORT.append("%-9s %-18s %-28s %-8s %s" %
                  (kind, name, path, tag, note if frames is None or img is None
                   else "%s (%d used)" % (note, len(use))))


# ------------------------------------------------------------------- units
# (key, grp path, walk blocks to show, attack block) -- blocks are 17 dirs.
UNITS = {
    # --- zerg units v2.8 never extracted (all original SC1 content)
    "ultra":     ("unit\\zerg\\ultra.grp", [0, 1], 2),
    "queen":     ("unit\\zerg\\queen.grp", [0, 1], 2),
    "guardian":  ("unit\\zerg\\guardian.grp", [0], 0),
    "defiler":   ("unit\\zerg\\defiler.grp", [0, 1], 2),
    "broodling": ("unit\\zerg\\brood.grp", [0], None),
    "egg":       ("unit\\zerg\\egg.grp", None, None),
    "cocoon":    ("unit\\zerg\\cocoon.grp", None, None),
    # --- Brood War zerg
    "lurker":    ("unit\\zerg\\lurknorm.grp", [0, 1], 2),
    "lurker_bur": ("unit\\zerg\\lurkburr.grp", None, None),
    "lurker_SDbw": ("unit\\zerg\\Lurker.grp", None, None),  # images.tbl id86
    "lurk_egg":  ("unit\\zerg\\LurkEgg.grp", None, None),
    "devourer":  ("unit\\zerg\\devour.grp", [0], 0),
    # --- Brood War terran
    "medic":     ("unit\\terran\\medic.grp", [0, 1], 2),
    "valkyrie":  ("unit\\terran\\bomber.grp", [0], 0),
    "spider":    ("unit\\terran\\Spider.grp", None, None),
    "nukemiss":  ("unit\\terran\\nukemiss.grp", None, None),
    # --- protoss, the entire race
    "probe":     ("unit\\protoss\\probe.grp", [0, 1], 2),
    "zealot":    ("unit\\protoss\\zealot.grp", [0, 1], 2),
    "dragoon":   ("unit\\protoss\\dragoon.grp", [0, 1], 2),
    "templar":   ("unit\\protoss\\templar.grp", [0, 1], 2),
    "dtemplar":  ("unit\\protoss\\dtemplar.grp", [0, 1], 2),
    "archon":    ("unit\\protoss\\archon.grp", None, None),
    "darchon":   ("unit\\protoss\\darchn.grp", None, None),
    "shuttle":   ("unit\\protoss\\shuttle.grp", [0], 0),
    "scout":     ("unit\\protoss\\scout.grp", [0], 0),
    "arbiter":   ("unit\\protoss\\arbiter.grp", [0], 0),
    "carrier":   ("unit\\protoss\\carrier.grp", [0], 0),
    "intercep":  ("unit\\protoss\\Intercep.grp", None, None),
    "reaver":    ("unit\\protoss\\trilob.grp", [0, 1], 2),
    "observer":  ("unit\\protoss\\witness.grp", None, None),
    "corsair":   ("unit\\protoss\\corsair.grp", [0], 0),
}

# --------------------------------------------------------------- buildings
BUILDINGS = {
    # zerg, the rest of the tech tree
    "creep":     "unit\\zerg\\fcolony.grp",    # creep colony (id 143)
    "sunken2":   "unit\\zerg\\SColony.grp",    # sunken colony (id 146) -- the
    #                                          real one; v2.8 shipped fcolony
    "spore":     "unit\\zerg\\RCluster.grp",   # spore colony (id 144)
    "evolcham":  "unit\\zerg\\MutaCham.grp",   # evolution chamber? (id 139) --
    #                                          confirm visually
    "mutapit":   "unit\\zerg\\Mutapit.grp",    # hydralisk den or defiler mound?
    "nest":      "unit\\zerg\\nest.grp",       # queen's nest (id 138)
    "nydus":     "unit\\zerg\\NydusPit.grp",   # nydus canal (id 134)
    "ucereb":    "unit\\zerg\\UCereb.grp",     # cerebrate daggoth? (id 152)
    "cerebrate": "unit\\zerg\\cerebrat.grp",   # cerebrate (id 151)
    "chrysal":   "unit\\zerg\\chrysal.grp",    # chrysalis (ids 150/216)
    "overmind1": "unit\\zerg\\Over1.grp",      # overmind (id 147)
    "overmind2": "unit\\zerg\\Over2.grp",      # overmind w/ cocoon (id 148)
    "zbuild":    "unit\\zerg\\ZBuild.grp",     # generic zerg building
    # terran add-ons & the three v2.8 wrongly declared missing
    "engbay":    "unit\\terran\\research.grp",   # engineering bay (id 122)
    "armory":    "unit\\terran\\weaponpl.grp",   # armory (id 123)
    "sciencefac": "unit\\terran\\physics.grp",   # science facility (id 116)
    "comsat":    "unit\\terran\\ComSat.grp",     # comsat add-on (id 107)
    "controlt":  "unit\\terran\\controlT.grp",   # control tower add-on (115)
    "covertops": "unit\\terran\\chemlab.grp",    # covert ops add-on (117)
    "physlab":   "unit\\terran\\GeneLab.grp",    # physics lab add-on (118)
    "machineshop": "unit\\terran\\machines.grp", # machine shop add-on (120)
    "nukesilo":  "unit\\terran\\nukesilo.grp",   # nuclear silo (108)
    "drydocks":  "unit\\terran\\DryDocks.grp",   # starport alt art? confirm
    "turret2":   "unit\\terran\\missileT.grp",   # turret w/AddonT suffix
    # protoss
    "nexus":     "unit\\protoss\\nexus.grp",
    "pylon":     "unit\\protoss\\pylon.grp",
    "assim":     "unit\\protoss\\assim.grp",
    "gateway":   "unit\\protoss\\gateway.grp",
    "forge":     "unit\\protoss\\forge.grp",
    "photon":    "unit\\protoss\\photon.grp",
    "gencore":   "unit\\protoss\\gencore.grp",   # cybernetics core (164)
    "citadel":   "unit\\protoss\\citadel.grp",   # citadel of adun (163)
    "robotic":   "unit\\protoss\\robotic.grp",   # robotics facility (155)
    "archives":  "unit\\protoss\\archives.grp",  # templar archives (165)
    "stargate":  "unit\\protoss\\stargate.grp",
    "beacon":    "unit\\protoss\\beacon.grp",    # fleet beacon (169)
    "sbattery":  "unit\\protoss\\sbattery.grp",  # shield battery (172)
    "tribunal":  "unit\\protoss\\warp.grp",      # arbiter tribunal? (170)
    "supportbay": "unit\\protoss\\prism.grp",    # robotics support bay? (171)
    "observatory": "unit\\protoss\\texture.grp", # observatory? (159) confirm
    # neutral / props
    "ion":       "unit\\neutral\\ion.grp",       # ion cannon (127)
    "temple":    "unit\\neutral\\temple.grp",    # xel'naga temple (175)
    "uraj":      "unit\\neutral\\Uraj.grp",      # uraj crystal (128, BrooDat)
    "khalis":    "unit\\neutral\\Khalis.grp",    # khalis crystal (129, BrooDat)
    "khyad":     "unit\\neutral\\Khyad01.grp",   # khaydarin formation (173/187)
    "civilian":  "unit\\neutral\\civilian.grp",  # (15)
    "acritter":  "unit\\neutral\\Acritter.grp",  # rhynadon (89)
    "bcritter":  "unit\\neutral\\Bcritter.grp",  # bengalaas (90)
    "jcritter":  "unit\\neutral\\Jcritter.grp",  # scantid/kakaru/... (93-96)
    "flag":      "unit\\neutral\\Flag.grp",      # (215)
    "startloc":  "unit\\thingy\\StartLoc.grp",   # (214)
    "maprev":    "unit\\neutral\\maprev.grp",    # map revealer (101)
    "psiemit":   "unit\\neutral\\PsiEmit.grp",   # psi emitter (217)
    "datadisk":  "unit\\neutral\\DataDisk.grp",  # (218)
    "gasorb":    "unit\\neutral\\GasOrb.grp",    # geyser w/ extractor state
    "gastank":   "unit\\neutral\\GasTank.grp",   # depleted geyser
}

# ------------------------------------------------------------------ effects
EFFECTS = {
    "nukehit":   "unit\\thingy\\NukeHit.grp",
    "nukebeam":  "unit\\thingy\\NukeBeam.grp",
    "nuketarg":  "unit\\thingy\\NukeTarg.grp",
    "psistorm":  "unit\\thingy\\psiStorm.grp",
    "zairdth_l": "unit\\thingy\\zAirDthL.grp",   # zerg air death, big
    "zairdth_s": "unit\\thingy\\zAirDthS.grp",
    "zblddth":   "unit\\thingy\\zBldDthS.grp",   # zerg building death
    "zrubble_s": "unit\\thingy\\ZRubbleS.grp",
    "zrubble_l": "unit\\thingy\\ZRubbleL.grp",
    "prubble_s": "unit\\thingy\\PRubbleS.grp",   # protoss rubble
    "prubble_l": "unit\\thingy\\PRubbleL.grp",
    "rubble_s":  "unit\\thingy\\RubbleS.grp",    # terran rubble
    "rubble_l":  "unit\\thingy\\RubbleL.grp",
    "zavexplo":  "unit\\zerg\\zavExplo.grp",     # devourer-class explosion
    "zbgexplo":  "unit\\thingy\\zbgExplo.grp",
    "spooge":    "unit\\thingy\\spooge.grp",     # zerg goo splat
    "zcirglow":  "unit\\zerg\\zcirGlow.grp",     # selection glow, zerg
    "pcirglow":  "unit\\protoss\\pCirGlow.grp",  # selection glow, protoss
    "pshield":   "unit\\thingy\\pshield.grp",    # protoss shield flare
    "plasma":    "unit\\thingy\\plasma.grp",
    "ehamed":    "unit\\thingy\\ehaMed.grp",     # heal flash (medic)
    "ensgoo_s":  "unit\\thingy\\ensGooS.grp",    # ensnare
    "recall":    "unit\\thingy\\recall.grp",     # arbiter recall
    "emp":       "unit\\thingy\\emp.grp",        # EMP (science vessel / darchon)
    "dswarm":    "unit\\thingy\\Dswarm.grp",     # dark swarm
    "dweb":      "unit\\thingy\\disrupt.grp",    # disruption web (BrooDat)
    "maelhit":   "unit\\thingy\\MaelHit.grp",    # maelstrom (BrooDat)
    "tmaexplo":  "unit\\thingy\\tmnExplo.grp",   # misc explosion
    "dbl_exp":   "unit\\thingy\\dbl_exp.grp",
    "hkexplod":  "unit\\thingy\\HKexplod.grp",
    "hktrail":   "unit\\thingy\\HKTrail.grp",
    "psaexplo":  "unit\\thingy\\psaExplo.grp",
    # bullet-class projectiles the weapon layer can pick from later
    "b_grenade": "unit\\bullet\\grenade.grp",
    "b_missile": "unit\\bullet\\missile.grp",
    "b_gemini":  "unit\\bullet\\gemini.grp",     # wraith missiles
    "b_dragbull": "unit\\bullet\\dragbull.grp",  # dragoon bolt
    "b_pspark":  "unit\\bullet\\pspark.grp",     # protoss hit spark
    "b_zspark":  "unit\\bullet\\zspark.grp",
    "b_tspark":  "unit\\bullet\\tspark.grp",
    "b_scvspark": "unit\\bullet\\scvspark.grp",
    "b_blastcan": "unit\\bullet\\blastcan.grp",  # battlecruiser laser
    "b_spores":  "unit\\bullet\\spores.grp",
}

# ------------------------------------------------------------------ doodads
# images.tbl entries 685/686 lost their names to the repack's byte gaps
# ("thingy\tileset\", "op0ngy\tileset\Badlands\LCShop06.grp"); LCShop05 is
# therefore reconstructed by pattern and LCShop06 by its tail. Verified to
# exist by the probe below (has() hashes the full path, so exact case/slashes
# don't matter).
DOODAD_FIXUPS = [
    "unit\\thingy\\tileset\\Badlands\\LCShop05.grp",
    "unit\\thingy\\tileset\\Badlands\\LCShop06.grp",
]
DOODADS = []
for p in DOODAD_FIXUPS:
    DOODADS.append(p[len("unit\\"):].lower())
for i, line in enumerate(open(os.path.join(os.path.dirname(__file__), "images_tbl2.txt"),
                              encoding="utf8")):
    idx, name = line.rstrip("\n").split("\t")
    low = name.lower()
    # entries the repack's gaps mangled (e.g. "op0ngy\tileset\...") would
    # produce paths no archive has; the real ones are covered by DOODAD_FIXUPS
    if not low.startswith("thingy\\tileset\\"):
        continue
    if low.endswith(".grp") and low not in DOODADS:
        DOODADS.append(low)

# -------------------------------------------------------------------- icons
# cmdicons frame == units.dat id. Every id the next versions may need.
ICONS_WANT = {
    # zerg units missing from v2.8
    "ic_egg": 36, "ic_ultra": 39, "ic_broodling": 40, "ic_guardian": 44,
    "ic_queen": 45, "ic_defiler": 46, "ic_scourge": 47, "ic_infest": 50,
    "ic_valkyrie": 58, "ic_cocoon": 59, "ic_lurker": 103, "ic_devourer": 62,
    "ic_lurkeregg": 97,
    # protoss units
    "ic_corsair": 60, "ic_dtemplar": 61, "ic_darchon": 63, "ic_probe": 64,
    "ic_zealot": 65, "ic_dragoon": 66, "ic_templar": 67, "ic_archon": 68,
    "ic_shuttle": 69, "ic_scout": 70, "ic_arbiter": 71, "ic_carrier": 72,
    "ic_intercep": 73, "ic_reaver": 83, "ic_observer": 84, "ic_scarab": 85,
    # terran buildings / add-ons
    "ic_nukesilo": 108, "ic_controlt": 115, "ic_machineshop": 120,
    # zerg buildings
    "ic_nydus": 134, "ic_hydden": 135, "ic_defmound": 136,
    "ic_gspire": 137, "ic_queensnest": 138, "ic_evolcham": 139,
    "ic_ultracav": 140, "ic_creep": 143, "ic_spore": 144, "ic_overmind": 147,
    # protoss buildings
    "ic_nexus": 154, "ic_robotic": 155, "ic_pylon": 156, "ic_assim": 157,
    "ic_observatory": 159, "ic_gateway": 160, "ic_photon": 162,
    "ic_citadel": 163, "ic_gencore": 164, "ic_archives": 165, "ic_forge": 166,
    "ic_stargate": 167, "ic_fleetbeacon": 169, "ic_tribunal": 170,
    "ic_supportbay": 171, "ic_sbattery": 172,
}


def extract_icons():
    grp, raw, ar = load_grp("unit\\cmdbtns\\cmdicons.grp")
    frames, mw, mh = grp if grp else (None, None, None)
    if frames is None:
        REPORT.append("icons      -                   cmdicons.grp               MISSING")
        return
    d = os.path.join(OUT, "icons")
    os.makedirs(d, exist_ok=True)
    ok = 0
    for name, idx in sorted(ICONS_WANT.items(), key=lambda kv: kv[1]):
        if idx >= len(frames):
            REPORT.append("icons      %-18s frame %d >= %d" % (name, idx, len(frames)))
            continue
        frame_image(frames[idx]).save(os.path.join(d, "%s.png" % name))
        ok += 1
    REPORT.append("icons      %d/%d icons written (cmdicons %d frames)"
                  % (ok, len(ICONS_WANT), len(frames)))
    # numbered grids for eyeballing: unit ids 30-90, buildings 100-180
    for lo, hi in ((30, 105), (105, 180), (180, 240)):
        use = list(range(lo, min(hi, len(frames))))
        g = render_sheet(frames, use, 10, pad=3, label_frame=True)
        if g:
            g.save(os.path.join(d, "_grid_%d_%d.png" % (lo, hi)))


# ------------------------------------------------------------------- sounds
# Full MPQ paths (case-insensitive, / vs \ irrelevant). The unit voices are
# cross-checked against the BrooDat listfile because the sfxdata.tbl strings
# are truncated by the repack's gaps for several BW units (lurker/devourer/
# corsair entries lose their directory prefix); glue sounds are not in the
# tbl at all.
SOUNDS = {
    # BrooDat glue UI sounds -- menu/pause/score polish, never extracted
    "ui_click":    "Sound\\Glue\\bnetclick.wav",
    "ui_mousedown": "Sound\\Glue\\mousedown2.wav",
    "ui_mouseover": "Sound\\Glue\\mouseover.wav",
    "ui_countdown": "Sound\\Glue\\countdown.wav",
    "ui_scorefill": "Sound\\Glue\\scorefill.wav",
    "ui_scoreend": "Sound\\Glue\\scorefillend.wav",
    "ui_swishin":  "Sound\\Glue\\swishin.wav",
    "ui_swishout": "Sound\\Glue\\swishout.wav",
    "ui_swishlock": "Sound\\Glue\\swishlock.wav",
    # Brood War unit voices (BrooDat only)
    "medic_ready": "sound\\terran\\medic\\TMdRdy00.wav",
    "medic_what":  "sound\\terran\\medic\\TMdWht00.wav",
    "medic_ack":   "sound\\terran\\medic\\TMdPss00.wav",
    "medic_die":   "sound\\terran\\medic\\TMdDth00.wav",
    "medic_heal":  "sound\\terran\\medic\\Tmedheal.wav",
    "valkyrie_ready": "sound\\terran\\frigate\\TVkRdy00.wav",
    "valkyrie_what":  "sound\\terran\\frigate\\TVkWht00.wav",
    "valkyrie_ack":   "sound\\terran\\frigate\\TVkPss00.wav",
    "valkyrie_die":   "sound\\terran\\frigate\\TVkDth00.wav",
    "lurker_ready":   "sound\\zerg\\lurker\\ZLuRdy00.wav",
    "lurker_what":    "sound\\zerg\\lurker\\ZLuWht00.wav",
    "lurker_ack":     "sound\\zerg\\lurker\\ZLuPss00.wav",
    "lurker_die":     "sound\\zerg\\lurker\\ZLuDth00.wav",
    "lurker_burrow":  "sound\\zerg\\lurker\\ZLUBURRW.WAV",
    "devourer_ready": "sound\\zerg\\devourer\\ZDvRdy00.wav",
    "devourer_what":  "sound\\zerg\\devourer\\ZDvWht00.wav",
    "devourer_ack":   "sound\\zerg\\devourer\\ZDvPss00.wav",
    "devourer_die":   "sound\\zerg\\devourer\\ZDvDth00.wav",
    "corsair_ready":  "sound\\protoss\\corsair\\PCoRdy00.wav",
    "corsair_what":   "sound\\protoss\\corsair\\PCoWht00.wav",
    "corsair_ack":    "sound\\protoss\\corsair\\PCoPss00.wav",
    "darchon_ready":  "sound\\protoss\\darchon\\PDaRdy00.wav",
    "darchon_what":   "sound\\protoss\\darchon\\PDaWht00.wav",
    "darchon_ack":    "sound\\protoss\\darchon\\PDaPss00.wav",
    # NOTE: the dark archon has NO death wav -- the BrooDat listfile carries
    # only ready/what/pss/yes lines for it, so PDaDth00.wav is intentionally
    # absent here.
}


def extract_sounds():
    d = os.path.join(OUT, "sounds")
    os.makedirs(d, exist_ok=True)
    ok = 0
    for out_name, mpq_path in SOUNDS.items():
        got = False
        for ar in (SD, BD):
            if ar.has(mpq_path):
                try:
                    data, _ = ar.read_with_gaps(mpq_path)
                except Exception:
                    continue
                if len(data) < 44 or data[:4] != b"RIFF":
                    continue
                data = data[:400000]
                data = data[:4] + struct.pack("<I", len(data) - 8) + data[8:]
                i = data.find(b"data")
                if i >= 0:
                    data = data[:i + 4] + struct.pack("<I", len(data) - i - 8) + data[i + 8:]
                with open(os.path.join(d, out_name + ".wav"), "wb") as fp:
                    fp.write(data)
                got = True
                break
        REPORT.append("%-9s %-18s %-34s %s" %
                      ("sounds", out_name, mpq_path, "ok" if got else "MISS"))
        ok += got
    REPORT.append("sounds     %d/%d written" % (ok, len(SOUNDS)))


def main():
    for name, (path, blocks, atk) in UNITS.items():
        blocks_use = ["blocks", [b for b in (blocks or []) if b is not None]]
        if atk is not None:
            blocks_use[1].append(atk)
        extract("units", name, path, use_mode=blocks_use if blocks_use[1] else "all")
    for name, path in BUILDINGS.items():
        extract("buildings", name, path)
    for name, path in EFFECTS.items():
        extract("effects", name, path)
    seen = set()
    for low in DOODADS:
        name = low.split("\\")[-1][:-4]
        if name in seen:
            name = name + "_2"
        seen.add(name)
        extract("doodads", name, "unit\\" + low, use_mode="all", cols=6)
    extract_icons()
    extract_sounds()

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "report.txt"), "w", encoding="utf8") as fp:
        fp.write("\n".join(REPORT) + "\n")
    miss = [r for r in REPORT if "MISS" in r or "MISSING" in r]
    print("\n".join(REPORT))
    print("--- total %d lines, %d MISS ---" % (len(REPORT), len(miss)))


main()
