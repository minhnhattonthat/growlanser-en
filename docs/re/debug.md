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
- `jump E:0xOFF` in scenes.txt: `tools/debug/vmjump.lua` (needs --debugger, warp_all adds it) sets the event VM's
  pointer (a0 at the dispatcher 0x8003AA3C) to that offset of SCEN entry E once, after frame 1600: reaches one
  handler (an NPC, a shop, a tutorial) without walking. Byte-scan a scene's script for an op to find OFF.
- MAP pairs: every field/screen map comes from (area, sub) through the table at 0x80100A10 into gp+0x4BA
  (0x80113D96), loaded by 0x8001DC38 -> 0x80018E58(pair). Area 84/85 = special full screens (tutorial picture
  85/6 = pair 575, credits 85/16 = 626). `tools/debug/maplog.lua` logs every pair load with its caller.

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
  Ending: scene 11 area 81 sub 0 (ティピの日記, the epilogue; scene 120 links to it) on disc 2: lands, then mashing
  Circle runs the diary and the portrait-over-sky epilogue (work/qa/ending1, f8100+). Wrong lead, dropped: the u16
  list at EXE 0x80109500 is not a special-screen file list but per-area field graphics: byte table 0x801083B0
  (83 areas x 10: u16 base, 8 sub -> record), records 0x801086F0 (16 bytes: 6 x u16 (count<<12 | start) into the
  list), reader 0x80068EF0 (area gp+0x8fa, sub gp+0x8fe); ids go past 1312, so they are not MAP.DAT entry numbers.
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

## Game over (warp `gameover`, phase 8 session 9)
- Unit records 0x801929CC + k*0xE4 (k 0 = hero), x/y +0x2C/+0x2E, HP +0x30, max HP +0x32 (tutorial battle RAM
  dumps: HUD 26 -> 23 on a Gel hit). The records at 0x80192AB0 are another copy: poking them does nothing.
- HP 0 by poke alone ends nothing: the death check runs on a hit. `tools/debug/kill.lua` holds the hero's HP at 1
  from KILL_AT; the tutorial battle (check menu 6 / 0) needs the walk left (240 + 900 frames) to meet the Gel, and
  Circle every 66 frames (`6 circle*250/60`): at every 36 frames the hero kills the Gel before it hits.
  Game over at ~f9500, still up at f11000.

## Appendix room (G4, phase 8 session 9, unsolved)
- Clear save fixture: `credits` warp on disc 2 with `--sav tools/pcsx/memcard1.mcd --state-every 3000` runs to
  "fin" (~f30300), then クリアデータをセーブしますか？ -> slot list -> OK/CANCEL box (CANCEL default). From the f30000
  state, route `6 up;30 -;6 circle;60 -` x25 saves it (work/qa/clear3/memcard1.mcd -> work/states/clear.mcd, slot 1
  "ＰＬＡＹＥＲ"). The emulator runs this stretch slowly: ~31k frames took >5000 s.
- A clear save alone still shows "Now Closing". Unlock flags (PS cheat codes, ds-cheat.boy.jp): GL chips cards
  0x801144D4-D6, music mode 0x801144DA, event CGs 0x801144E4-E7; also 0x801144FD. 0x800AD544 copies them from the
  save data (+0x50, +0x44, +0x54, +0x45) on APPENDIX. `tools/debug/appendix.lua` holds them: the room then shows four
  awake Gels and the label "GLチップスカード入れ (非売品)" (top-left cursor), e.g. work/qa/apx10 f2160.
- The room ignores every pad button (d-pad, Circle, Start, L/R...) and returns to the title ~200 frames after it
  appears, on the JP disc too (work/qa/apx_jp), so it is not a patch bug. It loads SCEN entry 245 (f2054) and entry
  143 into the MSYS buffer 0x80141778 (f2104): the room is script-driven. Next: read SCEN 245's script
  (tools/scendump.py) for the input/exit logic, or find the cursor variable and poke it to show the other labels.
- Session 10: the save data at memory card block +0x200 is what 0x800AD544 reads (a0; +0x44 music, +0x45 cleared
  = gp+0xC21, +0x50 cards, +0x54 CGs). Editing those bytes makes the save 破損データ (a checksum, not a plain byte /
  u16 / u32 sum over block ranges; a normal in-game save doesn't write these flags, so the game can't fix it). Same
  effect without the checksum: set the flags once right after the copy (exec hook 0x800AE77C, debugger run); the
  room still exits after ~200 frames and ignores input, so holding the flags every frame was not the cause.
- Title warps: `pick 2` fires before the title menu takes input (it opens LOAD); the title_appendix route recovers
  with cross / down / circle.

## Emulator notes
- `--debugger` runs (exec/write hooks) stall after a while on scene loads; use them only for short traces.
- Loading a savestate taken mid-scene hung at the next CD read (probably the same voice wait); warp from a cold
  boot instead.
