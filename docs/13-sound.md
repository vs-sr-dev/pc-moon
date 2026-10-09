# The sound

Phase 6 (session 6): Moon is heard. The ARM7's sound unit (16 channels,
2 capture units, the mixer) runs in the runtime in virtual time, sample
by sample at the DS's rate; the window plays it on the host's audio
device through SDL3, and any run can write it to a WAV file.

```sh
ROM="Moon (Europe) (En,Fr,De,Es,It).nds"
export PATH=/c/msys64/mingw64/bin:$PATH        # SDL3's DLL at run time
# the build as in 11-runtime.md; then:
build/recomp/b/ndsrun "$ROM" --window --out build/play                  # picture and sound, in real time
build/recomp/b/ndsrun "$ROM" --window --mute --out build/play           # without the sound
build/recomp/b/ndsrun "$ROM" --window --out build/play --wav build/play/moon.wav   # and a recording

# headless: the oracle's route into the first room, its sound as a file (61 s, in 2 s)
IN="1182:START,1542:tap:128:96,1902:START,2082:START,2262:START,2442:START,2622:A,2862:tap:128:120,3042:tap:128:120,3222:tap:128:120,3402:UP"
build/recomp/b/ndsrun "$ROM" --out build/p6 --vblanks 3644 --input "$IN" --wav build/p6/route.wav

# the sound registers against melonDS's at the same frame (no input, melonDS's save copied first)
mkdir -p build/p6o && cp "build/oracle/Moon (Europe) (En,Fr,De,Es,It).sav" build/p6o/
build/recomp/b/ndsrun "$ROM" --out build/p6o --vblanks 1154
python -m ndskit.melonds build/oracle/p6/t20.ml1 --compare build/p6o     # ends with both units' channels
python -m ndskit.melonds build/oracle/p6/t20.ml1 --info                  # a state's running channels
```

## The sound unit

| Part | How |
|---|---|
| Time | an output sample every 1 024 system cycles (2 048 ticks of the runtime's clock, 32 728.5 Hz). The unit is run lazily: up to the running CPU's time whenever the ARM7 reads or writes its registers, and up to the machine's at each frame's end. So the busy bit the SDK's driver polls drops when a one-shot's samples end, a run is the same with or without a listener, and the unit costs nothing measurable (the route headless: 1.09 s against 1.06 s without it) |
| Channels | each output sample a channel's timer (the system clock / 2, from the channel's reload) advances 512 and each overflow steps it: PCM8 and PCM16 read the next sample; IMA-ADPCM decodes the next nibble (the first word is the header, value and step index; the state at the loop start is kept for the loops); PSG on channels 8-13 the next eighth of a square wave of duty (n + 1) / 8; noise on 14-15 the next bit of a 15-bit LFSR. A sampled channel starts 3 steps late (ADPCM spends 8 nibbles' time on its header) and plays nothing with under 16 bytes; looped, it goes back to its loop start; one-shot, it stops after its last sample, silent, its busy bit cleared |
| Samples | read through the ARM7's memory map as they are played (main RAM, the shared WRAM, the ARM7's WRAM). The hardware's FIFO reads up to 32 bytes ahead: only data changing under a playing channel could tell the two apart (Moon's movies stream their sound through a ring buffer in main RAM, 0x0234F320, which the ARM9 refills behind the play position: an inference) |
| The mix | in integers at the hardware's widths: the sample times 16 >> the divider's shift (0, 1, 2, 4) times the volume (127 counting as 128); panned by 128 - pan and pan (127 as 128), >> 10; channels 1 and 3 left out of the mixer by SOUNDCNT bits 12-13; the outputs the mixer, channel 1, 3 or both (bits 8-11); the master volume (127 as 128) >> 7, then >> 8, plus SOUNDBIAS << 6, centred on 0x200 (the bias every SDK sets), clipped to 16 bits. Silent unless SOUNDCNT bit 15 and POWCNT2 bit 0 (the speakers). The DS truncates the output to 10 bits; it is kept at 16 here |
| Capture | units 0 and 1 take the left and right mixer (or channels 0 and 2), at the timers of channels 1 and 3, as PCM8 or PCM16 into the ARM7's memory, once or repeating; "add to the next channel" (bit 0) is noted, not done. Moon never starts one |
| To the host (`audio.cpp`) | each frame the samples go to an SDL3 audio stream, which resamples them to the device's rate. The window keeps the DS's pace by the host's clock and the device plays by its own: the stream's queue is held near three frames (about 50 ms) by nudging its playback ratio, by at most 0.5% (a twelfth of a semitone). A queue run dry plays silence until the next frame; one past half a second is cut back. At the end the run says how it went. WAV files: 16-bit stereo, 32 728 Hz in the header, the header rewritten each frame so a run stopped by an error leaves a whole file |

