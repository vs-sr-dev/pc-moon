# The recompiler

Phase 3 (session 3): both of Moon's programs translated to C++ by ndskit,
compiled with clang and linked against the runtime's first lines, and
held to an ARM interpreter by a self-test.

```sh
ROM="Moon (Europe) (En,Fr,De,Es,It).nds"
export PATH=/c/msys64/mingw64/bin:$PATH
python -m ndskit.recomp "$ROM" --out build/recomp --optest --copy 9:01FF9A60=0212FED4:659C
                                         # C++ for the ARM9 (with Mobiclip's ITCM copy, session 4), the ARM7, the instruction test
python -m ndskit.recomp.selftest "$ROM" --cpu 9 --auto --out build/recomp/selftest/arm9.txt
python -m ndskit.recomp.selftest "$ROM" --cpu 7 --auto --out build/recomp/selftest/arm7.txt
cmake -S build/recomp -B build/recomp/b -G Ninja -DCMAKE_CXX_COMPILER=clang++
ninja -C build/recomp/b
build/recomp/b/selftest build/recomp/selftest/optest9.txt build/recomp/selftest/optest7.txt \
    build/recomp/selftest/arm9.txt build/recomp/selftest/arm7.txt
python -m ndskit.armemu "$ROM" --cpu 9 --call 02126428 --regs r0=FFFFFF9C,r1=7   # ask the game's code
```

## The pieces

