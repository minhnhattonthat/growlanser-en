# Glossary - Growlanser

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.
The tables are lint-enforced (`tools/batches.py`): a JP form in the line needs one of the EN forms (`/` separates
alternatives); an Avoid spelling fails.

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics: kept, hyphenated (Tippi-chan, Luise-san). Kinship and role terms are translated, not kept:
  お兄ちゃん "Big Brother" (Luise to the hero; "big bro" never), お母さん "Mother"/"Mom", マスター "Master".
  Name order: Western (given name first).
- Romanisation source: no official English Growlanser I exists (D2): names follow the established fan spellings
  (growlanser.net, fan wiki), else the natural English/European form the katakana spells (リシャール Richard,
  ヴェンツェル Wenzel), else Hepburn without macrons. Recorded as D9.
- Credits: English.
- Register: fantasy-medieval setting, natural modern English. No thee/thou; royalty and knights speak formally,
  soldiers and mercenaries plainly, Tippi cheekily. Sound effects: plain words with asterisks, `*thud*`.
- Abbreviations: full names and terms everywhere, prefer engine changes over shortening.
- The player names the hero; his name is the variable `{s:0000}` (other `{s:XXXX}` are other drawn names). Copy
  every `{s:XXXX}` exactly; a possessive `'s` after it is fine, no other suffix ("1st", "-kun" glued on).

## Style rules
- Punctuation map: 「」 -> "...", 『』 -> '...' (titles, quoted terms), ‥‥ / ・・・ -> ..., ！？ -> ?!, ～ -> drop or
  stretch the word ("Heyyy"), ★ -> drop (no glyph; ♪ and ♥ exist), （…） -> (...).
- Font: ASCII letters and punctuation plus é … — ♪ ♥. No `# @ \ ^ \` { | }` (braces only in control codes).
- Voices: docs/style-reference.md.

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ティピ | Tippi | | homunculus fairy made by Sandra; cheeky, calls the hero アンタ "you" | Tipi |
| ルイセ | Luise | | Sandra's daughter, the hero's adoptive sister; shy, calls him お兄ちゃん | Ruise / Louise |
| サンドラ | Sandra | | Court Magician of Rolandia, the hero's adoptive mother; calm, polite | |
| ウォレス | Wallace | | one-eyed former mercenary captain | |
| アリオスト | Ariost | | half-Featherian researcher who dreams of flight | |
| エリオット | Elliot | | boy who looks exactly like Richard | Eliotte |
| ゼノス | Xenos | | swordsman, Karen's brother | Zenos |
| カレン | Karen | | healer, Xenos's sister | |
| ミーシャ | Misha | | Magic Academy student | |
| ジュリアン | Julian | | Burnstein officer | Jurian |
| ジュリア | Julia | | | |
| アルカディウス | Alcadius | | King of Rolandia | Arcadius |
| レティシア | Leticia | | Princess of Rolandia | |
| アンジェラ | Angela | | Queen Mother of Rolandia | |
| ステラ | Stella | | Featherian queen | |
| オスカー | Oscar | | Imperial Knight; full name Oscar Reeves (オスカー・リーヴス) | |
| リーヴス | Reeves | | | |
| アーネスト | Ernest | | Imperial Knight; full name Ernest Lyell | |
| ライエル | Lyell | | | |
| リシャール | Richard | | Burnstein Imperial Knight master, later king | Richart / Richar |
| ガムラン | Gamlan | | | |
| ベルナード | Bernard | | general | |
| ブロンソン | Bronson | | general | |
| ウェーバー | Weber | | general | |
| ヴェンツェル | Wenzel | | | Venzern / Ventzel |
| シエラ | Sierra | | | |
| ベルガー | Berger | | | |
| ブラッドレー | Bradley | | Magic Academy vice-headmaster | |
| マクスウェル | Maxwell | | Magic Academy headmaster | |
| アイリーン | Irene | | | |
| エレナ | Elena | | | |
| レダ | Leda | | | |
| オズワルド | Oswald | | | |
| ユング | Jung | | | |
| ゲーヴ | Gev | | | |
| ゲヴェル | Gevel | | | |
| グレンガル | Grengal | | | |
| ラルフ | Ralph | | | |
| ニック | Nick | | | |
| ダグラス | Douglas | | | |
| ジーナ | Gina | | | |
| 仮面騎士 | Masked Knight | | | |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ローランディア | Rolandia | | kingdom | |
| バーンシュタイン | Burnstein | | kingdom | Burnshutain |
| ランザック | Ranzak | | kingdom | Ranzack |
| ローザリア | Rosaria | | royal capital of Rolandia (王都ローザリア "the royal capital, Rosaria") | |
| デリス | Delis | | village | |
| ブローニュ | Boulogne | | village | |
| メディス | Medis | | village | |
| ラシェル | Rachelle | | town | |
| グランシル | Grancil | | town | |
| コムスプリングス | Comsprings | | town | |
| ガルアオス | Garuaos | | prison | |
| ヴァルミエ | Valmier | | mining town | |
| クレイン | Crane | | village | |
| シュッツベルグ | Schutzberg | | | |
| ガラシールズ | Galashiels | | | |
| ラージン | Rajin | | fort (ラージン砦 Fort Rajin) | |
| フェザーランド | Featherland | | | |
| オリビエ | Olivier | | lake (オリビエ湖 Lake Olivier) | |
| 魔法学院 | Magic Academy | | | |
| 時空制御塔 | Space-Time Control Tower | | | |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| グローシアン | Growsian | | people born under an eclipse with great magic power | Growshian |
| グローシュ | Grosh | | the magic energy Growsians draw on | |
| フェザリアン | Featherian | | winged people | |
| ホムンクルス | homunculus | | (pl. homunculi) | |
| インペリアル・ナイト | Imperial Knight | | Burnstein's elite knights | |
| 宮廷魔術師 | Court Magician | | | |
| 送魔線 | mana line | | lines that carry magic power between towns; 送魔線技師 "mana line engineer" | |
| 闘技大会 | tournament | | | |
| 傭兵 | mercenary | | | |
| エルム | Elm | | currency ("75 Elm") | |

## Decisions from earlier batches
- (none yet)
