# What this port gave ndskit

ndskit was born with this port, in `ndskit/`. When its second port,
pc-nostalgia, began, it was split out with its history (`git subtree
split --prefix ndskit`) into its own repository and came back here as a
git submodule at the same path (URL `../ndskit`, relative, so it follows
wherever the repositories live), as wiikit did from pc-victorious. A
commit that changes ndskit is made in the kit; this repository records
which commit of the kit it builds with, and each change of the kit is
checked here before it is taken.

## The split (pc-nostalgia's session 1)

The kit's eight commits came out of this history with their content
unchanged; `ndskit/` was replaced by the submodule. Checked on the
submodule: the recompiler's output builds, the self-test gives 81 555
vectors with no failure, and the run of 466 VBlanks is 74 bytes of main
RAM from melonDS's state at frame 464, as before.

## Session 1

| Module | What | Checked by |
|---|---|---|
| `rom` | cartridge images: header, CRC-16 checks, the secure area's state, ARM9/ARM7, NitroSDK ModuleParams through the footer (autoloads, BSS, compression, SDK version), overlay tables, FNT/FAT, banner titles and icon, extraction with `sys/`, NitroROM images nested as archives (`--nested`), the SDK's backward LZ | Moon and its five language archives; two other cartridges of the user's for the backward LZ (an ARM9 decompressed to exactly the end of its autoload list) and overlays (366 and 3). Those found two bugs: the autoload list read before decompressing, and the byte order of a backward-LZ pair |
| `hw` | the ARM9's and the ARM7's address maps and I/O register names (2D engines A and B, 3D, DMA, timers, IPC, card, VRAM banks, maths; the ARM7's sound channels, SPI, RTC, power) | the names met in Moon's code, read in context |
| `lz` | the BIOS's LZ77, LZ11 and RLE; `--scan` | Moon's 503 scene and collision files |
| `sdat` | SDAT: every record of the eight kinds, the symbols (sequence archives' inner names too), FAT, extraction by name | Moon's sound archive |
| `arm` | ARMv5TE/ARMv4T and Thumb decoder: structured fields, targets, interworking, `writes_pc`; disassembly with literals and register names; `--refs`, `--census`, `--arm7` | every Thumb halfword and 1.39 million ARM words against capstone 5: no disagreement on a v5TE encoding |

## Session 2

| Module | What | Checked by |
|---|---|---|
| `rom` | the ARM7's ModuleParams, found by its shape (it has no footer); `--info` shows its autoloads | three cartridges (SDK 4.1, 4.2, 5.4) |
| `recomp.discover` | function discovery: segments at their run addresses, ARM and Thumb, interworking, veneers and calls through registers by straight-line constants, CodeWarrior's `addls pc` switch, hand-written jumps through offset tables, lr set as a return address, opposite conditions ending a block, pointer/boundary/prologue seeds | Moon's ARM9 and ARM7 against Ghidra (99.6% and 535 of 536 of its functions, many more besides), 0 conflicts on three cartridges; a conflict on another cartridge taught two rules (an lr set further back, opposite conditions) |
| `ghidra/ExportFuncs.java` | Ghidra's functions with their mode, and a pre-script that gives analysis its root | Moon's ARM9, ITCM block and ARM7 |

## Session 3

| Module | What | Checked by |
|---|---|---|
| `armemu` | an ARM interpreter: ARMv5TE (the ARM9) and ARMv4T (the ARM7), ARM and Thumb, conditions, the shifter's carry, every addressing mode, ldm/stm with the DS's rules for the base in the list, the multiplies and the DSP group, CLZ, the saturating adds, interworking, the processor modes with their banked registers and SPSRs, exception returns; unaligned accesses as the two CPUs do them; the DS's memory map for tests; `--call` runs a function of a cartridge | Unicorn's ARM946 (scratch script): 12 993 ARM and 12 490 Thumb random instructions and 1 960 transfers, no difference outside unaligned accesses and what the architecture leaves open; the SDK's divisions on known answers |
| `recomp.discover` | each write to pc recorded with what it was taken for (`Function.sites`); constants through `add`/`sub #imm` and `mov rd, pc`; Thumb's `bx pc`; tables of offsets followed through registers, before or after the table; switch bounds through `subs rI, rX, #k` and past conditional branches; jumps into unrolled code; addresses a function puts in lr walked; the opposite-conditions rule redone across joins; no function opens with a condition; empty callbacks | Moon's ARM9 now 5 413 functions with 147 switches and 3 unresolved jumps, its ARM7 933; 0 conflicts on three cartridges; Ghidra's comparison unchanged (4 648 of 4 680 as entries) |
| `recomp.emit`, `python -m ndskit.recomp` | the recompiler: one C++ function per entry, one module per program; conditions, flags stored only where read (liveness), the PC as a value, literal pools folded, calls checked on return, calls through registers dispatched by address and mode, switches as `switch`, jumps to run time, the function's own lr addresses, exception returns, CP15/SWI as runtime calls, safe points | both of Moon's programs compile and link (clang 22, 42 s clean); the self-test |
| `recomp.selftest` | vectors recorded with armemu: the instruction test (every form per CPU, random sequences for the flags, hand-assembled control flow) and the game's functions that run alone (`--auto`) | 81 555 vectors, no difference; a planted wrong carry gives 91 failures |
| `runtime/` | the first lines, C++20: `arm.h` (the context, memory per CPU, the shifter, saturation, the CPSR), `core.cpp` (main RAM, ITCM, DTCM, the ARM7's WRAM and shared WRAM, modes and banks, dispatch over the modules), `services_stub.cpp`, `selftest.cpp`, `runtime.cmake` | the self-test |

## Session 4

| Module | What | Checked by |
|---|---|---|
| `runtime/` (the machine) | `machine.cpp` (both CPUs in quanta of virtual time, events, interrupts, halts, the SDK's threads each on a coroutine with the guest's context switches followed, CP15, a call trace, breaks, a store watch, the report), `coro` (fibers), `bios` (melonDS's direct boot, the SWIs, the IRQ entry and return), `mmio` (both CPUs' registers, the palettes, VRAM, OAM, the GBA slot, the BIOS's logo), `system` (timers, DMA, IPC, the maths unit), `video` (lines, DISPSTAT and VCOUNT, VRAM's nine banks, the geometry engine's registers), `cart` (the ROM's commands, the backup memory on AUXSPI), `spi` (power, firmware, touch; the RTC), `sound` (registers, channels' busy bits), `input` (a script), `main` (`ndsrun`) | Moon from its boot into its first room, deterministic; against melonDS's savestates at the same frame: 74 bytes of main RAM differ after 464 frames (the same save), the ITCM and the shared WRAM not at all |
| `melonds` | melonDS savestates: their sections, main RAM, the TCMs, the shared WRAM and the ARM7's WRAM located (checked against the runtime's memories: the shared WRAM identical); `--compare` with a run, by memory and range | Moon's oracle states |
| `recomp.discover` | context saves and their callers' landings; interrupt stubs (veneers in tables); two of three marks (literal, table, boundary) for a pointer's target, the table's mark to a fixed point within a pass; an unclassified `bx lr` as a function's end; entries inside walked code for `this` thunks; `addge` switches bounded further back; holes in tables of offsets; conditional code addresses (`addhs`/`addlo rX, pc`) | Moon's ARM9 6 580 functions (session 3: 5 413), all 4 680 of Ghidra's covered, every old entry kept; 0 conflicts on the three cartridges, which all gain functions |
| `recomp.emit`, `__main__` | calls in functions holding landings catch `ArmUnwind`; `arm_context_saved` after a context save; `ARM_ENTER` at each entry; `--copy` (code copied at run time, recompiled where it runs); segments marked as copied | the self-test unchanged (81 555 vectors, no difference); the runtime |

## Session 5

| Module | What | Checked by |
|---|---|---|
| `runtime/gpu2d.cpp` | the two 2D engines in software, a line at a time: text, affine, extended and large-bitmap backgrounds, 16 and 256 colours, the extended palettes; sprites (tiles in 1D and 2D mapping, bitmaps, affine, double-size, semi-transparent, window); windows; blending; the master brightness; the display modes; the 3D layer handed to the compositor as two words a pixel; the compositor in software | Moon's logos, movies, menus and lower screen in play, against melonDS's pictures: the menu's lower screen identical but for a pulsing border |
| `runtime/gx.cpp`, `render3d.h` | the geometry engine: packed GXFIFO and the ports, the matrix stacks, vertices, texture coordinate transforms, lighting, polygons and strips, culling, clipping, the viewport, BOX_TEST/POS_TEST/VEC_TEST and the read-backs, GXSTAT, the swap at the VBlank with a queue behind it; a frame's job for the rendering engine at line 215 | Moon's title and first room (1 103 polygons a frame) against melonDS's pictures; the memories at frame 464 unchanged |
| `runtime/render_gl.cpp`, `gl.h` | the rendering engine on OpenGL 4.5 at any scale: the texture memory read in the fragment shader (seven formats, wrap modes, colour 0), the DS's colour modes in integers, interpolation at the pixel's corner and texture coordinates in 1/16 texel, translucency, the alpha test, wireframe, fog | the title within 496 of 38 400 pixels of melonDS's |
| `runtime/display.cpp`, `display.h`, `png.cpp`, `main.cpp` | the window (SDL3): the compositor on the GPU, the pace by the clock with the vertical sync, keyboard and mouse as the DS's buttons and stylus, F12 pictures; headless pictures through a hidden window; `ndsrun --window --scale --shots --shot-every`; PNG files | the route played in the window in real time (3 660 frames in 62.2 s on a 120 Hz display); pictures at the DS's size and at the window's |
| `runtime/video.cpp`, `machine.cpp` | VRAM's areas exposed to the engines (the extended palettes mapped: banks E-I); the machine run a frame at a time (`nds_boot`, `nds_run_frame`, `nds_finish`); `io9.bin` with the memories | the self-test unchanged (81 555 vectors, no difference) |

## Session 6

| Module | What | Checked by |
|---|---|---|
| `runtime/sound.cpp` | the sound unit: 16 channels (PCM8, PCM16, IMA-ADPCM with its loop state, PSG on 8-13, noise on 14-15), the start delay, the FIFO's read-ahead, loops and one-shot ends with the busy bit; two capture units; the mixer in the hardware's integers (volume and divider, panning, SOUNDCNT's mixer outputs, the master volume, the bias, POWCNT2's speakers); run in virtual time after every quantum and at each register access; `sound.txt` (the channels' places) with the memories | Moon's music, effects and movie sound (the movie's stream, refilled right behind the play position: no sample read stale or overwritten before it played, counted over the movie's first 990 frames); at five frames with no input the same channels with the same registers as melonDS's savestates, every place in the samples apart by the same 87 frames (the cartridge's time); ADPCM, PSG, noise and capture not used by Moon |
| `runtime/audio.cpp`, `main.cpp` | the sound to an SDL3 audio stream (resampled to the device's rate, the queue held near three frames by the playback ratio, at most 0.5%), WAV files; `ndsrun --mute`, `--wav` | 2 500 frames in the window on a 44.1 kHz device: the queue never dry, never cut |
| `runtime/bios.cpp` | the ARM7's sine table times 32 767; the volume table out of 128 with 128 kept as 127 and 127 as 126 | all 64, 768 and 724 values against the BIOS's tables (DeSmuME's copy) |
| `runtime/mmio.cpp`, `machine.cpp` | POWCNT2 = 1 at the boot (the speakers on, as melonDS's boot and the real one leave it); `io7.bin` with the memories | the memories at frame 464 unchanged (74 bytes); the self-test unchanged (81 555 vectors) |
| `melonds` | the "SPU." section: the unit's registers and each channel's place; `--info` lists a state's running channels, `--compare` both units' channels side by side | Moon's states (registers that read back what the game wrote: format, volume, pan, source, timer, loop, length) |

These modules are checked on Moon only: the user's other two cartridges
have not been run on the runtime (it loads no overlays yet, and one has
366; discovery does not know the other's Thumb switches).
