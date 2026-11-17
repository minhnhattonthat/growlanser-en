# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5. Engine spike and marker build not started (phase 4 extract done 2026-11-18). Last build:
  2026-11-18, no patches, byte-identical to rom.sha1 (all 3 tracks), smoke ok on build/disc1.
- **Done:**
  - Step 0: template, tools fetched (PCSX-Redux nightly 31789, SCPH-5500 BIOS, mkpsxiso 2.30, armips 0.11.0 in
    `tools/`, gitignored), rom.sha1 (3 bins), check + pre-commit hook, guard hook, boot route `tools/routes/boot.txt`
    (ends on CONFIG), New Game route `tools/routes/newgame.txt`. Not proven: GUI keyboard input (headless only).
  - Phase 1 recon: docs/re/text.md (encoding, font, tbl, control codes, SCEN.DAT, EXE/MSYS text, scene load, file
    reads), docs/re/graphics.md (Japanese graphics G1-G8).
  - Phase 2 debug tool (docs/re/debug.md): `tools/debug/warp.lua` warps from a cold boot to any scene id (RAM patch
    of the New Game code: scene request 0x80113D66, map area/sub), forces voice off (headless XA voice hang), detects
    the title by RAM (gp+0x28C = 8). Scene 18 is the developers' check menu: story points (仕官話し, 休暇1-11明け,
    Gevel, after, celebration), 16 event checkpoints, 14 event battles, 5 dungeons, face/unit/param/name screens.
    `tools/debug/scenes.txt` (63 active entries) covers title + config, New Game prologue + home, the check menu
    screens incl. name entry, story points 仕官話し..休暇7明け, all 16 event checkpoints, 14 event battles,
    5 dungeons, the field menu (Select) with each top-level item, save screen and config. `tools/debug/warp_all.py`
    runs them all (proof shots in work/qa/warp/<name>/final.png, sheet*.png, results.tsv; `--states` regenerates
    work/states/). Last run 2026-11-18: 63/63 landed, every proof shot read (sheets 1-4).
  - Recon helpers: `tools/scendump.py` (scene text / summary), `tools/scenelinks.py` (scene-change ops 78/7A, noisy),
    `tools/vmstatic.py` + `tools/vmops.py` + `tools/debug/vmtrace.lua` (VM op lengths), `tools/debug/reqlog.lua`,
    `scenelog.lua` (CD request / scene-load traces, need --debugger).
  - Phase 3 identity build: `build.py` unpacks with dumpsxiso if `work/discN/tree` is missing (tree is never written),
    writes `build/discN/layout.xml` with absolute sources (patched files go to `build/discN/files/` via `patches()`),
    runs mkpsxiso, splits disc 2 at track 2's INDEX 00 into the Redump Track 1/2 bins, copies the original cue.
    `build.py --identity` (test `tests/test_rom.py` Identity) proves all 3 tracks byte-identical, ~6 s.
  - Phase 4 extract: `tools/extract.py` -> `script/scen/sNNN.json` (245 scenes), `script/msys/{items,magic,skills}`,
    `script/exe/<table>` (10 EXE string tables); 27,177 entries (247 empty, 2,859 `unref` choice lines). Pool
    codec `tools/textsec.py` (split / build section or table, pad rule). Tests (`tests/test_text.py` Script):
    script/ matches the disc and every pool rebuilds byte-identical from `jp`; EXE 0xE2138-0xE85C8 and MSYS
    0x42800-0x49E14 fully covered, no text outside; pad rule; disc 2 text files identical to disc 1.
- **Next (phase 5, engine spike + marker build):** `extract.pool_bytes(doc, "en")` rebuilds a pool from English;
  wire it into `build.py` `patches()` (SCEN entries regrow -> rewrite the SCEN.DAT sector table; MSYS sections:
  find how the game locates them first; EXE pools: re-point the 10 getters if they move or grow). VWF/font decision,
  marker build `[id]` per entry, width gate. Non-text candidates to confirm in the marker build: exe.sys.0000-0004
  (single punctuation / ‥‥, maybe kinsoku or padding), exe.dict (F4xx dictionary: English can drop F4 codes and
  write words out), names/units slots 0, 0x10, 0x131 and places slot 6 (RAM buffers, never drawn from the table).
- **Debug-tool gaps to grow later (phase 8):** disc 2 story points (休暇8明け on, Gevel, after, celebration;
  parked `#-` lines in scenes.txt, attempts and next ideas in docs/re/debug.md "Disc 2"); title LOAD/APPENDIX
  need a memory-card fixture; shop, inn, save screen in the field, level-up, game over, endings
  (the check menu's 祝賀会以降 / "誰と成功した？" flow), credits, arena (闘技大会), FC check details. Field-menu
  submenu items are reached by index; confirm which index is which when the menu is translated. Scene ids warped
  directly (`SCENE='scene N'`) run on the New Game map unless area/sub is given; correct maps per scene need a
  full VM parse (op lengths partly known).
- **Open bugs:** none.
- **Waiting on the user:** nothing (all once-per-project questions answered in docs/decisions.md).
- **Engine notes for phase 5:** every glyph is a 12 px cell and codes are 16-bit, so English text costs 2 bytes/letter
  in a 12 px cell: a VWF (or 2 letters per cell) is required, and SCEN sections will roughly double. Scene entries
  are packed back-to-back in RAM: find the allocator/cap before growing them.
