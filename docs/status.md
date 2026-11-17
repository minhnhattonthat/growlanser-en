# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool not started (phase 1 recon done 2026-11-17). Last build: none.
- **Done:**
  - Step 0: template, tools fetched (PCSX-Redux nightly 31789, SCPH-5500 BIOS, mkpsxiso 2.30, armips 0.11.0 in
    `tools/`, gitignored), rom.sha1 (3 bins), check + pre-commit hook, guard hook, boot route `tools/routes/boot.txt`.
    Not proven: GUI keyboard input (needs a human; headless only).
  - Phase 1 text recon (docs/re/text.md): u16 glyph-index encoding, EXE font 12x12 1bpp at 0xE85C8, `tbl/jp.tbl`,
    control codes, SCEN.DAT archive + scene text format (roundtrip test), EXE name/item/system text, F4xx dictionary,
    MSYS.DAT item descriptions. Scene load in RAM (entries N-280, N, N+280 back-to-back from 0x80128B98), CD file
    table + read-request handler (0x8001835C), free-space notes.
  - Phase 1 graphics survey (docs/re/graphics.md): static sweep of MSYS.DAT, MAP.DAT (2133 pages), TIM files, EXE,
    FMV samples. Japanese graphics G1-G8: title katakana + キャリアソフト (MAP 1161), affinity/element kanji (MSYS
    0x9100), appendix menu (MSYS 0x7C000), credits cast/staff (MAP 1257), kana atlas (MAP 1257 ~0x80000, name entry?),
    unknown atlas (MAP 1151), FMV logo subtitle (both STRs). Most UI art is already English.
- **Next (phase 2, debug tool):**
  1. Scene warp: hook the read-request handler 0x8001835C / scene-load path (docs/re/text.md "File reads") to load
     a chosen SCEN entry N (280-559) from a cold boot; write `tools/debug/warp.lua` + `tools/debug/scenes.txt`.
  2. Scene list must include: title, new game, name entry, field + menu screens (status, item, magic, equip,
     config, save/load, shop), battle HUD, level-up, game over, each chapter card, ending, credits, appendix room.
     Use them to confirm G2-G7 on screen (graphics.md "Still open"). Savestates: work/qa/ng/s00N000.sstate (frame
     3000 = first dialogue, scene 280); title state work/qa/vram_title/title.sstate.
  3. Phase 4 leftovers: EXE u16 word-offset tables (base per block), MSYS.DAT text table layout (0x42800, 0x47800).
- **Open bugs:** none.
- **Waiting on the user:** nothing (all once-per-project questions answered in docs/decisions.md).
- **Engine notes for phase 5:** every glyph is a 12 px cell and codes are 16-bit, so English text costs 2 bytes/letter
  in a 12 px cell: a VWF (or 2 letters per cell) is required, and SCEN sections will roughly double. Scene entries
  are packed back-to-back in RAM: find the allocator/cap before growing them.
