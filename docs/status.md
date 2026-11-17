# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1. Research and recon in progress (text side done; graphics-text survey not finished). Last build: none (2026-11-17).
- **Done:**
  - Step 0: template, tools fetched (PCSX-Redux nightly 31789, SCPH-5500 BIOS, mkpsxiso 2.30, armips 0.11.0 in
    `tools/`, gitignored), rom.sha1 (3 bins), check + pre-commit hook proven (failing test blocks commit), guard
    hook proven (sed -i blocked), boot route `tools/routes/boot.txt` (scripted input proven: title cursor moves).
    Not proven: GUI keyboard input (needs a human; headless only).
  - Phase 1 text recon (docs/re/text.md): u16 glyph-index encoding, EXE font 12x12 1bpp at 0xE85C8, `tbl/jp.tbl`
    (1960+ codes, MS Gothic match + context fixes), control codes and arg counts from the draw loop, SCEN.DAT
    archive + scene text section format (24,113 strings in 245 entries, roundtrip test), EXE name/item/system text
    at 0xE2000-0xE8000 + F4xx dictionary at 0xE8004, MSYS.DAT item descriptions. No text in MAP/MAGD/UPD/XATBL/FTIM.
  - Both discs share byte-identical EXE + data: one text patch, applied to both images.
- **Next:**
  1. Finish phase 1 graphics survey (docs/re/graphics.md "Still to do": MSYS.DAT graphics format, VRAM dumps of menus).
  2. Phase 1 leftovers worth doing early in phase 4: EXE u16 word-offset tables (base per block), MSYS.DAT layout,
     free RAM / scene load-buffer size (scene entries must grow ~2x for English).
  3. Phase 2 debug tool: savestates from the new-game route are in work/qa/ng/s00N000.sstate (frame 3000 = first
     dialogue); scene warp needs the scene-load call (SCEN entry index) found from the draw loop at 0x8006EBAC.
- **Open bugs:** none.
- **Waiting on the user:** nothing (all once-per-project questions answered in docs/decisions.md).
- **Engine notes for phase 5:** every glyph is a 12 px cell and codes are 16-bit, so English text costs 2 bytes/letter
  in a 12 px cell: a VWF (or 2 letters per cell) is required, and SCEN sections will roughly double.
