# The picture

Phase 5 (session 5): Moon on screen. The 2D engines draw in software a
line at a time, the geometry engine runs the 3D commands in software in
the DS's fixed point, the rendering engine draws its polygons with
OpenGL at any resolution, and a compositor puts the two together in a
window, played with the keyboard and the mouse. Headless runs write
pictures at given frames, compared with melonDS's.

```sh
ROM="Moon (Europe) (En,Fr,De,Es,It).nds"
export PATH=/c/msys64/mingw64/bin:$PATH        # clang, cmake, ninja, SDL3 (and its DLL at run time)
# the build as in 11-runtime.md; then:
build/recomp/b/ndsrun "$ROM" --window --out build/play          # the game, in real time
build/recomp/b/ndsrun "$ROM" --window --scale 4 --out build/play  # the 3D at 1024x768 (default: the window's)

# headless pictures (both screens, 256x384): at given VBlanks of the SDK's count, or every N
IN="1182:START,1542:tap:128:96,1902:START,2082:START,2262:START,2442:START,2622:A,2862:tap:128:120,3042:tap:128:120,3222:tap:128:120,3402:UP"
build/recomp/b/ndsrun "$ROM" --out build/p5 --vblanks 3644 --input "$IN" --shots 702,1782,2742,3342,3643
build/recomp/b/ndsrun "$ROM" --out build/p5 --vblanks 1500 --shot-every 60

# melonDS along the same route, pictures at wall-clock seconds (frame = 60 t - 18)
python tools/oracle.py --out build/oracle/p5 --fresh --at "12:shot,20:START,26:tap:128:96,30:shot,32:START,34:shot,35:START,38:START,41:START,44:A,46:shot,48:tap:128:120,51:tap:128:120,54:tap:128:120,56:shot,57:UP,61:framesv:3"
```

