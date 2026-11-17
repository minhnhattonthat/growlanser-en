# Graphics-text survey (phase 1, IN PROGRESS)

Tools: `tools/timscan.py FILE --render DIR` (raw TIMs), `$SKILL/scripts/emu.py ... --script $SKILL/scripts/lua/probes/ppudump.lua`
(PCSX-Redux VRAM dump: 1024x1024 u16 words in the file; rows 0-511 are the real 1024x512 VRAM).

## Static sweep so far
| File | Raw TIMs | Japanese text? |
|---|---|---|
| FTIM.DAT | 83 (8bpp 256x256) | no: character portraits (work/gfx/ftim_sheet.png) |
| MAGD.BIN | 67 | no: spell effects |
| UPD.UPD | 7 | no: effects |
| NEFF.BIN | 3 | no |
| SLPS_023.80, MSYS.DAT, SCEN.DAT, MAP.DAT | 0 raw TIMs | **not swept yet**: graphics are stored in another (packed/raw) form |

## Seen on screen (boot to first dialogue, work/qa/ng)
- Title: logo "GROWLANSER" in Latin letters plus a katakana subtitle グローランサー under it (graphics, VRAM 16bpp
  region of the title). D5: the logo has an official English form already; the katakana subtitle must be replaced
  or removed. Menu items START / LOAD / CONFIG / ... are English graphics already. "© ATLUS / CAREER SOFT 1999" English.
- Dialogue box speaker tag (e.g. 女, 男, ルイセ) is drawn with the text font from the scene's name strings: text, not graphics.
- In-game VRAM (work/qa/vram1/vram16.png): menu icon labels SAVE / MENU / LOAD / SORT are English; a strip at
  VRAM x~640-700, y~130-250 holds Japanese-looking labels (not identified yet).

## Still to do (phase 1 done-when)
1. Find the MSYS.DAT graphics format (starts with 0xEE padding; menus/windows live there) and render it; same for
   MAP.DAT entries and SCEN.DAT entries 0-155 / 560-715 (non-text data, may hold TIM-like blocks).
2. VRAM dumps of: title, main menu, status, item, magic, config, save/load, shop, battle HUD, level-up, game over,
   chapter/area banners, ending + credits (the debug tool from phase 2 reaches the later ones; list them then).
3. Identify the VRAM x~640-700 y~130-250 labels.
