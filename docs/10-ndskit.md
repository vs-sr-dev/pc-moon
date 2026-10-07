# What this port gave ndskit

ndskit is born with this port, in `ndskit/`. It will be split out with
its history (`git subtree split --prefix ndskit`) into its own
repository, `D:\Homebrew6\ndskit`, and come back here as a submodule at
the same path, as wiikit did from pc-victorious. Until then a commit
that changes `ndskit/` changes only `ndskit/`, so the split history reads
as the kit's.

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
