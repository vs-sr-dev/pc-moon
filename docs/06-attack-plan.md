# The porting route

## Verdict: feasible, by static recompilation

| Road | Meaning | Verdict |
|---|---|---|
| Reimplementation | a new engine reading the assets | No: Renegade Kid's engine and formats are undocumented, and the behaviour (AI, physics, scripting) lives in 1.3 MB of code |
| Decompilation | rebuild C source and compile it for PC | No: no symbols, a large program; a decompilation would be years of work |
| Enhanced emulation | an emulator with upscaling and a mouse | Not a port. melonDS is the oracle (`tools/oracle.py`) |
| **Static recompilation** | translate the ARM code to C++ mechanically; reimplement only the hardware | **Yes** |

Why it is favourable here:

1. **One program, resident, plain.** No overlays on either CPU, the ARM9
   stored uncompressed, the secure area already decrypted
   (`01-cartridge-layout.md`). The recompiler sees all the game's code
   at once, at the address it runs at, and nothing is loaded at run time.
   (The Mobiclip decoder is part of it: the movies need no work.)
2. **The ARM7 is Nintendo's, not the game's.** Its program is the SDK's
   standard ARM7 component, byte for byte the one in the placeholder
   ROMs of the language archives. Whatever the port does with it is done
   once for every game that ships the same component, and ndskit can
   recognise it by its crc32.
3. **The data is the GPU's own.** Textures are `TEXIMAGE_PARAM` words
   with texels and palettes; materials are raw register values
   (`02-data-formats.md`). A renderer that implements the DS's 3D
   engine draws the game without knowing its formats.
4. **The sound is the SDK's sequencer.** 43 sequences and 67 effects in
   one SDAT, no streams: the ARM7's own sequencer plays them, so the
   port needs the 16 sound channels, not a music player.
5. **The game runs at 30 frames a second**, measured in melonDS (eight
   counters of the game advance by 60 while the SDK's VBlank counter
   advances by 120, in two intervals of 2 seconds), on a machine whose
   CPU is a 67 MHz ARM946E-S: a PC has orders of magnitude to spare for
   the recompiled code, the geometry engine in software and a
   high-resolution renderer.

What makes it harder than a Saturn or Wii port:

1. **ARM is harder to translate than SH-2 or PowerPC.** Every
   instruction has a condition; the PC is a general register (reads give
   the instruction's address + 8 or + 4, writes are jumps: `ldr pc`,
   `pop {pc}`, `add pc, pc, rX, lsl #2` switch tables); code runs in two
   instruction sets and changes between them through `bx`/`blx`, so an
   indirect target carries the mode in its low bit; literal pools sit
   between functions; the processor modes bank r13/r14 (the IRQ handler
   runs on its own stack). None of these are new problems for static
   recompilation (they are what the GBA's and the 3DS's recompilers
   solve), but ndskit has to solve them before the first line of the
   game runs.
2. **Two CPUs.** The ARM9 hands the ARM7 the sound, the touch screen,
   the clock, the power and the backup memory through the IPC FIFO and
   shared main memory. Something must answer on the other side.
3. **VRAM is banked.** Nine banks (A-I, 656 KiB in all) are mapped by
   the VRAMCNT registers to the two 2D engines' backgrounds and
   sprites, to the 3D engine's texture and texture-palette slots, to the
   extended palettes or to the CPU (LCDC). The runtime keeps the banks
   and maps them the same way, and the renderers read through the
   mapping. This is the DS's real "memory mapping" problem; the rest of
   the address map is fixed.
4. **Two screens, one of them touched.** The PC needs a layout for them
   and a mouse that plays the stylus (below).
