# The runtime

Phase 4 (session 4): ndskit's runtime runs both of Moon's recompiled
programs as the DS would, headless: the boot, the movies, the files read
from the cartridge, the save, the menus and, with eleven presses, the
first room. Its memories are compared with melonDS's savestates at the
same frame.

```sh
ROM="Moon (Europe) (En,Fr,De,Es,It).nds"
export PATH=/c/msys64/mingw64/bin:$PATH
python -m ndskit.recomp "$ROM" --out build/recomp --optest --copy 9:01FF9A60=0212FED4:659C
cmake -S build/recomp -B build/recomp/b -G Ninja -DCMAKE_CXX_COMPILER=clang++
ninja -C build/recomp/b
mkdir -p build/run && cp "build/oracle/Moon (Europe) (En,Fr,De,Es,It).sav" build/run/   # the save melonDS had
build/recomp/b/ndsrun "$ROM" --out build/run --vblanks 466                        # 464 frames of the SDK's count
python -m ndskit.melonds build/oracle/first.ml1 --compare build/run                 # against melonDS at the same frame

# the oracle's route into the first room (tools/oracle.py's times x 60, less 18 frames of melonDS's start)
IN="1182:START,1542:tap:128:96,1902:START,2082:START,2262:START,2442:START,2622:A,2862:tap:128:120,3042:tap:128:120,3222:tap:128:120,3402:UP"
build/recomp/b/ndsrun "$ROM" --out build/route --vblanks 3644 --input "$IN"
python -m ndskit.melonds build/oracle/cam/t61.ml1 --compare build/route
```

`--copy` is the one thing Moon asks of the recompiler's command line (it
is the address of a block of its own code, not cartridge content):
Mobiclip copies its hand-written decoder, 0x659C bytes from 0x0212FED4,
into the ITCM at 0x01FF9A60 when the first movie starts, and runs it
there. The runtime found it by itself: a call to an address no module
has, whose bytes it found in the program's image, and it printed the
option to give.

A run writes into `--out` the memories (`main.bin`, `itcm.bin`,
`dtcm.bin`, `swram.bin`, `wram7.bin`), the CPUs' registers (`cpus.txt`)
and the game's save (`<rom>.sav`, read back by the next run in the same
directory: a run from a new cartridge wants a new directory).

## The machine

