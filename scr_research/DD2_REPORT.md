# StarCraft CHK doodad sections: `DD2 ` vs `DDDATA` — sourced findings

Scope: answers to the four questions, with quoted text and a URL per claim, plus what could not be
determined. Every non-quoted statement below is either (a) a documented fact from a cited source, or
(b) a measurement made against the classic install at `F:\KF\XJZB` (StarCraft 1.16.1, StarEdit.exe
"Version 1.02"), labelled as a measurement.

---

## Q1. Is `DD2 ` the Remastered replacement for `DDDATA`? Which patch added it?

**No. `DD2 ` is not a Remastered replacement for `DDDATA`, and `DDDATA` is not a CHK section tag at
all.** `DD2 ` is the classic StarEdit doodad section; it is present in the classic pre-Remastered
editor, and the section list attributed to "SCR/1.18" (`DD2 `, `IVE2`, `MBRF`, `SWNM`) is in fact a
classic list — all four tags are in classic StarEdit. The genuinely Remastered-only tags are `STRx`
and `CRGB`.

### The wiki documents `DD2 ` as a normal section, with no Remastered attribution

[Scenario.chk — Staredit Network Wiki](https://wiki.staredit.net/wiki/Scenario.chk), section 1.18,
verbatim:

> `"DD2 " - StarEdit Sprites (Doodads)`
> `Not Required.`
> `This section contains the doodad map of the level. There are several parts to doodads. The
> graphical portion is stored in the MTXM section. The second part of the doodad is stored in this
> section. This section is only used by the map editor.`

The page's table of contents lists it in normal numeric order between `TILE` and `THG2` — no
"since Remastered" note. The page's only explicit Remastered attributions are for `STRx` and `CRGB`:

> `Note, since StarCraft Remastered, the "STRx" section is also possible and it optionally replaces
> the STR section.`

> `"CRGB" - Remastered Player Colors`

### `DDDATA` is not a section tag; `DDDATA.BIN` is a data file

The confusion is between a **CHK section tag** and a **data file name**. `dddata.bin` is a real
classic file (doodad placeability, one per tileset). There is no `DDDATA` CHK section. Two checks:

1. The tag never appears in any documentation revision. Across ~50 revisions of the Scenario.chk
   page, no revision contains the string `DDATA`.
2. **Measurement:** a raw-byte scan of all 8778 files under `F:\KF\XJZB` found `b'DDDATA'` in only 5
   files, and every one is a note or probe script written during this investigation
   (`AndroidPort\v2.9方案-素材补全与三族齐备.md`, `tools\probe_chk_sec.py`, `tools\probe_ddd.py`,
   `tools\_scan_dd.py`, `tools\out\_b51.txt`) — never in a map, MPQ, or executable. The same scan
   found `b'DD2 '` in 172 files including 65 occurrences in `BroodWar.mpq`, 8 in `StarEdit.exe`, and
   one in each of the 205 maps that carry it. `b'DDOA'`: 0 files.
3. **Measurement:** the parent's own `tools\_scan_dd.py` over all 206 maps on disk reports
   `(DDDATA, DD2) counts: {(False, True): 205, (False, False): 1}` — 205 maps carry `DD2 `, zero
   carry `DDDATA`.

### The classic editor contains the `DD2 ` tag; the classic game does not

**Measurement** — literal byte counts in the shipped executables:

| file | `DD2 ` | `DDATA` | `MTXM` | `TILE` | `THG2` | `MBRF` | `SWNM` | `IVE2` | `CRGB` | `STRx` |
|---|---|---|---|---|---|---|---|---|---|---|
| `StarEdit.exe` (v1.02) | **8** | 0 | 3 | 8 | 3 | 8 | 8 | 6 | 0 | 0 |
| `StarCraft.exe` (1.16.1) | 0 | 0 | 5 | 0 | 5 | 1 | 0 | 0 | 0 | 0 |
| `Brood.exe` (launcher stub) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Each `DD2 ` hit in `StarEdit.exe` sits in a table of 4-character section names each followed by a
pointer, immediately adjacent to the other CHK tags. Verbatim context at offset 436128:

```
...PTEC <ptr> UNIT <ptr> ISOM <ptr> TILE <ptr> DD2  <ptr> THG2 <ptr> MASK <ptr> STR  <ptr>...
```

This is the classic editor's section-handler table. So classic StarEdit 1.02 already reads and writes
`DD2 `, and it writes `MBRF`, `SWNM`, `IVE2` too — none of those four is a Remastered addition. The
classic **game** contains no `DD2 ` at all, which matches the wiki's "This section is only used by
the map editor."

### Correcting the "1.18 added" list

- `MBRF` — [Scenario.chk](https://wiki.staredit.net/wiki/Scenario.chk): `"MBRF" - Mission
  Briefings` / `Required for all versions. Not required for Melee.` Classic.
- `SWNM` — same page: `"SWNM" - Switch Names` / `Not Required.` / `This section contains the strings
  used for each switch.` Classic.
- `IVE2` — same page: `"IVE2" - Additional File Format Version` / `Not required.` / `u16: "Additional
  file format version:"` / `11 - 1.04 StarCraft and above ("hybrid") or Brood War.` / `This section
  does not "replace" IVER in hybrid/Brood War scenarios: both seem to be written by StarEdit but not
  read by StarCraft.` Classic, editor-written, and not read by the game.
- Remastered-only, per [scm-js `docs/chk-format.md`](https://github.com/scm-js/scm-js/blob/HEAD/docs/chk-format.md):
  `STRx` (`The string table of StarCraft: Remastered`) and `CRGB` (`StarCraft: Remastered's player
  colours`). Both are 0 in classic `StarEdit.exe`, confirming they postdate it.

**Conclusion for Q1:** `DD2 ` is the classic StarEdit doodad section, not a Remastered replacement
for `DDDATA`. No patch "introduced" it as a replacement; it is the only doodad section tag that
exists. The Remastered revision code is `VER ` 206 (`206 - Starcraft Remastered (1.21) (Broodwar)`),
but no Remastered map is required to have `DD2 ` and no classic map is required to lack it.

---

## Q2. Exact `DD2 ` record layout

**8 bytes per doodad. The parent's assumed field order and widths are correct; byte 7 is an
*enabled flag*, not a "percent".**

[Scenario.chk](https://wiki.staredit.net/wiki/Scenario.chk), verbatim:

> `Each doodad in the map gets the following structure:`
> `u16: Number of the doodad. Size of the doodad is dependent on this. Doodads are different for each tileset.`
> `u16: X coordinate of the doodad unit`
> `u16: Y coordinate of the doodad unit`
> `u8: Player number that owns the doodad`
> `u8: Enabled flag`
> `00 - Doodad is enabled (trap can attack, door is closed, etc)`
> `01 - Doodad is disabled`

Corroborated field-by-field by [scm-js `docs/chk-format.md`](https://github.com/scm-js/scm-js/blob/HEAD/docs/chk-format.md)
(`| Size | 8 bytes per doodad. |`, `| Read by | Editors only. The game skips it. |`):

> `| 0 | u16 | Doodad number in the tileset's list of doodads |`
> `| 2 | u16 | X of the middle of the doodad, in pixels |`
> `| 4 | u16 | Y of the middle of the doodad, in pixels |`
> `| 6 | u8 | Owner |`
> `| 7 | u8 | 1 if disabled, else 0 |`

### Byte 7 is not "percent" — measurement

Over 15200 in-bounds records from the 117 `AndroidPort\assets_src\maps\*.chk` maps carrying `DD2 `,
byte 7 is `0` in 15005 records (98.7%); the remaining values are 2–15 with counts 12–23 each. It is
**never 100**. The parent's `u8 percent / normally 100` assumption is disproven; the "enabled flag"
reading is correct. (The nonzero tail is damage — see the note on gap-misalignment below.)

Byte 6 (owner) over the same records: `0` in 10403, then 7:1360, 1:944, 6:936, 2:441, 5:385, 4:336,
3:189, with a small damaged tail — i.e. a player number, 0 = neutral.

### X and Y are the *centre* of the doodad, not a corner — measurement

Verified end-to-end on `F:\KF\XJZB\maps\(4)Blood Bath.scm` (platform, 64x64), by diffing `MTXM`
against `TILE` to recover each doodad's tile footprint:

| DD2 id | DD2 (x, y) | recovered tile box | size | computed centre |
|---|---|---|---|---|
| 256 | (1408, 912) | (38,24)–(49,32) | 12×9 | (1408, 912) ✔ |
| 137 | (1088, 1056) | (32,32)–(35,33) | 4×2 | (1088, 1056) ✔ |
| 257 | (832, 880) | (20,23)–(31,31) | 12×9 | (832, 880) ✔ |

So, with `w`/`h` the doodad's width/height in tiles from CV5 (see Q3):

```
leftTile = (x - 16*w) / 32        topTile = (y - 16*h) / 32
x = 16 * (2*leftTile + w)         y = 16 * (2*topTile + h)
```

---

## Q3. The `doodadType` id numbering space — **per-tileset `dddata.bin` index**

**It is a per-tileset doodad-catalogue index, specifically the `dddata.bin` index (0–511), which is
in turn the CV5 doodad group's `ddDataIndex` field.** It is *not* a global index and *not* an
`images.tbl` index. Classic doodads are **not** renumbered by Remastered: SCR **extends** the table
in the numeric gaps above the classic entries and leaves classic indices untouched.

### The wiki states it outright

[Terrain_Format — Staredit Network Wiki](https://wiki.staredit.net/wiki/Terrain_Format), CV5 doodad
groups, verbatim:

> `u16 SC:R Doodad - Set to 1 on doodads added by SC:R`
> `u16 Group String - 1-based stat_txt.tbl string index`
> `u16 Unknown/unused (always 0)`
> `u16 Doodad ID - dddata.bin index`
> `u16 Width - Width in tiles of the doodad`
> `u16 Height - Height in tiles of the doodad`

and for the data file itself:

> `DDDATA.BIN` / `Doodad placeability. Referenced by CV5.` / `Struct Size: 512 Bytes (entire file is
> 256KB).` / `ID Range: 0-511` / `u16[256] - CV5 Group IDs to determine doodad placeability.`

Also, on the group layout: `For doodad tiles (1024+ in pre-remaster tilesets, but SC:R puts some
doodads before that index on some tilesets):` and `Struct Size: 52 bytes`.

### Three independent sources agree the id *is* the `dddata.bin` index

- **scm-js** [`src/formats/tileset/doodads.ts`](https://github.com/scm-js/scm-js/blob/HEAD/src/formats/tileset/doodads.ts):
  > `DD2 records store the `ddData` index, so it is the doodad's id here too.`
  and on `dddata.bin`: > `512 entries of 256 u16, indexed by `ddData``
- **Chkdraft** [`src/mapping_core/chk.h`](https://github.com/TheNitesWhoSay/Chkdraft/blob/master/src/mapping_core/chk.h):
  > `Sc::Terrain::Doodad::Type type; // ddDataIndex`
  and [`src/mapping_core/scenario.cpp`](https://github.com/TheNitesWhoSay/Chkdraft/blob/master/src/mapping_core/scenario.cpp)
  subscripts the per-tileset placeability table directly:
  > `const auto & placability = tileset.doodadPlacibility[doodad.type];`
- **staredit wiki**, quoted above: `u16 Doodad ID - dddata.bin index`.

The wiki's `Doodads are different for each tileset` (Scenario.chk, Q2 quote) and `DDDATA.BIN …
Referenced by CV5` make the per-tileset scoping explicit.

### Remastered extends, it does not renumber — from Chkdraft

Chkdraft defines the classic and Remastered CV5 tile-group ranges as exact **complements** per
tileset, so SCR's new doodads occupy group indices *above* the classic ones and classic indices are
unchanged ([`chkd_sc.h`](https://github.com/TheNitesWhoSay/Chkdraft/blob/master/src/mapping_core/sc.h)):

> `classicCv5Ranges { {0,1665},{1979,4096} | {0,933},{1024,1513},{2046,4096} | {0,4096} |
> {0,1262},{1418,4096} | {0,1578},{2046,4096} | {0,770},{1024,1520},{2046,4096} |
> {0,1415},{2039,4096} | {0,797},{1024,1494},{2047,4096} }`
> `scrCv5Ranges    { {1665,1979} | {933,1024},{1513,2046} | {} | {1262,1418} | {1578,2046} |
> {770,1024},{1520,2046} | {1415,2039} | {797,1024},{1494,2047} }`

(Tileset 2 = install has an empty Remastered range, i.e. SCR added no install doodads.) Chkdraft's
`DoodadCv5` struct confirms the two fields are **separate**, which is why classic ids survive:

> `u16 remasteredDoodad;   // 0x1000 = ...`
> `u16 ddDataIndex;        // dddata.bin index`

**Measurement:** in this classic install, `remasteredDoodad` (CV5 offset 6) is `0` for **every**
doodad group on all 8 tilesets — as expected for pre-Remastered data.

### Where the table lives — classic data, not SCR-only

**Measurement** — the tables ship in the classic MPQs:

- `StarDat.mpq`: `tileset\<name>.cv5` for **badlands, platform, install, ashworld, jungle**, plus
  `tileset\<name>\dddata.bin` for those same five tilesets.
- `BrooDat.mpq`: `tileset\<name>.cv5` for **desert, ice, twilight** (plus their `-nc` variants), plus
  `tileset\<name>\dddata.bin` for desert, ice, twilight.
- `arr\sprites.dat` in `StarDat.mpq` supplies the optional overlay sprite for doodads whose CV5
  flags have bit `0x1000` set.

So `dddata.bin` and `.cv5` are per-tileset files, split across the two data archives by tileset:
tilesets 0–4 (badlands, platform, install, ashworld, jungle) in `StarDat.mpq`, tilesets 5–7 (desert,
ice, twilight) in `BrooDat.mpq`.

So the complete id space is defined by **classic** data. SCR's contribution is the
`remasteredDoodad` field and the extra CV5 groups, not the table's existence.

### Measured per-tileset doodad id spaces (classic 1.16.1)

Read from the shipped CV5 files (doodad group = 52-byte record with `u16@0 == 1`; its `ddDataIndex`
is at offset 12):

| tileset | cv5 groups | doodad groups | distinct ids | id range | ids missing inside range |
|---|---|---|---|---|---|
| badlands | 1665 | 629 | **328** | 0–330 | 74, 204, 205 |
| platform | 1513 | 472 | **255** | 0–263 | 47, 48, 49, 96–101 |
| install | 1265 | 241 | **111** | 0–110 | none (contiguous) |
| ashworld | 1262 | 238 | **143** | 0–142 | none (contiguous) |
| jungle | 1578 | 554 | **272** | 0–271 | none (contiguous) |
| desert | 1520 | 496 | **244** | 0–243 | none (contiguous) |
| ice | 1415 | 391 | **204** | 0–203 | none (contiguous) |
| twilight | 1494 | 454 | **179** | 0–180 | 134, 135 |

1736 distinct ids across the 8 tilesets. Self-check that the parse is sound:
`len(groups for an id) == tileHeight` holds for 100% of ids on install (111/111), ashworld (143/143),
desert (244/244), ice (204/204), twilight (179/179), and for all but a handful on badlands
(325/328), platform (252/255), jungle (270/274) — the exceptions are gap-adjacent artifacts.

### This resolves the parent's puzzle

- **Platform {137, 256, 257}**: all three are valid platform ids (table runs 0–263). id 137 →
  CV5 group 1254, flags `0x0280`, 4×2 tiles, **no overlay**; id 256 → groups 1441–1449, flags
  `0x0080`, 12×9, no overlay; id 257 → groups 1450–1458, flags `0x0080`, 12×9, no overlay. ids above
  160 are normal.
- **Ashworld max id 142**: the ashworld table is exactly 0–142 (143 entries), so an observed maximum
  of 142 is the table's maximum, not a coincidence.
- **Ids reaching 287**: also normal — badlands runs to 330, platform to 263.

### Why the 160-GRP set is consistent with a 1736-id space

The GRP files are **optional overlay art**, not the doodad list. Only doodads whose CV5 flags have
bit `0x1000` (Sprites.dat overlay) or `0x2000` (Units.dat overlay) reference a GRP; the rest are pure
terrain doodads whose appearance comes from their `MTXM` tiles.

**Measurement** — overlay breakdown (ids with sprite overlay / unit overlay / terrain-only):

| tileset | sprite overlay | unit overlay | terrain-only |
|---|---|---|---|
| badlands | 58 | 0 | 270 |
| platform | 57 | 0 | 198 |
| install | 8 | 10 | 93 |
| ashworld | 29 | 0 | 114 |
| jungle | 55 | 0 | 219 |
| desert | 49 | 0 | 195 |
| ice | 45 | 0 | 159 |
| twilight | 22 | 0 | 157 |

Only 323 of 1736 ids have any overlay GRP. The `ddNNN.png` filenames in
`AndroidPort\extracted\expand\doodads\` are **not** a doodad-id naming scheme — e.g. jungle ids
25–31, 55, 56, 75–81, 91, 203–211 have overlays pointing at `zerg\*.grp`, `protoss\*.grp`,
`neutral\*.grp` (id 27 → `zerg\zavDeath.grp`, id 29 → `zerg\drone.grp`, id 209 →
`protoss\lshield.los`), and platform 137/256/257 have no overlay at all.

---

## Q4. How does classic pre-1.18 `DDDATA` number doodads?

**There is no classic `DDDATA` CHK section — so there is no `DDDATA` numbering to describe.** The
classic editor's doodad section is `DD2 ` (evidence in Q1), and it numbers doodads by the per-tileset
`dddata.bin` index (Q3). If the parent's source for "classic 8-byte `DDDATA` records" was a
description of `dddata.bin`, that file is not a record list at all: it is `512 × 256 u16` of
placeability constraints, not one entry per placed doodad.

The wiki is explicit that the id is per-tileset and that this section is the classic mechanism:

> `u16: Number of the doodad. Size of the doodad is dependent on this. Doodads are different for each tileset.`

**Classic per-tileset doodad counts (measurement, from the shipped classic CV5 tables):**
badlands **328**, platform **255**, install **111**, ashworld **143**, jungle **272**, desert
**244**, ice **204**, twilight **179**.

These are the counts of distinct doodad ids the classic tables define. They are *not* equal to the
GRP-file counts (ashworld 21 / badlands 42 / jungle 55 / platform 26 / install 16 = 160), because
most doodads have no overlay GRP (see Q3's overlay table).

---

## The concrete id → art mapping

There is **no** general map from a `DD2 ` id to a single GRP filename, because a doodad's art is its
`MTXM` tiles (VX4/VR4 mega-tiles), not a GRP. A GRP exists only for the minority of doodads with an
overlay. The precise algorithm is:

```
tileset = ERA  (0 badlands, 1 platform, 2 install, 3 ashworld,
                4 jungle, 5 desert, 6 ice, 7 twilight)
load "tileset\<name>.cv5"            # 52-byte records; StarDat (0-4) + BrooDat (5-7)

# 1. Build the id -> CV5 group list (the doodad's tile rows)
for g in 1024 .. len(cv5)/52 - 1:
    if u16(cv5, g*52 + 0) != 1: continue          # 1 = doodad group
    ddDataIndex = u16(cv5, g*52 + 12)
    groups_for_id[ddDataIndex].append(g)

# 2. Decode a DD2 record  (8 bytes, little-endian)
id     = u16(rec, 0)      # -> dddata.bin index, per tileset
x      = u16(rec, 2)      # centre X in pixels
y      = u16(rec, 4)      # centre Y in pixels
owner  = u8 (rec, 6)      # player number, 0 = neutral
enabled= u8 (rec, 7)      # 0 = enabled, 1 = disabled

w = u16(cv5, groups_for_id[id][0]*52 + 14)        # width in tiles
h = u16(cv5, groups_for_id[id][0]*52 + 16)        # height in tiles
leftTile = (x - 16*w) / 32
topTile  = (y - 16*h) / 32

# 3. Optional overlay GRP (absent for most doodads)
flags = u16(cv5, groups_for_id[id][0]*52 + 2)
overlayIndex = u16(cv5, groups_for_id[id][0]*52 + 4)
if flags & 0x1000:            # Sprites.dat overlay
    imageIndex = u16(sprites_dat, overlayIndex*8 + 0)   # arr\sprites.dat, 8-byte records
    grpPath    = images_tbl[imageIndex]                 # e.g. thingy\tileset\Platform\Dish1Sha.grp
elif flags & 0x2000:          # Units.dat overlay
    grpPath    = units_dat[overlayIndex]
else:
    grpPath    = None         # terrain-only doodad: its art is the MTXM tiles
```

Verified examples of the overlay chain: ashworld id 0 → `thingy\tileset\Platform\Dish1Sha.grp`;
ashworld id 122 → `thingy\tileset\Badlands\HDRock02.grp`; jungle id 27 → `zerg\zavDeath.grp`;
jungle id 203 → `zerg\zSpawn01.grp`; jungle id 211 → `neutral\stasis.grp`. Note doodads routinely
reference GRPs from *other* tilesets.

CV5 doodad record field offsets (52 bytes total), confirmed against both the wiki and Chkdraft:
`@0 index (1 = doodad)`, `@2 flags`, `@4 overlayIndex`, `@6 remasteredDoodad (0 in classic)`,
`@8 doodadName`, `@10 unknown`, `@12 ddDataIndex`, `@14 tileWidth`, `@16 tileHeight`,
`@18 unknown`, `@20 u16[16] megatile refs`.

---

## What could NOT be determined

1. **Whether any real-world map ever contained a `DDDATA` section.** No such map exists in this
   install, and no documentation describes the tag. It may exist in third-party tooling or
   pre-release builds, but nothing found supports that.
2. **The Remastered (SCR) doodad ids.** This install is classic 1.16.1 with no Remastered data, so
   the ids SCR adds inside the `scrCv5Ranges` gaps could not be enumerated — only the classic
   ranges and the fact that classic ids are unchanged.
3. **Exact classic counts as "official" numbers.** The counts in Q4 are measured from the shipped
   tables, not quoted from a spec. They are self-consistent (the `len(groups) == tileHeight`
   invariant holds for essentially all ids) but no published table states them.
4. **The `doodadName` field's meaning in this data.** scm-js describes CV5 offset 8 as a 1-based
   `stat_txt.tbl` palette-category index ("Trees", "Cliff"). In this repack those values resolve to
   unrelated ability strings (platform id 137 → `971 Return Gas`, ashworld id 0 → `978 Tank Mode`),
   so the field is not usable as a doodad name here. Unresolved.
5. **A handful of per-tileset count mismatches** — badlands (73,75,206), platform (46,50,261),
   jungle (79,235) have `len(groups) != tileHeight`. These are adjacent to MPQ gap positions in this
   install's damaged entries; the counts above treat the missing ids as absent.

## Method note / caveat on this install's MPQ data

`StarDat.mpq`/`BrooDat.mpq` here are a repack with truncated compressed sectors. The correct reader
is `AndroidPort\tools\gapio.py`'s `GapReader(data, gaps)` over `sc_archive.Archive(path).read_with_gaps(name)`,
which indexes the *original* padded coordinate space. An earlier attempt in this investigation
zero-padded at the wrong offset, producing misaligned CV5 data and a false "the local data is
corrupt" conclusion; the CV5 tables above are from the corrected reader and parse exactly per the
documented 52-byte layout. `dddata.bin` is stored uncompressed and was never affected.

DD2 sections in the damaged maps can contain byte-shifted records (e.g. `(4)Inferno.scm` shows
spurious ids 11520/11776/10240 after a one-byte shift at a gap). Any per-record analysis should
validate `id <= 511`, `x < 32*mapWidth`, `y < 32*mapHeight` and discard failures; of 15208 records
checked, 8 were out of bounds and 238 had `id > 511`.

---

## Sources

- [Scenario.chk — Staredit Network Wiki](https://wiki.staredit.net/wiki/Scenario.chk) — `DD2 `,
  `MBRF`, `SWNM`, `IVE2`, `THG2`, `VER ` sections; the 8-byte `DD2 ` record layout; "Doodads are
  different for each tileset"; "only used by the map editor".
- [Terrain_Format — Staredit Network Wiki](https://wiki.staredit.net/wiki/Terrain_Format) — CV5
  52-byte doodad group layout, `Doodad ID - dddata.bin index`, `SC:R Doodad`, DDDATA.BIN
  `ID Range: 0-511`, `entire file is 256KB`.
- [Doodad — Staredit Network Wiki](https://wiki.staredit.net/wiki/Doodad) — doodads are terrain
  chunks occasionally paired with sprites.
- [Chkdraft `src/mapping_core/chk.h`](https://github.com/TheNitesWhoSay/Chkdraft/blob/master/src/mapping_core/chk.h)
  — `Type type; // ddDataIndex`; `DD2 = 540165188` (0x20324444, proving the trailing space).
- [Chkdraft `src/mapping_core/sc.h`](https://github.com/TheNitesWhoSay/Chkdraft/blob/master/src/mapping_core/sc.h)
  — `DoodadCv5` struct; `DdData`/`DoodadPlacibility`; `classicCv5Ranges` vs `scrCv5Ranges`.
- [Chkdraft `src/mapping_core/sc.cpp`](https://github.com/TheNitesWhoSay/Chkdraft/blob/master/src/mapping_core/sc.cpp)
  — `doodadIdToTileGroup` / `getDoodadGroupIndex`; `isRemasteredDoodad`.
- [Chkdraft `src/mapping_core/scenario.cpp`](https://github.com/TheNitesWhoSay/Chkdraft/blob/master/src/mapping_core/scenario.cpp)
  — `tileset.doodadPlacibility[doodad.type]`; doodad placement/validation loop.
- [scm-js `docs/chk-format.md`](https://github.com/scm-js/scm-js/blob/HEAD/docs/chk-format.md) —
  `DD2 ` 8-byte layout table and worked example; "Editors only. The game skips it."
- [scm-js `src/formats/tileset/doodads.ts`](https://github.com/scm-js/scm-js/blob/HEAD/src/formats/tileset/doodads.ts)
  — "DD2 records store the `ddData` index, so it is the doodad's id here too."
- [scm-js `docs/chk.ksy`](https://github.com/scm-js/scm-js/blob/HEAD/docs/chk.ksy) — `sec_dd2`
  schema.
