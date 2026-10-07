# pc-moon

Toward a native PC port of **Moon** (Nintendo DS, Renegade Kid, 2009),
the first-person shooter set in a buried alien complex under the lunar
surface: corridors, a remote drone, a moon buggy, and some of the most
ambitious 3D the DS ran. The goal is the game running natively on PC,
and running as a PC shooter: the 3D at the screen's resolution, the
mouse as the camera, the lower screen where a PC player wants it.

This repository documents the cartridge, its formats and its code, and
grows the tooling for the port. Alongside it grows **ndskit**, a
game-agnostic toolkit for DS reverse engineering and static
recompilation: everything the port needs that is not specific to Moon.
ndskit lives in `ndskit/` for now; it will move to its own repository
and come back here as a submodule, as wiikit did from its first port.

## BYOA — Bring Your Own Assets

This repository contains **documentation and tools only**. No game data, no
executables, no assets. You need your own cartridge, dumped. The work is
done on the European release, `Moon (Europe) (En,Fr,De,Es,It).nds`
(game code COOP, version 0, NitroSDK 4.2), a 64 MiB image with its
secure area decrypted, placed in the repository's root or in `rom/`.

## Layout

    docs/            cartridge, format and code analysis, and the plan
    tools/           Moon-specific tools: oracle.py
    ndskit/          the game-agnostic DS toolkit (to become a submodule)
    rom/, build/     your cartridge and everything derived from it (ignored by git)

## Tools

The Python tools need only Python 3.8+ and no dependencies (the oracle
needs PIL for its screenshots). The oracle needs melonDS. Run from the
repository root.

```sh
ROM="Moon (Europe) (En,Fr,De,Es,It).nds"

# the cartridge: header, programs, autoloads, SDK, banner; its files, and the language archives inside
python -m ndskit.rom "$ROM" --info
python -m ndskit.rom "$ROM" --list
python -m ndskit.rom "$ROM" --extract build/extract --nested

# the formats: BIOS LZ77 in the scenes, the sound archive
python -m ndskit.lz --scan build/extract
python -m ndskit.lz build/extract/a0_000.scn --out build/a0_000.scn.dec
python -m ndskit.sdat build/extract/dsMoon.sdat --list

# the code: the ARM9's crt0, its hardware registers
python -m ndskit.arm "$ROM" --offset 4000 --size 152078 --base 02000000 --at 02000800 --count 40
python -m ndskit.arm "$ROM" --offset 4000 --size 152078 --base 02000000 --refs 04000000:04002000
python -m ndskit.hw 04000400 04000540 027E0000

# every function of both programs, and Ghidra's for comparison (ndskit/ghidra/ExportFuncs.java)
python -m ndskit.recomp.discover "$ROM" --cpu 9 --report --out build/disc9.tsv
python -m ndskit.recomp.discover "$ROM" --cpu 7 --out build/disc7.tsv

# the oracle: melonDS, pressed, photographed and read through its savestates
python tools/oracle.py --fresh --at 20:START,32:START,38:tap:128:96,44:A,48:shot,50:state
python tools/oracle.py --peek build/oracle/t50.ml1 027FFC3C:4
python tools/oracle.py --fresh --at 20:START,26:tap:128:96,32:START,35:START,38:START,41:START,44:A,48:tap:128:120,51:tap:128:120,54:tap:128:120,57:UP,61:state,64:drag:60:120:110:120,66:state
```

## Status

Session 1: feasibility. The cartridge read (one resident ARM9 program,
no overlays, the SDK's standard ARM7, five language archives that are
NitroROM images of their own), the formats at a glance (textures and
materials in the GPU's own form, BIOS-compressed scenes, Mobiclip
movies, all music sequenced), the oracle (melonDS driven from here,
into the first room in under 50 seconds; read through its savestates),
the frame rate measured (30 fps; session 2 found it is 60 in play), and the plan: static recompilation,
the hardware cut at its registers, the 3D drawn by the PC's GPU at its
resolution, the mouse first as the stylus and then as the camera
(`docs/06-attack-plan.md`). ndskit begun: `rom`, `hw`, `lz`, `sdat`,
`arm`.

Session 2: the code map. ndskit finds every function of both programs
(the ARM9's 5 395, 99.6% of what Ghidra finds and 749 more; the ARM7's
925, read where its autoloads run), with no conflict. The frame rate
corrected: Moon runs at 60 frames a second in play (session 1 had
measured a tutorial box). The play frame, the display lists sent by DMA
from ITCM, and the camera's view matrix found (`docs/03-executables.md`).

## Documentation

* [00-sessions.md](docs/00-sessions.md) — what each session did
* [01-cartridge-layout.md](docs/01-cartridge-layout.md) — header, programs, autoloads, the file system, the language archives
* [02-data-formats.md](docs/02-data-formats.md) — first look at the game's files
* [03-executables.md](docs/03-executables.md) — the ARM9 and the ARM7: crt0, memory, libraries
* [04-curiosities.md](docs/04-curiosities.md) — things found on the way
* [05-open-questions.md](docs/05-open-questions.md) — what is not known yet
* [06-attack-plan.md](docs/06-attack-plan.md) — feasibility, where to cut, a better Moon on PC, the phases
* [07-next-session.md](docs/07-next-session.md) — the next session's list
* [10-ndskit.md](docs/10-ndskit.md) — what this port gave ndskit

## Licence

MIT — see [LICENSE](LICENSE). Moon is © 2009 Renegade Kid; this project
contains none of it.
