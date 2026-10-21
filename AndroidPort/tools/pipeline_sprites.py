"""Complete asset pipeline: sprites with team colors -> Android app assets.

Outputs into AndroidPort/app/app/src/main/assets/sprites/:
    <key>_<team>.png   team in {b, r} -- unit / building / effect sheets
    <icon>.png                         -- single-frame command icons
    manifest.json                      -- full metadata (human readable)
    manifest.txt                       -- compact index the Android app reads

manifest.txt row:  key,kind,walkCount,hasAttack,frames,cols

    kind 0 = unit sheet   17 direction columns; rows = walkCount + hasAttack
    kind 1 = sheet        `frames` animation frames laid out `cols` per row
    kind 2 = icon         single frame, no team variants

This file is the ONLY writer of manifest.txt/manifest.json. Earlier the two
files were produced by different scripts, which let them drift: `stank` ended
up as a 17-wide unit sheet while its manifest row claimed a 6-frame building,
so the siege tank rendered as a slice of the wrong row.
"""
import json
import os

from PIL import Image

import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\app\app\src\main\assets")
SPR = os.path.join(OUT, "sprites")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

# ---------------------------------------------------------------- palette
# WPE stores each entry as R,G,B,0 -- the old code read it back-to-front
# (B,G,R), which swapped red and blue for every sprite, icon and effect in the
# pack: minerals rendered brown, muzzle flashes and explosions rendered blue.
# Verified against the muzzle-flash GRP, which is authored as a brightness ramp
# over indices 3..32 -- as RGB that ramp is dark blue-grey -> bright orange
# (correct); as BGR it is brown -> blue (impossible for fire).
wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
BASE_PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]
# index 255 is the GRP transparent filler


def _ramp(dark, bright, n=8):
    return [(int(dark[0] + (bright[0] - dark[0]) * k / (n - 1)),
             int(dark[1] + (bright[1] - dark[1]) * k / (n - 1)),
             int(dark[2] + (bright[2] - dark[2]) * k / (n - 1))) for k in range(n)]


TEAM_RAMPS = {
    "b": _ramp((16, 28, 96), (128, 176, 255)),
    "r": _ramp((96, 12, 12), (255, 132, 96)),
    "n": None,
}
PAL_TEAM = {}
for _t, _ramp8 in TEAM_RAMPS.items():
    if _ramp8 is None:
        PAL_TEAM[_t] = BASE_PAL + [(0, 0, 0)]
    else:
        _p = list(BASE_PAL)
        for _i in range(8):
            _p[8 + _i] = _ramp8[_i]
        PAL_TEAM[_t] = _p + [(0, 0, 0)]

