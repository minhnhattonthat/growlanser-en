# Debug tool: scene warp (phase 2)

All addresses are RAM (EXE file offset = addr - 0x80010000 + 0x800). gp = 0x801138DC.

## Scenes and maps (verified: request logs, RAM pokes, warp runs)
- A **scene** is a script set: SCEN.DAT entries N (script + text), N-280 (small) and N+280, scene id N = 0-279.
  The loader builds a type-4 CD request (`0x80018BD4(scene, ?, part 0/1/2, dst)`); parts land at 0x80128B98 and up.
- Scene request: u16 **0x80113D66** (gp+0x48A) and **0x80113D62** (gp+0x486); 0x80113D60 (gp+0x484) = -1 on a change.
  Loaded scene: save block 0x80196A70 + 0x2B4 (= 0x80196D24) and +0x2B6. The field loader (0x8001D8xx) compares them
  and loads what differs.
- A **map** is (area, sub): save block +0x2BA / +0x2BB (0x80196D2A / 0x80196D2B), copies gp+0x430 / gp+0x438.
  `0x80044014(area, sub)` looks the pair up in the EXE table at 0x80100A10 (u8 area, u8 sub, u16 MAP.DAT id,
  0x5BE rows) and stores the map id at gp+0x4BA. Scene and map are independent: a scene runs on whatever map is set.
- New Game (branch at 0x800166E8, reached from delay slots 0x80016614 / 0x8001662C `addiu a0, zero, 2`) sets
  area 2 / sub 5 (moonlit cliff), zeroes the scene request (0x8001670C, 0x80016714) and the field loader loads
  scene 0. Load Game (0x8001A2F8) takes scene from save +0x2C0 and area/sub from +0x26C/+0x26D.
- Boot init `0x8003A070(level)`: level 1 clears scene flags (save +0x274, 32 B), 2 also +0xC8 (100 B, story flags?),
  3 is New Game (everything, loaded scene = 0xFFFF). gp+0x48C (0x80113D68) = 2 after boot init.

## Event VM (verified by disassembly; op lengths partly)
- Script pointer gp+0x428 (0x80113D04), current op gp+0x4BC; dispatcher 0x8003AA3C reads the op byte, stores
  ptr+1 and jumps through the table at 0x800114F0 (0xD6 ops); common exit 0x8003DCA8. Call stack of script
  pointers at 0x801969B8 indexed by gp+0x4AC.
- Ops 0x77-0x7A, 0x7C (handler 0x8003CE84): map / scene change. `78 sub area16 scene16` and `7A ...` (same, plus a
  flag) set area/sub and request `scene`; 0x79 takes sub from a variable; `7C sub area16` changes map only; `77 sub`
  changes sub only. Op 0x76 `76 sub area x` sets area/sub and flags. `tools/scenelinks.py` scans scripts for 78/7A by
  byte pattern (noisy without op lengths; `tools/vmstatic.py` guesses lengths from the handlers, fall-through only).
- Scene 1's script starts at entry 281 + 0x225C (just before its text section, header word 22 = 0x2290).

## Warp (tools/debug/warp.lua)
Cold boot; once gp+0x48C = 2 (boot init done), patch the New Game code in RAM (area/sub immediates, the two zeroing
stores NOPed) and hold the request at the wanted scene; press Start through the logos and Circle on the title.
Landing is tested on RAM (loaded scene and area/sub match), not on a frame count. The scene's script then runs from
its start, with New Game story flags. No debugger needed (full speed).

## Developers' check menu (scene 18, verified on screen)
SCEN scene 18 is a leftover debug scene ("ダンジョンマン", "チェック項目を選んで下さい"); scene 0's script links to it
(op 78, area 2 sub 1). Warped to, it offers: Luise magic + M2 gear, encounters off, misc check, full check (story
points: 仕官話し, 休暇1-11明け, VSゲヴェル, ゲヴェル後, 祝賀会以降 x2), FC check, dungeons (5), event battles (14), event
quick check (16 points from キャラメイク to ランザック王), face graphics, units, parameter edit, name/territory change.
Story points set flags and load the scene the way the game does. `tools/debug/scenes.txt` drives it by menu index.
Scene 13 holds a note that it is only used during vacations (休暇). Full text: `python -X utf8 tools/scendump.py 18`
(`--summary` gives a one-line gist of every scene).

