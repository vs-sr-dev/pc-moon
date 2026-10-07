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

## The code

**Almost all ARM, very little Thumb.** A rough recursive descent from
the entry and `main` (following direct calls and the code pointers in
the literal pools; session 1's exploration, not yet ndskit's discovery)
reaches 1 518 functions: 1 515 in ARM, 3 in Thumb, 65 754
instructions. That is a fraction of the program (most functions are
reached through tables of pointers the descent does not read yet), but
the proportion is telling: CodeWarrior compiled this game for ARM.
For the recompiler, ARM is the simpler half (no BL pairs, one
instruction width), and Thumb must still be handled where the SDK or a
library uses it.

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

Measured in melonDS (`06-attack-plan.md`): in the first room, standing
still, eight counters of the game advance by exactly 60 every 120
VBlanks, in two intervals of 2 seconds: 30 frames a second.

## The ARM7

The SDK's standard component (crc32 0x1B16DBE2, the same in the five
language archives), all ARM in the reached code (135 functions from the
entry). Its crt0 starts as the ARM9's (`IME = 0`). The hardware it
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