# ---------------------------------------------------------------- units
# key: (grp path, walk_blocks, attack_block)  -- each block is 17 directions
UNITS = {
    "scv":      ("unit\\terran\\SCV.grp", [0, 1], 2),
    "marine":   ("unit\\terran\\marine.grp", [0, 1, 2], 3),
    "firebat":  ("unit\\terran\\firebat.grp", [0, 1], 2),
    "vulture":  ("unit\\terran\\Vulture.grp", [0], 0),
    "tank":     ("unit\\terran\\tank.grp", [0, 1], 2),
    "zergling": ("unit\\zerg\\zergling.grp", [0, 1, 2], 3),
    "hydra":    ("unit\\zerg\\hydra.grp", [0, 1], 2),
    "muta":     ("unit\\zerg\\mutalid.grp", [0, 1], 2),
    "over":     ("unit\\zerg\\overlord.grp", [0], None),
    "drone":    ("unit\\zerg\\drone.grp", [0, 1], 2),
    # v2.8: ghost and wraith passed the cmdicons/GRP gate this round. The wraith
    # has no file named after it -- units.dat id 8 is drawn from phoenix.grp,
    # which is a Terran flat swept-wing fighter (confirmed by rendering it next
    # to wessel/battlecr/dropship in tools/out/wraith_ident.png, not by name).
    "ghost":    ("unit\\terran\\ghost.grp", [0, 1], 2),
    "wraith":   ("unit\\terran\\phoenix.grp", [0], 0),
    # v2.8 zerg playable: the hatchery spawns larva, and the larva morphs into
    # every zerg unit, so it needs its own sheet. (There is no Scourge.grp in
    # any of the four archives -- images.tbl has no entry for it either.)
    "larva":    ("unit\\zerg\\larva.grp", [0], None),
    # ---------------------------------------------------------------- v2.10
    # The protoss block boundaries were NOT guessed from the file names: each
    # GRP was rendered as a per-block contact strip (tools/probe_v210*.py) and
    # the walk/attack split read off the pictures, using marine/scv as the
    # calibration rulers for what "walk" and "attack" look like in this pack.
    # Two of them are the reverse of the terran layout: templar and dtemplar
    # carry their attack blocks BEFORE the walk cycle.
    "probe":    ("unit\\protoss\\probe.grp", [0], None),
    "zealot":   ("unit\\protoss\\zealot.grp", [0, 1, 2, 3, 4], 5),
    "dragoon":  ("unit\\protoss\\dragoon.grp", [0, 1, 2, 3, 4, 5, 6, 7], 8),
    "templar":  ("unit\\protoss\\templar.grp",
                 [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16], 0),
    "dtemplar": ("unit\\protoss\\dtemplar.grp",
                 [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17], 0),
    # The archon files hold one 17-frame "energy ring" block and a 10-frame
    # "silhouette forms inside the ring" block -- that is a morph, not a walk
    # and an attack, so only the first block is used.
    "archon":   ("unit\\protoss\\archon.grp", [0], None),
    "darchon":  ("unit\\protoss\\darchn.grp", [0], None),
    "shuttle":  ("unit\\protoss\\shuttle.grp", [0], None),
    # scout and corsair have two/five blocks of identical size, so size alone
    # proves nothing -- rendering them showed block 0 is the clean hull and the
    # later blocks add a white/blue muzzle flare. First attack block taken.
    "scout":    ("unit\\protoss\\scout.grp", [0], 1),
    "corsair":  ("unit\\protoss\\corsair.grp", [0], 1),
    "arbiter":  ("unit\\protoss\\arbiter.grp", [0], None),
    "carrier":  ("unit\\protoss\\carrier.grp", [0], None),
    "intercep": ("unit\\protoss\\Intercep.grp", [0], None),
    "reaver":   ("unit\\protoss\\trilob.grp", [0], None),
    "observer": ("unit\\protoss\\witness.grp", [0], None),
    # ---------------------------------------------------------------- v2.11 B
    # Zerg completion. Every block boundary below was read off an UNCROPPED
    # per-block contact sheet (tools/probe_v211bk.py / bv.py / bz.py) and
    # cross-checked with the red-death detector (probe_v211bl.py). The crop
    # matters: with a tight crop the box follows each block and every block
    # looks different, which is exactly why all nine numeric seam detectors
    # failed even on units whose true walk length is known (marine 3).
    # The rule that finally worked: the walk loop is IMPLICIT (block W-1 wraps
    # to block 0), the body stays put and only the limbs swing.
    "ultra":    ("unit\\zerg\\ultra.grp", [0, 1, 2, 3, 4], None),
    "queen":    ("unit\\zerg\\queen.grp", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], None),
    "defiler":  ("unit\\zerg\\defiler.grp", [0, 1, 2, 3, 4, 5, 6, 7], None),
    "guardian": ("unit\\zerg\\guardian.grp", [0, 1, 2, 3, 4, 5, 6], None),
    "devourer": ("unit\\zerg\\devour.grp", [0, 1, 2, 3, 4, 5, 6, 7], 8),
    # lurker: block 7 is the attack (opaque px 20655 -> 11373, the scythe
    # forelimbs unfold) and block 11 is the red death burst.
    "lurker":   ("unit\\zerg\\lurknorm.grp", [0, 1, 2, 3, 4, 5, 6], 7),
    "lurker_bur": ("unit\\zerg\\lurkburr.grp",
                   [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], None),
    "broodling": ("unit\\zerg\\brood.grp",
                  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], None),
    # The lurker egg is one full 17-frame block followed by a 3-frame stub.
    "lurk_egg": ("unit\\zerg\\LurkEgg.grp", [0], None),
    # ---------------------------------------------------------------- v2.11 C
    # Terran Brood War. medic.grp and bomber.grp live only in BrooDat and have
    # no images.tbl row, so load_grp's PT -> SD -> BD fallback is the only way
    # to reach them.
    # medic: blocks 0-3 walk, 4-5 are the orange heal beam (b5 is the biggest
    # orb), 6-12 walk again, 13 the red death burst.
    "medic":    ("unit\\terran\\medic.grp", [0, 1, 2, 3], 4),
    "valkyrie": ("unit\\terran\\bomber.grp", [0], None),
    # BattleCruiser is a StarDat ship with exactly one 17-frame block, so it has
    # no walk/attack split at all -- the hull is the whole sheet. It needs a
    # sheet row (not just ic_battlecruiser) because batch C opens it up behind
    # the science facility and raceTests spawns one to check the tech gate.
    "battlecruiser": ("unit\\terran\\BattleCr.grp", [0], None),
    # v2.23 batch A/B. The goliath GRP is 170 frames / 10 blocks -- the exact
    # same layout as firebat.grp in this repack, which is shipped as walk
    # [0,1] + attack 2 with the remaining blocks holding the death sequence.
    # The blocks were cross-checked with tools/probe_v223_grp.py (per-block
    # opaque, bright-pixel and bbox statistics) and no block stood out as a
    # flare, so the sibling convention is the evidence-backed choice. The
    # dropship is a single 17-frame hull with no walk/attack split, exactly
    # like the shuttle.
    "goliath":  ("unit\\terran\\goliath.grp", [0, 1], 2),
    "dropship": ("unit\\terran\\dropship.grp", [0], None),
}

