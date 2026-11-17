# Growlanser (PS1, Atlus 1999, SLPS-02380/02381) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `~/.claude/plugins/marketplaces/retro-translation/skills/translate-retro-game/SKILL.md`; `$SKILL` = that directory, `python tools/skill.py` prints it). Read it before ROM, text or QA work.

## Commands (run from repo root)
- Build:    `python -X utf8 build.py` -> build/disc1/*.cue, build/disc2/*.cue (checks the dump against `rom.sha1` first) (not written yet: phase 3)
- Check:    `python -X utf8 tools/check.py` (tests + lint; the pre-commit hook runs this)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py "rom/Growlanser (Japan) (Disc 1).cue" --out work/qa/smoke --frames 2400 --mash 30 --mash-key start --smoke --sheet` (swap in the build's .cue)
- Warp:     `python -X utf8 $SKILL/scripts/emu.py <cue> --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='<name>'" --frames 900 --sheet` (scenes: `tools/debug/scenes.txt`; phase 2; never ask the user to play to a scene)
- Release:  `python -X utf8 tools/release.py` (xdelta per .bin + verify; never publish without the user) (phase 9)
- Clean:    `python -X utf8 tools/clean.py`

## Paths
- Original discs: `rom/` (gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Disc 2 has an audio track 2.
- Emulator: `tools/pcsx/` (PCSX-Redux nightly 31789.20261117, `$SKILL/scripts/fetch_emu.py pcsx`; BIOS `tools/bios/scph5500.bin` via `fetch_emu.py psx-bios`). Disc tools: `tools/mkpsxiso/` (mkpsxiso/dumpsxiso v2.30, github.com/Lameguy64/mkpsxiso), `tools/armips/` (v0.11.0). All gitignored; re-fetch on a fresh clone. Savestates: `work/states/`.
- Unpacked discs: `work/disc{1,2}/tree/` + `layout.xml` (`dumpsxiso -x tree -s layout.xml <cue>`). Both discs share byte-identical data files and EXE (`SLPS_023.80` == `SLPS_023.81`).
- Text: `script/` (TSV). Tables: `tbl/`. Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the plugin's agent types as `translate-retro-game:<type>` (Claude Code), `.codex/agents/` (Codex) or `.opencode/agents/` (opencode), never general-purpose.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the save into `work/states/`, reproduce, fix, commit with `Fixes #N`, update `docs/status.md`.
- Hooks: `git config core.hooksPath tools/hooks` once per clone.
- One translation patches both discs: every text change must be applied to disc 1 and disc 2.

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
