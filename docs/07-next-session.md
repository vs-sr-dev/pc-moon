# Next session: the PC version (phase 7)

Phases 5 and 6 are done (`12-picture.md`, `13-sound.md`): `ndsrun
--window` plays Moon in a window in real time, the 3D on OpenGL at the
window's resolution, the sound on the host's audio device. Before
anything else, **the user's ears**: the music, the effects and the
movies' sound against melonDS's, in the menus and in the first rooms
(a WAV of any run with `--wav`, if a passage needs a second listen).
If the held samples sound harsh, interpolation between them (linear or
cubic, as melonDS offers) is a small option to add.

Then phase 7, the PC version, starting with **the controls**, the
user's choice among the options of session 5 (the stylus is the camera
and also taps the lower screen's buttons):

1. the right mouse button held as a relative drag from a neutral point
   of the lower screen (the camera), the left button as the stylus;
2. the mouse captured whenever a game state in RAM says "playing", a
   key freeing the cursor for the lower screen;
3. true mouselook through a hook on the camera (the view matrix at
   0x021512E0, its writer still to find: `ndsrun --watch 021512E0:34`
   with a drag; the input script needs drags first), the lower screen's
   actions on keys.

And the key mapping, redone for a PC (the user's list); then the
screens' layout (the lower screen beside or over the upper), widescreen,
the draw distance (`DrawDistance` in the game's INI files), 60 frames.

Left from phases 4-6, when they matter: the cartridge's time (every
load ends at once; melonDS's take time, `05-open-questions.md`); the
DS's anti-aliasing (MSAA at the window's scale would do the same job),
edge marking and shadow polygons if a later room asks; the title's lines
1-24 one texel row apart from melonDS's; display capture, mosaic; a
finer cost of time than a fixed cost per safe point; the BIOS's SWI
frame on the SVC stack; the firmware's wireless block; the self-test
vectors regenerated over the 6 580 functions; ADPCM, PSG, noise and
capture checked on a game that uses them.

Before starting: the build as in `11-runtime.md` (MSYS2's clang, cmake,
ninja and SDL3 in PATH; the recompiler with `--copy
9:01FF9A60=0212FED4:659C`); `ndsrun` needs SDL3.dll from
`C:\msys64\mingw64\bin` at run time. A run writes its save into its
`--out` directory: a fresh directory is a new cartridge.