# key: (grp path, max_frames)  -- single-pose / building sheets, one row
SINGLES = {
    "stank":    ("unit\\terran\\stank.grp", 6),
    "cc":       ("unit\\terran\\control.grp", 6),
    "depot":    ("unit\\terran\\Depot.grp", 2),
    "barracks": ("unit\\terran\\TBarrack.grp", 6),
    "refinery": ("unit\\terran\\refinery.grp", 5),
    "factory":  ("unit\\terran\\factory.grp", 6),
    "turret":   ("unit\\terran\\missile.grp", 3),
    "bunker":   ("unit\\terran\\PillBox.grp", 2),
    "academy":  ("unit\\terran\\Academy.grp", 2),
    "starport": ("unit\\terran\\starport.grp", 6),
    # ---------------------------------------------------------------- v2.25
    # The five Terran add-ons whose GRPs this repack actually carries. The
    # names come from BrooDat arr\images.tbl (a proper name->GRP table, the
    # one artifact the identity forensics of v2.11 did not have), not from
    # guessing filenames: 284 ComSat.grp, 289 controlT.grp, 312 machines.grp,
    # 323 physics.grp, 341 nukesilo.grp. The Covert Ops add-on is genuinely
    # absent -- images.tbl has no entry for units.dat id 117 at all -- so the
    # ghost keeps its academy gate rather than pointing at art that is not
    # there.
    "comsat":     ("unit\\terran\\ComSat.grp", 2),
    "controlt":   ("unit\\terran\\controlT.grp", 1),
    "machineshop": ("unit\\terran\\machines.grp", 5),
    "physicslab": ("unit\\terran\\physics.grp", 7),
    "nukesilo":   ("unit\\terran\\nukesilo.grp", 2),
    "hatchery": ("unit\\zerg\\hatchery.grp", 6),
    "lair":     ("unit\\zerg\\Lair.grp", 5),
    "hive":     ("unit\\zerg\\Hive.grp", 5),
    "pool":     ("unit\\zerg\\Snakey.grp", 3),
    # v2.9: this used to point at fcolony.grp, which is the CREEP COLONY
    # (units.dat id 143) -- the sunken colony (id 146) lives in SColony.grp.
    # Confirmed by rendering both: only SColony has the attack tentacle.
    "sunken":   ("unit\\zerg\\SColony.grp", 4),
    # v2.8: the two zerg structures the player can now build that had no sheet.
    # There is no unit\zerg\Spire.grp (capital S) in StarDat -- only spire.grp.
    "extractor": ("unit\\zerg\\Extract.grp", 4),
    "spire":    ("unit\\zerg\\spire.grp", 4),
    "mineral":  ("unit\\neutral\\min01.grp", 4),
    "mineral2": ("unit\\neutral\\min02.grp", 4),
    "mineral3": ("unit\\neutral\\min03.grp", 4),
    "geyser":   ("unit\\neutral\\Geyser.grp", 4),
    # ---------------------------------------------------------------- v2.10
    # The protoss structures. Max frame counts come from the per-building
    # frame census in tools/out/v210_bld/contact.png.
    #
    # Two rows the plan asked for are deliberately absent, and both are art
    # problems rather than scheduling ones:
    #   sbattery  -- unit\protoss\sbattery.grp exists in the archive but
    #                decodes to 0 frames, so the shield battery has no art at
    #                all. (The plan already listed it as deferrable.)
    #   observatory -- there is no observatory GRP anywhere in the four
    #                archives: probe_v210q.py brute-forced 20 candidate names
    #                across unit\protoss, unit\thingy and unit\neutral and got
    #                no hit, and images.tbl has no entry for units.dat id 159
    #                either. An earlier pass pointed this key at texture.grp,
    #                which renders as a blue plasma swirl. The observer unit
    #                still exists; it just has no production building.
    "nexus":    ("unit\\protoss\\nexus.grp", 1),
    "pylon":    ("unit\\protoss\\pylon.grp", 1),
    "assim":    ("unit\\protoss\\assim.grp", 1),
    "gateway":  ("unit\\protoss\\gateway.grp", 1),
    "forge":    ("unit\\protoss\\forge.grp", 1),
    "photon":   ("unit\\protoss\\photon.grp", 4),
    "gencore":  ("unit\\protoss\\gencore.grp", 1),
    "citadel":  ("unit\\protoss\\citadel.grp", 1),
    "robotic":  ("unit\\protoss\\robotic.grp", 20),
    "archives": ("unit\\protoss\\archives.grp", 2),
    "stargate": ("unit\\protoss\\stargate.grp", 1),
    "beacon":   ("unit\\protoss\\beacon.grp", 1),
    # ---------------------------------------------------------------- v2.11 B
    # Zerg completion. The identity forensics for these five structures ran to
    # exhaustion -- units.dat / sprites.dat / images.dat / iscript.bin / the LO
    # files / BroodWar.mpq are all re-laid-out in this warez repack and none of
    # them yields a name->GRP map, and the 32x32 command-card icons are
    # hand-drawn art rather than scaled sprites, so silhouette matching scored
    # 4/6 WRONG even on buildings whose identity is known. The mapping below is
    # therefore the plan's own assignment plus morphology, and it is final: a
    # mis-assigned 4-frame static building is a cosmetic error, not a logic one.
    #   creep   (id 143) = fcolony.grp  -- creep colony, and the parent of both
    #                      defensive branches (plan: creep -> sunken/spore)
    #   spore   (id 144) = RCluster.grp -- the spore colony is the round pod
    #   evolcham(id 139) = MutaCham.grp
    #   mutapit (id 136) = Mutapit.grp  -- defiler mound, named by the plan
    #   nest    (id 138) = nest.grp     -- queen's nest
    #   hydraden(id 135) = MutaCham.grp recoloured -- the ONLY remaining doubt:
    #                      no dedicated hydralisk-den GRP exists in this repack,
    #                      and MutaCham is the closest organic mound. Flagged
    #                      here rather than silently shipped.
    #   nydus   (id 134) = NydusPit.grp
    #   ucereb  (id 140) = UCereb.grp
    #   cerebrate(id 151)= cerebrat.grp
    #   chrysal (id 150) = chrysal.grp
    #   overmind1(id 147)= Over1.grp / overmind2 (id 148) = Over2.grp
    #   zbuild           = ZBuild.grp -- the shared zerg construction scaffold
    "creep":      ("unit\\zerg\\fcolony.grp", 4),
    "spore":      ("unit\\zerg\\RCluster.grp", 3),
    "evolcham":   ("unit\\zerg\\MutaCham.grp", 4),
    "hydraden":   ("unit\\zerg\\MutaCham.grp", 4),
    "mutapit":    ("unit\\zerg\\Mutapit.grp", 4),
    "nest":       ("unit\\zerg\\nest.grp", 4),
    "nydus":      ("unit\\zerg\\NydusPit.grp", 5),
    "ucereb":     ("unit\\zerg\\UCereb.grp", 5),
    "cerebrate":  ("unit\\zerg\\cerebrat.grp", 3),
    "chrysal":    ("unit\\zerg\\chrysal.grp", 4),
    "overmind1":  ("unit\\zerg\\Over1.grp", 4),
    "overmind2":  ("unit\\zerg\\Over2.grp", 4),
    "zbuild":     ("unit\\zerg\\ZBuild.grp", 31),
    # The two upgrade forms the plan allows to be recolours: there is no
    # greater-spire GRP and no ultralisk-cavern GRP in any archive.
    "greatspire": ("unit\\zerg\\spire.grp", 4),
    "ultracavern": ("unit\\zerg\\MutaCham.grp", 4),
    # ---------------------------------------------------------------- v2.11 C
    # Terran Brood War structures. These three were already in the Type table
    # but had no art, so they drew as nothing.
    "engbay":     ("unit\\terran\\research.grp", 6),
    "armory":     ("unit\\terran\\weaponpl.grp", 6),
    "sciencefac": ("unit\\terran\\physics.grp", 7),
    # Spider Mine: Spider.grp holds 12 frames, which is NOT a multiple of 17,
    # so it cannot be a 17-direction unit sheet -- it is one flat 12-frame
    # animation and ships as kind 1.
    "spider":     ("unit\\terran\\Spider.grp", 12),
}

