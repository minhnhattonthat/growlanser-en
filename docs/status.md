# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 6. Translate: not started (phase 5 done 2026-11-18; width gate in docs/windows.md, fit lint
  `tools/fit.py`). Last build: 2026-11-18 `build.py --marker`, both discs (disc 1 bin sha1 6818b3d7...), smoke ok
  on both, 63/63 warps landed (work/qa/marker2), dialogue VWF clean across pages (work/qa/nt_c).
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
  - Phase 5 done (details docs/re/text.md "Text drawing and the English VWF"): English = letter pairs in one
    16-bit code (`tools/enfont.py` EnCodec, PAIR 0x800 + i<<7 + j; "・" stays game glyph D1), font `font/en12.txt`
    (own design, MIT; caps rows 2-9, x-height 4-9). `asm/vwf.asm` hooks both glyph routines of the printer
    (normal 0x800711E0 at jal 0x8006F3A8, double 0x80071650 at 0x8006F49C), per-canvas x slots, code in font cells
    0x6A0+. `tools/insert.py` builds SCEN.DAT (sections rebuilt, archive re-laid), MSYS (in place; magic+skills
    share subfile 7), EXE tables (string heap incl. free kanji cells, getters untouched) + armips; `build.py
    --marker`, `--qa F.tsv --out D --disc N` stress builds; `tools/stress.py` ruler files. Tests: test_vwf (unicorn,
    `tools/vwfemu.py`), test_insert (jp identity, marker EXE read-back).
    Typewriter fix: dialogue printed one code per frame into a 1-cell window, so every pair sat in its own 12 px
    cell (the "0. 186" gap; pairs wider than 12 px clipped). vwf.asm now branches both typewriters (0x80065444,
    0x800658F0) to the game's page-at-once path; found with `tools/debug/vwflog.lua` (exec hooks, --debugger).
    Width gate: docs/windows.md (measured: dialogue/portrait/choice 24 cells x 3 lines, name tag 144 px, help and
    descriptions 24 x 3, item/spell names 8 cells, config labels/values 8 cells; guesses: skills, classes, units,
    places, other sys text, double size). Glyph torture line ok (work/qa/s5). Fit lint `tools/fit.py` (+
    tests/test_fit.py, part of check: every `en` must fit; guesses only warn). New warps gear_items/equip/status/
    spell (check-menu item 0 fills the lists). Non-text: exe.sys.0000-0004 kept JP (`insert.KEEP_JP`, full-width
    punctuation still in the font); exe.places.0006 is `{s:0010}` (the player's territory name): copy as-is.
- **Next (phase 6, translate):** follow the skill's references/translation.md (batches work/tl/, translator and
  reviewer agent types, glossary.md, D1-D8 in docs/decisions.md). Budgets: docs/windows.md; every batch must pass
  `tools/fit.py`. English must wrap by hand ({n}), max 3 lines per {p} page in dialogue; no `# @ \ ^ \` { | }`.
- **Before phase 7 (engine, found in phase 5):** MSYS descriptions have almost no slack (one 4-line ruler in
  items, or 3 rulers in magic+skills, overflow `insert.MSYS_LIMIT`): grow the subfiles (sector table 0x8001273C,
  count table 0x800126BC, load buffers 0x80117B98 / 0x80141778). SCEN entries grow with English: find the scene
  RAM cap. Name entry screen still uses legacy full-width letters (12 px each).
- **Width rows to confirm in the phase 8 tour:** skills, classes, units (battle UI: bt_* warps land before the
  battle starts; Circle alone does not start it), places (world map), battle messages, shop, inn, save screen,
  double-size text.
- **Debug-tool gaps to grow later (phase 8):** disc 2 story points (休暇8明け on, Gevel, after, celebration;
  parked `#-` lines in scenes.txt, attempts and next ideas in docs/re/debug.md "Disc 2"); title LOAD/APPENDIX
  need a memory-card fixture; shop, inn, save screen in the field, level-up, game over, endings
  (the check menu's 祝賀会以降 / "誰と成功した？" flow), credits, arena (闘技大会), FC check details. Field-menu
  submenu items are reached by index; confirm which index is which when the menu is translated. Scene ids warped
  directly (`SCENE='scene N'`) run on the New Game map unless area/sub is given; correct maps per scene need a
  full VM parse (op lengths partly known).
- **Open bugs:** none. (The message-speed config option no longer does anything: text prints a page at a time.)
- **Waiting on the user:** nothing (all once-per-project questions answered in docs/decisions.md).
- **Engine notes:** pair coding costs ~1 byte per English letter (JP: 2 bytes per character), so sections grow
  roughly by the English/JP character ratio / 2. Scene entries are packed back-to-back in RAM: find the
  allocator/cap before English text grows them. The dialogue box takes ~50 English characters per line.
