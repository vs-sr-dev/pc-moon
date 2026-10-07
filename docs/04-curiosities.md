# Curiosities

Things found on the way that do not change the port but are worth
writing down.

* **Development switches left on the cartridge.** `config/moon.ini` has
  `EnableAllEpisodes = false` and `SkipIntro = false`, read at run time
  from a text file. Whether the engine honours them in the retail build
  is to be seen; the port could expose them as options.
* **The buggy's tuning history.** `config/buggy.ini` keeps the earlier
  values commented out above the shipped ones: reverse gear -1.5 became
  -1.4, first 1.5 became 1.36, second 0.85 became 0.675, third 0.65 became
  0.525, and the differential ratio doubled from 10 to 20.
* **A weapon's file name and its name in the game differ.**
  `plasmarifle.ini` begins "; Quanta Rifle": the weapon was renamed and
  the file kept its first name. The others: `ls` Lepton Spread, `mp`
  Muon Pistol, `oc` Oxid Cannon, `sp` Seeker Pods, `sr` Fermion Snipe;
  `rsd` and `sar` have no comment.
* **ROMs inside the ROM.** The texts of each language are not in a
  plain directory but in a complete NitroROM image (`en.srl` and the
  others), with a header titled `NINTENDO`, game code `NTRJ`, its own
  file system, a 4 KiB placeholder ARM9 and a copy of the SDK's ARM7:
  the SDK's ROM builder used as an archiver, mounted by the game as
  `lng:`. The same ARM7 is thus on the cartridge six times.
* **The game code is `COOP`.**
* **38% of the cartridge is video**: 48 Mobiclip movies, 24.8 MB of the
  64 MB image, `intro.mo` alone 4.2 MB.
* **The banner credits only the publisher**: "Moon / Gamebridge Ltd." in
  all six languages, Japanese included.
