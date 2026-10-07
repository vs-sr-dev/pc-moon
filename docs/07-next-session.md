# Next session: the runtime core (phase 4)

Phase 3 is done (`09-recompiler.md`): both programs are C++ that
compiles, links and agrees with the interpreter on 81 555 vectors. The
target now is **the boot to the first `OS_WaitVBlankIntr` (0x0211860C),
headless**, its main RAM, ITCM and DTCM compared with melonDS's
savestates at the same point; then on to the title screen.

1. **The machine as the BIOS and the firmware leave it**: both programs
   copied to their load addresses from the cartridge's header, the
   header's copy and the firmware's user settings in the shared area
   (0x027FFC00-0x027FFFFF: what the SDK reads there, from melonDS's
   state at boot), each CPU in its mode with its stacks, the ARM9 at
   0x02000800 and the ARM7 at its entry.
2. **The two CPUs**: the ARM7 as a coroutine of the ARM9 (as saturnkit
   runs the slave SH-2): it runs when the ARM9 waits on it (IPCSYNC, the
   IPC FIFO, a poll of shared memory) and at its interrupts; the safe
   points (`ARM_POLL`) are where the switch happens.
3. **Interrupts**: IME/IE/IF on each CPU; the BIOS's entry (IRQ mode, the
   user handler at DTCM+0x3FFC on the ARM9 and 0x0380FFFC on the ARM7,
   the flags the BIOS's IntrWait checks at DTCM+0x3FF8 and 0x0380FFF8),
   the exception return; taken at safe points.
4. **The BIOS's SWIs** as HLE (`arm_swi`): IntrWait, VBlankIntrWait,
   Halt, WaitByLoop, CpuSet, CpuFastSet, the decompressors (ndskit.lz's
   formats), Div, Sqrt, GetCRC16: whichever the boot calls first.
5. **The memory map** beyond the host arrays: the I/O registers of each
   CPU, VRAM with its banks (VRAMCNT), palettes, OAM, the shared WRAM by
   WRAMCNT, the BIOS area; the math unit (DIVCNT, SQRTCNT, exact).
6. **Time**: VCOUNT and DISPSTAT (263 lines of 355 dots, the VBlank and
   HBlank flags and interrupts), the timers, DMA (immediate, VBlank,
   HBlank, the geometry FIFO's), IPC (SYNC and both FIFOs, their
   interrupts).
7. **The cartridge**: ROMCTRL and the main-data read (0xB7) over the
   .nds file, as the SDK's CARD and FS libraries issue it; the backup
   memory (AUXSPI) as a file. On the ARM7: SPI (touch, firmware, power),
   the RTC.
8. **The jumps left to run time** (`09-recompiler.md`): the context
   restored at 0x021283AC, the ARM7's thread start at 0x038072C0, read
   with the runtime running.
9. **The comparison**: the runtime stops after N VBlanks and writes its
   memories; `tools/oracle.py framesv:` gives melonDS's at the same
   count. First mismatch, first fix.
10. **ndskit** as the runtime grows: a store watch (for the camera's
    writer) and hooks, as saturnkit has; `armemu` keeps its role as the
    reference for anything the runtime's CPU side changes.

Before starting: `python -m ndskit.rom ... --extract build/extract --nested`
if `build/` is empty; the recompiled build is `09-recompiler.md`'s
commands (MSYS2's clang, cmake and ninja in PATH); the oracle needs PIL
(`C:\Python314\python.exe`).
