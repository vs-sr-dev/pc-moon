# The executables

Session 1's look at the two programs, with `ndskit.arm` (ARMv5TE/Thumb
decoder, equal to capstone on every v5TE encoding tested,
`10-ndskit.md`).

```sh
ROM="Moon (Europe) (En,Fr,De,Es,It).nds"
A9="--offset 4000 --size 152078 --base 02000000"
A7="--offset 156200 --size 27080 --base 02380000 --arm7"
python -m ndskit.arm "$ROM" $A9 --at 02000800 --count 80      # crt0
python -m ndskit.arm "$ROM" $A9 --at 02000C00 --count 60      # main
python -m ndskit.arm "$ROM" $A9 --refs 04000000:04002000      # hardware registers by address
python -m ndskit.arm "$ROM" $A7 --refs 04000000:04900000
```

## Memory

| Range | What |
|---|---|
| 0x01FF8000-0x01FF9A60 | ITCM (the SDK's mirror of address 0): 0x1A60 bytes of autoloaded code, the IRQ handler among them |
| 0x02000000-0x021505A0 | the ARM9 program: the secure area's filler (0x800), crt0 at 0x02000800, ModuleParams at 0x02000B9C, `main` at 0x02000C00, code, then data |
| 0x021505A0-0x0215A460 | static BSS (over the autoload sources, dead after boot) |
| 0x0215A460-... | the heap (the game's own counters were found at 0x022F0240-0x022F5D48, `06-attack-plan.md`) |
| 0x02380000-0x023A7080 | where the ARM7 program loads, in main RAM |
| 0x027E0000-0x027E4000 | DTCM: 0x60 bytes of autoloaded data, the stacks |
| 0x027FFC00-0x02800000 | the SDK's shared area (0x027FFC3C: the VBlank count the ARM7 keeps; 0x027FFF9C: zeroed by crt0) |

## The ARM9's boot (crt0, 0x02000800)

Read from the disassembly (an inference is marked as one):

1. Interrupts off (`IME = 0`), then a wait for VCOUNT to read 0.
2. CP15 (0x02000AB0): protection unit, caches and TCMs off; caches
   invalidated; eight protection regions (I/O, main RAM 8 MB, 0x027E0000
   128 KB, GBA slot, DTCM 16 KB, ITCM, BIOS, 0x027FF000 4 KB); ITCM at 0
   (`c9,c1,1` = 0x20), DTCM at 0x027E0000 (`c9,c1,0` = 0x027E000A, 16 KB);
   cacheability and write buffer for main RAM and the BIOS; everything
   switched on.
3. Stacks in DTCM: SVC at DTCM+0x3FC0, IRQ just below it, System mode
   0x800 below that (inference: an IRQ stack of 0x800 bytes).
4. DTCM and the palette cleared; OAM filled with 0x200 (inference: every
   sprite hidden).
5. The SDK's backward-LZ decompressor (0x02000970) on
   ModuleParams' `compressed_static_end`: here 0, so it returns at once.
6. The autoload loop (0x02000A1C): the table at ModuleParams'
   `autoload_list`, each block copied, its BSS zeroed, the cache lines
   maintained.
7. The static BSS cleared.
8. The IRQ vector: 0x01FF969C written at DTCM+0x3FFC, where the BIOS
   looks for the user's IRQ handler. At 0x01FF969C, in ITCM, is the SDK's
   handler: it returns at once if IME is 0, else takes `IE & IF` and
   dispatches.
9. Three calls (0x02126818, 0x02108920, 0x02127D3C; inference: the SDK's
   initialisation and the static constructors), then `bx` to `main` at
   0x02000C00 with lr = 0xFFFF0000.

`main` starts by setting both screens' master brightness (MASTER_BRIGHT
and MASTER_BRIGHT_B, value 0x10) and calling into the SDK.

## The code map (session 2)

```sh
python -m ndskit.recomp.discover "$ROM" --cpu 9 --report --out build/disc9.tsv
python -m ndskit.recomp.discover "$ROM" --cpu 7 --out build/disc7.tsv
```

| | Functions | ARM / Thumb | Instructions | Switches | Through registers, unresolved | Conflicts |
|---|---|---|---|---|---|---|
| ARM9 (main + ITCM) | 5 413 | 5 410 / 3 | 305 574 | 147 (1 834 targets) | 2 386 | 0 |
| ARM7 (where its autoloads run) | 933 | 924 / 9 | 37 664 | 40 (712 targets) | 42 | 0 |

(Session 3's figures. Session 2 had 5 395 and 925 functions: 17 of the
ARM9's were a data area read as code, and discovery has since learned
the forms below; `10-ndskit.md`.) Of the transfers through registers left
unresolved, all but five are calls (`blx rN`, dispatched at run time);
the five jumps are read in `09-recompiler.md`.

**Almost all ARM.** The three Thumb functions of the ARM9 are the SDK's
BIOS-call wrappers, which sit in the secure area's first 0x800 bytes
(0x020004AA `SVC_WaitByLoop`, `swi 3`; 0x020006CE `SVC_CpuSet`,
`swi 11`). CodeWarrior compiled the game for ARM.

**Against Ghidra 12's auto-analysis** (`ndskit/ghidra/ExportFuncs.java`;
build/ghidra): of its 4 680 functions in the ARM9's segments, 4 648 are
entries here and 15 lie inside another function's code (session 2: 4 646
and 17); 17 are not
reached, 15 of them routines of Mobiclip's hand-written decoder
(0x0213042C-0x02131590) that are reached through tables of offsets whose
base a register carries in from elsewhere (`ldr r5, [r6, r5, lsl #2];
mov lr, r8; add pc, r5, r6`). 765 functions are found that Ghidra has
not. The ARM7, compared at its run addresses: 535 of Ghidra's 536, 390
more.

