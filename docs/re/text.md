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
- Load buffer size for a scene: unknown yet (phase 5: find the read size / RAM area before growing entries).

## EXE text (guess on structure, verified content by decoding)
- 0xE2000-0xE8000: system messages, memory-card prompts, config menu, character/enemy names, skill, item, place
  names, item descriptions (some). Strings end with FFFF; no absolute pointers to them exist (searched), blocks are
  preceded by u16 tables of **word** offsets (e.g. 0xE3300..0xE3372 ascending 0x216..0x278). Base and every table:
  phase 4.
- 0xE8004-0xE85C8: word dictionary for F4xx codes ("その代償として", "といわれる", ...), FFFF-terminated.
- 0xE0000-0xE1FFF: tables only (noise in the scan).

## MSYS.DAT
- Item/equipment descriptions at ~0x42A00+, preceded by a u16 offset table, text uses F4xx dictionary codes.
  The rest of MSYS.DAT (2.4 MB) is mostly graphics. Structure: phase 4.

## No text found
- MAP.DAT, MAGD.BIN, UPD.UPD, XATBL.DAT, FTIM.DAT, NEFF.BIN, SND.DAT: `tools/scantext.py` finds only noise.
- MOVIE0/1.STR: FMVs (subtitles? check in phase 8 tour), VOICE.XA voice clips.

## Prior work
- A PS1 English fan patch by poorchief/Rex exists only as a leaked beta whose team asked people not to redistribute
  it; not used. growlanser6english.blogspot.com (2020) reports 1-byte encoding + VWF work on the PSP version only.
  Official English names: the PSP remake "Growlanser: Wayfarer of Time" (Atlus USA, 2011) - use it for names (D2).
