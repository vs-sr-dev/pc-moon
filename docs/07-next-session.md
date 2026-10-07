# Next session: the recompiler (phase 3)

Phase 2 is done in what matters for the recompiler: every function of
both programs is known (`03-executables.md`). Its remaining questions
(the camera's writer, the SDK's names) are easier to answer with the
runtime's store watch than by reading, so they move on with it.

1. **An ARM interpreter in ndskit** (`armemu`): ARMv5TE and Thumb,
   conditions and flags, the shifter's carry, LDM/STM with every mode,
   the multiplies and the DSP extensions, CLZ, interworking, processor
   modes with their banked registers. The recompiler's oracle, as
   `sh2emu` was saturnkit's. Checked by running functions of the game
   that run alone (the SDK's division, memory and string routines, the
   fixed-point maths) and by known answers.
2. **The emitter** (`ndskit/recomp/emit.py` and `python -m
   ndskit.recomp`): one C++ function per entry; the condition on each
   instruction; the shifter and the flags computed only where read; the
   PC as a value; calls through registers by a dispatch over the known
   entries, with the mode in bit 0; switches as `switch`; literal pools
   read as constants; the ITCM block at its run address; CP15 operations
   as runtime calls. One module per program (ARM9, ARM7).
3. **The self-test**: vectors recorded with `armemu` for every
   instruction form (ARM and Thumb, each condition) and for game
   functions that run alone; the generated C++ compiled with clang
   (MSYS2) and compared. Done when both programs compile and link and
   the self-test shows no difference.
4. **The runtime's first lines** (`ndskit/runtime/`, C++20): the CPU
   context, main RAM, the TCMs, the dispatch, the self-test harness: what
   the self-test needs and nothing more.

Then phase 4 (the runtime core) begins: the first target is the boot to
the first `OS_WaitVBlankIntr`, headless, compared with melonDS's
savestates.

Before starting: `python -m ndskit.rom ... --extract build/extract --nested`
if `build/` is empty; the oracle needs PIL (`C:\Python314\python.exe`).
