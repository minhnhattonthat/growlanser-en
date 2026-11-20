Growlanser - English translation patch v{VERSION}
=================================================

Unofficial fan translation of Growlanser (PlayStation, Atlus / Career Soft, 1999; SLPS-02380/02381).
This zip holds only patches: no game data. You need your own dump of the Japanese discs (Redump).
Do not share patched disc images.

What is translated
------------------
Everything the game shows as text: dialogue on both discs, menus, items, spells, skills, help, title screen, chapter
and battle cards, status graphics and the credits roll. The name-entry keyboard keeps the game's kana and full-width
Latin grids (use the Latin grid for English names). Voice acting stays Japanese.

How to patch
------------
Use xdelta3 (or Delta Patcher, https://github.com/marco-calautti/DeltaPatcher) on each .bin listed below:

    xdelta3 -d -s "Growlanser (Japan) (Disc 1).bin" "Growlanser (Japan) (Disc 1).xdelta" "Growlanser (Disc 1) [EN].bin"

Keep the patched .bin next to a copy of the original .cue, with the FILE line in the .cue renamed to the new .bin
name (disc 2: rename the Track 1 line; Track 2 is unchanged and stays as it is).

Required files (Redump) and results
-----------------------------------
{FILES}
Notes
-----
- Tested in PCSX-Redux. Start from a cold boot: a savestate made on the Japanese game keeps the old code and font.
  Memory card saves carry over.
- Known issue: the message-speed option has no effect (text prints a page at a time).
- Bugs: https://github.com/minhnhattonthat/growlanser-en/issues (a savestate helps).

Credits
-------
Translation, tools and hacking: minhnhattonthat, made with extensive AI assistance (Claude by Anthropic).
Growlanser is (c) Atlus / Career Soft. This project is not affiliated with them.