# Recolour factors for the keys that borrow another building's art, so the
# upgraded form is distinguishable on the map. Values are per-channel
# multipliers applied by write_sheet's `_tint`.
SINGLE_TINTS = {
    "greatspire":  (0.72, 0.80, 1.25),
    "ultracavern": (1.20, 0.86, 0.70),
    "hydraden":    (0.78, 1.18, 0.82),
}

# key: (grp path, first_frame or None for "whole file")
# The bang effects live under unit\thingy\ (the old paths omitted `unit\`,
# so these three sheets were never produced at all).
ANIMS = {
    "bang_s":        ("unit\\thingy\\tBangS.grp", None),
    "bang_m":        ("unit\\thingy\\tBangL.grp", None),
    "bang_l":        ("unit\\thingy\\tBangX.grp", None),
    "death_marine":  ("unit\\terran\\marine.grp", 13 * 17),
    "death_zergling": ("unit\\zerg\\zergling.grp", 17 * 17),
    # v2.44: was 17*17. hydra.grp is 297 frames, so block 17 is the trailing
    # partial block (frames 289..296) and it is blank filler (meanRGB
    # (1.9,1.9,2.1), zero red pixels, max frame 15x10) -- the hydra died with no
    # explosion at all. Measured every block (tools/_hydrablocks.py): the real
    # death is block 12 (frames 204..220), meanRGB (36.6,14.0,12.0), 6984 red
    # pixels, frames up to 92x71. marine (block 13) and zergling (block 17) were
    # already correct, which is why only the hydra looked wrong.
    "death_hydra":   ("unit\\zerg\\hydra.grp", 12 * 17),
    "death_terran":  ("unit\\terran\\tmeDeath.grp", None),
    # muzzle flashes, picked by weapon weight; missile trail puff; impact spark.
    # These live only in BrooDat and are absent from images.tbl, which is why an
    # earlier pass concluded tmeFlsh/bsmoke could not be resolved.
    "flsh_s":        ("unit\\thingy\\tmeFlshS.grp", None),
    "flsh_m":        ("unit\\thingy\\tmeFlshM.grp", None),
    "flsh_l":        ("unit\\thingy\\tmeFlshL.grp", None),
    "smoke":         ("unit\\thingy\\bsmoke.grp", None),
    "hit":           ("unit\\bullet\\ephFire.grp", None),
    # ---------------------------------------------------------------- v2.10
    # protoss effects. psistorm is the templar's area spell, pshield the
    # shield-flare loop, b_pspark the shield-hit spark (the plan calls for it
    # as the shield damage cue) and pcirglow the selection ring.
    "psistorm":      ("unit\\thingy\\psiStorm.grp", None),
    "pshield":       ("unit\\thingy\\pshield.grp", None),
    "b_pspark":      ("unit\\bullet\\pspark.grp", None),
    "pcirglow":      ("unit\\protoss\\pCirGlow.grp", None),
    # Death sequences: the protoss units whose GRPs carry a 7-frame tail block
    # (zealot b13, dragoon b24, templar b17 -- found numerically by
    # probe_v210o.py, which looks for the frame block that is both short and
    # far brighter than its neighbours). dtemplar and reaver have no tail.
    "death_zealot":  ("unit\\protoss\\zealot.grp", 13 * 17),
    "death_dragoon": ("unit\\protoss\\dragoon.grp", 24 * 17),
    "death_templar": ("unit\\protoss\\templar.grp", 17 * 17),
    # ---------------------------------------------------------------- v2.11 B
    # zerg deaths. Only four of the new zerg units carry a death block at all
    # (probe_v211bl.py: queen, guardian, broodling and devourer show no red
    # burst anywhere), and the ones that do start on the block the detector
    # flagged:
    "death_ultra":   ("unit\\zerg\\ultra.grp", 15 * 17),
    "death_defiler": ("unit\\zerg\\defiler.grp", 8 * 17),
    "death_lurker":  ("unit\\zerg\\lurknorm.grp", 11 * 17),
    "death_lurker_bur": ("unit\\zerg\\lurkburr.grp", 14 * 17),
    # zerg spells and effects. Dswarm is the defiler's Dark Swarm cloud and
    # ensGooS/M/L the three sizes of the Ensnare goo splash; both were
    # extracted by probe_v211cf.py and are absent from the old table.
    "dswarm":        ("unit\\thingy\\Dswarm.grp", None),
    "ensgoo_s":      ("unit\\thingy\\ensGooS.grp", None),
    "ensgoo_m":      ("unit\\thingy\\ensGooM.grp", None),
    "ensgoo_l":      ("unit\\thingy\\ensGooL.grp", None),
    "maelhit":       ("unit\\thingy\\MaelHit.grp", None),
    # ---------------------------------------------------------------- v2.11 C
    # the medic's heal beam (13 frames, 96x96) and its death burst.
    "heal":          ("unit\\thingy\\ehaMed.grp", None),
    "death_medic":   ("unit\\terran\\medic.grp", 13 * 17),
    # ---------------------------------------------------------------- v2.14
    # The five caster spells, keyed by the exact anim key Game.java plays.
    #
    # The plan's 素材 column was only half right. It named emp.grp and
    # b_blastcan.grp (both real) and "dweb.grp" -- which does NOT exist in any
    # of the three archives, so the disruption web reads `disrupt.grp`
    # (BrooDat only, 11 frames). Irradiate and Lockdown had no asset named at
    # all; the two thingy GRPs that actually match their look are `empl`
    # (the yellow-green cloud the plan asked for as the green irradiate) and
    # `elect02` (the blue electric crackle of a unit being stunned).
    "emp":           ("unit\\thingy\\emp.grp", None),
    "ehamed":        ("unit\\thingy\\empl.grp", None),
    "dweb":          ("unit\\thingy\\disrupt.grp", None),
    "elect02":       ("unit\\thingy\\elect02.grp", None),
    "b_blastcan":    ("unit\\bullet\\blastcan.grp", None),
    "plasma":        ("unit\\thingy\\plasma.grp", None),
    # ---------------------------------------------------------------- v2.25
    # The nuclear strike. NukeHit.grp is the 26-frame ground burst (252x252,
    # the biggest effect sheet in the pack after plasma), NukeBeam.grp the
    # 34-frame falling trail and NukeTarg.grp the little 8x8 ground marker.
    # All three are in StarDat, all three are named in images.tbl (236/237/347),
    # and all three are capped so the sheet holds exactly the frames Game
    # plays -- a longer sheet is not an error, but the extra cells would be
    # unreachable and the manifest would lie about the length.
    "nukehit":       ("unit\\thingy\\NukeHit.grp", None),
    "nukebeam":      ("unit\\thingy\\NukeBeam.grp", None),
    "nuketarg":      ("unit\\thingy\\NukeTarg.grp", None),
}

