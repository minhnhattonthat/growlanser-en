references/platform-ps1.md: PCSX-Redux getVRAM() dump via ppudump.lua is 2 MB (1024x1024 u16); only rows 0-511 are real VRAM.
references/platform-ps1.md: games that ship a fixed 12px kanji font often copy MS Gothic's 12px bitmaps; a pixel match against msgothic.ttc at size 12 identified 1859/1995 glyphs exactly (tools/fontmatch.py in growlanser-en).
references/emulator-qa.md: emu.py --state-in restarts frame numbering at 0, so --shots/DUMP_AT count from the state, not from boot.
