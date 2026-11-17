# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5. Engine spike + marker build in progress: VWF and marker build done, width gate partly measured.
  Last build: 2026-11-18 `build.py --marker` (build/disc1 b168554b..., disc 2 built earlier the same day from the
  pre-slot VWF: rebuild both), 63/63 warps landed on the marker build (work/qa/marker), English shows everywhere
  text is drawn.
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
  - Phase 5 so far (details docs/re/text.md "Text drawing and the English VWF"): English = letter pairs in one
    16-bit code (`tools/enfont.py` EnCodec, PAIR 0x800 + i<<7 + j; "・" stays game glyph D1), font `font/en12.txt`
    (own design, MIT; caps rows 2-9, x-height 4-9). `asm/vwf.asm` hooks both glyph routines of the printer
    (normal 0x800711E0 at jal 0x8006F3A8, double 0x80071650 at 0x8006F49C), per-canvas x slots, code in font cells
    0x6A0+. `tools/insert.py` builds SCEN.DAT (sections rebuilt, archive re-laid), MSYS (in place; magic+skills
    share subfile 7), EXE tables (string heap incl. free kanji cells, getters untouched) + armips; `build.py
    --marker`, `--qa F.tsv --out D --disc N` stress builds; `tools/stress.py` ruler files. Tests: test_vwf (unicorn,
    `tools/vwfemu.py`), test_insert (jp identity, marker EXE read-back).
- **Next (phase 5 width gate, docs/windows.md):** measure the rows still "to measure": help line (shot already in
  work/qa/s2/title_config), list fields for item/magic/skill/class/unit/place names (debug start has empty lists:
  use dbg_params / a check-menu option that gives items, or `bt_*` battle UI), descriptions (msys), config labels,
  battle messages, a portrait dialogue box if one exists, the double-size text path (never seen on screen yet).
  Then the glyph torture line (all ASCII + double spaces) in a dialogue box, then write the fit lint against
  docs/windows.md (simulate pairs: each pair must start at x <= 12 * (W - 1)). Non-text candidates still to
  confirm: exe.sys.0000-0004 (kept Japanese, `insert.KEEP_JP`), names/units slots 0, 0x10, 0x131, places slot 6.
  Not yet checked: scene entries grew (pair coding keeps markers the same size as the JP; real English may grow
  SCEN entries: find the scene RAM cap before phase 7), name entry screen (legacy full-width letters, 12 px each).
- **Debug-tool gaps to grow later (phase 8):** disc 2 story points (休暇8明け on, Gevel, after, celebration;
  parked `#-` lines in scenes.txt, attempts and next ideas in docs/re/debug.md "Disc 2"); title LOAD/APPENDIX
  need a memory-card fixture; shop, inn, save screen in the field, level-up, game over, endings
  (the check menu's 祝賀会以降 / "誰と成功した？" flow), credits, arena (闘技大会), FC check details. Field-menu
  submenu items are reached by index; confirm which index is which when the menu is translated. Scene ids warped
  directly (`SCENE='scene N'`) run on the New Game map unless area/sub is given; correct maps per scene need a
  full VM parse (op lengths partly known).
- **Open bugs:**
  - VWF gap after the first pair of a typewriter dialogue line: newgame shows "0. 186 The qu" (marker
    "0.186 The qu", ~4 px gap = resync to col 1 * 12). Per-canvas slots did not fix it. RAM dumps every 4 frames
    (`emu.py ... --script warp.lua --var SCENE='newgame' --script $SKILL/scripts/lua/probes/ramdump.lua --var
    RAM_EVERY=4 --frames 3000`, then `python tools/debug/vwfprobe.py slots DIR`) show the dialogue canvas slot
    (base 801C6278) at x 8 -> 10 -> 12, col 1, over frames 2480-2488, then never changing although the rest of the
    line appears; `vwfprobe.py readers` finds no other font reader or caller. Next: find what draws the rest
    (watch writes to the canvas rows, or log a0/a1/a2 per vwf_draw call into a RAM ring buffer from the asm);
    suspects: the printer redraws from the line start each frame on a second canvas whose base equals...,
    or the first pair takes a different path (kinsoku/line-start check calls with col 1 twice).
    The debug menu (scene 18, drawn at once, no typewriter) renders perfectly.
- **Waiting on the user:** nothing (all once-per-project questions answered in docs/decisions.md).
- **Engine notes:** pair coding costs ~1 byte per English letter (JP: 2 bytes per character), so sections grow
  roughly by the English/JP character ratio / 2. Scene entries are packed back-to-back in RAM: find the
  allocator/cap before English text grows them. The dialogue box takes ~50 English characters per line.
