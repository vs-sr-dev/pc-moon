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
  savestates (eight game counters +60 per 120 VBlanks).
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