**The layout.** The code runs from 0x02000800 to 0x021369A8; the 103 KB
after it to the end of the program are data (strings, tables,
initialised variables). Inside the code area 49 KB stay unclassified
(4%): tables inside functions and the unreached decoder routines.

**The forms met**: CodeWarrior's switch (`cmp rI, #N; addls pc, pc,
rI, lsl #2; b default;` N + 1 branches), also with the bound found
further back (`cmp r0, #12; str r0, [r1]; addls ...`) and for a range of
cases (`cmp r3, #0x47; bgt ...; subs r0, r3, #0x41; addpl pc, pc, r0,
lsl #2`); its long-branch veneers (`ldr r12, [pc]; bx r12`); calls
through registers (`blx rN`, 2 378 left to run time: virtual methods
and callbacks); the SDK's divisions (0x02126428 signed, 0x0212663C
unsigned), which jump into their unrolled loop (`add r2, r2, r2, lsl
#1; add pc, pc, r2, lsl #2`); Mobiclip's hand-written code: computed
calls (`sub r3, pc, #k; add lr, pc, #4; ldr r8, [r3, r7, lsl #2]; add
pc, r8, r3`), targets built in two steps (`add r4, pc, #0x38; add r4,
r4, #0x2600; movle pc, r4`), tables of offsets followed through
registers (`add r6, pc, #k; ldr r12, [r6, r12, lsl #2]; add r6, r6,
r12; ...; mov pc, r6`), tables indexed by bytes with their targets before
them (`sub r5, pc, #0x18; ldr r6, [r5, r8]; add pc, r5, r6`), local
subroutines entered with lr set (`add lr, pc, #4; beq ...; bne ...`).

## The frame loop

* `main` (0x02000C00) calls the game's state machine 0x0200625C (2 152
  instructions), which holds the movie loops (each waits for a VBlank,
  then steps Mobiclip's player, a C++ object reached through thin
  wrappers at 0x0207A234-0x0207A3F8) and the play loop.
* `OS_WaitVBlankIntr` is 0x0211860C (`SVC_WaitByLoop(1)`, then
  `OS_WaitIrq(TRUE, VBlank)`); the SDK's threads wait in it, and the idle
  thread halts the ARM9 with CP15's wait-for-interrupt (0x021188DC). There
  is no `swi 5` in the program.
* The play frame (around 0x020081B0) writes SWAP_BUFFERS = 3 (manual
  translucent sort, W-buffering), finishes the frame's work, and calls
  `OS_WaitVBlankIntr` once (0x02008214), unless flags in 0x021505B0 say
  otherwise: 60 frames a second when the work fits in a VBlank period.

## The geometry path

* **Display lists by DMA.** 0x01FF99B8, in ITCM, sends a list to GXFIFO
  by DMA in blocks of 0x1D8 words (control 0x84400000: 32-bit, source
  incrementing, destination fixed, started at once), waiting for the
  channel between blocks: the SDK's `MI_SendGXCommand` form. Its
  callers: the scene renderer 0x01FF8000 (405 instructions, in ITCM,
  called by the state machine), the mesh drawer 0x020607AC (called by
  15 object routines), 0x0209B7F0 (8 more), 0x0206D050, 0x0207768C,
  0x020BE1E8 and 0x020BE24C. The scenes and models therefore hold packed
  command lists (inference: the lists are the data of `.scn` and `.msh`).
* **Matrices through the ports**: MTX_MODE, MTX_PUSH, MTX_POP,
  MTX_STORE and the rest written directly (the scene renderer and the
  mesh code), as well as the SDK's small G3 wrappers at
  0x021147FC-0x02114A00 that write GXFIFO.
