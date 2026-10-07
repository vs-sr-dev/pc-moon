# Next session: the code map (phase 2)

Goal: know every function of both programs and what the game does each
frame, so the recompiler of phase 3 has its input.

1. **Function discovery in ndskit** (`ndskit/recomp/discover.py`, on the
   model of saturnkit's): recursive descent over ARM and Thumb with the
   mode carried through `bx`/`blx` and odd addresses; literal pools as
   data; constant propagation for calls through registers; CodeWarrior's
   switch forms (`add pc, pc, rX, lsl #2` + branch table, `ldr pc, [pc,
   rX, lsl #2]` + address table, Thumb's); code pointers in data
   (function tables, C++ vtables if any); the ITCM block at its run
   address. Done when: no function's descent meets data or an undefined
   instruction, every switch target is code, and Ghidra's auto-analysis
   of the ARM9 (headless, ARM:LE:32:v5t) finds nothing discovery misses
   except what nothing references.
2. **The SDK named by signature**: OS (interrupts, threads, alarms,
   arena/heap), FS/CARD, GX/G3/G2, SND, TP, PM, RTC, MI (DMA, copies),
   FX; at least the entry points the port will hook or watch:
   `OS_WaitVBlankIntr`, the IRQ table, `FS_ReadFile`, the touch sampling,
   the geometry FIFO's DMA. ndskit gets a signature format the next game
   reuses.
3. **The frame loop**: from `main` to the per-frame loop; how it waits
   (VBlank interrupts, `SVC_WaitVBlankIntr`), how many VBlanks a frame,
   whether the logic steps per frame or by elapsed time; checked live
   with the oracle (counters in savestates, as in session 1).
4. **The geometry path**: how the scenes and models reach the GPU
   (display lists by DMA to GXFIFO, the ports, or both), what the game
   reads back from the 3D engine (BOX_TEST, POS_TEST, results).
5. **The camera**: from the touch screen's samples (the TP library) to
   the camera's yaw and pitch: the addresses of the angles, found in the
   code and confirmed in savestates taken before and after a drag.
6. **The ARM7**: its PXI command handlers, so the list of hardware it
   needs is complete; whether its crc32 is in the other cartridges on
   this machine.
7. **An ARM interpreter in ndskit** (`armemu`), if time allows: the
   recompiler's oracle, as `sh2emu` was saturnkit's.

Before starting: `python -m ndskit.rom ... --extract build/extract --nested`
if `build/` is empty; the oracle needs PIL (`C:\Python314\python.exe`).
