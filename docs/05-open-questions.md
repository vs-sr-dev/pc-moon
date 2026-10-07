# Open questions

What is not known yet, roughly in the order the port will need it.

## The code

* **How much is ARM and how much Thumb**, and where the switch tables
  are: CodeWarrior's forms (`add pc, pc, rX, lsl #2` followed by a table
  of branches, `ldr pc, [pc, rX, lsl #2]` with a table of addresses, and
  Thumb's computed `add pc`/`bx` sequences) must all be recognised by
  discovery.
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
