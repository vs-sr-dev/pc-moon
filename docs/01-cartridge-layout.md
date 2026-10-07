# The cartridge

Everything here was read from the user's dump with `ndskit.rom`:

```sh
python -m ndskit.rom "Moon (Europe) (En,Fr,De,Es,It).nds" --info
python -m ndskit.rom "Moon (Europe) (En,Fr,De,Es,It).nds" --list
python -m ndskit.rom "Moon (Europe) (En,Fr,De,Es,It).nds" --extract build/extract --nested
```

## The image

| Field | Value |
|---|---|
| File | `Moon (Europe) (En,Fr,De,Es,It).nds`, 67 108 864 bytes (a 64 MiB cartridge, 0x3FFC424 bytes used) |
| Title / game code / maker | `MOON` / `COOP` / `KJ` |
| Unit code, version, region | 0 (DS), 0, 0 |
| Header CRC, logo CRC | 0x51C7 and 0xCF56, both correct |
| Secure area | decrypted (the 0xE7FFDEFF marker in place of "encryObj") |
| Banner | version 1 (six languages), every title "Moon / Gamebridge Ltd." |
| SDK | NitroSDK 4.2 (ModuleParams' version word 0x04027533, relstep 30003) |

Gamebridge published the European release; the title screen also shows
Mastiff, the American publisher, and Renegade Kid, the developer.

## The two programs

| | Image offset | Size | Loads at | Entry |
|---|---|---|---|---|
| ARM9 | 0x00004000 | 0x152078 (1.32 MiB) | 0x02000000 | 0x02000800 |
| ARM7 | 0x00156200 | 0x027080 (156 KiB) | 0x02380000 | 0x02380000 |

* **No overlays**, on either CPU: the whole game is one ARM9 program,
  resident from boot. For a static recompiler that is the easiest case
  there is: one module, nothing loaded at run time, no code swapped at
  one address.
* **The ARM9 is stored plain**: ModuleParams (at 0x02000B9C, found
  through the footer 0xDEC00621 / 0xB9C after the program) says
  `compressed_static_end = 0`.
* **Autoloads** (copied by the crt0 at boot): 0x1A60 bytes to ITCM
  (0x01FF8000, the SDK's mirror of address 0) from 0x021505A0, and 0x60
  bytes plus 0x20 of BSS to DTCM (0x027E0000) from 0x02152000. The static
  BSS is 0x021505A0-0x0215A460 (it overlaps the autoload sources, which
  are dead once copied).
* **The ARM7 is Nintendo's**: byte for byte the same program (crc32
  0x1B16DBE2) as the ARM7 of the five language archives below, which
  carry a placeholder ARM9. It is the SDK's standard ARM7 component, not
  Renegade Kid's code (`03-executables.md`).

## The file system

2 593 files in 7 directories, from 0x0018B000 to the end of the used
area; every FAT entry is named (no anonymous files).

| Directory | Files | Size | What |
|---|---|---|---|
| (root) | 1 838 | 59.4 MB | levels, models, animations, 2D screens, movies, sound, the language archives |
| `config/` | 10 | 0.01 MB | text INI files: `moon.ini` (start sections, flags, draw distance), `buggy.ini` (the vehicle's dynamics), one per weapon (`ls`, `mp`, `oc`, `plasmarifle`, `rsd`, `sar`, `sp`, `sr`: ammunition, clip, damage, range) |
| `config/easy/`, `config/norm/`, `config/hard/` | 30 each | | one INI per enemy type per difficulty |
| `markers/` | 25 | | 16 `.mom`, 8 `.bin`, 1 `.ini`, named by section (map markers?) |
| `tex/` | 630 | 5.1 MB | textures in the GPU's own format |

By kind, over the whole tree:

| Extension | Files | Size | Format |
|---|---|---|---|
| `.mo` | 48 | 24.8 MB | Mobiclip video (`MODS`), Actimagine's codec: the cut-scenes |
| `.scn` | 251 | 13.1 MB | a section's scene, BIOS LZ77 (239 LZ10, 12 LZ11) |
| `.col` | 252 | 10.9 MB | a section's collision, BIOS LZ77 (240 LZ10, 12 LZ11) |
| `.tex` | 630 | 5.1 MB | textures: a TEXIMAGE_PARAM word, texels, palette |
| `.sdat` | 1 | 2.6 MB | `dsMoon.sdat`, the NitroSDK sound archive |
| `.srl` | 5 | 2.1 MB | the language archives (below) |
| `.nclr` `.ncgr` `.nscr` | 288, 288, 281 | 3.8 MB | Nintendo G2D palettes, characters, screens (the lower screen's panels, menus) |
| `.ncer` `.nanr` | 13, 13 | | G2D cells and their animations (sprites) |
| `.anm` | 159 | 1.6 MB | model animations |
| `.msh` | 80 | 0.6 MB | models (meshes) |
| `.uva`, `.msa` | 72, 59 | | UV and material animations (inferred from the names and contents) |
| `.ini` | 101 | | text configuration |
| `.bin`, `.mom` | 32, 16 | | `parammap*.bin` (24, one per episode?) and the markers |
| `.nftr` | 2 | | Nintendo fonts |
| `.opa` | 2 | | `ff_dam_*`: a byte ramp, a force field's opacity cycle? |

## The language archives

`de.srl`, `en.srl`, `fr.srl`, `it.srl`, `sp.srl` (about 415 KB each) are
whole NitroROM images (title `NINTENDO`, code `NTRJ`, maker `01`) with a
header, an FNT and an FAT of their own: 287 files in 3 directories. Their
ARM9 is a 4 KiB placeholder (entry 0x02000850) and their ARM7 the same
standard component as the game's: they are made by the SDK's ROM builder
as data containers, never run. The game's ARM9 names them with the
format strings `rom:/%c%c.srl` and `lng:/%s%03u%s`: it opens the
language's `.srl` from the cartridge's file system and mounts its file
system as an archive called `lng:` (the NitroSDK FS library can mount a
NitroROM image as an archive).

Each holds what differs by language: the episode and mission texts
(`episode.000-023`, `examine.*`, `inform.*`, `inform2.*`, `open.*`), the
movies' subtitles (`briefing.sub`, `intro.sub`, `fin.sub`, ...), the
menus' tables (`gui.tbl`, `options.tbl`, `save.tbl`, `credits.tbl`,
`controls.tbl`, `missions.tbl`, `map.tbl`), screens with text on them
(`deathtop.*`), `comlink/` (105 files, `ep000.000` on: the radio
messages by episode) and `tex/` (one texture, `signs_01.tex`: the
signs on the walls, translated).
