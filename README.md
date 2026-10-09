# pc-moon

A native PC port of **Moon** (Nintendo DS, Renegade Kid, 2009), the
first-person shooter set in a buried alien complex under the lunar
surface: corridors, a remote drone, a moon buggy, and some of the most
ambitious 3D the DS ran. Both of the cartridge's programs are
recompiled statically to C++ and run on a runtime that replaces the
DS's hardware: Moon plays on PC in a window, its 3D drawn by the PC's
GPU at the window's resolution, its sound on the PC's audio device. The
goal beyond that is a PC shooter: the mouse as the camera, the keys of a
PC shooter, the lower screen where a PC player wants it.

This repository documents the cartridge, its formats and its code, and
holds the port's tooling. Alongside it grows **ndskit**, a
game-agnostic toolkit for DS reverse engineering and static
recompilation: everything the port needs that is not specific to Moon.
ndskit was split out of this repository with its history and is taken
back as a git submodule at `ndskit/`: clone with `--recursive` (or run
`git submodule update --init` after a clone).

## BYOA — Bring Your Own Assets

This repository contains **documentation and tools only**. No game data, no
executables, no assets. You need your own cartridge, dumped. The work is
done on the European release, `Moon (Europe) (En,Fr,De,Es,It).nds`
(game code COOP, version 0, NitroSDK 4.2), a 64 MiB image with its
secure area decrypted, placed in the repository's root or in `rom/`.

## Playing it

