# Open questions

What is not known yet, roughly in the order the port will need it.

## The runtime (session 4)

* **Time.** A safe point costs a fixed number of ticks; the DS's cycles
  differ by instruction and by memory. A few counters that follow time
  (not frames) end up apart from melonDS's after 464 frames
  (`11-runtime.md`). Whether any of the game's behaviour depends on them
  (a random seed, a movie's pacing) is to be seen; a finer cost (per
  block, from the instructions) is the remedy if so.
* ~~**The BIOS's sound tables**~~ (session 6): every value checked
  against the BIOS's own tables; the sine and the volume rounded
  differently at first (`13-sound.md`).
* **The cartridge's time** (session 6). A command of the cartridge
  answers at once; melonDS takes the card's time. Early in the boot
  (frames 520-639 with no input) the game's frame counters stand still
  in melonDS for some 85 frames and not in the runtime, and from there
  every sound plays 87 frames earlier than melonDS's, with the same
  registers (`13-sound.md`). A file being read is the likely reason (an
  inference). On a PC a load that ends at once is welcome; it matters
  only if a sound or a movie is timed against a load.
* **The firmware's wireless block** (0x2A-0x163) is left empty; melonDS
  fills it with its defaults. Moon has no multiplayer: harmless unless
  the wireless driver checks it at boot (it did not stop a run).
* **The runtime's BIOS frames**: melonDS's BIOS (FreeBIOS) pushes a SWI
  frame on the SVC stack, the runtime does not: 16 bytes of stack
  differ.
* **Three of the jumps left to run time were not met** (`11-runtime.md`):
  the C++ exception path (0x021283AC: an exception thrown would need an
  unwind to a catch block up the host stack), the ARM9's `bx r12` at
  0x02117DF4, the ARM7's thread start at 0x038072C0.

## The code

* **The main loop's structure.** One VBlank wait per frame, 60 in play
  (session 2); which rooms drop below it on the DS, and whether the logic
  steps per frame or by time (it matters only for rates above 60).
* **The display lists' layout in `.scn` and `.msh`** (session 2: they
  reach GXFIFO by DMA from an ITCM routine; `03-executables.md`).
* **Whether any test or result register is read through a base
  address** (session 2 found only GXSTAT by its own address).
* **The camera's writer** (session 2: the view matrix is at 0x021512E0,
  kept as a matrix, no angle found): where the stylus's motion turns it,
  the hook for mouselook. The runtime's store watch can now name it (a
  run along the oracle's route stands in the first room at frame 3 642;
  a drag in the input script is the next step).
* **The interrupt handlers**: the ARM9 enables VBlank, timers 0 and 1
  and the IPC FIFO's receive (the card's completion is raised but polled);
  the ARM7 VBlank, timers 0 and 1, the RTC, the IPC FIFO and the wireless
  (their IE in the runtime's runs). What each does is still to read.
* **Which SDK libraries are linked** and which version of each: OS, FS,
  CARD, GX/G2/G3, SND, TP, RTC, PM, MI, FX; Mobiclip's own. Their
  functions are the same in every NitroSDK 4.2 game: named by signature
  once, named everywhere. Named so far, by reading: the thread switch,
  the interrupt masks, `OS_Terminate`, `OS_WaitVBlankIntr`, PXI's
  handshake (`03-executables.md`).
* **ARM9 threads 1 and 2** (0x0211F3E8, 0x02120190): inference, the card
  and file system's and another of the SDK's.
* **What `rsd.ini` and `sar.ini` configure.**

## The ARM7

* **Which SDK ARM7 component this is** (the SDK ships several, with or
  without wireless), and what it serves: sound, touch, RTC, power,
  microphone, backup memory, wireless. It runs eight threads
  (`11-runtime.md`); reading its PXI command handlers tells which.
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
* The oracle presses by the wall clock, so a press lands on a frame that
  varies from run to run; frame-exact input (pausing and stepping, as
  `framesv:` does) would let the two runs be compared after the menus as
  closely as before them.
* The meaning of the other fields of melonDS's savestate sections (the
  CPU registers' order in `ARM9`/`ARM7`), when the port needs the
  registers at a moment and not only the memory.
