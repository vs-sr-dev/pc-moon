# Next session: the sound (phase 6)

Phase 5 is done (`12-picture.md`): `ndsrun --window` plays Moon in a
window in real time, the 2D engines in software, the geometry engine in
the DS's fixed point, the 3D on OpenGL at the window's resolution; along
the route its pictures match melonDS's. Before anything else, **the
user's own play** of the window build: the keys, the mouse as the stylus
(the menus, the "look around" drags in the first room), what looks wrong.

The target now is **the music and the effects**, by ear against melonDS.

1. **The channels** (`sound.cpp`, the ARM7's 0x04000400-0x040004FF): the
   16 channels' PCM8, PCM16 and IMA-ADPCM (its header, loop restart with
   the saved state), PSG on 8-13 (duty), noise on 14-15; the timer as the
   sample rate (the system clock / 2 over the timer), loop start and
   length, one-shot and repeat; volume with its divider, panning; the
   master volume and SOUNDCNT's mixer outputs; the busy bit ending when a
   one-shot ends (now a guess from the length).
2. **The capture units** (0x04000500-0x0400051F) if Moon uses them (the
   SDK's reverb would, an inference): what the ARM7's driver writes will say.
3. **The mixer**: the channels at the DS's rate (about 32 730 Hz, a
   sample every 1 024 system cycles, 2 048 ticks of the runtime's clock),
   in step with virtual time, into a ring that SDL3's audio stream drains,
   resampled to the host's rate. Real time is paced by the host's clock:
   the ring's slow drift against the audio device's clock to absorb.
4. **The BIOS's sound tables** (`bios.cpp`): the volume, pitch and sine
   tables are worked out from their definitions; with sound playing, the
   driver's use of them can be checked by ear and against melonDS's
   savestates (whose sections should hold the sound registers: to check).
5. **The comparison**: melonDS's audio by ear; a headless WAV of a run
   (`--wav`), and the channel registers against melonDS's savestates at
   the same frame.

Left from phase 5, when they matter: the DS's anti-aliasing (MSAA at the
window's scale would do the same job); edge marking and shadow polygons
if a later room asks (each is noted once in the log); the title's lines
1-24 one texel row apart from melonDS's; display capture, mosaic.
From phase 4: a finer cost of time than a fixed cost per safe point; the
BIOS's SWI frame on the SVC stack; the firmware's wireless block; the
camera's writer (`ndsrun --watch 021512E0:34` with a drag; the input
script has no drags yet); the self-test vectors regenerated over the
6 580 functions.

Before starting: the build as in `11-runtime.md` (MSYS2's clang, cmake,
ninja and SDL3 in PATH; the recompiler with `--copy
9:01FF9A60=0212FED4:659C`); `ndsrun` needs SDL3.dll from
`C:\msys64\mingw64\bin` at run time. A run writes its save into its
`--out` directory: a fresh directory is a new cartridge.
