# Window data (width gate, phase 5)

Budgets for the fit lint (`tools/fit.py`, `BUDGETS`; test `tests/test_fit.py`) and the translators. Measured = read
off a zoomed shot of a ruler line (`tools/stress.py`, every ruler character 6 px); lower bound = the pool's longest
JP string shows in that field, so it is at least that wide (an error row); guess = not measured yet (the lint warns,
and test_fit fails on warnings too, so the shipped text holds every row; confirm in the phase 8 tour). Font: `font/en12.txt` (VWF, advance = width + 1). Screen
320x240: one engine column (cell) = 12 px.

**Engine rule (verified, docs/re/text.md):** the printer auto-wraps when its column s6 (= ceil(x / 12) after each
code, vwf.asm) reaches the window width before a code is drawn. So a line fits a W-cell window when every code
(a letter pair) starts at x <= 12 * (W - 1). The lint simulates pairs, and treats any auto-wrap as an error (wrap
by hand with {n}). Dialogue prints a page at a time (vwf.asm skips the typewriter): keep wait codes at line ends.

| Variant | Pools / ids | Budget per line | Lines per page | Status | Proof |
|---|---|---|---|---|---|
| Dialogue box (no portrait) | scen messages (term end) | 24 cells: every pair starts at x <= 276, total <= 288 px | 3 | measured | work/qa/s1/newgame (scen000.0186 ruler: wrap after 48 chars = 288 px; 3 lines, page arrow right of line 3) |
| Dialogue with portrait | scen | same box: the portrait sits above it | 3 | measured | work/qa/marker2/ev_battle001 (scen014.0190 in the full-width box under the face) |
| Script menu / choice window | scen018 menu lines, choice lines after "・" | 24 cells after the bullet column (288 px) | 6 rows visible | measured | work/qa/s1/dbgmenu (scen018.0002/0003 rulers) |
| Name tag | scene speaker names (term null), exe.names | 144 px visible (clipped by the tag frame); tag width = code count, so insert.Encoder.tag_pad adds zero-width codes | 1 | measured | work/qa/s1/newgame (scen000.0003 ruler clipped after "C234" = 24 chars); phase 7 "Man" -> "Ma" fixed (work/qa/p7dlg4) |
| Help box (bottom of menus) | exe.help | 24 cells (288 px) | 3 | measured | work/qa/s2/title_config (ruler wraps after 48 chars), work/qa/s4/title_config (5-line help: 3 shown) |
| Descriptions | msys.items / magic / skills | 24 cells (288 px), same help box | 3 | measured | work/qa/g4 f6000 (msys.magic.0000 ruler wraps at 48), work/qa/s4/gear_spell (5 lines: 3 shown) |
| Item names (item list, equip / status slots) | exe.items | 8 cells (96 px) | 1 | measured | work/qa/s2/menu_1, work/qa/g3_1..3 (wrap after "A234567890B23456" = 16 chars) |
| Spell names | exe.magic | 8 cells (96 px) | 1 | measured | work/qa/g4 f6000 (gear_spell: wrap after 16 chars) |
| Config labels | exe.sys.0121 (one label per line) | 8 cells (96 px) | 9 lines | measured | work/qa/s3/title_config, menu_config (each label wraps after 16 chars) |
| Config values | exe.sys.0122-0133 | 8 cells (96 px) | 1 | measured | work/qa/s3/title_config (values wrap after 16 chars) |
| Skill names | exe.skills | 8 cells (96 px) | 1 | measured | work/qa/p8m/gs_ci (status, Circle: skills share the spell list column, "Critical 1" under "Magic Arrow") |
| Class names | exe.classes | 11 cells | 1 | lower bound | JP max 11 cells: the field shows the longest JP class, so it is at least that wide; not seen yet |
| Unit names | exe.units | 144 px clip | 1 | lower bound | JP max 12 cells (144 px); battle UI not reached yet |
| Place names | exe.places, scene strings shown in the popup | 12 cells; frame = VWF pixel width (asm popup_width, phase 8; was 12 px x code count) | 1 | measured | popup 0x8006BA48 (struct byte 8 = 0: scene message via 0x80070C04, else place getter 0x80070E60), printed by 0x800708E8(win, 12, 1); "Nostridge Plains Garrison" centred (work/qa/bern); world map not reached |
| Field-menu bubble | exe.sys.0062-0067 | same popup routine as place names (has a tail): frame = pixel width + 14 via popup_width | 1 | measured | margins L8 R6 vs JP L10 R7 (work/qa/tour/menu_2) |
| Scene caption | scen entries "　text　" (is_caption) | frame 12 px x code count, text 15 px in | 1 | measured | insert.Encoder.centre + CAPTION_BIAS (work/qa/tour/ev_battle003 f002760: L21 R21) |
| Name-entry labels | exe.sys.0069 | one line cut into slices: title 60 px, blank 12, 5 labels x 24 px | 1 | measured | insert.SLOTS (work/qa/fix4/name_entry) |
| Growth graph | exe.sys.0102 caption, exe.sys.0103 legend | caption 24 cells x 3; legend 4 cells per label, 7 lines | 3 / 7 | lower bound | JP caption line 3 = 23 cells with the heading centred by 9 blanks; JP labels max 4 cells; screen not reached |
| Other system text | exe.sys (rest) | 24 cells (guess) | 3 | guess | every current string passes (check gates warnings too); battle messages, shop, inn, save screen: phase 8 tour |
| Double-size text | printer path 0x80071650 | ? | ? | never seen on screen | vwf_big handles it (unicorn test only) |

Notes:
- Glyph torture line (every ASCII glyph the font has, é … — ♪ ♥, single/double/triple spaces, WWWWMMMM, iiiill) in
  the dialogue box: work/qa/s5/newgame, all legible. The font has no `# @ \ ^ \` { | }`: EnCodec rejects them.
- {s:XXXX} name substitutions count 96 px in the lint (fit.SUB_PX) until names are translated.
- MSYS blocks have almost no slack: 1 four-line ruler in msys.items or 3 rulers in magic+skills already overflow
  (`insert.py` MSYS_LIMIT). English descriptions will need the subfile growth (sector + count tables, load buffers;
  docs/re/text.md MSYS) before phase 7.
