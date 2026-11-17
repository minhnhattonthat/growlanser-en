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
- Mid-game screens not reached yet: game over, chapter/area cards, ending, credits, appendix room. Their art is in
  MAP.DAT / MSYS.DAT, which the sweep covered, but confirm each on screen by warping (phase 2 scene list).