In the window: X is A, Z B, S X, A Y, Q L, W R, Enter START, Backspace
SELECT, the arrows the D-pad (melonDS's keys in the oracle); the left
mouse button on the lower screen is the stylus. F12 writes a picture
(`shotN.png` at the DS's size and `shotN-window.png` as the window shows
it) into `--out`; Escape quits (the save is written, as at every stop).
A run with `--input` takes its input from the script, not the host.

## How a frame is made

| Part | How |
|---|---|
| 2D engines (`gpu2d.cpp`) | each visible line drawn as it starts, with the registers as they are then: text, affine, extended (16-bit entries, 256-colour and direct-colour bitmaps) and large-bitmap backgrounds in every mode, 16 and 256 colours, the extended palettes; sprites in tiles (1D and 2D mapping), bitmaps, affine and double-size, semi-transparent and window sprites; windows 0, 1 and the OBJ window; alpha blending, brighter, darker; the master brightness; the display off, graphics and VRAM display modes. Colours as the DS keeps them inside (6 bits a component) |
| The 3D layer | engine A's BG0 when DISPCNT bit 3 is set: the 2D engine leaves its pixels to the compositor, with what lies under them and how they blend (two words a pixel, `nds.h`) |
| Geometry engine (`gx.cpp`) | GXFIFO's packed commands and the command ports; the matrix stacks with GXSTAT's levels and error bit; vertices in their five forms; texture coordinates and their three transforms; lighting at NORMAL (four lights, the shininess table); triangles, quads and their strips; face culling; clipping against the view volume (the far plane by POLYGON_ATTR bit 12); the viewport; BOX_TEST, POS_TEST, VEC_TEST and the matrix read-backs. SWAP_BUFFERS waits for the VBlank: the commands behind it queue (GXSTAT busy, the FIFO's count) and run after the swap |
| Its hand-over | at line 215, as the DS starts drawing the next frame's 3D: the lists sorted (opaque, then translucent; by y unless the swap asked for manual order), the 3D registers, the texture and texture-palette slots copied (`render3d.h`). It is shown in the next frame |
| Rendering engine (`render_gl.cpp`) | OpenGL 4.5, into a target of 256x192 times the scale. The screen positions are the geometry engine's exact ones (at scale 1 the DS's own, rounded as it rounds them); colours and texture coordinates interpolated with perspective at each pixel's top left corner, as the DS does; depth z/w across the screen or w. The texture memory goes up whole each frame (608 KiB) and the fragment shader reads it as the DS's texture unit does (the seven formats, 4x4 compressed included; repeat, flip, clamp; colour 0 transparent), then combines in the DS's integers (modulation, decal, toon, highlight; the alpha test). Translucent polygons blended, their depth written by POLYGON_ATTR bit 11; wireframe polygons as lines. Fog afterwards, from each pixel's depth and fog flag (melonDS's density steps) |
| Compositor (`display.cpp`) | the 2D words and the 3D picture per pixel of the window: the 2D at the DS's resolution, the 3D at its own; the 3D's alpha blended with the layer under it, a 2D layer blended over the 3D, the master brightness. The same logic in software (`gpu2d_compose`) for headless pictures, from the 3D drawn at scale 1 and read back |
| Window and pace | SDL3, OpenGL 4.5 core; the two screens one above the other (engine A on top when POWCNT1 bit 15 says so), as large as the window allows. The DS's 59.83 frames a second by the host's clock, each presented with the vertical sync (twice per frame on a 120 Hz display) |
| Headless | the 2D engines draw, and the 3D's hand-over is copied, only for the frames a picture is taken of; a hidden window gives OpenGL for the 3D |

## What Moon asks of them

Read from the registers at the menu (frame 900) and in the first room
(frame 3 644), and from the polygons of one frame there:

| | Menu | First room |
|---|---|---|
| Engine A (upper screen, POWCNT1 bit 15) | mode 4, only BG0, the 3D: the title is one textured quad over the whole screen | mode 0: BG0 the 3D (priority 3), BG1 and BG2 text layers (the frame and the HUD), sprites |
| Engine B (lower screen) | mode 0: BG0-BG2 16-colour text layers, BG3 a 256-colour one, sprites; extended palettes on; alpha blending with BG3 as the second target (no first target: for semi-transparent sprites) | mode 3: three text layers and BG3 an extended one, sprites; alpha blending with BG3 and the backdrop as second targets |
| DISP3DCNT | 0x301B: textures, highlight shading, blending, anti-aliasing | 0x309B: the same and fog (colour grey 0x4A52, offset 0, shift 0) |
| Polygons | 1 | 1 103 a frame, 3 780 vertices (the DS's limits: 2 048 and 6 144); all modulated; textures in 4, 16 and 256 colours; 1 088 with the fog flag |

No display capture, no edge marking, no shadow polygons, no mosaic, no
equal depth test, no 4x4-compressed or direct-colour texture have been
met (each would be noted once in the log).

## Against melonDS

Pictures of both screens at the same frames of the SDK's count, along the
route (`build/oracle/p5`): the menu, the "Gamebridge presents" movie, the
tutorial's text over the darkened room, the first room. The same screens
at each step; melonDS's presses follow the wall clock, so a picture can
fall a few frames earlier or later in a transition (at 34 s melonDS is
still on black where the runtime is in the room).

| Picture | Pixels differing by more than 24 in a component | Where |
|---|---|---|
| The menu's lower screen (2D) | 564 of 49 152 | the selected button's border, which pulses |
| The title's upper screen (3D, one quad) | 496 of 38 400 (lines 0-169) | lines 1-24 sample the texture one row lower in melonDS; lines 25-191 the same texel for texel |
| The first room's upper screen | 7 411 of 40 960 | polygon edges (the DS's anti-aliasing is not drawn) and the player a little elsewhere (the presses' frames) |

The memories at frame 464 are unchanged by the phase: 74 bytes of main
RAM differ from melonDS's, as in session 4 (`11-runtime.md`).

## What drawing taught

* **The DS interpolates at a pixel's corner**: the first pictures of the
  title stood one line higher than melonDS's on every line. Its quad's
  texture runs from 0 to 191.5 over 192 lines; GL interpolates at the
  pixel's centre, the DS at its top left corner, half a line earlier.
  Interpolating there (`interpolateAtOffset`) put 165 of 189 lines in
  place. The rest, lines 1-24, are still one row apart: melonDS's
  interpolator and the corner give the same rows by the formula; not
  found yet.
* **Texture coordinates in 1/16 texel**, as the DS keeps them: the
  coordinate rounded there (with a bias against the float's error)
  before the texel is taken.
* **Headless speed**: drawing both engines' 192 lines every frame made
  the route ten times slower (8.8 s). They now draw only for a picture's
  frame: 1.3 s (session 4: 0.9; the geometry engine works every frame).

## Not yet

The DS's anti-aliasing; edge marking; shadow polygons (skipped); the
translucent polygon ID rule; the equal depth test (drawn as less); the
clear image; 1-dot polygons; a translucent pixel over a cleared pixel of
alpha 0 is blended with the clear colour (the DS writes it as it is);
display capture; mosaic; main memory display; the 3D layer's horizontal
scroll.
