# The formats at a glance

A first look, session 1. What is marked *verified* was checked on every
file of the kind; the rest is read from a few files and marked as
inference.

## The engine feeds the GPU its own formats

The strongest impression of the first look: Renegade Kid's engine stores
its 3D data in the DS GPU's native forms. Textures are `TEXIMAGE_PARAM`
words with texels and palettes ready to copy into texture VRAM;
materials in the scenes and models are raw register values
(`POLYGON_ATTR` 0x001F808F, `DIF_AMB` 0x14A54A52, `SPE_EMI`). For the
port this is good news: if the geometry also goes to the GPU as command
lists, a renderer that implements the DS geometry and rendering engines
draws everything without knowing the game's formats.

## `.tex` — textures (*verified*, 630 of 630)

    u32   TEXIMAGE_PARAM, its low 16 bits (the VRAM offset) 0: filled in when uploaded
    ...   texels: width x height at the format's bits per pixel
    ...   palette: BGR555, as many colours as the format has

| Format | Files | Palette bytes |
|---|---|---|
| 16-colour (4 bpp) | 442 | 32 |
| 256-colour (8 bpp) | 97 | 512 |
| A5I3 (8 colours, 5-bit alpha) | 48 | 16 |
| A3I5 (32 colours, 3-bit alpha) | 35 | 64 |
| 4-colour (2 bpp) | 8 | 8 |

No 4x4-compressed and no direct-colour texture. 89 set "colour 0 is
transparent". Sizes from 32x32 to 256x256, most 128x128 (198) and 64x64
(160). A textured file is therefore its own decoder input: width,
height, format and transparency are in its first word.

## `.scn` and `.col` — a section's scene and collision

Every one is compressed with the BIOS's LZ77 (*verified*: 251 `.scn`,
252 `.col`, all decode to their stated size with `ndskit.lz`; 12 of each
use the LZ11 variant). Sections are named by area and number: `a0`-`a6`
(36, 22, 29, 37, 23, 20, 16 sections), `s0`/`s1`, `v1`-`v6` (the buggy's
areas, inferred from `buggy.ini` and the counts), `d0`, `m0`, and four
`dummy*.scn`.

`a0_000.scn` decompressed (49 888 bytes) starts with a table of offsets
and counts into itself, then records in which the material words above
recur. Its exact structure is for a later session; whether the geometry
is stored as packed GX command lists (sent to GXFIFO by DMA) is the
question that matters for the renderer (`05-open-questions.md`).

## `.msh`, `.anm`, `.uva`, `.msa` — models and their animation

`.msh` (80): a small header of counts and fixed-point values, then the
same material records as the scenes (`ar15.msh`: at 0x44). `.anm` (159):
a count, then fixed-point (20.12?) values: keyframes. `.uva` (72):
a count, then a falling sequence of fixed-point values (texture
coordinate scrolls, inferred). `.msa` (59): a count, then pairs of
BGR555 colours (`a_in_cr1.msa`: a ramp from dark to white), material
colour animations (inferred).

## `.ini` — configuration in plain text

The game parses INI files with `sscanf` (its format strings are in the
ARM9: `%31[^][)(,:;."'/\ ]...`). `config/moon.ini`:

    StartSection0 = s0_000 ... StartSection23 = v6_000   (where each episode starts)
    StartCinema0 = intro
    EnableAllEpisodes = false
    SkipIntro = false
    BgmVolume = 127
    DrawDistance = 49

`buggy.ini` holds the buggy's physics as floats (mass, inertia, grip,
gear ratios, drag, `CameraDist`); a weapon's INI its ammunition, clip,
damage and range; `config/{easy,norm,hard}/enemy_*.ini` each enemy's
parameters per difficulty. **`DrawDistance` is a setting the engine
reads**: the first candidate for a longer view on PC, once it is known
what else bounds it (fog, culling, the GPU's 2048 polygons per frame).

## `.mo` — Mobiclip video

48 files, 24.8 MB (38% of the cartridge): the cut-scenes, in
Actimagine's Mobiclip format (magic `MODS`); the ARM9 carries the
decoder (`[SDK+Actimagine:Mobiclip SDK V1.0.3]`). In a recompilation the
decoder is just more ARM code and runs as it is; nothing to write
unless the port wants the movies re-encoded.

## `dsMoon.sdat` — sound (*verified*: every record)

`python -m ndskit.sdat build/extract/dsMoon.sdat --list`:

| Kind | Count | |
|---|---|---|
| SEQ | 43 | the music: `SEQ_MUSIC01_TUNE01` ... `SEQ_MUSIC11_TUNE07`, each with its bank (14-24) |
| SEQARC | 1 | `SEQ_SE`: 67 sound effects |
| BANK | 31 | instruments |
| WAVEARC | 1 | 2.5 MB of samples, all the sound's data |
| PLAYER | 1 | `PLAYER_DEFAULT` |
| STRM | 0 | no streamed audio |

All the music is sequenced: it is played by the sequencer in the SDK's
ARM7 component, from one wave archive. (The movies' sound is inside the
`.mo` files.)

## Nintendo's 2D formats

`.nclr`/`.ncgr`/`.nscr` (palettes, characters, screens: the lower
screen's panels, menus and the title), `.ncer`/`.nanr` (sprite cells and
their animations), `.nftr` (two fonts). These are the SDK's standard G2D
formats, shared by most DS games: decoders for them belong in ndskit
when the port needs them.

## Smaller ones

`parammap0-23.bin` (24, one per start section, inferred), `markers/`
(`.mom` of 8 bytes, `.bin`), `ff_dam_1/2.opa` (a count and a byte ramp:
a force field's opacity cycle, inferred), the language archives' `.tbl`,
`.sub` and numbered text files (`01-cartridge-layout.md`).