# Frame budget for animations whose tail runs to the end of the GRP. Without
# this death_defiler would swallow everything from block 8 to the end of the
# file (153 frames of wreckage instead of the 4 red-burst blocks the detector
# actually flagged). Each value is the real length of the death block.
ANIM_COUNTS = {
    # v2.44: death_hydra points at block 12 (204..220), exactly 17 frames --
    # without a count the sheet would run to the end of the GRP and drag the
    # trailing filler blocks (13..17) in behind the burst.
    "death_hydra": 17,
    "death_ultra": 10,      # block 15 is a short 10-frame burst
    "death_defiler": 4 * 17,  # blocks 8-11 are the burst, 12-16 the wreckage
    "death_lurker": 10,
    "death_lurker_bur": 10,
    "death_medic": 9,
    # v2.14: the two new effects whose GRP is longer than one readable pass.
    # Each is capped so the sheet holds exactly the number of frames
    # Game.animFrames() plays -- a longer sheet is not an error, but the extra
    # cells are unreachable and the manifest would lie about the length.
    "dweb": 8,              # disrupt.grp has 11; it is at full size by frame 5
    "b_blastcan": 8,        # blastcan.grp has 17 frames of muzzle spark
    # v2.25: the nuclear burst is a 26-frame ground bloom; the falling trail is
    # 34 frames of a beam that is fully drawn by 20.
    "nukehit": 26,
    "nukebeam": 20,
}

