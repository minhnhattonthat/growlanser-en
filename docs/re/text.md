# Text: encoding, font, containers

## Disc layout (verified: dumpsxiso listing, cmp)
- Disc 1 SLPS-02380, disc 2 SLPS-02381. Every data file and the EXE are byte-identical between discs
  (`SLPS_023.80` == `SLPS_023.81`); disc 1 adds MOVIE0/1.STR, disc 2 adds BGM40.WAV + CD-DA track 2.
- EXE: PS-X EXE, t_addr 0x80010000, RAM = file offset - 0x800 + 0x80010000.

## Encoding (verified: relative search in a RAM dump, decoded on-screen lines match the shots)
- Text is u16 little-endian words. Words < 0xF000 are **glyph indices** into the EXE font (no Shift-JIS).
- Font: SLPS_023.80 file 0xE85C8 (RAM 0x800F7DC8), 12x12 1bpp, rows packed MSB-first, 18 bytes/glyph,
  codes 0x0000-0x07CA (verified: on-screen glyph searched in RAM, `tools/font.py render` sheets).
  It is MS Gothic's 12px bitmap almost verbatim: `tools/fontmatch.py` matched 1859 of 1995 glyphs exactly.
- Layout: 00 blank, 01 『, 02 』, 03 、, 04 。, 05 ？, 06 ！, 07-10 0-9, 11-2A A-Z,
  2B-7A hiragana ぁ..ん in JIS order without ゎゐゑ, 7B-CA katakana ァ..ヴ (JIS order without ヮヰヱ),
  CB ゐ, CC ゑ, CD ー, CE ゛, CF ゜(0D0), D1 ・, D2 ヰ, D3 ヱ, D4-ED a-z, EE-106 ＋－％＆♪～（）．，：；‘’／＼￣＿＾ゝ＜＞≦≧＠,
  107-117 item-type icons, 118 ー, 119 ─, 11A ―, 11B ‥, 11C+ kanji (font order, not JIS).
  Odd cells: 028B-028E = "ペンダント" squeezed into 4 cells, 0298/02A4 key-item icons, 03AD/0571/0643/0644 = ○□△✕ buttons,
  01BE a flourish after ～, 0530 ♥. Table: `tbl/jp.tbl`, codec `tools/gltext.py`.
- 0x0000 is drawn as a blank cell; ASCII-width (half-width) glyphs do not exist: every cell is 12 px. English needs
  a VWF or a narrow font (phase 5).

## Control codes (verified: text-draw loop at 0x8006EBAC, dispatch at 0x8006F4E4, jump table 0x80013298)
- FFFE end of message (draw loop exits), FFFF empty/name terminator, FFFC newline, FFFD new page.
- FFE8-FFFF dispatch through the 24-entry jump table at 0x80013298; FFEB-FFF7 seen (colour/emphasis: FFEF..FFF1
  wraps item names, FFEE/FFF1 around button icons). FFF9 FFFB/FFFA seen too. No argument words (statistics).
- Words >= 0xDFFF and < FFE8: high byte = command, low byte = parameter.
  F600 + 1 word: substitute string (arg < 0x8000 = index, else 0x8019_6A70 + 2*(arg-0xFFED) + 0x220 table) - names.
  F700 + 1 word (skipped). F800 + 1 word: voice clip (calls 0x80053F74; VOICE.XA). F2xx, F4xx, F5xx, F9xx, FAxx,
  FBxx, FCxx, FExx use only the low byte. F4xx = dictionary word xx (item descriptions, see below).
  FDxx is ignored by the dialogue loop. Codec names: {s:XXXX} {v:XXXX} {f7:XXXX} {n} {p} {end} {null} {XXXX}.

## SCEN.DAT (verified: `tools/scen.py`, every offset of all 245 text entries lands in its section)
- Archive (`tools/dat.py`): u32 count (840), count x (u16 start sector, u16 sector count), 2048-byte sectors; the
  entries tile the file exactly. 300 entries are empty.
- Entries 280-559 are scenes. Scene header = 25 u32, word 0 = 0x64; **word 22 = offset of the text section**.
  Text section (always last in the entry, zero padding to the sector after it): u32 size, then u16 offsets
  relative to the section start (count = (first offset - 4) / 2; not sorted, may repeat), then messages.
