# Sessions

## Session 1 (2026-10-07) — feasibility, the cartridge, the oracle, the plan

* **The cartridge** (`01-cartridge-layout.md`): the European release,
  game code COOP, NitroSDK 4.2, its secure area decrypted. One resident
  ARM9 program of 1.32 MiB at 0x02000000, stored plain, **no overlays**
  on either CPU; two small autoloads (ITCM, DTCM). The ARM7 is the
  SDK's standard component, byte-identical in six places. 2 593 files in
  7 directories, every FAT entry named; five language archives
  (`en.srl`...) that are NitroROM images of their own, mounted by the
  game as `lng:`.
* **The formats at a glance** (`02-data-formats.md`): textures in the
  GPU's own format (a `TEXIMAGE_PARAM` word, texels, palette: checked on
  all 630), materials as raw register values, scenes and collisions in
  the BIOS's LZ77 (all 503 decoded), 48 Mobiclip movies (38% of the
  cartridge), all music sequenced in one SDAT (43 sequences, 67
  effects, no streams), the game's parameters in plain INI files
  (`DrawDistance = 49`, `EnableAllEpisodes`, `SkipIntro`, the buggy's
  physics, each weapon and each enemy per difficulty).
* **The code** (`03-executables.md`): the crt0 read (CP15, TCMs,
  stacks, autoloads, the SDK's IRQ handler in ITCM, `main` at
  0x02000C00); the code is almost all ARM (1 515 of 1 518 functions
  reached in a first descent); the hardware each CPU touches; the ARM7
  carries the wireless driver and serves the touch screen, the sound and
  the backup memory.
* **The oracle**: melonDS, a copy in `D:\Tools\melonDS-oracle` with its
  own settings, driven by `tools/oracle.py`: launched, pressed through
  the keyboard and the mouse, photographed, and read through its
  savestates (main RAM, ITCM, DTCM located in them). Its GDB stub drops
  the connection on this build. The scripted route reaches the first
  room in under 50 seconds.
* **The frame rate**: 30 frames a second, measured from three
  savestates (eight game counters +60 per 120 VBlanks). *Wrong, found in
  session 2: the tutorial's modal box was open; the game runs at 60 in
  play.*
* **The plan** (`06-attack-plan.md`): static recompilation of both
  CPUs (the ARM7 as a coroutine, its recompiled module reusable by every
  game with the same component), the hardware cut at its registers, the
  3D's geometry engine in software and its rendering on the PC's GPU at
  any resolution, the mouse first as the stylus then as the camera, the
  camera at the display's rate before the whole game at 60.
* **ndskit begun** (`10-ndskit.md`), as a subdirectory to be split out:
  `rom`, `hw`, `lz`, `sdat`, `arm` (equal to capstone on every ARMv5TE
  encoding tested). `rom`'s overlays and backward LZ checked on two
  other cartridges of the user's, which found two bugs.

## Session 2 (2026-10-07) — the code map, the frame rate corrected

* **Function discovery in ndskit** (`recomp.discover`, `10-ndskit.md`):
  the programs read where they run (the ARM7 mostly in WRAM and at
  0x027E0000, its ModuleParams found by shape), ARM and Thumb, switches,
  veneers, hand-written dispatch. Moon's ARM9: 5 395 functions, 303 106
  instructions, 0 conflicts; 99.6% of Ghidra's functions covered and 749
  more. Its ARM7: 925, 535 of Ghidra's 536. Checked on two other
  cartridges, one of which taught two rules.
* **The frame rate is 60 in play** (`03-executables.md`): session 1's
  30 was measured with the tutorial's modal box open. The user found the
  claim online that the engine runs at 60 and asked; three measurements
  of the loop counter (box, menu, play) and the play frame's single
  `OS_WaitVBlankIntr` settled it.
* **The geometry path**: display lists by DMA to GXFIFO from an ITCM
  routine, called by the scene renderer (also in ITCM) and the mesh
  drawers; matrices through the ports; only GXSTAT read back.
* **The camera**: the view matrix at 0x021512E0, found from savestates
  around stylus drags; no angle variable behind it.
* The oracle learned `drag:` and `frames:`/`framesv:` (melonDS's frame
  step proved unreliable for counting: the VBlank count does not advance
  once per step).

## Session 3 (2026-10-07) — the recompiler

* **An ARM interpreter in ndskit** (`armemu`): both CPUs, ARM and Thumb,
  the modes and their banked registers. Checked against Unicorn's ARM946
  on 25 483 random instructions and 1 960 transfers (no difference
  outside unaligned accesses, which the DS's CPUs rotate or align and
  QEMU does not) and on the SDK's divisions with known answers.
* **Discovery learned what the recompiler needed** (`10-ndskit.md`):
  Mobiclip's hand-written jumps (constants in two steps, tables of
  offsets through registers, local subroutines through lr), the SDK's
  unrolled division, switch bounds further back, Thumb's `bx pc`, empty
  callbacks; 17 false functions in a data table are gone (no function
  opens with a condition), and a rule that could skip code at a join was
  corrected. Moon: ARM9 5 413 functions, ARM7 933, 0 conflicts on three
  cartridges.
* **The recompiler** (`09-recompiler.md`): one C++ function per entry,
  one module per program; flags stored only where some path reads them;
  the PC as a constant; calls through registers dispatched with the mode
  in bit 0; switches as `switch`. Both programs compile and link (31 MB
  of C++, 42 seconds with clang).
* **The self-test**: the instruction test of each CPU and 1 512 of the
  game's own functions, 81 555 vectors recorded with the interpreter and
  replayed on the recompiled code: no difference.
* **The runtime's first lines** (`ndskit/runtime/`): the CPU context,
  the memories the CPUs reach directly, the modes, the dispatch, the
  self-test harness.

## Session 4 (2026-10-07) — the runtime core

* **The machine in ndskit** (`11-runtime.md`): both CPUs in quanta of
  virtual time, each of the SDK's threads on its own coroutine (the
  context switches of `OS_LoadContext` and of the IRQ handler followed
  to the right one), interrupts as the BIOS takes them, the SWIs,
  melonDS's direct boot, the I/O of both CPUs with VRAM's banks, timers,
  DMA, IPC, the maths unit, the cartridge's reads and its EEPROM, SPI
  (power, firmware, touch), the RTC, the sound registers. `ndsrun` runs
  the game headless, deterministically.
* **Moon runs**: it boots, plays its movies (Mobiclip's decoder copied
  to the ITCM, recompiled where it runs: `--copy`), reads its save, and
  with eleven presses goes through its menus into the first room.
* **Against melonDS** (`ndskit.melonds`): at the same frame of the SDK's
  VBlank count, after 464 frames with the same save, 74 bytes of main RAM differ (the RTC's
  date, counters that follow time), the ITCM and the shared WRAM not at
  all; after the route, the same room with the camera turned the same
  way.
* **What running taught** the kit: byte writes to a device's register,
  the BIOS's wait giving the other CPU time, the backup memory's chip
  select, the ARM7's BIOS sound tables; and discovery five more forms
  (vtables of tiny methods, `this` thunks, interrupt stubs, a switch
  bounded by its first compare, conditional code addresses and holes in
  offset tables): Moon's ARM9 6 580 functions, all of Ghidra's covered,
  0 conflicts on the three cartridges.
* **Seeing inside**: a call trace (`ARM_ENTER`), breaks, a store watch
  (it found the save check's failure), where each CPU polls, its stack.
* Speed, headless: about 210 times the DS.