# Subsampling for GRPs that are far longer than the effect needs. plasma.grp is
# 136 frames in which every frame duplicates its predecessor (68 unique steps
# of one long explosion); reading every 8th frame covers the whole arc -- the
# fireball growing, breaking up, and fading out -- in exactly 17 cells.
# Applied after the `first` slice and before ANIM_COUNTS.
ANIM_STRIDES = {
    "plasma": 8,
}

# ---------------------------------------------------------------- icons
# cmdicons.grp frame index == units.dat unit id for units/buildings, and the
# order-button block starts at 228. The previous table used hand-guessed
# indices, which is why the SCV/Firebat/Tank/Turret/Bunker buttons showed the
# wrong artwork (e.g. the supply depot icon appeared on the turret button).
ICONS_WANT = {
    # units (units.dat ids)
    "ic_marine": 0, "ic_ghost": 1, "ic_vulture": 2, "ic_goliath": 3,
    "ic_tank": 5, "ic_scv": 7, "ic_wraith": 8, "ic_science": 9,
    # 10 is 'Gui Montag', the hero firebat; 32 is 'Terran Firebat'. The earlier
    # 10 was the hero's portrait and did not match core/Game.java, which has
    # always trained id 32.
    "ic_firebat": 32, "ic_dropship": 11, "ic_battlecruiser": 12,
    # buildings (units.dat ids) -- verified against rez/stat_txt.tbl:
    # 117='Terran Covert Ops', 118='Terran Physics Lab', so the missile turret
    # is 124 and the bunker 125 (the first pass had them two slots off).
    # 115 is 'Terran Control Tower' and 116 'Terran Science Facility'; 123 is
    # 'Terran Armory'. The first pass had sciencefac on the control tower and
    # armory on the science facility.
    "ic_cc": 106, "ic_comsat": 107, "ic_nuke": 108, "ic_depot": 109,
    "ic_refinery": 110, "ic_barracks": 111, "ic_academy": 112,
    "ic_factory": 113, "ic_starport": 114, "ic_sciencefac": 116,
    "ic_armory": 123, "ic_engbay": 122, "ic_turret": 124, "ic_bunker": 125,
    # v2.8: the zerg rows, needed now that zerg is a playable race. Same
    # units.dat id rule as the terran ones (35 Larva, 37 Zergling, 38
    # Hydralisk, 41 Drone, 42 Overlord, 43 Mutalisk; buildings 131 Hatchery,
    # 141 Spire, 142 Spawning Pool, 146 Sunken Colony, 149 Extractor).
    "ic_larva": 35, "ic_zergling": 37, "ic_hydra": 38, "ic_drone": 41,
    "ic_overlord": 42, "ic_mutalisk": 43, "ic_hatchery": 131, "ic_spire": 141,
    "ic_pool": 142, "ic_sunken": 146, "ic_extractor": 149,
    # order buttons. 228=move 229=stop 230=attack 231=harvest 234=siege
    # 235=unsiege were verified by rendering the frames; 236 (ring-with-slash
    # = hold position) and 237 (crossed tools = repair) were identified the
    # same way -- see tools/out/cmdicons_grid.png.
    "ic_move": 228, "ic_stop": 229, "ic_attack": 230, "ic_harvest": 231,
    "ic_siege": 234, "ic_unsiege": 235, "ic_hold": 236, "ic_repair": 237,
    # 232 is a plain X (cancel/clear) and 233 a bare ring (patrol loop)
    "ic_cancel": 232, "ic_patrol": 233,
    # ---------------------------------------------------------------- v2.10
    # protoss units, same units.dat id rule (see rez/stat_txt.tbl). 60 Corsair
    # through 73 Interceptor, then 83 Reaver and 84 Observer -- there is a gap
    # because 74..82 are the heroes and the scarab.
    "ic_corsair": 60, "ic_dtemplar": 61, "ic_darchon": 63, "ic_probe": 64,
    "ic_zealot": 65, "ic_dragoon": 66, "ic_templar": 67, "ic_archon": 68,
    "ic_shuttle": 69, "ic_scout": 70, "ic_arbiter": 71, "ic_carrier": 72,
    "ic_intercep": 73, "ic_reaver": 83, "ic_observer": 84,
    # protoss buildings, 154 Nexus .. 172 Shield Battery. Observatory (159)
    # is kept for the wireframe even though the building itself has no art.
    "ic_nexus": 154, "ic_robotic": 155, "ic_pylon": 156, "ic_assim": 157,
    "ic_observatory": 159, "ic_gateway": 160, "ic_photon": 162,
    "ic_citadel": 163, "ic_gencore": 164, "ic_archives": 165, "ic_forge": 166,
    "ic_stargate": 167, "ic_fleetbeacon": 169, "ic_tribunal": 170,
    "ic_supportbay": 171, "ic_sbattery": 172,
    # ---------------------------------------------------------------- v2.11 B
    # zerg completion, same units.dat id rule (rez/stat_txt.tbl). 39 Ultralisk,
    # 40 Broodling, 44 Guardian, 45 Queen, 46 Defiler, 103 Lurker, 62
    # Devourer. Buildings 134 Nydus Canal .. 151 Cerebrate.
    # #97 (Lurker Egg) is a literal "BLANK" placeholder in this repack -- the
    # word is drawn as art, so an emptiness test cannot detect it. Borrow the
    # Zerg Egg icon at #36 instead; it is the same round egg silhouette.
    "ic_ultra": 39, "ic_broodling": 40, "ic_guardian": 44, "ic_queen": 45,
    "ic_defiler": 46, "ic_devourer": 62, "ic_lurk_egg": 36, "ic_lurker": 103,
    "ic_nydus": 134, "ic_hydraden": 135, "ic_mutapit": 136,
    "ic_greatspire": 137, "ic_nest": 138, "ic_evolcham": 139,
    "ic_ultracavern": 140, "ic_creep": 143, "ic_spore": 144,
    "ic_overmind": 147, "ic_chrysal": 150, "ic_cerebrate": 151,
    # lair/hive were art-only rows before v2.11 and never had icons; now that
    # the pool -> lair -> hive chain is buildable they need them.
    "ic_lair": 132, "ic_hive": 133,
    # ---------------------------------------------------------------- v2.11 C
    # terran Brood War: 34 Medic, 58 Valkyrie Frigate, 13 Vulture Spider Mine.
    "ic_medic": 34, "ic_valkyrie": 58, "ic_spider": 13,
    # ---------------------------------------------------------------- v2.25
    # the two ability buttons, indexed by the repack's own id->name table
    # (app/app/src/main/assets/ui/unitnames.txt): 316 "Scanner Sweep",
    # 257 "Nuclear Strike". Everything else in the 240..330 range is a
    # non-ability string (hero names, map names), so the pair is unambiguous.
    "ic_scan": 316, "ic_nukestrike": 257,
    # the add-on buildings' own cells, same units.dat-id rule (107 comsat and
    # 108 silo are already above): 115 Control Tower, 118 Physics Lab,
    # 120 Machine Shop.
    "ic_controlt": 115, "ic_physicslab": 118, "ic_machineshop": 120,
    "ic_nukesilo": 108,
}