On the user's machine (an RTX 3060 Ti at 120 Hz, a USB audio interface
at 44 100 Hz), 2 500 frames of the route in the window: the queue never
ran dry and was never cut; the ratio averaged 1.0009, the queue
sawtoothing around its target as the device takes its blocks.

## What Moon uses

From the channels' starts in a run, the sound archive's banks and its
wave archive:

* **Music and effects**: the SDK's sequencer on the ARM7, every
  instrument a sampled one (95 instruments and 20 key-split regions in
  31 banks; no PSG, no noise), its waves in one archive (`WAVE_SE`: 85
  one-shot PCM8, 17 looped PCM8, one PCM16 of each; no ADPCM). The notes
  play as PCM8 one-shots at the pitch of the note (the same wave at 1 682
  and 3 364 Hz an octave apart).
* **The movies' sound**: PCM16 from a ring buffer of 0xA80 words in main
  RAM (0x0234F320), played looped at 22 077 Hz by channels 0 and 1,
  panned hard left and right, from the same buffer. They start with the
  introduction's movie (frame 1 607 of the route, "GAMEBRIDGE PRESENTS"
  on screen and SKIP below).
* SOUNDCNT 0x807F (the master volume at 127) or 0x8040 (at 64, as the
  game sets it at times), the bias at 0x200, no capture.

So ADPCM, PSG, noise and capture are written from GBATEK and melonDS's
behaviour and are not exercised by Moon: the next game that uses them
checks them.

## The boot's state, and the BIOS's tables

Two things were wrong before a sample was heard:

* **The speakers.** melonDS's direct boot (and the real boot) leaves
  POWCNT2 = 1, the speakers on; the SDK only sets the wireless bit (1)
  beside it. The runtime's boot left 0, so the first WAV of the route was
  60 seconds of silence with every channel running.
* **The BIOS's sound tables** (SWIs 0x1A-0x1C on the ARM7, which the
  SDK's driver calls for every note's timer and volume), worked out in
  session 4 from their definitions, checked now against the BIOS's own
  tables (as DeSmuME's source carries them): the pitch table (2^(i/768)
  - 1 in 16.16, 768 values) was exact; the sine table is the quarter wave
  times 32 767, not 32 768 (44 of 64 values were one too high); the
  volume table (724 bytes, -72.3 dB to 0 in tenths) is 128 x 10^(dB/200),
  rounded, times the divider the SDK pairs with each range (16, 4, 2, 1
  below -24, -12, -6 dB), where 128 is kept as 127 and 127 as 126: the
  channels read a volume of 127 as 128, so a true 127 cannot be written
  (an inference that makes all 724 values exact; 238 were one off).
  Before the fix a note melonDS plays at volume 95 played at 94.

## Against melonDS

melonDS's savestates hold the sound unit (section `SPU.`: SOUNDCNT, the
master volume, the bias, then 105 bytes a channel and 51 a capture unit:
registers, timer, position, current sample, ADPCM state, FIFO).
`ndskit.melonds` now reads it and shows a state's running channels
(`--info`) and, in `--compare`, both units' channels side by side with
the runtime's (`io7.bin`, the ARM7's registers, and `sound.txt`, each
channel's place, written at a run's end).

Five states with no input (`build/oracle/p6`, melonDS's save), at the
SDK's VBlanks 639, 732, 912, 1 152 and 1 452: **the same channels
running, with the same registers**: format, repeat mode, volume, divider,
pan, source, timer, loop and length, on the same channel numbers (one to
three channels each, notes of the opening's music and its effects).

The places in the samples differ by a constant: at 8 002 Hz every
channel of the runtime is 11 627 samples ahead (1.453 s, 87 frames), at
4 759 Hz 6 915, at 4 001 Hz 5 814, the same time; between two states both
move by the same count (12 439 samples from 639 to 732). The whole sound
plays 87 frames earlier than melonDS's. The reason is not the sound: the
game's frame counters (0x02157244, 0x0216A520 and two more) stand at 464
in melonDS at VBlank 520 and at 502 at VBlank 639, 38 counts in 119
frames, while the runtime's count every frame; from there melonDS's are
83 to 86 behind for good. The game waits early in its boot in melonDS
and not in the runtime, whose cartridge answers at once (an inference:
a file being read; `05-open-questions.md`).

Along the route, at frame 3 642 in the first room, both play notes of
the same samples with the same volumes, at other pitches: the music is
at another point, the presses landing on other frames.

By ear: the user's, in the window, against melonDS.

## Leftovers

* Interpolation between samples: the DS has none (each sample holds
  until the next); melonDS offers linear, cosine, cubic and SNES-gaussian
  as options. A choice for the PC version, by ear.
* Capture's "add to the next channel" mode; the FIFO's read-ahead;
  the 10-bit output (kept at 16 bits on purpose).
* The cartridge's time (above).