You need Python 3, and to build: clang, CMake, Ninja and SDL3 (on
Windows, MSYS2's `mingw-w64-x86_64` packages), and a GPU with OpenGL
4.5. From the repository's root, with your cartridge there:

```sh
ROM="Moon (Europe) (En,Fr,De,Es,It).nds"
export PATH=/c/msys64/mingw64/bin:$PATH       # Windows: MSYS2's tools, and SDL3.dll at run time
python -m ndskit.recomp "$ROM" --out build/recomp --copy 9:01FF9A60=0212FED4:659C   # about 20 s
cmake -S build/recomp -B build/recomp/b -G Ninja -DCMAKE_CXX_COMPILER=clang++
ninja -C build/recomp/b                                                             # about a minute
build/recomp/b/ndsrun "$ROM" --window --out build/play
```

The save is kept in `build/play` (the `--out` directory). For now the
keys are melonDS's defaults; a PC shooter's keys and the mouse as the
camera are the next step.

| Key | DS |
|---|---|
| X, Z, S, A | A, B, X, Y |
| Q, W | L, R |
| Enter, Backspace | START, SELECT |
| the arrows | the D-pad |
| left mouse button, on the lower screen | the stylus |
| F12 | a picture into `build/play` |
| Escape | quit (the save is written) |

`--scale N` draws the 3D at N times the DS's resolution (by default,
the window's); `--mute` turns the sound off; `--wav FILE` records it.

## Layout

    docs/            cartridge, format and code analysis, and the plan
    tools/           Moon-specific tools: oracle.py
    ndskit/          the game-agnostic DS toolkit (a submodule)
    rom/, build/     your cartridge and everything derived from it (ignored by git)

## Tools

The Python tools need only Python 3 and no dependencies (the oracle
needs PIL for its screenshots, and a copy of melonDS for itself:
`ORACLE_DIR`, `tools/oracle.py`). The recompiled code needs clang, CMake,
Ninja and SDL3. Run from the repository root.

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

# the recompiler: both programs to C++, the self-test (docs/09-recompiler.md)
python -m ndskit.recomp "$ROM" --out build/recomp --optest --copy 9:01FF9A60=0212FED4:659C
python -m ndskit.recomp.selftest "$ROM" --cpu 9 --auto --out build/recomp/selftest/arm9.txt
python -m ndskit.recomp.selftest "$ROM" --cpu 7 --auto --out build/recomp/selftest/arm7.txt
cmake -S build/recomp -B build/recomp/b -G Ninja -DCMAKE_CXX_COMPILER=clang++ && ninja -C build/recomp/b
build/recomp/b/selftest build/recomp/selftest/*.txt
python -m ndskit.armemu "$ROM" --cpu 9 --call 02126428 --regs r0=64,r1=7      # run one of the game's functions

# the runtime: the game headless, compared with melonDS at the same frame (docs/11-runtime.md)
build/recomp/b/ndsrun "$ROM" --out build/run --vblanks 466
python -m ndskit.melonds build/oracle/first.ml1 --compare build/run
build/recomp/b/ndsrun "$ROM" --out build/route --vblanks 3644 --input "1182:START,1542:tap:128:96,1902:START,2082:START,2262:START,2442:START,2622:A,2862:tap:128:120,3042:tap:128:120,3222:tap:128:120,3402:UP"

# the picture and the sound, headless: both screens at given frames, the sound as a file (docs/12, 13)
build/recomp/b/ndsrun "$ROM" --out build/p5 --vblanks 1500 --shots 700,1400 --wav build/p5/sound.wav
python -m ndskit.melonds build/oracle/first.ml1 --info                 # a state's sections and sound channels

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

Session 3: the recompiler. ndskit gained an ARM interpreter (checked
against Unicorn's ARM946), a recompiler from ARM and Thumb to C++ and the
runtime's first lines. Both of Moon's programs, 5 413 and 933 functions,
compile and link, and agree with the interpreter on 81 555 vectors: an
instruction test of each CPU and 1 512 of the game's own functions
(`docs/09-recompiler.md`).

Session 4: the runtime core. ndskit's machine runs both programs as the
DS does, headless and deterministic: two CPUs in virtual time, the SDK's
threads each on a coroutine, interrupts, the BIOS, the I/O, VRAM's banks,
timers, DMA, IPC, the cartridge and its save, SPI and the RTC. Moon boots,
plays its movies (their decoder copied to the ITCM and recompiled where
it runs), reads its save and, with eleven presses, walks its menus into
the first room. Against melonDS at the same frame and with the same save, 74 bytes of
4 MiB of main RAM differ after 464 frames (`docs/11-runtime.md`).

Session 5: the picture. Moon plays in a window in real time: the 2D
engines in software, the geometry engine in the DS's fixed point, the
3D drawn with OpenGL at the window's resolution, the keyboard and the
mouse as the DS's buttons and stylus. Along the route the pictures match
melonDS's at the same frames (`docs/12-picture.md`).

Session 6: the sound. The ARM7's sound unit (16 channels, capture, the
mixer) runs in virtual time and plays through SDL3; any run can write
it to a WAV file. Its registers match melonDS's at the same frames, and
the user's ears confirmed it against melonDS, after a crackle at the
start of the movies was traced to when samples were read
(`docs/13-sound.md`).

## Documentation

* [00-sessions.md](docs/00-sessions.md) — what each session did
* [01-cartridge-layout.md](docs/01-cartridge-layout.md) — header, programs, autoloads, the file system, the language archives
* [02-data-formats.md](docs/02-data-formats.md) — first look at the game's files
* [03-executables.md](docs/03-executables.md) — the ARM9 and the ARM7: crt0, memory, libraries
* [04-curiosities.md](docs/04-curiosities.md) — things found on the way
* [05-open-questions.md](docs/05-open-questions.md) — what is not known yet
* [06-attack-plan.md](docs/06-attack-plan.md) — feasibility, where to cut, a better Moon on PC, the phases
* [07-next-session.md](docs/07-next-session.md) — the next session's list
* [09-recompiler.md](docs/09-recompiler.md) — ARM and Thumb to C++, the self-test
* [11-runtime.md](docs/11-runtime.md) — the machine: CPUs, threads, interrupts, BIOS, I/O; against melonDS
* [12-picture.md](docs/12-picture.md) — the 2D engines, the geometry engine, the OpenGL renderer, the window
* [13-sound.md](docs/13-sound.md) — the sound unit, the audio device, the movies' crackle
* [10-ndskit.md](docs/10-ndskit.md) — what this port gave ndskit

## Licence

MIT — see [LICENSE](LICENSE). Moon is © 2009 Renegade Kid; this project
contains none of it.
