# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 9. Release in progress (session 20). **Next:** `tools/release.py` (all QA gates green on build 8528a8c2).
- **Phase 9 session 20 (2026-11-21): release-candidate QA.** Build disc 1 8528a8c29559426023a9fc2564f9321275274779,
  disc 2 T1 cb1fd0d5833de94407760f9c3572d73af7a5f9a2, T2 485017be (unchanged), copied to work/qa/tourbuild.
  Re-tour 83/83 + credits alone (exit 124 at its frame cap after the roll, as in s17) and stress 10/10 on b9fad4d1;
  275 tour + 43 stress sheets changed, all re-verdicted by plugin visual-qa agents (codex out of credits until
  11-26), dispatch work/qa/dispatch_s20.md. 1 issue: msys.magic.0010/0017/0021/0022 lacked "that" ("Attack magic
  solidifies...") -> reworded, refit (3 lines each), rebuilt; stress_skills/stress_spell re-run on the fix, ok. Only
  MSYS.DAT + its EXE tables changed after the tour (SCEN/MAP identical, build/strings.tsv differs in those 4 ids
  only), so the tour sheets stand; manifests re-inited with --build on 8528a8c2. 44 stale stress sheets from the s15
  run (longer runs, old verdicts) moved to work/qa/stress_stale_s15 and dropped from the manifest. Cover: full
  cover.py rerun into work/qa/cov (old in cov_s17; hashes had all moved), `textcover` exit 0 (22249 shown, 1822
  waived). Gotcha: cover.py 0-279 at --jobs 4 took ~1 h per 45 scenes; three range processes in parallel finish in
  ~1 h. Not fixed (cosmetic, noted by vqa): name tags sit left in their box (code-count width, accepted since s2);
  "Target: Group." on Grow Protect vs "1 ally group" elsewhere (JP says グループ); scen018 dev-menu row with "-" vs
  "--"; scen018.0099 "??" (JP too).
- **Phase 9 session 19 (2026-11-21): story pass done, polish done.** Story gate green: `qa_gate check
  work/qa/story/manifest.tsv work/qa/story/verdicts` exit 0 (40/40; work/qa/story/verdicts/final_s19.tsv). c06-c17
  story-reviewed (plugin reviewer agents), c01-c05 diff-reviewed after polish round 1 (new tools/story_diff.py: changed
  lines since a commit, `--ctx N`), then all 40 diff-reviewed after round 2 (vs 12990ab). Fixed: 1 Critical + more
  Julian pronoun leaks (077.0111, 260.0072, 016.0191), Importants (030.0258, 037.0115, 040.0264, 059.0049, 153.0062,
  191.0025, 198.0038). Polish round 2 p12-p15 (221 ids: 197 fixed, 24 waived) merged; docs/polish.md has no open line.
  Global fixes: 117 choice lines lost their final period (`batches.py choices`, now a problems() check too); dialogue
  pages break at sentence ends (batches.page_flow in the wrapper; `rewrap.py --pages` re-paged ~100 entries; runs with a
  hand-made {n} layout are skipped: a first pass flattened the scen001.0174 legend, restored); Misha's お兄さま = "Big
  Brother" everywhere; " -san" after name variables dropped (s041); skill trigger labels "On normal attacks.";
  bookshelf titles one per line (s069); "{FFEB} Elm." (FFEB prints a number; batches' edge lint treated it as silent,
  fixed). Colon glyph polish line waived (same dot as "."). Build before the last hand fixes: disc 1 4e5b4bd2, smoke ok;
  REBUILD before touring. Text changes invalidate the tour/stress manifests (build hash) and cover hashes: re-tour
  (`tools/debug/warp_all.py --cue build/... --out work/qa/tour` per the s17 notes), `qa_gate init` + vqa changed sheets,
  stress warps the same, cover.py rerun (or `textcover --runs-for` on the changed ids), then `tools/release.py`.
  Open, non-blocking: "Rolandia army" vs "Rolandian army" (s103 uses the adjective); arena rank wording (s111) left as is.
- **Phase 9 session 18 (2026-11-21).** New: `tools/story.py` (chapter files from docs/synopsis.md, 40 parts in
  work/qa/story/chapters; manifest work/qa/story/manifest.tsv), `docs/story-reviewer-brief.md` (plugin reviewer
  agents, one per part; Minors -> docs/polish.md "Story pass Minors"), `tools/polish.py` (split open polish lines
  into work/tl/pNN.tsv for translator agents per `docs/polish-brief.md`; `merge pNN` = batches merge + tick),
  `tools/release.py` (all gates -> xdelta per changed .bin + re-apply check -> release/Growlanser_EN_vX.Y.zip with
  docs/release-readme.txt), README.md filled (base hashes, status table). jp_left byte scan is noise here (u16 glyph
  text, packed English): release.py checks the script instead (leftover_jp) + textcover for runtime.
  Story verdicts so far: see work/qa/story/verdicts (c01_1..c03_6 done; Importants fixed: scen019.0192 "My
  teacher?!", scen029.0309 "Uncle, ..."; c03_4's "-san after {s:} variable" Important overruled by glossary rule).
  Polish: first round p01-p08 (435 ids, the lines open before the story pass) by plugin translator agents, merged
  with `polish.py merge` (p01-p04: 223 fixed, 16 waived); p09 = global system-message pass (tools/sysmsg.py, 62
  lines); p10 = c05_1's 3 Importants. batches.py check_batch no longer strips U+3000 (edge "　{n}" lines failed).
  Polish round 1 done: p01-p08 all merged (~430 fixed, ~25 waived, reasons on the ticked lines); p11 = 2 lint fixes
  (scen113.0108 choice prompt, msys.magic.0027 widow). `batches.py check`: 27177 entries, 0 problems; test_fit OK.
  49 polish lines open (story Minors, p08 siblings, 3 id-less). Story reviews done on the PRE-polish text: c01_1
  c01_2 c02_1 c02_2 c03_1..c03_6 c04 c05_1 c05_2 (13/40; Importants fixed), verdicts moved to
  work/qa/story/verdicts_pre_polish/ because the polish merges changed 39/40 chapter files (manifest re-inited on
  the current text). **Next:** for those 13, a diff review (old text: `git worktree add ../gl-old 40db776`, copy
  tools/story.py into it (40db776 predates it), run `python -X utf8 tools/story.py` there -> ../gl-old/work/qa/story/chapters; diff per chapter; a reviewer
  agent checks only the changed lines in context; write `fixed`/`ok` verdicts into work/qa/story/verdicts) or a plain
  re-review; then review c06_1..c17_2 (27 left, 4 at a time, docs/story-reviewer-brief.md); then a second polish round
  for the "Story pass Minors" section (`polish.py split` numbers on from p11; tools/polish.py ids for id-less lines:
  vqa-s15 msys.skills trigger label, vqa-s15 font colon, story-c01_2 cipher check); recurring mid-sentence page
  breaks in story Minors: consider a wrapper rule (prefer a page break at a sentence end). Text changes invalidate tour/stress manifests (--build hash) and cover hashes: re-tour changed
  scenes or `qa_gate waive`, and rerun cover.py before release.py.
- **Phase 8 session 17 (2026-11-21): phase 8 gate green.** Build disc 1 a5c879ef57e23f55c749741ccbbef7456ee4e690,
  disc 2 T1 0742c53077f3bca40565943f6d4776a378ac7fc9, T2 485017be606e6b517760076c9b05ceba89f5cdba; smoke ok;
  check.py 52 tests OK. scen014.0185 "Take it" centring committed (batches.EDGE_FREE entry). Re-tour 84/84 (credits
  alone) on a5c879ef: `qa_gate check work/qa/tour/manifest.tsv work/qa/tour/verdicts` exit 0 (303 sheets; 5
  changed: ev_battle001/sheet_2 centred, inkbox 112/113; gear_equip = NPC timing; verdicts/recheck_5.tsv). Stress
  10/10: all 46 non-boot-identical sheets changed (field NPCs move run to run), reviewed by hand, all ok
  (work/qa/stress/verdicts/recheck_s17.tsv); `qa_gate check work/qa/stress/...` exit 0. Text coverage: cover.py
  scene 14 rerun + x18 (13 reruns) + x279 (7) into work/qa/cov; exe.items.0084 "Hammer" waived like its neighbours
  (it used to match a scene string's hash); `textcover.py work/qa/cov build/strings.tsv --waive
  docs/text_unshown.tsv` exit 0 (22248 shown, 1823 waived). work/qa/tour_prev/manifest.tsv renamed .retired.
  Gotcha: check.py takes ~15 min and batches check ~10 min now; a background run was reaped once on low memory.
- **Phase 8 session 16 (2026-11-21): pen gap fixed, final tour vqa.** (a) **Bug fixed (asm/vwf.asm):** a dialogue
  message prints its first code alone (print wrapper called from 0x80065E5C), then the rest from the page path
  (wrapper calls at 0x80065630 / 0x80065AF4), again after each wait code; the new-string flag resynced the pen to
  col*12 ("We  lcome"). vwf_newstr now flags those two callers -1 and vwf_draw keeps the pen when the column matches
  (row ignored: FFFB resumes one line lower with row 0). fit.py no longer snaps x at wait codes (the resumed print
  still wraps on a code's end: "Such a fra/il", work/qa/waitwrap.tsv). Tests test_vwf test_continuation_keeps_pen,
  test_newstr_flags; docs/re/text.md. Commit 7a86fe9. (b) Build 6a97dc86acd5f9f76f6923c92bc8173e9c51dc9d (disc 2 T1
  3b54023b80c9f8b8b31dd2acc0885f3089ab7f0b): re-tour 84/84 + 10 stress warps, qa_gate init both; vqa (plugin
  visual-qa agents; codex out of credits until 2026-11-26) of all 214 tour + 3 stress sheets without a verdict:
  1 issue: ev_battle001/sheet_2 f2640 scen014.0185 "...Take it..." 17 px left of centre -> fixed in script (8
  full-width spaces + 1 space; only that string's hash changes, checked with build --out work/qa/bnew). (c) Full
  cover.py rerun on 6a97dc86 into work/qa/cov (old run moved to work/qa/cov_s15; dictionary re-encoding had made
  17133 hashes stale).
- **Phase 8 session 15 (2026-11-21): stress complete, final tour.** (a) Party > 1: warp stress_party (story point
  vac07, 5 units, status paged). Menu nameplates are art (debug.md "Inventory"), so no "hero name copy" exists.
  (b) Long names: warp stress_name (8-cell hero name + territory name screen). **Bug fixed:** default territory
  name drew "MY ※CI TY": now full-width ＭＹ ＣＩＴＹ (D18, KEEP_JP) and glyph 01C2 kept out of insert.FONT_FREE;
  scen120.0001 "DATA[0793]BANK" -> "DATA BANK" (0793 is a vwf.asm cell); new test
  test_insert.test_raw_codes_not_reused. Build 7521ea80081d577e93a8a53af97845cf5ce7321d (disc 2 T1
  2408c74ca461e87130b03329b20fc750c52a18e5): stress gate 90 sheets ok; tour run (credits warp times out under
  CPU load: run it alone). (c) **Bug fixed (tour chunk 004):** wait codes mid-line: the resumed print snaps to a
  column and wraps on a code's end (scen070.0017 left "a" alone on line 2). fit.lint models it (test_fit
  test_wait_codes); new tools/rewrap.py re-flowed 66 entries; scen093.0181 rewritten with waits at line ends.
  Polish added: skill trigger label wording, colon glyph. Built: disc 1 4c647f4ca917183e61acd1ef619b264b26e74c73,
  disc 2 T1 559f33299192429a665b065dd90c5f4cf9d84a9d, smoke ok (not yet toured; tour + stress sheets are on
  7521ea80). Tour vqa so far: chunks 000-005 verdicted (2 issues: 004 dn_glocian/sheet_2 = the wait wrap, fixed
  above; 005 dn_mystery/sheet_2 = open bug below). Tour sheets are deterministic (same build -> same sha1).
  **Open bug (engine, asm/vwf.asm): pen gap after a message's first code.** scen018.0134 (Dungeon Man, warp
  dn_mystery f2040) drew "Welcome   to" (dictionary word "Welcome" 41 px, then the pen snapped to col 4 = 48 px).
  Repro build: `build.py --qa work/qa/dictgap.tsv --out work/qa/bdict --disc 1` + warp dn_mystery: "We  lcome to
  my labyrinth." (gap after the first pair; lines 2-3 of the same message fine). Cause (inferred): the printer
  (0x8006E794) is entered twice for this message (first code, then the rest), and vwf_newstr's new-string flag
  makes vwf_draw resync x to col*12; the wait-code gap is the same mechanism. Most dialogue doesn't show it
  ("...Hmm" and "Surprised" fine): find which caller prints the first code alone (exec hook on 0x8006E794, log ra
  per call in dn_mystery), then skip the flag for that continuation (keep it for the item-list case, test_vwf
  test_new_string_resyncs). After the fix the wait snap may go too: then drop fit.WAITS' column snap.
  **Next after that:** finish tour vqa chunks 006-023 (re-init after the re-tour first: changed sheets only).
  Credits warp: a re-run was in flight on 7521ea80 at hand-back; rerun it alone in the re-tour.
- **Phase 8 session 14 (2026-11-20): stress spells + skills.** Spell/skill known bytes mapped (debug.md
  "Inventory": record + 0x3C + spell id, + 0x7C + skill id; list builder filter word sp+0xD8). The field spell
  screen (and battle Triangle menu) only ever lists Teleport + 5 heals; stress.lua now gives every unit all 34
  spells + 63 skills and forces the battle filter, so stress_spell pages all 33 battle spells. New warp
  stress_skills (status -> down -> Circle sub-list: spells then skills; 13400 frames). warp_all adds --debugger for
  stress warps. Skills 59-62 show next-table strings as descriptions: JP same, not a bug. vqa (3 chunks, plugin
  agents): description breaks fixed, no one-word last line and no label cut from its value (msys.magic 0004 0006
  0007 0010 0011 0013 0015 0016 0018 0019 0021 0024 0025 0029 0031 0033, skills 0006-0016 0024 0025 0045, items
  0042 0044) + new test test_fit.test_description_widows. Build disc 1 bc3d97dd88f3c6c30e6640696788aa8b0d95d263,
  disc 2 T1 69b54a5d6f359a3608d6e306736465a0d964fb5c. Stress gate: 74 sheets, init on bc3d97dd (stress_itemdesc
  etc. not re-run: their sheets show no changed text). Party > 1: this debug state's field party is the hero alone
  (check menu 9 = unit viewer); still open, with the field-menu hero name copy. Init gotcha: `qa_gate init` with
  several dirs keys ids to the first dir; use `init M work/qa/stress --glob "stress_*/*sheet*.png"`.
  **Next:** party > 1 (a story save or party list RAM), then re-tour + qa_gate + vqa + textcover on the final build.
- **Phase 8 session 13 (2026-11-20): stress saves, part 1.** Phase 8 gate items left: stress cases (this),
  re-tour + vqa + textcover on the final build. RAM mapped (docs/re/debug.md "Inventory"): item lists per
  category, quantities, money. New tools/debug/stress.lua (warp keyword `stress`, warp_all adds it): every item
  list filled with its category's ids, x9 (menu draws 1 digit: 99 showed "x9"), money 999999. Warps stress_menu, stress_items (pages every list),
  stress_itemdesc; manifest work/qa/stress/manifest.tsv (chunk 000 verdicts: 9 ok, 3 issue). **Bug fixed:** the
  item description's name tag clipped by code count ("Broadswo"): exe.items added to insert.TAG_POOLS (zero-width
  pad codes, as name tags); shot work/qa/stress_fix/stress_itemdesc. Build disc 1 32cd282d9c0826fc5965dd2d9b683bcb1a9201c4, disc 2 T1
  51961cca4d8506716371458d68bbf8956c20f10e, smoke ok. Part 2: stats held at max too (unit records are live in the
  field; debug.md "Inventory"); warps stress_status, stress_equip, stress_spell. Stress run on 32cd282d: 48
  sheets in work/qa/stress/manifest.tsv, 14 ok (chunk bf72..._000), chunks de96..._000-002 to verdict (one
  visual-qa agent at a time). Names: not on screen (the field menu's hero-name copy is unknown, debug.md);
  dialogue covered by the lint (fit.SUB_PX 96 = 8 cells). **Next:** finish the stress verdicts; open: full spell
  lists (spell-known flags), party > 1 on status, save/load screen with stress data. Then re-tour + qa_gate +
  textcover on the final build.
  Part 3: vqa found (a) item list long left names carried the right column's first letter ("Boomerang SwordD /
  ouble Edge"): pre-existing (same on an unpadded build), VWF pen continued across strings; fixed in asm/vwf.asm
  (printer-entry hook, docs/re/text.md); 8 regression warps pixel-identical to the tour except st_vac01 (sprite
  area only). (b) exe.items.0233 + scen041 kept JP glyph codes "Promise[028B..028E]" -> "Promise Pendant"
  (glossary). New warp stress_save (save screen after saving with stress data; no `card` keyword: it breaks the
  New Game landing). Build disc 1 32c60d517bd88e8decc40754b333e0bf5e37b598, disc 2 T1
  8e2f5c82fb8bf7d21fa50ea94ac39876e3660ecb. Stress chunks 0275..._000/001: 24 ok. New test
  test_vwf.test_new_string_resyncs. stress_save runs on a fresh copy of the blank card (warp_all, like card_save):
  a save without --sav landed in the shared tools/pcsx/memcard1.mcd once this session and broke landing (restored
  from work/states/blank.mcd; bad card in work/mcd_backup/memcard1_s13.mcd).
- **Phase 8 session 12 (2026-11-20): vqa on re-tour 6.** Re-tour 6 (84 warps, build e694af15, work/qa/tourbuild)
  -> qa_gate init -> 18 chunks of 12 by plugin visual-qa agents one at a time: 210 ok, 3 issue, all fixed
  (verdicts/recheck_4.tsv); `qa_gate check` exit 0. Fixes (build ab9f96a84322c9abbfdcf5171415a17dbd935b1e, disc 2
  T1 07e4918eaf320505a7af8d9ba102792ead1fc60f; smoke ok, check.py 46 tests OK; work/qa/fix9):
  (a) choice prompts that wrapped to 2 lines where JP is 1 (option scrolled out of the 3-row box): 24 shortened
  to one line (s008 s016 s018 s019 s038 s067 s069 s070 s112 s113 s120 s169 s213); new test
  test_fit.test_choice_prompts (prompts before "・" options only; built-in Yes/No dev prompts in scen018 not
  covered: none left with {n}). (b) scen001.0174/0176/0179 re-paged: pages end at sentence ends.
  Gate caveat: the tour ran on e694af15; current build differs by those text entries only. Re-tour (or `qa_gate
  waive` with reason) on the final build before release.
  Polish candidates (original Latin art, not bugs; ask owner): spell-screen nameplate art "RUISE" vs glossary
  Luise; item screen art "ACCESORIES"; field menu art SPELL/TACTICS vs our popups "Magic"/"Strategy".
  Non-bugs seen: captions mid-open/close ("Dutside tne...Cacin" = closing frame, work/qa/cap_bandits f002270
  reads right), name tag box before text, "NOW LOA" sweep, battle ring labels overlapping mid-rotation.
- **Phase 8 session 11 (2026-11-20): G5b + "morth".** (a) G5b done: credits cast line now "Player / PLAYER"
  (D17: default hero name kept full-width ＰＬＡＹＥＲ via KEEP_JP; atlas block lettered, credits.py player_label;
  graphics.md G5b; shot work/qa/g5b/run f011400). Hero name now shows in full-width glyphs everywhere (as a typed
  name does): the re-tour covers it. (b) "morth" = the caption box mid-open (box + text scaled narrower), not a
  bug: current build at the settled frame reads "month" (work/qa/morth f004080); added to the vqa brief's
  non-bugs. Build disc 1 e694af15c932ebf8ba05bef2b2159ad5408d80d7, disc 2 T1
  48411bb39e1a56bbbd2f9b6ae8f18815fa9b7f88. **Next:** re-tour (build changed; add tut_status), `qa_gate init`,
  vqa one chunk at a time (plugin visual-qa agents; codex out until 2026-11-26), then the phase 8 gate list.
- **Phase 8 session 10b (2026-11-20): text coverage.** `tools/debug/cover.py` (host mode, docs/re/debug.md "Text
  coverage"): every scene string through the real printer, `textcover.py work/qa/cov build/strings.tsv --waive
  docs/text_unshown.tsv` exit 0; EXE/MSYS table strings waived on new test test_exe_getters + test_msys_getters.
  Build extract for cover.py: `dumpsxiso -x work/qa/btree/tree -s work/qa/btree/layout.xml <build cue>`
  (rerun after each build). Item 3: no chapter-card art; world map not reached (docs/re/graphics.md "Still open").
  World map labels are art only, English in the original (graphics.md). Re-tour 5 on cf329b11: 84/84 landed,
  qa_gate init (52 sheets to verdict). Codex out of credits until 2026-11-26: verdicts by plugin visual-qa agents,
  one chunk at a time (5 chunks): 41 ok, 11 issue. Fixed (build 1271385f, work/qa/fix6): tag "LLM Magic Class
  Instructor" lost "LL" on the tut_status screen -> "LLM Magic Instructor" (6 scenes); scen088.0021 indent/break;
  scen232.0004 page break mid-sentence; credits cast names stamped at column <= 254 (page column 255 not shown:
  "Barc", "Oswalc"). Open then (both closed in session 11): (a) G5b credits "プレイヤー／" + player name (graphics.md "G5b"); (b) popup caption
  "One month later..." shows "morth": the n of pair "nt" loses its right stem in the popup only (vwfemu draws it
  right, canvas split col 12, x 0; dialogue "month" fine): find where the popup canvas loses a texel column.
  Then: re-tour (build changed), qa_gate init, verdicts.
- **Phase 8 session 10 (2026-11-19): G4 done.** Appendix room labels English (tools/appendixgfx.py, D16, docs/re/
  graphics.md "G4"): "GL CARDS (PROMO)", "VISUAL ROOM" from the sheet's own letters. In game OMAKE/1 at work/qa/g4
  f2200 (title_appendix warp + clear.mcd + one-shot flag hook, docs/re/debug.md "Appendix room"); OMAKE/2 offline
  only (room takes no input, JP too). Save editing: checksum unknown, see debug.md. Build disc 1
  cf329b110e3fca42dfc99e6b9e005aefd4cf198a. Tour gate still stale. Next: item 3 chapter/area cards, item 4 text
  coverage, then the re-tour (add tut_status) + qa_gate init + vqa.
- **Phase 8 session 9 (2026-11-19): game over.** Warp `gameover` (tools/debug/kill.lua holds hero HP at 1 in the
  tutorial battle; warp.lua route step `N key*R/IDLE` = custom idle between presses). Game over art is English in
  the original (docs/re/graphics.md, docs/re/debug.md "Game over"); shot work/qa/go2/gameover. No build change.
  G4 appendix room partly reached (docs/re/debug.md "Appendix room"): clear save fixture work/states/clear.mcd,
  tools/debug/appendix.lua opens the room (GL chips label visible), but the room takes no input and exits after
  ~200 frames (JP too). Left: SCEN 245 script for its input/exit, then redraw G4 (MSYS ~0x7C000-0x84000).
  Sessions 8 and 9 were cut short by an account hold (2026-11-19 02:09 and 04:05 UTC), probably from many parallel
  Orca worker sessions: run one worker at a time, no fan-out agents, until that's clear.
- **Phase 8 session 8 (2026-11-19): G7.** G7 = Rosaria's LLM magic class tutorial status picture (MAP pair 575),
  English via tools/tutorialgfx.py (docs/re/graphics.md "Done"); new warp `tut_status` (scenes.txt `jump` keyword,
  tools/debug/vmjump.lua); tools/debug/maplog.lua, tools/spritesrc.py (dither-tolerant pixel -> texel mapper, slow;
  not needed in the end). scen001.0178/0179 now quote the grid labels. Build disc 1
  a00e301227a445a1081884bd3b76f64bda5a79eb, smoke ok, check.py 44 tests OK. Tour gate still stale (build
  changed); add tut_status to the re-tour. Session ended at the context limit: resume at item 3 (game over) below.
- **Phase 8 session 7 (2026-11-19): G5, G6, G8.**
  - G5 credits English (tools/credits.py, docs/re/graphics.md "Done"): 36 cast roles in the game's own Latin atlas
    font over the kept romanized actor lines; "Developed by CARRIER SOFT / Copyright ATLUS / CARRIER SOFT / Produced
    by ATLUS", (c) line "ATLUS／CARRIER SOFT 1999". In game: `warp_all.py credits --cue work/qa/g5build/...(Disc 1).cue`
    (both discs' cues must sit in one folder for disc 2 warps) -> work/qa/g5/credits f012000-f027000.
  - G6 = the credits' kana+Latin atlas, loaded but never drawn: nothing to do.
  - G8 FMV logo (tools/fmvlogo.py, needs Java + tools/jpsxdec): both movies show the logo twice (MOVIE0 764-823 /
    1525-1578, MOVIE1 755-820 / 1518-1556); subtitle masked + filled, jPSXdec partial-replace; build.py adds the
    STRs to disc 1 (cache work/fmv/en; delete MOVIE*.STR there to rebuild). In game: idle boot (attract movie from
    ~f4900) work/qa/g8boot3, logo at ~f8000 and ~f11050.
  - G7 (MAP.DAT 1150/1151 = pair 575): no warp loads it (all 82 warps with tools/debug/reqlog.lua, work/qa/req:
    reqlog `file=2 entry=N` = MAP pair N, MAP entry 2N; title = 580, credits 626-628). Its pieces look like a
    help/tutorial or game-over screen: find the screen that requests pair 575 (game over = a lost battle: poke
    party HP to 0 in a bt_* warp, or find the loader of pair 575 from 0x8001835C callers).
  - Build changed (MAP.DAT credits, disc 1 STRs): **tour gate stale** for the build hash only (no tour screen shows
    credits or FMV): re-tour + qa_gate init + vqa at the end of phase 8.
- **Phase 8 session 6 (2026-11-19): ending + credits reached.**
  - `ending` / `credits` in scenes.txt: scene 11 area 81 sub 0 on disc 2 (ティピの日記 epilogue) + mash Circle. JP
    run work/qa/ending2 (shot every 600): diary + portraits f8000-11000, CAST f12000-19200 (Japanese role／actor
    lines, romanized actor line under each), staff pages, last page 開発 キャリアソフト / 著作 アトラス／キャリアソフト /
    制作 アトラス + (c) line ~f28800. Run as `warp_all.py credits --cue <cue>` (~10 min).
  - Status lead "MAP.DAT 1256/1257 via EXE 0x80109500" was wrong (per-area field gfx table, docs/re/debug.md).
    G5 source still = MAP.DAT entry 1257 per the sweep: confirm with a VRAM dump on a CAST page (ppudump.lua
    DUMP_AT ~f13000, then vramsrc.py against MAP.DAT) before redrawing.
  - G8: jPSXdec v2.1 fetched to tools/jpsxdec/ (gitignored); running it was refused by the auto-mode permission
    check (new download). Needs the owner to allow `java -jar tools/jpsxdec/...` (see Waiting on the user).
- **Phase 8 session 5 (2026-11-19): re-tour, disc 2 + memory card warps.**
  - Tour 4 on build 82ef6e4c (work/qa/tourbuild now holds disc 1 and disc 2): 69 + 8 disc 2 story points + title_load /
    title_appendix, JP baseline for all in work/qa/tour_jp. vqa (work/qa/vqa4.log, vqa5.log): all ok except
    st_vac08/sheet_2 = popup open animation, JP the same (verdicts/recheck_3.tsv). **Gate green:** `qa_gate.py check
    work/qa/tour/manifest.tsv work/qa/tour/verdicts` exit 0, 264 sheets, build disc 1 82ef6e4ca34b30cabb268cb723949eaf0f80bb3d.
  - Disc 2 solved: `tools/debug/disc2.lua` (hold gp+0x724 = 1 on the disc 2 cue); scenes.txt `disc 2` keyword,
    warp_all.py picks the disc 2 cue. All 8 parked story points unparked and landing (docs/re/debug.md "Disc 2").
  - Memory card fixture: `warp_all.py card_save` -> work/states/save1.mcd; `card` keyword (title_load, title_appendix).
    APPENDIX with a normal save = "AORI's APPENDIX ROOM / Now Closing" (English art already); the room (G4) needs a
    cleared-game save.
  - `tools/debug/where.lua`: logs scene/map changes. Credits (G5) still unreached: 祝賀会以降 = scene 93, free-roam
    Grancil; ending follows the final tower. Leads in docs/re/debug.md "Disc 2".
- **Phase 8 session 1 (2026-11-19):** tools + first tour.
  - Tour: `warp_all.py --cue <build cue> --out work/qa/tour --shot-every 120` (tour mode = per-warp `--sheet`):
    68/68 landed, 224 sheets in work/qa/tour/manifest.tsv (qa_gate init, --build disc 1 bin); JP baseline
    work/qa/tour_jp (same command on rom/). Brief: docs/visual-qa-brief.md (Growlanser non-bugs).
  - Verdicts: `tools/vqa_run.py work/qa/tour` (qa_gate todo -> codex exec read-only per chunk, final message parsed
    into work/qa/tour/verdicts/chunk_*.tsv; a chunk missing ids is not written, re-run). Result: see "vqa" below.
  - Text coverage: `tools/strings.py` (also written by build.py as build/strings.tsv: id -> hash of the printer's
    words; 24,071 reachable strings) + probe `tools/debug/textlog.lua` (printer entry 0x8006E794, text =
    *(*(sp+0x1C)), logs `TEXT <hash>`). `warp_all.py --script tools/debug/textlog.lua` adds --debugger. Verified:
    newgame warp key matched scen000.0003. Report: `textcover.py work/qa/cov build/strings.tsv`.
  - Message forcing: `tools/debug/msgforce.lua` replaces each scene-message printer call with the next message of
    the loaded section (shots mKKKK_PP.png). Scene 0 test (work/qa/mf_try): section found (184 messages), 21
    forced, then the scene's own flow ended (cutscene). Needs a looping trigger (NPC talked to repeatedly, or a
    `FROM=k` rerun loop) before it can cover every scene: the next session's main job for coverage.
    `warp_all.py --raw N-M [--then ROUTE] [--frames F]` runs bare scene ids (folders scene_NNN).
  - G1 title: VRAM page x=640-767 is a mosaic of 8bpp tile pieces (logo, menu words, © line glyphs) from MAP.DAT
    entry 1161; the arrangement is probably entry 1160 (4 KB: u16 0x0B14, then 0x28 0x0F = 40x15 cells of 8 px = 320x120, the title band? guess;
    then u32 offsets 0x74 0x48C 0x48C 0x524 0x528 0x634 0x634 0xAE4 0xAE4 to sub-blocks). Decode that before redrawing.
    D5 reading: drop the katakana subtitle (official English logos have none), キャリアソフト -> CARRIER SOFT.
  - vqa (codex, 2026-11-19, build 2281f05f): 204 ok, 20 issue (work/qa/vqa.log, verdicts in work/qa/tour/verdicts).
    Open, next session fixes these first, then re-tour the warps and add `verdicts/recheck_N.tsv`:
    (a) field-menu bubble labels Magic / Equipment / Strategy sit 5-10 px left of centre (menu*, gear_equip,
        gear_status, menu_save, tour sheet_4): the bubble centres by code count, like the name tags: pad or measure.
    (b) place popup: "Nostridge Plains Garrison" off-centre (bt_bernard f002640), "Delis Village" drawn overlapped
        as "Dels'lage" (gear_spell f003360). Popup = 0x8006BB78 (exe.places, width 12, code-count frame).
    (c) bt_oswald2 f002400: centred popup with two Japanese/garbled glyphs (no popup in the JP frame: timing?).
    (d) name_entry f002160+: keyboard labels and romanized rows clipped/fragmented (JP intact).
    (e) empty dialogue body: bt_bandits f002400 (Wallace), ev_charamake f003600 (Citizen): check frame timing first.
    (f) one-word last lines: dn_glocian f002640 "interior.", st_vac01 f003360 "closer.", st_vac02 f003240
        "person.": reword or make the wrapper avoid a single-word final line.
- **Phase 8 session 2 (2026-11-19): vqa issues (a)-(f) fixed** (shots work/qa/fix2-fix4, pop1, bern, bandits*):
  (a)+(b) field-menu bubbles (exe.sys.0062-0067) and the place popup (exe.places, scene strings like "Nostridge
  Plains Garrison") are one routine 0x8006BA48 (frame 12 px x codes): asm `popup_width` hooks 0x8006BBB8/0x8006BCA0
  so the frame is the text's VWF pixel width. Round-2 vqa: scene captions "　The next day　" (code-count box):
  `insert.Encoder.centre` + CAPTION_BIAS leads with blank spacer glyphs (font U+E001-E00B, 1-11 px,
  `enfont.SPACERS`, decode drops them). "Dels'lage" and (c) were the popup's
  open/close scale animation (full frames read fine). (d) name entry: grids exe.sys.0070-0099 kept JP (one code per
  key, D14); exe.sys.0069 is one printed line cut into fixed slices (title 60 px, blank 12, labels 24 px):
  `insert.SLOTS` + `Encoder.slots`, labels Hira/Kata/ABC/Del/OK. (e) empty box = JP too (box opens ~24 frames
  before text). (f) `batches.py widows --write` (also run by `wrap`): a page's one-word last line takes the word
  before it unless that line ends a sentence; 1,899 lines changed, lint 0 problems.
  vqa round 2 (217 sheets): 218 ok / 6 issue -> bubbles (spacers were redundant once popup_width sized them:
  removed; now L8 R6 vs JP L9-10 R6-7) + caption centring; round 3 (20 changed sheets) all ok; bt_bandits empty
  box rechecked by hand (verdicts/recheck_1.tsv). **Tour gate green:** `qa_gate.py check work/qa/tour/manifest.tsv
  work/qa/tour/verdicts` exit 0, 224 sheets, build disc 1 0567dc36586aa9a7c3721c8e9cc49d6436ded943 (disc 2 T1
  5402e94684434f53919899c3ce1123866d012fd0). Any later build change needs a re-tour + `qa_gate init` + vqa of the
  changed sheets (deterministic: only changed screens differ).
- **Phase 8 session 3 (2026-11-19): inkbox pass + G1 groundwork.**
  - `tools/inkqa.py DIR..` (warp folders shot every 20 frames): finds field-menu bubbles (cream) and popup/caption
    boxes (border 0x836252) and runs inkbox (`tools/inkcheck.py` = inkbox from a seed point by flood fill). New warp
    `menu_bubbles` (cursor through all 6 items). Results: 6 bubbles L7/R5 ok (JP L8/R5); caption ev_battle003 21/21
    ok; place popup "Nostridge Plains Garrison" was L3/R10 -> fixed, now L6/R7.
  - Popup finding: the scene place/event-title popup is NOT 0x8006BA48 (tools/debug/popuplog.lua: only the menu
    bubbles call it, style 2). Its box is the text's width in whole 12 px columns (pre-parser extent), text at the
    left. Fix: `insert.is_title` (scene string, one line, no codes, no sentence punctuation, not a choice/caption:
    503 entries) -> `Encoder.title_lead` leads with a spacer of half the slack. Changing the bubble routine's text
    x (0x8006BBD0) to an odd value garbles text (4bpp canvas): don't.
  - Choice boxes (Yes/No, dungeon floors) are left-aligned like the JP (vqa verdicts): not inkbox targets.
  - Build after this session: disc 1 a77695dd651f67b8c802f17d0e2c1c0d08ba9bb0, disc 2 T1
    81f4baf1a881dfa66baedf687f1fdbea71157106. **The tour gate is stale** (503 title strings changed): re-tour,
    `qa_gate init`, vqa the changed sheets (deterministic: only screens with those titles differ).
  - G1 title: layout decoded enough to edit (docs/re/graphics.md "G1 title layout"): the title is one 16x16-cell
    mosaic baked into MAP.DAT entry 1161; `tools/cellsrc.py` maps screen cells to texels. Next: tools/title.py
    (render the screen from e1161 + cell map, edit -> indices, MAP.DAT in place in insert.patched), redraw per the
    notes, cold-boot zoomed shot.
- **Phase 8 session 4 (2026-11-19): re-tour + G1, G2/G3 graphics.**
  - Tour 3 on build a77695dd (copy in work/qa/tourbuild, so builds don't touch it): 69/69 landed, qa_gate init
    (93 sheets new/changed), vqa (tools/vqa_run.py, work/qa/vqa3.log): all ok except bt_bandits/sheet_2 (the known
    empty-box frame timing, verdicts/recheck_2.tsv). The vqa reviewers did NOT flag the status screen's Japanese
    resistance grid: graphics need their own zoomed look, not the tour verdicts.
  - G1 title done (tools/title.py, MAP.DAT entry 1161 in place), G2/G3 done (tools/statusgfx.py, MSYS 0x9100, D15).
    Details docs/re/graphics.md "Done". Cold-boot shots: work/qa/g1/title (title), work/qa/g2/gear_status.
    tools/allowed.txt + test_romdiff cover MAP.DAT now.
  - Build after this session: disc 1 82ef6e4ca34b30cabb268cb723949eaf0f80bb3d, disc 2 T1
    ab5cbb3164f6e49adcf6f7f041ccb8b1d7bdd17a, smoke ok, check.py green (40 tests). **The tour gate is stale** (title and
    status screens changed): re-tour from a copy of the build, qa_gate init, vqa the changed sheets.
  - G5 credits (MAP.DAT entry 1257, sweep sheet work/gfx/map/0125.png): staff roles are already romanized English;
    Japanese = cast lines "ティピ／豊口 めぐみ" (role／actor, a romanized actor line under each: replace the JP line
    with the English role name, keep the actor line), the "CAST" pages, 開発 キャリアソフト / 著作 アトラス／キャリアソフト /
    制作 アトラス lines and the (c) line at 0x70000+. The kana+Latin atlas at 0x80000 (G6) is probably the credits'
    own font (check by VRAM on the credits screen). Needs a credits warp first (debug-tool gap: the check menu's
    祝賀会以降 ending flow).
- **Phase 8 still to do (next sessions, in this order):**
  1. (done session 5: tour gate green on 82ef6e4c; any build change -> re-tour into work/qa/tour from a copy in
     work/qa/tourbuild, qa_gate init, vqa_run.py)
  1b. (done session 6: `ending`, `credits` warps.) Still open: the cleared-game flag (G4 appendix room); try a card
     save taken after the `credits` warp finishes (the game may offer a clear save after the staff roll).
  2. (done session 3: inkbox on bubbles, popup, caption; shop/inn when reached)
  3. Graphics text (docs/re/graphics.md): G1-G8, game over done (G4 session 10). Left: chapter/area cards (check on screen). Session 8: bt_medis left idle for 24000
     frames never ends (work/qa/go1): find the party's HP in RAM (ramsearch.py on a bt_* warp, damage taken
     between two dumps) and poke it to 0 in a probe; or find the game-over request (an area 84/85 pair, or a
     scene id) by its loader.
  4. Text coverage: done session 10b (see top). Old plan, kept for reference (session 8): in msgforce, remember the dispatcher's a0 (0x8003AA3C) at
     the last dispatch before the first forced printer call = the message op; when that thread resumes (first
     dispatch with a0 just past the op), set a0 back to the op, so mashing Circle prints every message of the
     section through the real printer (vmjump.lua shows the a0 write works). Run per scene (`warp_all.py --raw`,
     frames ~ messages x 120) with textlog.lua. EXE/MSYS table strings (items, help, places...) may be waived with
     the reason "read through the game's own getters under unicorn for every ref (test_insert test_msys_getters)"
     where no menu shows them.
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
  (5) edge blanks restored in 566 entries (D13; full-width blank = game glyph 0x0000; MSYS can't hold it:
  msys.skills.0123-0132 in batches.EDGE_FREE), checked by problems(). Minor (short final lines) in docs/polish.md.
  check.py green (39 tests), fit 0 errors / 0 warnings, smoke ok, newgame warp lands with English (work/qa/p7r_ab).
  Build 2026-11-19: disc 1 2281f05f7502da30eccfdeaba86f21bb7a39d62c, disc 2 T1 115d825f9b5249da673188cc4b36a95a95e517ee.
  Gotcha: never save in game without `--sav` (tools/pcsx/memcard1.mcd is shared; a save there breaks every warp).
  Phase 8 leads: status screen Circle = spell/skill page (gear_status THEN "...;20 circle"); growth graph
  (exe.sys.0102/0103) and the place popup (0x8006BB78) not reached yet.
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
- **Waiting on the user:** nothing (jPSXdec ran fine in session 7).
- **Engine notes:** pair coding costs ~1 byte per English letter (JP: 2 bytes per character), so sections grow
  roughly by the English/JP character ratio / 2. Scene entries are packed back-to-back in RAM: find the
  allocator/cap before English text grows them. The dialogue box takes ~50 English characters per line.
