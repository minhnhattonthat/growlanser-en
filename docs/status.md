# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 8. QA in the emulator, next (phase 7 done 2026-11-19).
- **Phase 8 starts here:** follow the skill's phase 8 (tour routes through changed scenes via the debug tool,
  contact sheets, visual-QA verdicts with `qa_gate.py`, graphics text G1-G8 from docs/re/graphics.md, `inkbox.py`
  on choice/centred boxes, `textcover.py`). Things to watch, found in phase 7: (1) any other window the game sizes
  by code count (choice boxes, menus, battle messages, shop/inn): symptom = text cut at a column edge while the
  script line is longer; fix like the tags (zero-width 0x0800 padding) or the pre-parser (docs/re/text.md);
  (2) wait codes mid-line resume at the column, not the pixel; (3) width rows still guesses in docs/windows.md.
- **Phase 7 review fixes (2026-11-19, H:\translation\.harness\reviews\growlanser-en-phase7.md, all 5 Important):**
  (1) fit gate: test_fit fails on warnings too; unreachable fields use the JP-max lower bound (docs/windows.md),
  skills measured (status Circle page, work/qa/p8m/gs_ci), places popup width 12 + code-count frame from the
  disassembly (exe.places in insert.TAG_POOLS); 7 strings rephrased (D12). (2) test_insert
  English.test_scen_integrity: every SCEN leaf identical except text leaves, whose bytes before section 22 match.
  (3) write provenance: insert.patched(log=) records every EXE/MSYS write (heap ranges as construction writes)
  and test_romdiff passes them to romdiff; armips asserts insert.HOOKS original bytes and may write only there and
  in FREE_START-FREE_END; insert.hook_branches (test_hook_sites) finds no branch into a hook span. (4) batches
  check fails on missing English (one keep-list: insert.KEEP_JP / needs_english; the inserter raises too).
  (5) edge blanks restored in 576 entries (D13; full-width blank = game glyph 0x0000), checked by problems().
  Minor (short final lines) left for phase 9 polish.
- **Phase 7 (done 2026-11-19):** English build green: 68/68 warps land (work/qa/p7warp, sheets read), smoke ok,
  check.py green (romdiff vs `tools/allowed.txt`, fit lint, every pool read back). Pieces (docs/re/text.md):
  - RAM limits: scene slot 0x7000 (`insert.SCENE_SLOT`), MSYS buffer 0x80141778 20 KB then the heap (base kept:
    any heap shift is unsafe). Word dictionary for dialogue (`tools/dictenc.py`, codes 0x4800+, ~1080 entries).
  - MSYS descriptions Huffman+BPE packed (`tools/msyspack.py`, model 3.2 KB in the EXE heap): items 37 KB of pairs
    -> 15.7 KB; the six description getters jump to asm `msys_get`, which unpacks into 16 slots at the top of the
    buffer (pointer cache). Test: test_insert English.test_msys_getters runs the real getters under unicorn for all
    476 refs. In game: spell help (gear_spell) and item status (new warp gear_itemdesc: Square on an item) correct.
  - Message pre-parser measured 1 column per code, so pages with dictionary codes were cut ("I want you to have",
    "Oh, Big"): asm `vwf_measure`/`vwf_width` (test_vwf_width). Name tags are code-count wide ("Ma" for "Man"):
    `insert.Encoder.tag_pad` adds zero-width codes. Both verified in the newgame prologue (work/qa/p7dlg4, p7dlg6).
  - RE helpers: `tools/gpscan.py` (gp+offset users), `tools/lenloops.py` (length loops), `tools/straddr.py`
    (EXE string RAM address), `tools/debug/measurelog.lua` (parser trace).
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
- **Phase 6 setup (done):** `tools/batches.py` (split / check / merge / wrap; translators write running English,
  the wrapper adds {n} by pixel width and {p} every 3 lines in dialogue; checks codes incl. `[XXXX]` icons, glossary,
  honorifics after glossary names, fit lint), `tools/tl_run.py` (codex exec read-only per batch: translate -> check
  (3 fix rounds) -> review (docs/reviewer-brief.md) -> fix Critical/Important -> merge; Minors -> docs/polish.md;
  `run.lock` = one runner at a time; logs work/tl/log, reviews work/tl/reviews), `tools/termscan.py` (terms pass;
  82 terms added to glossary). docs/translator-brief.md, docs/style-reference.md, docs/synopsis.md (codex, from
  per-scene summaries in docs/scenes/), D9-D11. Item names are hard-capped at 96 px: 15 key items shortened in b003
  (e.g. "[02A4]Search Warrant", "Palsy Ward Tome"); widen the item field in phase 7 if possible, then restore.
- **Phase 6 (done 2026-11-18):** all 204 batches merged (work/tl/bNNN.done), 0 entries without English, lint 0
  problems on 27,177 entries. b112/b114/b122/b123/b156 (Critical/Important left after 3 codex rounds) fixed by hand
  from their r2 reviews. `{s:0127}` is 目 drawn from the names table ("Eye"), not a name: `batches.GLYPH_VARS`
  lets English drop it (brief + glossary note); 9 merged lines fixed. Wave-2 term conflicts picked by majority/table
  spelling (glossary section "wave 2"), losers fixed; `normalize.py --majority 3 --write` gave 774 repeated strings
  one English. Reviewer Minors (486 lines) are in docs/polish.md for phase 9.
- **Optional, carried from phase 7:** item-name width (restore the 15 shortened key items if the field widens).
  Name entry screen still uses legacy full-width letters (12 px each).
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
