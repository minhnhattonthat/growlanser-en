# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

All of D1-D7 came pre-answered in the owner's one-shot run brief (Orca coordinator), 2026-11-17.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-11-17 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western order (given name first). Owner's standing default. |
| D2 | 2026-11-17 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist (Growlanser Collection / Heritage of War localisations), else an earlier fan patch, else Hepburn without macrons. |
| D3 | 2026-11-17 | Credits | stay Japanese, translate | English. |
| D4 | 2026-11-17 | Abbreviations | engine work first (default), abbreviate | Engine work first (skill default); abbreviate only as a flagged last resort. |
| D5 | 2026-11-17 | Graphics text left in Japanese | none (default), list | Translate all of it (titles, menus, banners, cards); keep the Japanese logo only if it has no official English version. The title logo is already "GROWLANSER" with a katakana subtitle. |
| D6 | 2026-11-17 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through every checkpoint, report at the end. |
| D7 | 2026-11-17 | Existing saves / memory cards | user supplies, none | None provided; build the debug tool as usual. |
| D9 | 2026-11-18 | Name spellings (no official English G1) | fan site literal (Ruise, Richart, Venzern), natural European forms, Hepburn | Agent default under D6: fan spellings where they read as names (Tippi, Luise, Wallace, Xenos, Karen, Misha, Gevel), the European name the katakana spells otherwise (リシャール Richard, ヴェンツェル Wenzel, エリオット Elliot), Hepburn last. Binding list: glossary.md; rejected forms in its Avoid column. Owner may override. |
| D10 | 2026-11-18 | Kinship terms with honorific ruling D1 | keep onii-chan, translate | Agent default: honorifics stay after names (Tippi-chan), kinship and role words are translated (お兄ちゃん "Big Brother", お母さん "Mother", マスター "Master"). |
| D11 | 2026-11-18 | Translator/reviewer agents in an Orca worker | Claude subagents, codex exec | codex exec (read-only, prompt in, final message parsed) via `tools/tl_run.py`, per the run brief (no nested workers) and translation.md §Review. |
| D8 | 2026-11-17 | Publishing | - | Never run `gh release create` or change repo visibility; the run ends at a built, verified release zip. Commit and push to main at each phase end. |
| D12 | 2026-11-19 | Phase 7 review: strings over a proven width (agent default under D4/D6) | widen the field, abbreviate, rephrase | Rephrase without abbreviating: 全周囲攻撃 "Whirlwind Attack" (96 px skill list), 副学院長秘書 "Vice Headmaster's Aide" (1 px over 144), 送魔線技師 "Mana Line Engineer" (glossary). Growth-graph legend fits a 4-cell lower bound: "HP", "MP", "Intellect", "Move" (倍率 "multiplier" dropped). Flagged: revisit in phase 8 if the graph screen shows more room. |
| D14 | 2026-11-19 | Name-entry keyboard (agent default under D6) | romanize the keys, keep the grids | Keep the kana and full-width Latin grids exactly (exe.sys.0070-0099 in insert.KEEP_JP): each key is one code and the code is what the name receives, so English pairs broke input. Labels: "Enter Name", "Hira", "Kata", "ABC", "Del", "OK" (fixed 24 px slices, insert.SLOTS). Kana keys stay visible on that screen. |
| D15 | 2026-11-19 | Status-screen resistance grid G2/G3 (agent default under D4/D6) | words, abbreviations, pictograms | Affinity labels (24 px) get full words in a 7-row pixel font: 急所 VITAL, 半減 HALF, 弱点 WEAK, 無効 NULL, 普通 EVEN, 吸収 DRAIN. Element icons are 16 px plates with ~11 px inside: no English word fits, so pictograms instead of abbreviations: fire flame, wind gusts, holy sparkle, cold snowflake, thunder bolt, dark crescent, earth mountain, physical sword, spirit rings (`tools/statusgfx.py`). Title: katakana subtitle dropped, キャリアソフト -> CARRIER SOFT (D5). |
| D13 | 2026-11-19 | Edge blanks (phase 7 review) | strip, keep | Keep the JP's leading/trailing blanks and {n} exactly (blank first line of item notices, indents, grid padding): `batches.py edges --write`, checked by `problems()`; exemptions only via `batches.EDGE_FREE` with a reason. |
