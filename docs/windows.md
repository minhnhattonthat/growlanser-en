# Window data (width gate, phase 5)

Budgets for the fit lint and the translators. Measured = read off a zoomed shot of a ruler line (`tools/stress.py`,
every ruler character 6 px); guess = not measured yet (the lint warns on those). Font: `font/en12.txt` (VWF,
advance = width + 1). Screen 320x240: one engine column = 12 px.

**Engine rule (verified, docs/re/text.md):** the printer auto-wraps when its column s6 (= ceil(x / 12) after each
code, vwf.asm) reaches the window width before a code is drawn. So a line fits a W-column window when every code
(a letter pair) starts at x <= 12 * (W - 1). The lint must simulate pairs, not just compare the line's total px.

| Variant | Pools / ids | Budget per line | Lines per page | Status | Proof |
|---|---|---|---|---|---|
| Dialogue box (no portrait) | scen messages (term end) | 24 columns: every pair starts at x <= 276, total <= 288 px | 3 | measured | work/qa/s1/newgame (scen000.0186 ruler: wrap after 48 chars = 288 px; 3 lines shown, page arrow right of line 3, no overlap) |
| Script menu / choice window | scen018 menu lines, choice lines after "・" | 24 columns after the bullet column (288 px) | 6 rows visible | measured | work/qa/s1/dbgmenu (scen018.0002/0003 rulers) |
| Name tag | scene speaker names (term null), exe.names | 144 px visible (clipped by the tag frame) | 1 | measured | work/qa/s1/newgame (scen000.0003 ruler clipped after "C234" = 24 chars) |
| Dialogue with portrait | ? | ? | ? | guess: not seen yet in the tour | - |
| Help line (bottom of menus) | exe.help, some exe.sys | ? (ruler shown, not read yet) | 1 | to measure | work/qa/s2/title_config |
| Item / magic / skill / class / unit / place names in lists | exe.items, magic, skills, classes, units, places | ? | 1 | to measure (debug start has empty lists; needs a state with items) | work/qa/s2 menu_* |
| Descriptions | msys.items / magic / skills | ? | ? | to measure | - |
| Config labels | exe.sys (config) | very short fields: "sy121 Th" clipped | 1 | to measure | work/qa/marker/title_config |
| Battle messages, shop, inn, save screen | exe.sys, scen | ? | ? | to measure | - |
