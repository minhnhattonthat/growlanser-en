# Graphics-text survey (phase 1, static sweep done; on-screen confirmation of G2-G7 waits for the phase 2 warps)

Most UI art is **already English** (menu buttons, status labels, SAVE/LOAD/ITEM/SORT, BATTLESTART, CONGRATULATION...):
Atlus drew the system graphics in English. The Japanese drawn as graphics is the short list below. Speaker names,
dialogue, menus' item/spell names and place names are font text (docs/re/text.md), not graphics.

Tools: `tools/rawgfx.py` (raw 4/8/16bpp strips by file offset), `tools/gfxsweep.py` (sector archive -> deduped review
sheets + index.tsv), `tools/vramsrc.py` (find a VRAM rectangle's rows in disc files), `tools/timscan.py` (raw TIMs),
`tools/bsscan.py` (MDEC .BS stills: none on the disc), `tools/str2352.py` (STR -> ffmpeg), probes `ppudump.lua` /
`ramdump.lua` via `emu.py`. Review brief for sweep sheets: `docs/gfx-sweep-brief.md`.

## Japanese graphics to redraw (phase 8)
| # | Element | Screen | Source (verified how) | Format |
|---|---|---|---|---|
| G1 | Title: katakana subtitle グローランサー under the logo, and "キャリアソフト" in the "© ATLUS / キャリアソフト 1999" line | title | MAP.DAT entry 1161 (+4 KB): title VRAM x=640/704 rows found byte-exact by `vramsrc.py` (work/qa/vram_title). Title is drawn from tile pieces; the tile arrangement is probably entry 1160 (guess) | 8bpp, 256 px rows (two 128 px texture pages side by side), CLUT in the entry (guess) |
| G2 | Affinity labels 急所 半減 / 弱点 無効 / ?? (unclear, likely 普通) 吸収 | status / enemy info (guess) | MSYS.DAT 0x9100-0xBFFF, x 192-255 px (byte 96-127 of each 128-byte row); VRAM page x=896 matched at 0x9A00 by `vramsrc.py` | 4bpp, 256 px rows |
| G3 | Element icons 炎 風 聖 / 冷 雷 闇 / 地 物(?) 精 (fire wind holy / cold thunder dark / earth phys(?) spirit) | spell / equipment info (guess) | same block as G2, rows below it | 4bpp |
| G4 | Appendix (OMAKE) menu: "GLチップスカード入れ" + "(非売品)" (OMAKE/1), "VISUALビューモード" (OMAKE/2) | おまけ appendix room (after clearing, guess) | MSYS.DAT ~0x7C000-0x84000 (rendered `rawgfx.py --bpp 8 --stride 256 --at 0x7C000`) | 8bpp, 256 px rows |
| G5 | Credits: cast list (role／actor, ~40 lines: ティピ／豊口 めぐみ ... ヴェンツェル／江川 央生, each with a romanized line under it), staff lines 開発 キャリアソフト / 著作 アトラス／キャリアソフト / 制作 アトラス, © line with キャリアソフト | ending credits | MAP.DAT entry 1257, offsets 0x0-0x40000 (cast) and ~0x70000 (staff), codex sweep sheet 0125 | 8bpp tile pages (128 px, as swept) |
| G6 | Kana glyph atlas (hiragana あ..ん, katakana ア..ン, voiced/small kana) beside a Latin alphabet | name entry keyboard or credits font (guess: the hero is named by the player) | MAP.DAT entry 1257 ~0x80000 (sheet 0125) | 8bpp |
| G7 | Texture atlas with Japanese: katakana runs (ス アビ.., ドコッ, ドー ザフィ..), 服 の手, boxed kanji labels (無, 通, 冷, 聖, 炎, 定...) mixed with English UI pieces and a portrait | unknown (a snapshot of a menu's VRAM page?); identify on screen by VRAM match in phase 8 | MAP.DAT entry 1151 (4bpp at 128-byte rows for the text part; mixed formats in the entry) | 4bpp + others |
| G8 | Logo frame "GROWLANSER" with the katakana subtitle グローランサー, burned into the video | MOVIE0.STR and MOVIE1.STR, ~54 s and ~105 s in (frames 0018/0035 of the 3 s sampling) | FMV (MDEC): needs a frame re-encode (jPSXdec `-replaceframes`, `references/platform-ps1.md`) or leave as logo art; D5 says replace | STR video |

## Done (phase 8 session 4, 2026-11-19)
- G1 title: `tools/title.py` (cells -> gfx/title/cells.json = cell map + CLUT from a cold-boot shot; draw ->
  gfx/title/title_en.png; check). insert.patched writes MAP.DAT entry 1161 in place (title.patch). Subtitle replaced
  by marble, (c) line "CARRIER SOFT 1999" drawn in the line's own style (letter_line). Cold boot: work/qa/g1.
- G2/G3: shown on the status screen's resistance grid (gear_status warp, bottom right: 9 x element icon + affinity
  label). `tools/statusgfx.py` redraws MSYS 0x9100 x 192-239 in place (D15). Label CLUT VRAM (288,505), icon CLUT
  (256,505) (work/qa/g2v dump). Only NULL is seen in the warp (debug unit has all 無効); the other labels' colours
  come from the label's own brightest index.
- G5 credits (session 7): MAP.DAT entry 1256 ends (at its offset-table field 0x38 = 0x13AC) with 19 upload records
  (u16 sector in e1257, flags = sectors | 0x100 if 8bpp, VRAM x, y, width px, rows). Pages 2-16 = 4bpp 256x255
  credit pages shown in record order as one scrolling strip (index ramp 1 = ink .. 15 = white bg; page 16 bg 14);
  page 18 = the kana+Latin atlas (G6), 12x12 cells from (120,0), baseline row 9. `tools/credits.py` (pages / show /
  patch, run by insert.patched) erases each cast JP line (role／actor) and right-aligns the English role (glossary
  names, 36 entries Tippi..Wenzel) in the atlas Latin font above the kept romanized actor line; closing lines ->
  "Developed by CARRIER SOFT" / "Copyright ATLUS / CARRIER SOFT" / "Produced by ATLUS"; (c) line keeps "(c)ATLUS／"
  and "1999", CARRIER SOFT in small caps cut from actor lines. In game: work/qa/g5/credits (f012000-f027000).
- G8 FMV logo (session 7): MOVIE0.STR (disc 1 only; 1621 frames, 15 fps) frames ~764-824 (logo over clouds, then
  a zoom into white) and MOVIE1.STR frames ~1516-1557 (zoom out of white, fade). `tools/fmvlogo.py` finds the bar
  line per frame, masks the subtitle (redder than the row's background right of it, plus its grey drop shadow),
  fills it from that row background + a little diffusion, and re-encodes only that rect with jPSXdec
  `partial-replace` (tools/jpsxdec, Java). build.py adds the two STRs to disc 1 (`fmvlogo.patched()`, cached in
  work/fmv/en). Before/after frames: work/fmv/en/MOVIE{0,1}/orig vs fNNNN.png.
- G7 (session 8): the LLM magic class tutorial in Rosaria (scene 1 op `76 06 55 00` -> area 85 sub 6 -> MAP pair 575
  via the area table 0x80100A10; warp `tut_status`). A picture of a status screen: entry 1150 = header (CLUTs at
  0xB0, VRAM rows 480-484; background tilemap 0xF74, words 0x00XX, CLUT 0 = gradient + dark panels; front tilemap
  0x11CC, 20x15 x 16 px, words 0x2000 | page << 8 | row << 4 | col, CLUT 1, colour 0 transparent; sprite pieces at
  0xDBC: portrait + magenta highlight frames, tpages 0x87-0x89), entry 1151 = texture (records 0/1 = both tilemaps'
  cells, every cell in use). Japanese: equipment names (with an opaque 1 px black shadow) and the resistance grid; the
  "STATUS画面" callout is scene text (scen001.0171). `tools/tutorialgfx.py` (render / draw / check, insert.patched):
  names from exe.items in the English font with a shadow, the grid = statusgfx art at the real screen's place;
  "Thick Clothes" needs one more cell: (9,10) shares (8,10)'s now-transparent cell, its own goes to (7,11).
  Dialogue scen001.0178/0179 quotes the grid labels (VITAL, DRAIN, NULL, HALF, EVEN, WEAK). In game: work/qa/g7en.
- G6: the atlas is loaded with the credits (VRAM 768,256) but never drawn: every credits frame of the JP and English
  runs (work/qa/ending2, work/qa/g5) shows only the pages. No visible Japanese; left as is.
- G4 (session 10): appendix room labels, MSYS 0x70000 + row*256 (8bpp; room VRAM x 896, y row+88). OMAKE/1
  "GL CARDS" + "(PROMO)", OMAKE/2 "VISUAL ROOM" (D16), built by `tools/appendixgfx.py` from the sheet's own
  letters (G, L kept; C A S from CV MESSAGE, R from MUSIC ROOM scaled to their height, D = mirrored C + stem, P R O M
  from "AORI's APPENDIX ROOM", parens from (非売品); ROOM from MUSIC ROOM). Letter = inner fill (index < 0x60) plus
  its nearest ring pixels; 222 = black outline. In game (OMAKE/1 only, the room takes no input): work/qa/g4 f2200.
  OMAKE/2 checked offline only (`appendixgfx.py OUT.png SHOT.png`, palette voted from a JP room shot).

## G1 title layout (phase 8 session 3, 2026-11-19)
- MAP.DAT entry 1160 (4 KB) tail at 0xAE4: 4 upload records (u16 ?, ?, VRAM x, VRAM y, width in bytes, rows):
  (640,0) 256x256, (768,0) 128x256, (640,256) 64x96, (704,256) 192x80. Entry 1161 = those 4 rects back to back
  (offsets 0, 65536, 98304, 104448; 1024 zero bytes at the end; verified row-exact against the VRAM dump).
  R4 holds the "DISC 2" swap prompt. 0x634: a 40x15 u16 grid (descending codes 0x500-0x7F7, 0x15xx): not decoded,
  not needed.
- The whole 640x240 title (background marble, logo, katakana subtitle, © line) is ONE mosaic of 16x16 cells baked
  into the texture: `tools/cellsrc.py work/qa/vram_title/final.png work/qa/vram_title/ppu_001490.vram.bin
  work/gfx/title/cellmap.json --cells 0,2,40,13` finds the texture cell (u, v texels from VRAM hw x 640, 8bpp) of
  348/400 screen cells on a 16-px grid (missing: rows 7-9 x 20-39 = the menu words, drawn on top and animated).
  So an edit = change screen pixels, map each through its cell to a texel of e1161 (u < 256: R1 at v*256+u;
  256-383: R2 at 65536 + v*128 + u-256), index = the CLUT index of the wanted colour (colour -> index map from the
  same cells; the entry's 1024-byte tail is zero, so take the CLUT from the matches). Check no texture cell is
  shared with an unedited screen cell.
- Subtitle グローランサー: screen x 38-252, y 98-119 (logo bar bottom edge rows 96 grey, 97 cream, 98 dark at
  x=300; at x<~45 there is no bar). Fill with the marble from rows 121-142 (shift 22) and redraw the bar edge.
- © line: glyph band y 162-176 (black outline rows 164/174, cream body 165-173, black 2 px strokes inside, shadow
  175-176), cells rows 10-11. Glyph x runs: © 166-185, A 204-220, T 224-237, L 243-254, U 261-276, S 283-295,
  / 317-328, キャリアソフト 346-506 (7 glyphs, ~20 px pitch), 1999 520-588. "CARRIER SOFT 1999" needs ~16 glyphs:
  redraw x 340-630 (marble source: same rows x 0-159), copy A/T/S/1/9 from the line, build C R I E O F in the same
  layers (stroke -> body = stroke dilated 2 px, cream 238,213,205, top row 222,197,180 -> 1 px black outline).
  `tools/inkruns.py SHOT Y0 Y1` lists glyph runs.

## Checked, no Japanese
- MSYS.DAT (2.4 MB, raw, no directory in the file; region widths vary): 0x0-0x30000 4bpp 256 px system UI (English
  labels, digits, icons, character map sprites); 0x30000 world map with English place names (Rolandia...);
  0x48000-0x80000 GL chips card collection (English "GL CHIPS CHARACTER CARD COLLECTION", "NOT FOR SALE!!", numbered
  card art), MUSIC ROOM, CV MESSAGE, "AORI's APPENDIX ROOM Now Closing"; 0x90000+ face portraits. 0x42000 is a CLUT,
  0x42800 / 0x47800 are text tables (item descriptions). Reviewed: codex pass (11 sheets, work/gfx/msys/review.tsv)
  + own pass of 0x30000-end at 256 px stride (the codex pass missed G4 at the wrong stride: always re-render 8bpp
  regions at 256 px too).
- MAP.DAT (1312 entries, pairs of a small header/tilemap entry + 8bpp 128 px tile pages): `gfxsweep.py` 2133 unique
  pages in 134 sheets (work/gfx/map), codex pass: only low-confidence candidates, each zoomed by hand: ornaments,
  sparkle animation frames, Latin pseudo-script plaques (0025 255:30000, 0033 341:20000, 0037 379:20000, 0081 769:0,
  0088 859:0). Special screens live here too (the title is entry 1161): entries ~1156-1311 = title/system screens
  (guess). Sheets 0090-0133 (codex pass C): G1, G5, G6, G7 above; nothing else.
- FTIM.DAT (83 TIMs, portraits), MAGD.BIN (67 TIMs, spell effects; VRAM shows rune glyphs, not Japanese), UPD.UPD,
  NEFF.BIN: no text. EXE: only the 12x12 font (text); 0xF1000-end is tables.
- SCEN.DAT entries 560-715 and 839: compressed (high entropy, unknown codec), loaded with each scene (entry N+280,
  RAM 0x80146778 in scene 280); the scene's VRAM (work/qa/vram_scene) holds only character sprites and effects, so
  these are per-scene sprite packs (guess). Entries 0-155 are small tables. Re-check in the phase 8 tour.
- Dialogue box speaker tag, dialogue, menus: font text drawn into VRAM at runtime (VRAM shows the rendered lines).

## Still open (needs the phase 2 debug tool; re-check in the phase 8 tour)
- FMV MOVIE0/1.STR (anime, 2336-byte sectors -> `str2352.py` -> ffmpeg): frames every 3 s in work/fmv, codex pass
  found only G8; other captions are English. A 3 s sampling can miss short captions: watch both in full in phase 8.
- Game over (warp `gameover`, session 9): "GAMEOVER / STAND AGAIN.. PRESS START BUTTON." is English art in the
  original: nothing to redraw (zoomed shot work/qa/go2/gameover f011000).
- Mid-game screens not reached yet: chapter/area cards, appendix room (ending, credits done). Their art is in
  MAP.DAT / MSYS.DAT, which the sweep covered, but confirm each on screen by warping (phase 2 scene list).
- G5b credits player line (open, tour 5 vqa): under CAST the game draws "プレイヤー／" + the player's name at run
  time from the atlas page 18 (MAP.DAT 1257 record 18: kana, Latin, and a ready "プレイヤー／" cell on row 7 right
  of ゴ); not printer text (textlog, RAM search find nothing). EN shows "プレイヤー／" and no name (the name is pair
  codes; the credits typesetter maps single codes to atlas cells). Fix: letter "Player /" over that atlas cell, and
  find the typesetter (it reads the name buffer 0x8019431A) to expand pair codes into two Latin codes.
  Session 10b: no chapter-card art exists in the sweeps; area names are the place popup (font text, English,
  work/qa/bern). The other place-getter caller (0x8009D448, fn ~0x8009D308) is the name-entry check: it compares
  the typed name with every names / places string (rejects a clash), it draws nothing. So the world map's place
  names are only its art (MSYS 0x30000, English in the original); not seen on screen (warps to area 0/1 sub 0 land
  in towns).
