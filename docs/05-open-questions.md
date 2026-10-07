# Open questions

What is not known yet, roughly in the order the port will need it.

## The code

* **Five jumps through registers** that the recompiler leaves to run
  time (`09-recompiler.md`): a context restored and jumped into at
  0x021283AC (a thread switch or a longjmp?), a thread's start on the
  ARM7 at 0x038072C0. The runtime has to give each its meaning.
* **The 17 functions Ghidra finds and discovery does not reach**, 15 of
  them Mobiclip decoder routines dispatched through a table whose base
  comes in a register: when the movies play, a call to one of them stops
  the runtime (`arm_call_unknown`) and names it.
* **The main loop's structure.** One VBlank wait per frame, 60 in play
  (session 2); which rooms drop below it on the DS, and whether the logic
  steps per frame or by time (it matters only for rates above 60).
* **The display lists' layout in `.scn` and `.msh`** (session 2: they
  reach GXFIFO by DMA from an ITCM routine; `03-executables.md`).
* **Whether any test or result register is read through a base
  address** (session 2 found only GXSTAT by its own address).
* **The camera's writer** (session 2: the view matrix is at 0x021512E0,
  kept as a matrix, no angle found): where the stylus's motion turns it,
  the hook for mouselook. A store watch in the runtime will name it.
* **The interrupt handlers**: which interrupts the game takes (VBlank,
  HBlank, timers, IPC, the geometry FIFO, the card) and what each does.
* **Which SDK libraries are linked** and which version of each: OS, FS,
  CARD, GX/G2/G3, SND, TP, RTC, PM, MI, FX; Mobiclip's own. Their
  functions are the same in every NitroSDK 4.2 game: named by signature
  once, named everywhere.
* **What `rsd.ini` and `sar.ini` configure.**

## The ARM7

* **Which SDK ARM7 component this is** (the SDK ships several, with or
  without wireless), and what it serves: sound, touch, RTC, power,
  microphone, backup memory, wireless. Recompiling it means emulating
  the ARM7's hardware it touches; reading its PXI command handlers tells
  which.
* **Whether its crc32 (0x1B16DBE2) appears in other games**: if many
  NitroSDK 4.2 games ship this same binary, ndskit's recompiled ARM7 is
  shared by all of them.

## The formats

* The structure of `.scn`, `.col`, `.msh` and `.anm`; `parammap*.bin`;
  the markers.
* Whether `DrawDistance` is the only bound on the view distance.

## The oracle

* melonDS's GDB stub drops the connection at the first packet on this
  build (Windows, 2025-11). Savestates serve; a working stub (another
  build) would add breakpoints and live reads.
* The meaning of the other fields of melonDS's savestate sections (the
  CPU registers' order in `ARM9`/`ARM7`), when the port needs the
  registers at a moment and not only the memory.