- Messages end with FFFE; names (speaker list at the start) end with FFFF. Choice options (start with D1 ・) sit
  right after their question and are **not** in the offset table: the engine reads on past the FFFE. So rebuild the
  section as the ordered list of all terminated strings and re-point offsets by string index.
- 10 offsets in entry 329 point 2 bytes into a string (past a leading FD00): record (string, delta).
- 25,557 strings in 245 entries (~24,113 referenced). Entries 0-155 / 560-715: no text (other data).
- Scene load (verified: `tools/scenram.py` on a RAM dump of scene 280, work/qa/ram_scene): entries N-280, N and
  N+280 load together. Entry 0 at 0x80128B98 (0x318 B), entry 280 right after it at 0x80128EC0 (0x6260 B), 0xA79 zero
  bytes, other data from 0x8012FB99; entry 560 at 0x80146778. Packed back-to-back, so allocation looks dynamic
  (guess). Largest scene entry: 308, 14 sectors (28 KB). Phase 5: find the allocator / cap before growing entries.
- File reads (verified by disassembly): CdSearchFile fills a CdlFILE table at 0x80190328 (0x18 B each) for
  MAP, SCEN, XATBL, MSYS, FTIM, SND, NEFF, ... (names at EXE 0xE0128, code 0x800181F0); read requests are 12-byte
  records at 0x80191120 handled by 0x8001835C (type switch via jump table 0x8001038C). Hook here for scene warps.

## EXE text (verified: disassembly of the getters, `tools/extract.py --check` rebuilds every table byte-identical)
- 10 string tables tile 0xE2138-0xE85C8 exactly (test `Script.test_exe_range_covered`; 2-byte zero pads at E22C2,
  E310E, E55BA, E722A). Each has a getter at 0x80070C04-0x80071094: `if i < count: return base + 2*table[i]`
  (u16 **word** offsets), else entry 0 of the sys table. Table list with file offsets: `EXE_TABLES` in
  `tools/extract.py` (sys, names, units, classes, magic, skills, items, help, places, dict).
  RAM = file + 0x8000F800.
- Special cases in the getters: names/units slots 0, 0x10, 0x131 return RAM buffers 0x8019431A / 0x80194308 (player
  and custom names); places slot 6 returns a RAM buffer too (the renamable town, scene 67).
- `dict` (0xE722C, 256 entries) is the F4xx dictionary: {F4xx} expands to entry xx (verified: item descriptions read
  naturally when expanded, e.g. F4C1 = "で、", F4BA = "。{n}"). Its first entries are long phrases, the rest words.
- No code builds an address inside the pools other than through the getters (lui/addiu scan; the only extra hit,
  0xE3130 = names table slot 0x10, is a table read). So the pools can be resized or moved by re-pointing the 10
  getters' (table, base) pairs (phase 5).
- 0xE2000-0xE2138: pointer data (0x800Fxxxx words); 0xE0000-0xE1FFF: tables; scans elsewhere find only noise.

## MSYS.DAT (verified: `tools/extract.py --check`, test `Script.test_msys_range_covered`)
- 3 text sections in the SCEN section format (u32 size, u16 byte offsets, strings): 0x42800 items (268
  descriptions), 0x47800 magic (35), 0x485BC skills (173: skill descriptions, then appendix CG titles, extras, voice
  cast). They tile 0x42800-0x49E14 (zero to 0x47800 after the first, zero 0x49E14-0x4A000). Text uses F4xx codes.
  No text elsewhere in the file. How the game finds each section (no u32 0x42800/0x485BC in the EXE): phase 5;
  section 3 directly follows section 2, so growing section 2 moves section 3.
- The rest of MSYS.DAT (2.4 MB) is graphics.

## Script (phase 4; `script/*/*.json`, format in the `tools/extract.py` docstring)
- Section padding rule (all 245 + 3 sections): after the last string, at least one FFFF, then FFFF to a 4-byte size
  (`textsec.pad_for`).
- Every SCEN string with no offset pointing at it (2,859) is a choice line read on past its question, incl. 5
  "　{FFEE}キャンセル{FFF1}" cancel options in scene 67.