* **What the game reads back**: GXSTAT only (7 places: busy, matrix
  stack); no literal of BOX_TEST, POS_TEST, VEC_TEST or the result
  registers. The port's geometry engine has to answer GXSTAT; the tests
  are not used (inference: unless an address is formed from a base).

## The camera

Savestates around stylus drags in the first room (`tools/oracle.py`,
`drag:`) show the **view matrix at 0x021512E0**: a flag word, then a 4x3
matrix in 20.12 fixed point (the 3x3 rotation at 0x021512E4-0x02151304,
the translation at 0x02151308-0x02151310), with a copy at 0x0216A540.
Two drags to the right turned it by 66 and 59 degrees about the vertical
axis; a drag down tilted it by 20 degrees. No 16- or 32-bit word in main
RAM follows the yaw in proportion: the orientation seems to be kept as
the matrix itself, rotated each frame (inference). 0x02061108, a model
drawer, reads it; its writer is still to be found, the first job for a
store watch when the runtime runs.

**The hardware the ARM9 touches** (addresses loaded from literal pools,
in the reached code): the division and square-root units (DIVCNT 39,
DIV_RESULT 30, SQRT_RESULT 25, SQRTCNT 22, DIV_NUMER 19), the VRAM bank
controls (VRAMCNT_A-I, 48 in all), the 3D engine (MTX_MODE 12, MTX_PUSH
9, MTX_POP 9, DISP3DCNT 7, GXSTAT 7, SWAP_BUFFERS 6, GXFIFO 6,
TEXIMAGE_PARAM 4, fog, light, viewport, clear colour, POLYGON_ATTR),
the 2D engines (DISPCNT_B 14, MASTER_BRIGHT 11, MASTER_BRIGHT_B 10, BG
controls), interrupts (IME 10, IF), EXMEMCNT 10, POWCNT1 5, the IPC
FIFO, the card (ROMCTRL 4, CARD_DATA_RD 3), timers 0 and 1, KEYINPUT,
DMA. The game writes the geometry engine's ports directly (matrix
commands) as well as GXFIFO.

**Libraries.** The only SDK tag in the program is `[SDK+NINTENDO:BACKUP]`
(the backup-memory library); the other NitroSDK libraries carry none.
Actimagine's Mobiclip SDK V1.0.3 is tagged. Which of the SDK's
libraries are linked is for phase 2 (signatures).

## The frame rate

**60 frames a second in play.** The game's frame (in the big state
function 0x0200625C that `main` calls) ends by writing SWAP_BUFFERS
(value 3) and calling `OS_WaitVBlankIntr` (0x0211860C: `SVC_WaitByLoop(1)`
then `OS_WaitIrq(1, VBlank)`) once: a loop that aims at 60 and drops to
30 when a frame's work outlasts one VBlank period.

Measured in melonDS from savestates taken 2 seconds apart: the word at
0x022F0240 (inference: the game loop's iteration count) advances by
120 every 120 VBlanks in play (the first room, the HUD up, standing
still) and in the options menu, and by 60 every 120 VBlanks while the
tutorial's modal box is open. Session 1 measured only the last case and
wrote "30 frames a second"; the claim found online that the engine runs
at 60 (Renegade Kid's engine from Dementium) is right for play. Heavier
rooms may still drop below 60 on the DS: to be measured as the port gets
there.

## The ARM7

The SDK's standard component (crc32 0x1B16DBE2, the same in the five
language archives), all ARM in the reached code (135 functions from the
entry). It runs from three places (session 3): its crt0 (488 bytes) at
0x02380000, 96 376 bytes autoloaded to 0x027E0000 (main RAM, on the
ARM7's side) and 62 984 bytes autoloaded to 0x037F8000, which run from
the shared WRAM (all of it the ARM7's) on into the ARM7's own WRAM at
0x03800000. Its crt0 starts as the ARM9's (`IME = 0`). The hardware it
touches, by the addresses in its literal pools: **the wireless hardware**
(218: this component carries the wireless driver, though Moon has no
multiplayer), SPI (SPICNT 43, SPIDATA 35: the touch screen, the
firmware, the power manager), VCOUNT, the sound (SOUNDCNT 7 as the base
of the channel registers, the capture units), AUXSPI (10: the backup
memory is served by the ARM7), timers 0, 1 and 3, POWCNT2, EXTKEYIN
(X, Y, the pen-down bit, the hinge), RCNT, the IPC registers and the
card. The RTC's register (0x04000138) is not loaded by its own address
in the reached code (inference: it is reached from a nearby base).

For the port: recompiling it means emulating SPI (touch, firmware, power),
the RTC, AUXSPI over a save file, the sound channels and the capture
units, and leaving the wireless hardware present but silent.
