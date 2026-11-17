# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

| File | Covers | State |
|---|---|---|
| text.md | encoding, font, control codes, SCEN.DAT / EXE / MSYS.DAT text containers, scene load, file reads, free space | encoding, font, SCEN, scene load, EXE tables + getters, MSYS sections, F4xx dictionary verified (extract roundtrip); how MSYS sections are located, free space guessed |
| debug.md | scene/map ids, scene-change VM ops, New Game warp patch, developers' check menu (scene 18), title flag, voice-off bit | warp verified on screen (`tools/debug/warp_all.py`); VM op lengths partly |
| graphics.md | graphics-text survey: Japanese graphics G1-G8 with sources | static sweep done (MSYS, MAP, TIM files, EXE, FMV samples); on-screen checks of mid-game screens in phase 2/8 |