## Text drawing and the English VWF (phase 5; verified: RAM dump of the debug menu, unicorn test `tests/test_vwf.py`, marker build shots)
- One printer, 0x8006E794 (a0 window struct, a1 x, a2 y, a3 width in columns, stack: height, text pointer...),
  called from 0x800677F4 and 0x80070934; it draws into a 4bpp RAM canvas (struct 0x801D2808: base1, stride1,
  split column, -, base2, stride2; texels from split*12 on go to canvas 2; low nibble = left texel) that is then
  uploaded to VRAM. The font is read only by its two glyph routines (only `lw 0x9A0($gp)` in the EXE and RAM):
  - 0x800711E0 (col, s2+1, code), jal at 0x8006F3A8: normal text, 1 texel per font pixel, y = row*16+2, x = col*12
    texels, then s6 += 1. **The screen is 320x240: a column is 12 screen px, a text line 16.**
  - 0x80071650 (col, s2, code), jal at 0x8006F49C: double size (2x2 texels per pixel), s6 += 2. Chosen per line
    by the per-line size tables at 0xA4/0xA8(sp) (< 2 = normal); not yet seen on screen.
  - Before each glyph the printer checks s6 against the window width (0x8C(sp)) and the per-line widths (0x50(sp))
    and wraps on its own (s6 = 0, next row) if it does not fit; kinsoku codes are compared with gp halfwords
    0x984-0x996.
- asm/vwf.asm hooks both jals: pair codes (tools/enfont.py, PAIR 0x800 + i<<7 + j) are drawn as two proportional
  glyphs from font/en12.txt, game glyphs 12 px wide; the printer gets back s6 = ceil(x / 12). The texel x resyncs
  to col*12 when the column, row or canvas changes. Code + English font sit in font cells 0x6A0-0x7CA.
- **Typewriter** (verified, `tools/debug/vwflog.lua` exec hooks): dialogue goes through the print wrapper
  0x8006777C (a0 x col, a1 y row, a2 width, a3 height, stack: &dx, &dy, ...). With gp+0x87E = 1 (set at
  0x80065120) the caller at 0x800654B4 (and its twin after 0x800658E8) prints ONE code per frame into a 1x1-column
  window at the cursor (gp+0x84A + gp+0x838, gp+0x852 + gp+0x83C) and adds the columns used, so the glyph routine
  always sees col 0 and each pair sat in its own 12 px cell (clipped past 12 px: "brow n"). Otherwise it prints the
  rest of the page at once (0x800655C8 / 0x80065A4C: x = window left, width = whole window, dx = &gp+0x838).
  vwf.asm branches both typewriters to the page-at-once path: text appears a page, or up to the next wait code, at
  a time (the message-speed option no longer changes anything). A wait code mid-line resumes at the column, not the
  pixel (up to 11 px gap): keep waits at line ends in the English.
- EXE string tables: the u16 arrays and getters stay; strings go in a heap (tools/insert.py `Heap`: the original
  string blocks plus free kanji cells 0x11C-0x69F minus the icon/button cells), anywhere within 128 KB above the
  table's base (u16 word offsets).
- MSYS.DAT subfiles are found by a sector table at 0x8001273C (u16 start sector per subfile) and a count table at
  0x800126BC (u16, read as a byte); 63 subfiles. 0x8004CED8(n) loads subfile n + 6 to 0x80141778: items = subfile
  6 (n = 0), magic + skills = subfile 7 (n = 1; skills found at magic + magic's u32 size, 0x8004C13C). (Subfiles
  15-62 go to the 0x80117B98 buffer through 0x8004BC60; that is not where items load.) Phase 7: a grown subfile
  moves to the end of MSYS.DAT (tables re-pointed, `insert.msys_text`) and the heap base moves up (below).

## RAM map and the English size limits (phase 7; verified by disassembly + `tools/debug/heapwatch.lua`)
- 0x80128B98-0x8012FB98 (0x7000): scene slot. 0x80018BD4 loads entry N-280 to 0x80128B98 and entry N right after
  it; 0x8012FB98 is a fixed buffer (4 refs). JP's largest pair (scene 2) is 28632 bytes. `insert.scen_dat` fails
  the build when a scene outgrows the slot (or its JP size, if larger).