## Title / voice
- gp+0x28C (0x80113B68) is the front-end state: 8 while the title menu (START / LOAD / CONFIG / APPENDIX) is up.
- Voice: the voice player 0x80053F74 skips when bit 0x10 of 0x80194AA5 is set (config byte). Headless PCSX hangs
  mid-dialogue waiting for XA voice (frames stop; looked like an FMV hang at ~frame 7000 of New Game), so warp.lua
  sets that bit unless VOICE=1.

## Disc 2 (solved 2026-11-19, phase 8 session 5)
- **Fix:** boot the disc 2 cue and hold the expected-disc byte gp+0x724 (0x80114000, `lb` in the check below) at 1
  (`tools/debug/disc2.lua`): New Game then accepts disc 2 and the late story points need no swap. scenes.txt marks
  such entries `disc 2`; warp_all.py swaps "(Disc 1)" for "(Disc 2)" in --cue's file name. All 8 disc 2 story
  points land on both the original and the English build.
- `tools/debug/where.lua` logs "WHERE f scene area sub" on each change. 祝賀会以降 (pick 14) loads scene 93 (map
  59/4: Grancil celebration, free roam: Circle alone does not advance it); scene 93 links to scene 2 / area 62.
  The ending + staff roll (G5) is still unreached: it follows the final tower (時空制御塔). Leads: the MAP.DAT id
  list at EXE 0x801094FC.. (u16 ids, 1256/1257 at 0x80109F0A, title 1160/1161 at 0x80109E0E) is the special-screen
  file list; find its reader (not a plain lui/addiu of that address) to get the credits entry point.
- Memory card: `warp_all.py card_save` saves a New Game (menu_save route + OK) to work/states/save1.mcd; entries
  marked `card` run with it. With a save the title cursor starts on LOAD. APPENDIX then shows "GROW LANSER /
  AORI's APPENDIX ROOM / Now Closing" (graphics, already English) and goes back: the room itself (G4) needs a
  cleared-game save (flag unknown).

Older notes:
- Story points from 休暇8明け on (and Gevel, after, celebration) show "Please Change Disc 2" with
  "DISC 2に交換してください" (graphics + font text: add to the graphics list). Booting disc 2 shows "Please Change
  Disc 1": New Game needs disc 1, so a warp has to change discs mid-run.
- Disc check (verified by disassembly): `0x80054968` = CdSearchFile(names[gp+0x724]) over `\SLPS_023.80;1` /
  `\SLPS_023.81;1` (EXE RAM 0x8001294C, 15 bytes each); 0 = right disc.
- Tried: `PCSX.CDRom.openLid(); setIso(disc2); scheduleCloseLid()` at the prompt: the prompt stays (libcd's
  directory cache? the game may also want the lid seen open for longer). Stubbing 0x80054968 to return 0 in RAM
  passed the check but the run hung on black right after (frames stop). Data LBAs match between discs except
  FTIM.DAT (91378 vs 91410). Next ideas: hold the lid open for ~60 frames before setIso/closeLid; or stub the check
  and also patch FTIM's CdlFILE entry; or find what the black hang waits on (likely a CD read).
- Title LOAD and APPENDIX bounce back to the title without save data on the card: needs a memory card fixture
  (save from a warp: menu_save) and `--sav`.

## Emulator notes
- `--debugger` runs (exec/write hooks) stall after a while on scene loads; use them only for short traces.
- Loading a savestate taken mid-scene hung at the next CD read (probably the same voice wait); warp from a cold
  boot instead.
