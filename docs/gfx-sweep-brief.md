# Graphics static sweep: reviewer brief (read-only)

You review raw-render sheets of a Japanese PS1 game (Growlanser) for **Japanese text drawn as graphics**.

- Each sheet is a PNG of grey strips; the label above each strip is `entry:offset` (MAP.DAT) or a hex file offset (MSYS.DAT).
  Pixels are raw 4bpp/8bpp data shown in grey, so pictures look noisy or doubled; text still shows as glyph shapes.
- Open every sheet assigned to you with your image-viewing tool. Zoom (crop) any area that might hold text.
- Report every cell that shows **Japanese** (hiragana, katakana, kanji), even a single character or a partial glyph run.
  English/Latin text, digits and pictures are not findings, but list English words you can read in a second section
  (one line per sheet, short) so the survey knows what is already English.
- Do not edit any file except the output file named in your task.

Output: a TSV at the path in your task, columns `sheet  strip_label  y_px  text_or_description  confidence(high/low)`,
one row per Japanese element; then a line `# english:` per sheet with English words seen; then `# reviewed: N sheets`.
If a sheet has nothing Japanese, write no row for it (it still counts in `reviewed`).
