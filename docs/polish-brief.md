# Polish brief - Growlanser (PS1)

You settle one polish batch: reviewer Minors on already-translated lines. Style, glossary and code rules are those of
`docs/translator-brief.md` (read it first, in parts with offset/limit: whole-file Reads return a stub), plus
`docs/style-reference.md` and `glossary.md`. Edit nothing but your two output files; no git, no subagents.

## Input: `work/tl/pNN.tsv`
One row per string id: `id <TAB> JP <TAB> current English ({n} shown as a space) <TAB> notes` (several reviewer
notes for the same id joined by ` || `; they may disagree: pick the best, or none).

## Decide per id
- **fix** when a note is right: wrong meaning, a flattened voice, an awkward phrase, an inconsistency with the
  glossary or with another line it names. Write the whole new English for that id, in running form: no `{n}`, the
  wrapper re-breaks lines. Keep every other code of the current English exactly (`{v:XXXX}` voice codes, `{p}` before
  them, colour codes like `{FFEF}..{FFF1}`, `{s:XXXX}` names, `[XXXX]` glyphs, leading/trailing blanks: same count and
  order). Item, spell and skill names (exe.items, exe.magic, exe.skills, exe.classes, exe.names, exe.places, exe.units)
  have hard pixel limits: keep a fix no longer than the current English unless the note is about a cut word.
- **keep** when the note is wrong, a matter of taste, or the fix would not fit: copy the current English unchanged
  (with the codes, no `{n}`).
- Names and terms: glossary.md wins over a note. A note that asks to rename an item/term used elsewhere: grep
  `script/` for the other uses; if they would all need changing, keep and say so.
- Check a fix with `python -X utf8 tools/batches.py wrap ID "English"` (prints the layout and "OK" or the problems).
  A fix that won't fit after a rephrase: keep the old line and waive.

## Output (both files, same ids, same order as pNN.tsv)
- `work/tl/pNN.out.tsv`: `id <TAB> English`.
- `work/tl/pNN.notes.tsv`: `id <TAB> fixed` or `id <TAB> waived: <reason, one short clause>`.
Then run `python -X utf8 tools/batches.py check pNN` and fix until it prints OK. Final message: one line,
`pNN: N fixed, M waived, check OK`.
