# Next session: the PC version (phase 7)

Phases 5 and 6 are done (`12-picture.md`, `13-sound.md`): `ndsrun
--window` plays Moon in a window in real time, the 3D on OpenGL at the
window's resolution, the sound on the host's audio device. The user
listened against melonDS: the levels are the game's own, and the one
fault heard (the introduction's movie crackling at first) is fixed; the
sound is confirmed. Interpolation between samples (linear or cubic, as
melonDS offers) stays a small option should a later room sound harsh.

Next, phase 7, the PC version, starting with **the controls**. The
user chose (session 6) true mouselook, and the classic keys of a PC
shooter, reached step by step:

* **Mouselook** through a hook on the camera: the view matrix at
  0x021512E0, its writer still to find (`ndsrun --watch 021512E0:34`
  with a drag; the input script needs drags first). The stylus's drags
  on the lower screen are how the DS turns the camera; the mouse then
  turns it directly.
* **The left mouse button fires** (on the DS a shoulder button: L or R,
  to confirm in the game's options).
* **WASD as the D-pad.**
* **E for the lower screen's interaction button** (doors and the
  like: a tap at its place on the lower screen, to find).
* Then the rest of a PC shooter's map, as the user lists it; the
  lower screen's other actions on keys.

Then the screens' layout (the lower screen beside or over the upper),
widescreen, the draw distance (`DrawDistance` in the game's INI files),
60 frames.

**Publication.** Moon works "until proven otherwise", the line for
creating the repositories, but they are created only when ndskit has a
second game (the rule: a kit proven on two). The next port is
pc-nostalgia (Nostalgia, DS); when it reaches that point, the three
repositories (ndskit split out of `ndskit/` with its history, pc-moon,
pc-nostalgia) are created and pushed together. Until then nothing here
is pushed. Session 6 swept this repository for publication: no
cartridge content in the history, a clean clone builds and runs as the
README says.

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