| Part | How |
|---|---|
| Time | ticks of the ARM9's clock; a line is 4 260 (355 dots of 6 system cycles), a frame 263 lines. A safe point stands for a fixed number of ticks (16 on the ARM9, 24 on the ARM7). The machine runs in quanta of a quarter of a line or up to the next event: the ARM9 until its clock passes the quantum's end, then the ARM7, then the events due (HBlank, the line, timers). A halted CPU waits for IE & IF. A run is the same run every time |
| The two CPUs | each on its own coroutine (Windows fibers; ucontext elsewhere, not built yet), with its own clock; a wait in the BIOS (`SVC_WaitByLoop`) gives the other CPU its turn, which is how the SDK's PXI handshake (each CPU waiting for the other's echo in IPCSYNC) goes through |
| Threads | each of the SDK's threads on its own coroutine too: recompiled code nests its calls on the host stack, so a thread switched out keeps its frames until it is switched back in. The switches are the guest's: `OS_LoadContext`'s exception return and the IRQ handler's return with another thread's context in the BIOS's frame. The target names the thread: an interrupt taken at a safe point pushes a marker (0x0F000000 + 16 x the thread's number) as its return address; a context saved by `OS_SaveContext` is found by the sp the runtime noted when the save returned; an entry is a new thread. A thread switched back in at its save returns through the save's `bx lr`, and the save's caller (`OSi_RescheduleThread`, 0x02116B00) unwinds to the call's return address |
| Interrupts | IME, IE and IF on each CPU, taken at safe points, at a halt's end and after an `msr` that unmasks them: IRQ mode, r0-r3, r12 and the return address pushed on the IRQ stack, the handler at the DTCM's end (0x027E3FFC) or 0x0380FFFC called, the frame popped, CPSR = SPSR_irq |
| BIOS | melonDS's direct boot (the programs at their load addresses, the header at 0x027FFE00, the chip ID, the firmware's user settings at 0x027FFC80, both CPUs in system mode with the BIOS's stacks); the SWIs the game calls in C++ (WaitByLoop, IntrWait, VBlankIntrWait, Halt, Div, CpuSet, CpuFastSet, Sqrt, GetCRC16, IsDebugger, the LZ77 and RL decompressors, SoundBias, the ARM7's sine, pitch and volume tables); the Nintendo logo the SDK copies from the ARM9 BIOS (served from the cartridge's header, where it is the same) |
| Memory | main RAM, the TCMs (where CP15 puts them, on or off), the ARM7's WRAM and the shared WRAM as host arrays; the palettes, OAM and VRAM through its nine banks, mapped by VRAMCNT to the LCDC area, the 2D engines, the texture slots and the ARM7 in 16 KiB pages; the GBA slot empty |
| I/O | each CPU's registers as storage, the ones with an effect sent to their device: DISPSTAT and VCOUNT, the timers (counters worked out from the time, an event at each overflow, count-up), DMA (immediate, VBlank, HBlank, the card's, the geometry FIFO's), IPC (SYNC, both FIFOs, their interrupts), the maths unit (DIV and SQRT with melonDS's results), KEYINPUT, EXTKEYIN, HALTCNT, POWCNT, WRAMCNT |
| The cartridge | ROMCTRL runs a command at once: the main-data read 0xB7 over the .nds file, the chip ID 0xB8; its words at 0x04100010 for the CPU or the card's DMA, the card interrupt at the end. The backup memory on AUXSPI: Moon's is an EEPROM of 64 Kbit (2-byte addresses), kept in the save file |
| The ARM7's devices | SPI: the power manager's registers, the firmware (made up as melonDS makes it: user settings "melonDS", English; the MAC address 00:09:BF:11:22:33; reads, writes, status), the touch screen's controller (positions from the input script); the RTC (its serial protocol, a fixed date: 2009-04-20, Moon's European release); the sound registers, a one-shot channel busy until its samples would have played |
| Not yet | the 2D engines and the geometry engine (phase 5: GXFIFO takes every word, GXSTAT reads idle and empty), the mixer (phase 6) |

## Against melonDS

The SDK's VBlank count (0x027FFC3C, kept by the ARM7) gives the frame of
a savestate; the runtime runs to the same count.

| | No input, 464 frames (`first.ml1`), with melonDS's save | The oracle's route, 3 642 frames (`cam/t61.ml1`), from a new cartridge |
|---|---|---|
| Main RAM (4 MiB) | 74 bytes differ, in 15 places (from a new cartridge: 85) | 19 450 bytes (0.46%) |
| ITCM | the same | the same (the copied decoder included) |
| DTCM | 16 bytes (the BIOS's SWI frame on the SVC stack, which the runtime does not push) | 683 bytes (stacks) |
| Shared WRAM | the same | the same |
| ARM7 WRAM | 429 bytes | 788 bytes |

With no input the games stand at the same point: the heap's objects at
the same addresses, the same threads, the same files read. What differs:
the RTC's date (melonDS gives the host's: 2026-10-07; the runtime its
fixed one), a few counters that follow time rather than frames (the
runtime's cost per safe point is not the DS's cycles), the firmware's
wireless block (left empty here) and stack garbage. After the route both
are in the first room with the camera turned the same way (the view
matrix at 0x021512E0 has the same rotation); the player stands elsewhere,
since a press lands on a different frame than in melonDS, whose presses
are timed by the wall clock.

## What the boot taught

Each found by running, read in the code, then fixed in the kit:

* **Byte writes to a device's register** kept the other byte as the
  storage had it, not as the device: the SDK writes CARD_COMMAND a byte
  at a time, so every command but its last byte was lost; the ARM9 took
  the card for pulled out and sent the ARM7 the PXI message that stops
  it (tag 14, the card's).
* **The BIOS's wait gives the other CPU time**: the ARM7's half of the
  PXI handshake writes a value, waits with `SVC_WaitByLoop` and expects
  the ARM9's echo. A wait that only counted ticks read before the ARM9
  had run.
* **The backup memory's chip select** falls after a byte sent without
  the hold bit, not when AUXSPICNT is rewritten: the SDK clears the hold
  bit before the last byte. Until then RDSR read 0xFF and the game's
  first read of its save failed: Moon shows its error message from
  `gui.tbl` and calls `OS_Terminate` (0x0207B460, through 0x0200625C),
  found with the store watch on the status it sets (2 at 0x022AA568).
* **Discovery**, five forms it did not know (`recomp/discover.py`):
  - an interrupt table's stubs of three instructions (`ldr r12,
    =handler; mov r0, #n; bx r12`, the ARM7's DMA and timer handlers);
  - C++'s tiny virtual methods (`mov r0, #0x1a; bx lr`, an empty
    `bx lr`), in vtables, one after another; the table's mark now spreads
    within a pass, and an unclassified `bx lr` before one counts as a
    function's end. Moon's ARM9 went from 5 413 functions to 6 580, all
    4 680 of Ghidra's covered;
  - thunks that adjust `this` and branch into the method (`ldr r12, =-k;
    add r0, r0, r12; b method`), the method in a vtable too;
  - the static constructors' table (0x0213C0A0), empty ones included;
  - a switch `cmp r0, #0x20; bgt ...; cmp r0, #0; addge pc, pc, r0, lsl
    #2` whose bound is the first compare, not the second (it read one
    case and the game returned to the middle of the table);
  - Mobiclip's decoder: a call through `addhs r4, pc, #a; addlo r4, pc,
    #b; ...; bx r4`, and tables of offsets with holes (an offset of 0 for
    a code with no case).
* **Context saves** (`OS_SaveContext`, 0x02117214 and the ARM7's
  0x037FC64C) are found by their shape (an address of their own code
  stored to memory), and their callers' return addresses become landings
  (`recomp.emit`).
* **The ARM7's BIOS sound tables**: the sound driver asks for the volume
  table at frame 518; the runtime works the three tables (volume, pitch,
  sine) out from their definitions (an inference: the BIOS's rounding is
  to be checked in phase 6).

## Threads

| CPU | Thread | Entry | What (inference) |
|---|---|---|---|
| ARM9 | 0 | 0x02000800 | the launcher: crt0, `main`, the game |
| | 1 | 0x0211F3E8 | the SDK's card and file system |
| | 2 | 0x02120190 | |
| | 3 | 0x02117110 | the idle thread: CP15's wait for interrupt |
| ARM7 | 0 | 0x02380000 | the launcher, then the main loop (VBlank count) |
| | 1-7 | 0x037FF008, 0x038032B8, 0x027F60A8, 0x027E0898, 0x027E1CC0, 0x037F84E0, 0x03803C7C | the SDK's ARM7 component: PXI, sound, touch, RTC, power, card, wireless |

## Seeing inside a run

| Option | What |
|---|---|
| `--trace` | thread starts and switches, SWIs, VRAMCNT, DMA, card reads, backup bytes, firmware reads |
| `--calls N` | every function's entry recorded (`ARM_ENTER`, one branch on a flag otherwise); the last N of each CPU at the end, a repeated call shown once with its count |
| `--break ADDR`, `--break7 ADDR` | stop at the first call to an entry, with the last calls |
| `--watch ADDR[:LEN]` | every store into the range: the value, the recompiled function that stored, the thread, lr |
| (always) | at the end or a fatal error: each CPU's mode, thread, registers, interrupts taken, the functions it has been polling in (from the host's return addresses), the words on its stack that point into code |

## Speed

Headless, with no picture: ten minutes of the DS (36 000 frames at the
title, waiting) in 2.9 seconds, about 210 times the DS's speed; the
route, a minute with the movies, the menus and the first room's frames,
in 0.9 seconds.

## The jumps left to run time

Of the five read in `09-recompiler.md`, none stopped a run. The
functions holding three of them were not called in the route (checked
with `--break`): the C++ exception path's context restore (0x021283AC),
the ARM9's `bx r12` (0x02117DD4) and the ARM7's thread start
(0x038072C0). Whether Mobiclip's return through r6 (0x02131C04, and its
copy in the ITCM) and the ARM7's `bx r0` ran is not checked. The
threads' switches themselves are the runtime's (above).
