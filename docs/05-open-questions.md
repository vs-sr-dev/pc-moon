# Open questions

What is not known yet, roughly in the order the port will need it.

## The code

* **How much is ARM and how much Thumb**, and where the switch tables
  are: CodeWarrior's forms (`add pc, pc, rX, lsl #2` followed by a table
  of branches, `ldr pc, [pc, rX, lsl #2]` with a table of addresses, and
  Thumb's computed `add pc`/`bx` sequences) must all be recognised by
  discovery.
* **The main loop and its pacing.** The game runs at 30 frames a second
  (`06-attack-plan.md`): does it wait for two VBlanks every frame, and
  does its logic step per frame or by the VBlanks elapsed? The answer
  decides how 60 fps is reached.
* **How geometry reaches the GPU**: packed command lists sent to GXFIFO
  by DMA (the geometry FIFO start mode), lists written by the CPU, or
  the command ports one by one. And whether the scenes and models hold
  ready display lists (`02-data-formats.md`).
* **What the ARM9 reads back from the 3D engine**: BOX_TEST for
  culling, POS_TEST/VEC_TEST, the clip matrix, RAM_COUNT, the rendered
  line count. Anything it reads must come out of the port's geometry
  engine exactly.
* **Where the touch screen's samples go**: the stylus's motion turns the
  camera; following it leads to the camera's yaw and pitch, the hooks for
  mouselook.
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