| Piece | What it does |
|---|---|
| `ndskit.armemu` | the reference: an ARM interpreter (ARMv5TE for the ARM9, ARMv4T for the ARM7, ARM and Thumb, the modes and their banked registers) |
| `ndskit.recomp.discover` | every function, and what each write to pc is: a return, a call, a switch, a jump (`Function.sites`) |
| `ndskit.recomp.emit` | one C++ function per entry |
| `python -m ndskit.recomp` | one module per program (`p_arm9`, `p_arm7`): the functions in files of about 8 000 instructions, the segments with their crc32, the table of entries, CMake |
| `ndskit/runtime/` | `arm.h` (the CPU context, memory, the helpers the generated code calls), `core.cpp` (main RAM, the TCMs, the ARM7's WRAMs, the modes, the dispatch), `services_stub.cpp` (no hardware), `selftest.cpp` |
| `ndskit.recomp.selftest` | vectors recorded with armemu, replayed by the `selftest` executable |

## How the code is translated

A function is `void f_02000C00(ArmContext& c)` (`t_...` for Thumb), its
instructions in address order with a label wherever something jumps.
What the ARM makes hard (`06-attack-plan.md`) is met so:

* **Conditions**: each instruction under an `if`. **Flags**: N, Z, C and V
  are stored only where some path reads them before they are set again
  (a backward liveness pass over the function; all four live at its
  exits and before its calls). The shifter's carry is computed only for a
  logical instruction with S whose C is live.
* **The PC is a value**: reads of r15 are constants (+8, +4 in Thumb,
  aligned for Thumb's literals and `adr`); literal loads are constants
  read from the image (unless another literal points at the slot).
* **Branches and calls**: `b` is a `goto`, or a tail call to another
  entry; `bl`/`blx` set lr and call, then check that the callee came back
  to lr (`ARM_RET`).
* **Writes to pc from a value** take discovery's decision at that address:
  a return (`c.pc = lr; return;`), a call through a register (compared
  with the target discovery expects, else dispatched by `arm_call` over
  the module's entries, the mode in bit 0), a switch (a C++ `switch` over
  its targets), a jump (to a known entry as a tail call, else
  `arm_jump`, which calls an entry or takes anything else for a return).
  When the function itself put the address in lr (hand-written local
  subroutines), control coming back there goes on there.
* **Interworking**: `bx`, `blx` and, on the ARM9, loads into pc take the
  mode from bit 0; `mov`/`add pc` keep it.
* **Modes, the SPSR, exception returns** (`subs pc, lr, #4`), **CP15**,
  **SWI** and undefined instructions are runtime calls.
* **Safe points** (`ARM_POLL`) at backward jumps, before calls and after
  an `msr` that may unmask interrupts: where the runtime will take
  interrupts and run the other CPU.
* **Memory**: main RAM (with its mirrors), the ITCM and DTCM on the ARM9,
  the ARM7's WRAM and the shared WRAM (all the ARM7's, as the SDK's boot
  leaves WRAMCNT) are host arrays; the rest goes to the hardware's
  handlers. Unaligned words rotate, halfwords align on the ARM9 and
  rotate on the ARM7, as the CPUs do.

## Moon in numbers

| | Functions | Instructions | C++ files | Calls through registers: expected / dispatched | Switches (targets) | Jumps to a known target | Jumps left to run time |
|---|---|---|---|---|---|---|---|
| ARM9 | 5 413 | 305 574 | 39 | 4 / 2 382 | 147 (1 834) | 272 | 3 |
| ARM7 | 933 | 37 664 | 6 | 0 / 39 | 40 (712) | 68 | 2 |

Session 4, with what the runtime asked of discovery (`11-runtime.md`)
and Mobiclip's decoder as it runs from the ITCM (`--copy`):

| | Functions | Instructions | Calls through registers: expected / dispatched | Switches (targets) | Jumps to a known target | Jumps left to run time |
|---|---|---|---|---|---|---|
| ARM9 | 6 618 (38 in the ITCM copy) | 341 308 | 4 / 2 383 | 213 (2 652) | 516 | 4 |
| ARM7 | 943 | 37 690 | 0 / 39 | 40 (712) | 76 | 2 |

(Instructions are counted per function: code that several functions
share, as the decoder's routines do, counts once for each.) The fourth
jump of the ARM9 is the ITCM copy's own `mov pc, r6`.

Generating both takes about 20 seconds and gives 31 MB of C++; a clean
build of them with the instruction tests (clang 22, -O3, Ninja, 16
threads) takes 42 seconds on this machine. *(Inference: the 2 382 calls dispatched
at run time are virtual methods and callbacks: `blx rN` after a load
from an object.)*

The jumps left to run time, read one by one:

| Where | What | At run time |
|---|---|---|
| ARM9 0x021283D8 `bx r2` | registers and sp loaded from a context (r0), then a jump: a thread switch or a longjmp (inference) | `arm_jump`: an entry is called, else a return. To be read again with the runtime |
| ARM9 0x02131C04 `mov pc, r6` | Mobiclip: lr saved in r6 around a call, then returned through it | a return |
| ARM9 0x02117DF4 `bx r12` | `mov lr, pc` on one path only, before a call through r12 | a call: lr is the function's own address, control goes on there |
| ARM7 0x03806078 `bx r0` | lr set on one path only (`add lr, pc, #0`) | as ARM9 0x02117DF4 |
| ARM7 0x03807324 `bx r12` | r0-r3 cleared, lr = r12, then a jump to r12: a thread's start (inference) | `arm_jump` calls it; its return goes to its own entry, which the caller's check will refuse: for phase 4 |

## The checks

1. **armemu against Unicorn** (QEMU's ARM946, a scratch script, never a
   kit dependency): 12 993 random ARM instructions and 12 490 Thumb ones
   with random registers and memory, every register, the flags and the
   memory compared: no difference. The only cases set apart are the
   unaligned accesses (QEMU reads them as an ARMv6 would; the DS's CPUs
   rotate or align, which armemu does, as melonDS does) and `swp`, which
   Unicorn does not run. 1 960 branches, calls and loads into pc
   (interworking both ways) agree, except `bx` to an ARM address with
   bit 1 set, which the architecture leaves open.
2. **Known answers**: the SDK's divisions run in armemu: 0x02126428
   (signed: −100 / 7 = −14 remainder −2, 0x12345678 / 0x1000) and
   0x0212663C (unsigned: 0xFFFFFF9C / 7 = 0x24924916 remainder 2),
   quotient in r0 and remainder in r1.
3. **The instruction test** (`--optest`), one program per CPU: every
   instruction form, drawn at random within the form, memory
   instructions with their bases in a block of random data; random
   straight-line and branching sequences (for the flags stored only
   where read); and hand-assembled control flow: loops, calls, a
   conditional call and return, calls through registers, veneers, both
   switch forms, interworking each way, `bx pc`, Thumb's push/pop
   returns, modes with their banked registers (FIQ's r8-r12 too), user
   mode, an exception return. ARM9: 3 747 functions, 29 708 vectors;
   ARM7: 3 545 functions, 28 041 vectors. **No difference.** The test
   catches a wrong carry on subtraction (91 failures when one was planted).
4. **The game's own functions** that run alone (`--auto`: on random
   registers they return having written only their stack, or only the
   data their pointer arguments point at), 16 vectors each, run on the
   program as the cartridge loads it: the ARM9's 1 340 (510 on their
   stack alone, 830 with pointer arguments; the SDK's divisions among
   them), 21 077 vectors; the
   ARM7's 172, 2 729 vectors. **No difference**, in the registers, the
   flags or the memory after each function's vectors.

In all, 81 555 vectors and no difference: phase 3's mark (`06-attack-plan.md`).

## Added in session 4

* **Context saves and landings**: a function that stores an address of
  its own code (`OS_SaveContext`) returns twice. After a call to it the
  runtime is told the caller's sp (`arm_context_saved`); in the functions
  that call it, every call catches `ArmUnwind` and goes on at the save's
  return address, where a thread's context comes back when it is loaded
  (`11-runtime.md`, threads).
* **`ARM_ENTER`** at each function's entry: one branch on a flag, for the
  runtime's call trace and breaks.
* **`--copy CPU:DEST=SRC:LEN`**: a block the program copies elsewhere and
  runs there, as a segment at its destination (checked by the runtime
  only once copied).
* **A store watch** in the fast stores (one compare): `ndsrun --watch`.

## What it does not do yet

* Hooks (replacing a function of the game by the port's own), as
  saturnkit has.
* Thumb switches and halfword-offset tables: Moon has none; other
  cartridges do (`ndskit/recomp/discover.py`, known gaps).
