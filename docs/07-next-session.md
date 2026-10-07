# Next session: the picture (phase 5)

Phase 4 is done (`11-runtime.md`): the runtime runs Moon headless from
its boot into its first room, deterministically, its memories matching
melonDS's at the same frame (74 bytes of main RAM after 464 frames, with the same save). The
target now is **the logos, the title and the first room on screen, in a
window, played with the keyboard and the mouse as the stylus**, the
pictures compared with the oracle's at the same frames.

1. **The window and the pace**: SDL3 and OpenGL 4.5 (as wiikit and
   saturnkit), the two screens one above the other at first; the runtime
   paced to the display (a frame of the DS per VBlank, waiting for the
   host's clock), headless kept for the comparisons.
2. **Input**: the keyboard as the buttons (the oracle's mapping), the
   mouse on the lower screen as the stylus (EXTKEYIN's pen bit, the touch
   controller's positions through the firmware's calibration: the input
   script already drives them).
3. **The 2D engines in software** at 256x192 per screen, a line at a
   time: DISPCNT's modes, text and affine and extended backgrounds,
   bitmaps (the movies: inference, Mobiclip draws into a bitmap or
   VRAM in LCDC mode), sprites, windows, blending, master brightness, the
   3D layer as engine A's BG0; VRAM through the bank pages (the extended
   palettes' mappings still to add: E, F, G, H, I).
4. **The geometry engine in software**: the packed commands from GXFIFO
   (DMA from 0x01FF99B8) and the ports, the matrix stacks with GXSTAT's
   levels and busy bit (the only thing the game reads back), vertices,
   lighting, clipping, the polygon and vertex lists, SWAP_BUFFERS.
5. **The renderer**: the lists drawn with OpenGL, first at 256x192 to
   compare with melonDS, then at N times: the seven texture formats from
   the texture slots, the polygon modes, translucency and its sort, alpha
   test, fog, edge marking, w-buffering, the clear colour.
6. **The comparison**: `tools/oracle.py` takes pictures at wall-clock
   times; the runtime writes its screens at a VBlank; the frame of each
   picture from the SDK's count (`framesv:`).

Left from phase 4, when they matter: a finer cost of time than a fixed
cost per safe point; the BIOS's SWI frame on the SVC stack; the
firmware's wireless block; the camera's writer, now within reach of
`ndsrun --watch 021512E0:34` with a drag in the input script; the
game's self-test vectors (`recomp.selftest --auto`) regenerated over the
6 580 functions discovery now finds.

Before starting: `python -m ndskit.rom ... --extract build/extract
--nested` if `build/` is empty; the recompiled build and `ndsrun` are in
`11-runtime.md` (MSYS2's clang, cmake and ninja in PATH, the recompiler
with `--copy 9:01FF9A60=0212FED4:659C`); the oracle needs PIL
(`C:\Python314\python.exe`). A run writes its save into its `--out`
directory: a fresh directory is a new cartridge.