def load_grp(path):
    """Decode a GRP from whichever archive holds it (patch -> StarDat -> BrooDat)."""
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def frame_image(f, pal):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    px = im.load()
    src = f["px"]
    for y in range(f["h"]):
        base = y * f["w"]
        for x in range(f["w"]):
            v = src[base + x]
            if v != 255:
                px[x, y] = pal[v] + (255,)
    return im


def _tint(im, f):
    """Multiply the RGB channels by `f` (keep alpha). Used for the two v2.11
    buildings the plan allows to reuse another building's art: the greater
    spire borrows spire.grp and the ultralisk cavern borrows MutaCham.grp, so
    without a colour shift the upgrade would be indistinguishable on the map."""
    r, g, b, a = im.split()
    r = r.point(lambda v: min(255, int(v * f[0])))
    g = g.point(lambda v: min(255, int(v * f[1])))
    b = b.point(lambda v: min(255, int(v * f[2])))
    return Image.merge("RGBA", (r, g, b, a))


def write_sheet(key, frames, use, cols, mw, mh, teams=("b", "r"), tint=None):
    """Blit `use` frames into a cols-wide grid, once per team palette."""
    rows = (len(use) + cols - 1) // cols
    for team in teams:
        pal = PAL_TEAM[team]
        img = Image.new("RGBA", (cols * mw, rows * mh), (0, 0, 0, 0))
        for k, fi in enumerate(use):
            f = frames[fi]
            ox = (k % cols) * mw + f["x"]
            oy = (k // cols) * mh + f["y"]
            im = frame_image(f, pal)
            if tint is not None:
                im = _tint(im, tint)
            img.paste(im, (ox, oy), im)
        img.save(os.path.join(SPR, "%s_%s.png" % (key, team)), optimize=True)
    return rows


def add_unit(key, path, walk_blocks, attack_block, rows_out, meta_out):
    r = load_grp(path)
    if r is None:
        print("MISS", key, path)
        return None
    frames, mw, mh = r
    n = len(frames)
    use = []
    for b in (walk_blocks or []):
        use += [b * 17 + d for d in range(17)]
    if attack_block is not None:
        use += [attack_block * 17 + d for d in range(17)]
    if not use:
        use = list(range(min(n, 17)))
    use = [f for f in use if f < n]
    rows = write_sheet(key, frames, use, 17, mw, mh)
    entry = {"key": key, "grp": path, "total": n, "kind": "unit", "dirs": 17,
             "walk": walk_blocks, "attack": attack_block,
             "frame": {"w": mw, "h": mh}}
    meta_out[key] = entry
    walk_count = len(walk_blocks or [])
    has_attack = 1 if attack_block is not None else 0
    rows_out.append("%s,0,%d,%d,0,0" % (key, walk_count, has_attack))
    print("sprite %-14s unit   %4dx%-4d rows=%d fw=%d fh=%d" % (key, mw * 17, mh * rows, rows, mw, mh))
    return entry


def add_single(key, path, max_frames, rows_out, meta_out, tint=None):
    r = load_grp(path)
    if r is None:
        print("MISS", key, path)
        return None
    frames, mw, mh = r
    n = min(len(frames), max_frames) if max_frames else len(frames)
    use = list(range(n))
    write_sheet(key, frames, use, n, mw, mh, tint=tint)
    entry = {"key": key, "grp": path, "total": len(frames), "kind": "single",
             "frames": n, "dirs": 1, "frame": {"w": mw, "h": mh}}
    if tint is not None:
        entry["tint"] = list(tint)
    meta_out[key] = entry
    rows_out.append("%s,1,0,0,%d,%d" % (key, n, n))
    print("sprite %-14s single %4dx%-4d frames=%d cell=%dx%d" % (key, mw * n, mh, n, mw, mh))
    return entry


def add_anim(key, path, first, rows_out, meta_out, count=None, stride=1):
    r = load_grp(path)
    if r is None:
        print("MISS", key, path)
        return None
    frames, mw, mh = r
    use = list(range(first, len(frames))) if first is not None else list(range(len(frames)))
    if stride > 1:
        use = use[::stride]
    if count is not None:
        use = use[:count]
    if not use:
        print("EMPTY", key, path)
        return None
    cols = min(len(use), 8)
    write_sheet(key, frames, use, cols, mw, mh)
    entry = {"key": key, "grp": path, "total": len(frames), "kind": "anim",
             "first": first, "frames": len(use), "cols": cols,
             "frame": {"w": mw, "h": mh}}
    if stride > 1:
        entry["stride"] = stride
    meta_out[key] = entry
    rows_out.append("%s,1,0,0,%d,%d" % (key, len(use), cols))
    print("anim   %-14s %4dx%-4d frames=%d cols=%d cell=%dx%d%s"
          % (key, mw * cols, mh * ((len(use) + cols - 1) // cols), len(use), cols, mw, mh,
             " stride=%d" % stride if stride > 1 else ""))
    return entry


def add_icons(rows_out, meta_out):
    r = load_grp("unit\\cmdbtns\\cmdicons.grp")
    if r is None:
        print("MISS cmdicons")
        return
    frames, mw, mh = r
    print("cmdicons: %d frames %dx%d" % (len(frames), mw, mh))
    for key, idx in ICONS_WANT.items():
        if idx >= len(frames):
            print("icon miss", key, idx)
            continue
        im = frame_image(frames[idx], BASE_PAL)
        im.save(os.path.join(SPR, "%s.png" % key), optimize=True)
        meta_out[key] = {"x": frames[idx]["x"], "y": frames[idx]["y"],
                         "w": im.width, "h": im.height}
        rows_out.append("%s,2,0,0,1,1" % key)
    print("icons: %d written" % len(ICONS_WANT))


def main():
    os.makedirs(SPR, exist_ok=True)
    rows, units_meta, icons_meta = [], {}, {}
    for key, (path, walk, atk) in UNITS.items():
        add_unit(key, path, walk, atk, rows, units_meta)
    for key, (path, maxf) in SINGLES.items():
        add_single(key, path, maxf, rows, units_meta, tint=SINGLE_TINTS.get(key))
    for key, (path, first) in ANIMS.items():
        add_anim(key, path, first, rows, units_meta, count=ANIM_COUNTS.get(key),
                 stride=ANIM_STRIDES.get(key, 1))
    add_icons(rows, icons_meta)

    # manifest.txt is what the Android app reads; keep it the single source
    with open(os.path.join(SPR, "manifest.txt"), "w", encoding="utf8") as fp:
        fp.write("\n".join(rows) + "\n")
    with open(os.path.join(SPR, "manifest.json"), "w", encoding="utf8") as fp:
        json.dump({"units": units_meta, "icons": icons_meta}, fp,
                  ensure_ascii=False, indent=1)
    print("--- %d manifest rows ---" % len(rows))


if __name__ == '__main__':
    main()