5. **No symbols.** Function boundaries, switch tables and indirect
   targets come from analysis; the SDK's functions can be named by
   signature (they are the same library in every NitroSDK game, which is
   ndskit's to collect).

## Where to cut, subsystem by subsystem

The rule of the kits: **cut at the hardware registers, not at library
APIs**. Then NitroSDK, other libraries and a game's own code all work the
same, and the cut is reusable for the next game. Exceptions are made
where the hardware is a BIOS call.

| Subsystem | Cut | Notes |
|---|---|---|
| ARM9 | recompiled | ARMv5TE, ARM and Thumb; CP15 (caches, TCM placement, protection unit): the cache operations are no-ops, the TCM settings place the ITCM/DTCM windows |
| ARM7 | **recompiled, a coroutine** | the same recompiler (ARMv4T is a subset); run like the Saturn's slave SH-2, deterministically, when the ARM9 waits on it (IPC FIFO, IPCSYNC, shared memory polls) and at its interrupts. Its program is the SDK's, so its recompiled module is reusable by every game with that crc32. The alternative, HLE of the SDK's PXI protocol (sound commands, touch, RTC, power, backup), is kept in reserve: it means reimplementing the SDK's sequencer, which recompiling avoids |
| BIOS | HLE of the SWIs | the few the SDK calls (VBlankIntrWait/IntrWait, Halt, CpuSet/CpuFastSet, the decompressors, Div/Sqrt, GetCRC16): the state as the boot leaves it, the firmware's user settings in main RAM's shared area |
| Interrupts, timers, DMA | registers | IME/IE/IF on both CPUs; four timers each; four DMA channels each, with the ARM9's start modes (VBlank, HBlank, display start, main-memory display, card, geometry FIFO) |
| IPC | registers | IPCSYNC and the two FIFOs between the CPUs, with their interrupts |
| Cartridge | **registers (ROMCTRL, CARD_COMMAND, CARD_DATA_RD)** | the card protocol's main-data read (0xB7) over the .nds file, as the SDK's CARD/FS libraries issue it; the backup memory (EEPROM or flash, on AUXSPI) as a host file. This is the DS's "disc" |
| Math | registers | DIVCNT and SQRTCNT, exact |
| 2D engines A and B | **registers + VRAM, composed per line** | BG layers (text, affine, extended, bitmap), sprites (OBJ), windows, blending, master brightness, the 3D layer as engine A's BG0; drawn in software at 256x192 like saturnkit's VDP2, then scaled with the 3D on top |
| 3D: geometry engine | **GXFIFO and the command ports, in software** | the matrix stacks, lighting, clipping, the vertex and polygon lists, BOX_TEST/POS_TEST/VEC_TEST and the results the game can read back: exact fixed point, because the game's code may depend on them |
| 3D: rendering engine | **OpenGL at the PC's resolution** | the polygon lists drawn by the PC's GPU: the seven texture formats decoded, the polygon modes (modulate, decal, toon/highlight, shadow), translucency and its sort order, alpha test, fog, edge marking, anti-aliasing, the clear image, w- or z-buffering, 1-dot polygons. **This is where the resolution comes from** |
| Sound | registers | the 16 channels (PCM8, PCM16, IMA-ADPCM, PSG, noise) and the two capture units, mixed and played through SDL3 |
| Touch screen, RTC, firmware, power | registers on the ARM7 side (SPI, RTC) | the touch screen from the mouse; the firmware's user settings (name, language) from the port's options |
| Wireless | absent | Moon has no multiplayer; the hardware answers as if no access point were around |
| Window, input | SDL3, OpenGL 4.5 | as in saturnkit and wiikit |

## A better Moon on PC

### Resolution

The 3D engine's polygons are drawn by the PC's GPU at the window's
resolution: the DS computes screen coordinates with sub-pixel bits, and
the port takes them before they are rounded to 256x192. Textures stay as
the cartridge has them (most are 128x128 or less), filtered or not as
the player chooses; higher-resolution textures could be added later as
an optional pack (the `.tex` format is trivial to replace).

The 2D layers (the HUD over the 3D, the lower screen's panels and text)
are drawn at 256x192 and scaled: nearest-neighbour or a pixel-art
scaler, never blurred.

**Widescreen** is possible because the port owns the code: the
projection the game sets up (a 4:3 frustum for 256x192), the culling
that matches it, and the HUD's placement. It is the hardest of these
and comes last.

**Draw distance**: `moon.ini` sets `DrawDistance = 49`. Raising it is one
setting, if fog, the game's own culling and the DS's limits (2 048
polygons and 6 144 vertices a frame, which the port's renderer need not
keep) allow it.

### Mouselook and PC controls

Moon is played with the D-pad to move and the stylus to look ("Slide
Stylus on Touch Screen to look around", "Press +Control Pad to move", in
the first room), a button to fire, and the lower screen's icons for the
map, the weapons and the options. Its controls screen offers a
right-handed and a left-handed layout (`controls.tbl`: "RIGHT HANDED",
"LEFT HANDED", "Shoot", "Move", "Stylus Look / Aim"); which buttons each
uses is drawn on the screen, not written, and is still to be read.

**Level 1 — the mouse is the stylus.** The mouse, in relative mode,
drives a stylus held down on the lower screen; WASD the D-pad; the left
mouse button the fire button; keys for the lower screen's icons. No change to the
game: it already turns by the stylus's motion. Limits: the game's own
sensitivity curve, and turning only as fast as the stylus could.

**Level 2 — the mouse is the camera.** The camera's yaw and pitch, found
in the recompiled code (by following what the touch screen's samples
feed), set directly from the mouse's raw deltas, at full precision, with
a sensitivity setting and invert. Then the view turns at the display's
rate even while the world steps at 30 frames a second: the camera's
orientation is the one thing a player feels at once, and the port can
render the scene with the latest orientation at every display refresh.

### The frame rate

30 frames a second, locked, in the first room. Before promising 60, the
port has to learn how the game steps (per frame or by elapsed VBlanks),
as Virtual Hydlide taught (its logic looked time-based and was not).
Three levels, as there:

1. **No slowdown**: the original 30, never below it (the DS's own
   slowdowns, if Moon has them, vanish).
2. **The camera at the display's rate** (level 2 above): most of what 60
   fps gives an FPS, without touching the game's logic.
3. **60 for everything**: either the game's steps halved where they are
   (if the logic follows a time step, changing it), or the geometry
   interpolated between two frames by the port's own geometry engine
   (it sees every matrix and vertex the game sends).

### The two screens

The upper screen is the game; the lower one is the map, the scanner and
the menus. On PC: the upper screen fills the window, the lower one shown
on demand (a key, as Tab for a map) or as a panel beside or under it,
clickable with the mouse when the cursor is released.

## The phases

| Phase | What | Done when |
|---|---|---|
| 1. Recognise (session 1) | the cartridge, the formats, the oracle, this plan; ndskit: `rom`, `hw`, `lz`, `sdat`, `arm` | this document |
| 2. Code map | function discovery for CodeWarrior's ARM and Thumb code (switches, literal pools, interworking), the SDK's libraries named by signature, the main loop and its pacing, the interrupt handlers, what the ARM9 asks of the ARM7, how geometry reaches the GPU, where the touch screen's samples go (the camera) | every function of the ARM9 and ARM7 found, checked against Ghidra; the frame loop read |
| 3. Recompiler | ARM and Thumb to C++, one module per program; an ARM interpreter as its oracle; the self-test (vectors from the interpreter) | both programs compile and link; the self-test has no difference |
| 4. Runtime core | memory map with VRAM banks, interrupts, timers, DMA, IPC, the cartridge, the BIOS HLE; the ARM7 as a coroutine | headless, the game boots to its title, its RAM matching melonDS's states at the same points |
| 5. Video | the 2D engines in software, the geometry engine, the OpenGL renderer at N times the resolution; the window, the keyboard, the mouse as the stylus | the logos, the title, the first room on screen, played |
| 6. Sound | the 16 channels and capture | the music and effects, by ear against melonDS |
| 7. PC | mouselook on the camera, the screens' layout, the frame rate, widescreen, draw distance; the backup memory as a file | played by the user |

## Oracle

melonDS (`D:\Tools\melonDS-oracle`, a copy of the user's with its own
settings), driven by `tools/oracle.py`: launched with the cartridge,
pressed through the keyboard and the mouse, photographed, and read
through its savestates, whose sections hold the whole machine (main
RAM, the TCMs, the CPUs, the GPU, the sound). The runtime's RAM can be
compared with melonDS's at the same point of the game, which is a much
sharper check than pictures. The scripted route from launch into the
first room takes under 50 seconds.
