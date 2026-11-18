"""dictenc.py: English word dictionary, so the script fits the game's RAM (used by tools/insert.py).

    python -X utf8 tools/dictenc.py        build the dictionary, print its size and the bytes saved per pool

English costs ~1 byte per letter (letter pairs), JP 2 bytes per character but far fewer characters: item
descriptions grew from 20 KB to 37 KB (load buffer 0x80141778 holds 20 KB, scene data follows), and 18 scenes
outgrew the 0x7000 scene slot (0x80128B98-0x8012FB98). Codes DICT + i (0x4800-0x57FF, past the pair codes) stand
for dictionary entry i; asm/vwf.asm draws an entry's letters in one call (docs/re/text.md "Dictionary").

Only dialogue (scen, term end, not a choice line) is compressed (POOLS): names, choice lines, EXE tables and MSYS
descriptions stay letter pairs, because some code sizes help-box text by its code count (docs/re/text.md).
Width rule (docs/windows.md): the printer auto-wraps when a code starts past 12 * (W - 1) px, so the compressor
never starts a code there (x per letter does not depend on how letters are grouped into codes).
"""
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import enfont  # noqa: E402
import fit  # noqa: E402
import gltext  # noqa: E402

DICT = 0x4800
MAXN = 0x1000
N = 1536  # candidates tried
BUDGET = 18000  # bytes for entries + offset table (EXE heap: ~23 KB free after the English tables)
LIMIT = 12 * (24 - 1)  # dialogue box and help box: 24 cells
POOLS = ("scen",)  # fit.BUDGETS keys compressed (msys help boxes clip dictionary text: docs/re/text.md)
WEIGHT = {}  # pool -> weight when picking entries
TOKENS = re.compile(r"(?:^| )[A-Za-z0-9'\-]+(?: [A-Za-z0-9'\-]+){0,2}[,.!?]?")


def compressible(e):
    if not e.get("en") or e["id"].startswith("exe."):
        return False
    return fit.budget(e["id"], e)[0] in POOLS


class Dict:
    def __init__(self, entries, codec=None, font=None):
        self.codec, self.font = codec or enfont.EnCodec(), font or enfont.load()
        self.entries = list(entries)
        self.index = {s: i for i, s in enumerate(self.entries)}
        self.lens = sorted({len(s) for s in self.entries}, reverse=True)

    def adv(self, ch):
        return self.font[ch][2]

    def compress(self, words, uses=None):
        """words (EnCodec output) -> same text with dictionary codes; no code starts past LIMIT px on its line."""
        out, run, x0, x, i = [], [], 0, 0, 0

        def flush():
            nonlocal x0
            if run:
                out.extend(self._run("".join(run), x0, uses))
                run.clear()
            x0 = x
        while i < len(words):
            w = words[i]
            i += 1
            if enfont.PAIR <= w < enfont.PAIR + 0x4000:
                for k in ((w - enfont.PAIR) >> 7, w & 0x7F):
                    if k:
                        ch = self.codec.rev[k]
                        run.append(ch)
                        x += self.adv(ch)
                continue
            flush()
            out.append(w)
            if w in (0xFFFC, 0xFFFD):
                x = 0
            elif w in gltext.ARG1:
                out.append(words[i])
                i += 1
                if w == 0xF600:
                    x += fit.SUB_PX
            elif w < 0xF000:
                x += 12
            x0 = x
        flush()
        return out

    def _run(self, s, x0, uses):
        n, xs = len(s), [x0]
        for ch in s:
            xs.append(xs[-1] + self.adv(ch))
        inf = 1 << 30
        cost, step = [inf] * n + [0], [0] * (n + 1)
        for p in range(n - 1, -1, -1):
            if xs[p] > LIMIT:
                continue
            if p + 1 == n or cost[p + 1] < cost[p + 2]:
                best, bl = cost[p + 1], 1  # one letter
            else:
                best, bl = cost[p + 2], 2  # a letter pair
            if p == 0 or s[p] == " " or not s[p - 1].isalnum():
                for ln in self.lens:
                    if p + ln <= n and cost[p + ln] < best and s[p:p + ln] in self.index:
                        best, bl = cost[p + ln], ln
            cost[p], step[p] = best + 1, bl
        if cost[0] >= inf:  # cannot happen when the pair encoding passes the lint; keep the pairs
            return self.codec.encode(s)
        out, p = [], 0
        while p < n:
            ln = step[p]
            if ln <= 2:
                out.extend(self.codec.encode(s[p:p + ln]))
            else:
                k = self.index[s[p:p + ln]]
                out.append(DICT + k)
                if uses is not None:
                    uses[k] += 1
            p += ln
        return out

    def blobs(self):
        """Each entry as its pair codes (u16 LE) + 0000."""
        return [gltext.pack(self.codec.encode(s) + [0]) for s in self.entries]


def build(docs):
    """Dictionary for the compressible entries of docs (deterministic)."""
    codec, font = enfont.EnCodec(), enfont.load()
    items = [(d_id(e), codec.encode(e["en"])) for d in docs for e in d["entries"] if compressible(e)]
    cand = Counter()
    for pool, words in items:
        wt = WEIGHT.get(pool, 1)
        for run in re.split(r"[^%s]+" % re.escape("".join(codec.cs)), codec.decode(_letters(words))):
            for m in TOKENS.finditer(run):
                cand[m.group(0)] += wt
                if m.group(0)[-1] in ",.!?":
                    cand[m.group(0)[:-1]] += wt
    def est(s):
        return cand[s] * (len(s) - 2) - (len(s) + 6)  # bytes: ~1 per letter saved minus 2 per code, entry cost
    pool_c = sorted((s for s in cand if len(s) >= 3 and est(s) > 0), key=lambda s: (-est(s), s))
    chosen, rest = pool_c[:N], pool_c[N:]
    for _ in range(3):
        d = Dict(chosen, codec, font)
        uses = Counter()
        for pool, words in items:
            d.compress(words, uses)
        gain = {s: uses[k] * (len(s) - 2) - (len(s) + 6) for k, s in enumerate(chosen)}
        keep = sorted((s for s in chosen if gain[s] > 0), key=lambda s: (-gain[s], s))
        chosen = keep + rest[:N - len(keep)]
        rest = rest[N - len(keep):]
    size, final = 0, []
    for s in keep:  # best first, within the EXE space
        size += 2 * len(codec.encode(s)) + 4
        if size > BUDGET:
            break
        final.append(s)
    return Dict(sorted(final, key=lambda s: (s.lower(), s)), codec, font)


def _letters(words):
    """Pair codes kept, every other code replaced by a code that decodes to a non-letter separator."""
    return [w if enfont.PAIR <= w < enfont.PAIR + 0x4000 else 0xFFFC for w in words]


def d_id(e):
    return e["id"].rsplit(".", 1)[0]


if __name__ == "__main__":
    import insert
    docs = list(insert.docs())
    d = build(docs)
    print("%d entries, %d bytes + %d table" % (len(d.entries), sum(map(len, d.blobs())), 2 * len(d.entries)))
