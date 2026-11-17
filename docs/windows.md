# Window data (width gate, phase 5)

Budgets for the fit lint (`tools/fit.py`, `BUDGETS`; test `tests/test_fit.py`) and the translators. Measured = read
off a zoomed shot of a ruler line (`tools/stress.py`, every ruler character 6 px); guess = not measured yet (the
lint only warns on those; confirm in the phase 8 tour). Font: `font/en12.txt` (VWF, advance = width + 1). Screen
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
| Name tag | scene speaker names (term null), exe.names | 144 px visible (clipped by the tag frame) | 1 | measured | work/qa/s1/newgame (scen000.0003 ruler clipped after "C234" = 24 chars) |
| Help box (bottom of menus) | exe.help | 24 cells (288 px) | 3 | measured | work/qa/s2/title_config (ruler wraps after 48 chars), work/qa/s4/title_config (5-line help: 3 shown) |
| Descriptions | msys.items / magic / skills | 24 cells (288 px), same help box | 3 | measured | work/qa/g4 f6000 (msys.magic.0000 ruler wraps at 48), work/qa/s4/gear_spell (5 lines: 3 shown) |
| Item names (item list, equip / status slots) | exe.items | 8 cells (96 px) | 1 | measured | work/qa/s2/menu_1, work/qa/g3_1..3 (wrap after "A234567890B23456" = 16 chars) |
| Spell names | exe.magic | 8 cells (96 px) | 1 | measured | work/qa/g4 f6000 (gear_spell: wrap after 16 chars) |
| Config labels | exe.sys.0121 (one label per line) | 8 cells (96 px) | 9 lines | measured | work/qa/s3/title_config, menu_config (each label wraps after 16 chars) |
| Config values | exe.sys.0122-0133 | 8 cells (96 px) | 1 | measured | work/qa/s3/title_config (values wrap after 16 chars) |
| Skill names | exe.skills | 8 cells (guess: same list as spells, JP max 8) | 1 | guess | - |
| Class names | exe.classes | 11 cells (guess: JP max 11) | 1 | guess | not seen in any menu yet |
| Unit names | exe.units | 144 px (guess: name tag) | 1 | guess | battle UI not reached (bt_* warps land before the battle starts) |
| Place names | exe.places | 10 cells (guess: JP max 10) | 1 | guess | world map not reached |
| Other system text | exe.sys (rest) | 24 cells (guess) | 3 | guess | battle messages, shop, inn, save screen: phase 8 tour |
| Double-size text | printer path 0x80071650 | ? | ? | never seen on screen | vwf_big handles it (unicorn test only) |

Notes:
- Glyph torture line (every ASCII glyph the font has, é … — ♪ ♥, single/double/triple spaces, WWWWMMMM, iiiill) in
  the dialogue box: work/qa/s5/newgame, all legible. The font has no `# @ \ ^ \` { | }`: EnCodec rejects them.
- {s:XXXX} name substitutions count 96 px in the lint (fit.SUB_PX) until names are translated.
- MSYS blocks have almost no slack: 1 four-line ruler in msys.items or 3 rulers in magic+skills already overflow
  (`insert.py` MSYS_LIMIT). English descriptions will need the subfile growth (sector + count tables, load buffers;
  docs/re/text.md MSYS) before phase 7.