- 0x80141778: MSYS text buffer (subfile 6 or 7), JP 10 sectors, up to the heap.
- 0x80146778-0x80186778: heap. Base stored at gp+0xCC4 by 0x800C1AA4 / 0x800C1AD4 (lui/addiu pairs at 0x800C1AA8,
  0x800C1AD8) and range-checked at 0x800C2D58 (the only 3 refs); bump pointer gp+0xD0C (0x801145E8) starts at base
  + 0x800. High-water mark over all 67 warps (field, menus, event battles before they start, dungeons) and 14000
  mashed frames in 3 of them: 0x80166E58 (129 KB of 256), the same value everywhere. asm/vwf.asm sets HEAP_BASE from
  insert.py (buffer end, capped at `insert.HEAP_MAX`). **But the space above the bump pointer is not free**: with
  the base +0x3000 (12 KB) the gear_spell warp opened the field menu; with +0x4800 (18 KB, two builds) the menu
  never opened (Select did nothing, field kept running). The +0x3000 build also hung st_vac03/04/07 at ~f2000
  (2 runs each; original ROM lands them) - cause not isolated (heap shift, dictionary or scene text). So: assume
  any heap shift is unsafe until proven.

## Dictionary (phase 7; tools/dictenc.py, asm/vwf.asm, tests test_dict + test_vwf + test_insert English)
- English letter pairs cost ~1 byte per letter: item descriptions grew 20 KB -> 37 KB, 18 scenes outgrew the slot.
  Codes 0x4800 + i (past the pairs, below the 0xDFFF commands, so the printer sends them to the glyph routine) are
  dictionary entries: vwf_draw draws the entry's pair codes (0000-terminated) in one call and returns ceil(x/12).
- ~1070 entries (words / short phrases picked by gain, item descriptions weighted x3; 18 KB incl. the u16 offset
  table) live in the EXE heap (free font cells), offsets from 0x800F1938 (gen.inc DICT_TAB / DICT_BASE / DICT_N).
- Compressed: dialogue only (`dictenc.POOLS`; scen, term end, not choice lines). Not compressed: names, choice
  lines, EXE tables, MSYS. The compressor never starts a code past 276 px on its line (the printer auto-wraps
  there; the letter x does not depend on grouping). Result: SCEN sections 30-35% smaller than letter pairs, every
  scene inside the slot. **Dialogue boxes with dictionary codes not yet seen in-game.**
- MSYS descriptions with dictionary codes broke in the spell help box (work/qa/p7warp/gear_spell, shot kept in
  work/qa/z_spell.png): text clipped at ~266 px (the "r" of " power" half drawn), the rest of the line wrapped
  early, last row's tail dropped, stray pixels on a "b". Unicorn draws the same words correctly, so the game
  derives something (clear / upload width, or a line length) from the code count. Printer facts found while
  looking: per-code limit check at 0x8006F2E4: draw only while s6 < a3 (width) and x0 + s6 < limit[k], limit[0]
  = window x + w (- 1 when window+0x48 is set), limit[1] = x + w for kinsoku punctuation (gp+0x984..0x996 codes);
  else wrap (0x8006F324) if a row is left, else skip the code. A Lua read-watch of the MSYS buffer
  (probes/watch.lua, --debugger) caught only 3 reads, so the measuring code is still unknown.
- Idea for MSYS (untested): expand dictionary codes in the description getter into a scratch buffer, so the
  printer and any measuring code see plain letter pairs. Even so items would be ~29-32 KB > 0x5000.

## Free space
- Disc: files can grow (dumpsxiso/mkpsxiso rebuild re-lays the LBAs; the game finds files by CdSearchFile, so moved
  files are found by name - verified only by reading the code at 0x800181F0, prove with the phase 3 identity build).
- EXE (t_addr 0x80010000, t_size 0x104000 -> ends 0x80114000): no proven free space. Zero runs `tools/zeroruns.py`:
  0x80111A45 len 0x106B, 0x80113B26 len 0x4DA, 0x80112DE0 len 0x421 - may be runtime data (guess): write-watch before
  use. RAM 0x80114000-0x80128B98 is BSS/heap below the scene load area (guess). Phase 5 decides where VWF code goes.

## No text found
- MAP.DAT, MAGD.BIN, UPD.UPD, XATBL.DAT, FTIM.DAT, NEFF.BIN, SND.DAT: `tools/scantext.py` finds only noise.
- MOVIE0/1.STR: FMVs (subtitles? check in phase 8 tour), VOICE.XA voice clips.

## Prior work
- A PS1 English fan patch by poorchief/Rex exists only as a leaked beta whose team asked people not to redistribute
  it; not used. growlanser6english.blogspot.com (2020) reports 1-byte encoding + VWF work on the PSP version only.
  Official English names: the PSP remake "Growlanser: Wayfarer of Time" (Atlus USA, 2011) - use it for names (D2).
