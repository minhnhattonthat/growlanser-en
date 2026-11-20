# Growlanser English translation

Unofficial English fan translation of **Growlanser** (PlayStation, Atlus / Career Soft, 1999; SLPS-02380/02381):
the source text and tools that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Dialogue / story (both discs, every scene, endings) | Translated |
| Menus, items, spells, skills, classes, help, system messages | Translated |
| Title screen, chapter and battle cards, status graphics, appendix rooms, credits roll | Translated |
| Name entry | Keyboard keeps the game's kana and full-width Latin grids (each key is one character code); use the Latin grid for English names |
| Voice acting, songs | Japanese audio (not subtitled beyond the text boxes the game already shows) |

Known issues: the message-speed option has no effect (text prints a page at a time); see [Issues](../../issues).

## Base dump (Redump, Growlanser (Japan))

| File | Size | CRC32 | MD5 | SHA-1 |
|---|---|---|---|---|
| Growlanser (Japan) (Disc 1).bin | 736408848 | 7180DFD0 | 8c03397f19347383199bba84c4baa8bf | 78a595317b9ed3a7d6bbdcff48f6144cbff38a48 |
| Growlanser (Japan) (Disc 2) (Track 1).bin | 670590480 | 53DF3E70 | 6282b5df449afe43c5b79daae885ca8f | 572dae9c95a84fe93ec209f7fcffa745bb57014d |
| Growlanser (Japan) (Disc 2) (Track 2).bin | 51010176 | 2C07FC5E | 89c57293e94f8b11b4faf9f81568903d | 485017be606e6b517760076c9b05ceba89f5cdba |

Disc 2 track 2 (audio) is unchanged. Tested in PCSX-Redux; start from a cold boot (a savestate made on the Japanese
game keeps the old code and font in memory). Saves on the memory card carry over.

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `asm/`, `font/` | Variable-width font routine (armips) and the English font. |
| `tests/` | Test suite (disc-dependent tests skip when the dump is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.codex/agents/`, `.opencode/agents/` | Subagent types (translator, reviewer, visual QA, playtester, graphics) for Codex and opencode; Claude Code gets them from the plugin. |

## Build your own patched discs

Needs Python 3.12+, your own dump (the three .bin files above plus their .cue files in `rom/`), and mkpsxiso,
armips and jPSXdec in `tools/` (see `AGENTS.md`). The build refuses any other dump (see `rom.sha1`).

```sh
git clone https://github.com/minhnhattonthat/growlanser-en
cd growlanser-en
python -X utf8 build.py                  # -> build/disc1/*.cue, build/disc2/*.cue
python -X utf8 tools/check.py            # tests + text lint
python -X utf8 tools/release.py          # every gate, then xdelta patches + zip in release/
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Atlus's and is included only so the
translation can be checked against it. Growlanser is (c) Atlus / Career Soft; this project is not affiliated with
them. Unofficial: do not share patched disc images.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
