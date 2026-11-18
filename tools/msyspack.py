"""msyspack.py: Huffman-packed MSYS descriptions (items, magic, skills), unpacked per string by asm/vwf.asm.

    python -X utf8 tools/msyspack.py        build the model, print packed sizes per pool

English item descriptions are 37 KB as letter pairs; the load buffer at 0x80141778 holds 20 KB and the heap follows
(docs/re/text.md "RAM map"). Each string is packed as a canonical Huffman bit stream (MSB first) over symbols; the
six description getters (0x80070EC0..) unpack it into a scratch slot as ordinary pair codes, so the printer and any
measuring code see what an unpacked build would give them.

Symbols: events (a letter index 1-127, or a raw u16 word >= 0x80: control, icon, legacy glyph), END, and byte-pair
merges (symbol = two symbols, built by BPE). The unpacker pairs letters exactly like enfont.EnCodec (a letter run is
cut by any raw word). Model blob (u16 words): maxlen, counts[1..maxlen], then per symbol in canonical order L, R:
R = 0xFFFF: event L (0 = END); else the canonical indexes of the two halves.
"""
import heapq
import struct
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import enfont  # noqa: E402

END = -1
MERGES = 700  # BPE merges; model ~4 bytes per symbol, stored in the EXE heap (~5 KB free after the dictionary)
DEPTH = 24  # max merge depth (unpacker stack)
LEAF = 0xFFFF


def events(words):
    """Event list of an encoded string (pair codes split into letter indexes, other words raw)."""
    out = []
    for w in words:
        if enfont.PAIR <= w < enfont.PAIR + 0x4000:
            out += [w - enfont.PAIR >> 7] + ([w & 0x7F] if w & 0x7F else [])
        elif w >= 0x80:
            out.append(w)
        else:
            raise ValueError("word 0x%04X: the unpacker tells letters from raw words by value" % w)
    return out


def section_words(packed):
    """A packed string as the u16 words textsec.build_section takes."""
    return list(struct.unpack("<%dH" % (len(packed) // 2), packed))


def pairs(evs):
    """Pair codes of an event list (what the unpacker writes)."""
    out, pend = [], 0
    for e in evs:
        if e < 0x80:
            if pend:
                out.append(enfont.PAIR + (pend << 7) + e)
                pend = 0
            else:
                pend = e
        else:
            if pend:
                out.append(enfont.PAIR + (pend << 7))
                pend = 0
            out.append(e)
    if pend:
        out.append(enfont.PAIR + (pend << 7))
    return out


def _lengths(freq):
    """Huffman code length per symbol."""
    if len(freq) == 1:
        return {next(iter(freq)): 1}
    h = [(f, i, (s,)) for i, (s, f) in enumerate(freq.items())]
    heapq.heapify(h)
    depth, n = Counter(), len(h)
    while len(h) > 1:
        f1, _, a = heapq.heappop(h)
        f2, _, b = heapq.heappop(h)
        for s in a + b:
            depth[s] += 1
        heapq.heappush(h, (f1 + f2, n, a + b))
        n += 1
    return dict(depth)


class Model:
    def __init__(self, strings, merges=MERGES):
        """strings: event lists (each ends with its terminator word). Symbols: events as themselves, merge k as
        0x10000 + k, END as -1."""
        seqs = [list(s) for s in strings]
        self.merge, self.passes, depth = [], [], {}
        while len(self.merge) < merges:
            cnt = Counter()
            for s in seqs:
                cnt.update(zip(s, s[1:]))
            chosen, used = {}, set()
            for (a, b), n in cnt.most_common():
                if n < 3 or len(chosen) >= 32 or len(self.merge) + len(chosen) >= merges:
                    break
                d = 1 + max(depth.get(a, 0), depth.get(b, 0))
                if a in used or b in used or d > DEPTH:
                    continue
                sym = 0x10000 + len(self.merge) + len(chosen)
                chosen[(a, b)] = sym
                depth[sym] = d
                used |= {a, b}
            if not chosen:
                break
            for (a, b), sym in sorted(chosen.items(), key=lambda kv: kv[1]):
                self.merge.append((a, b))
            self.passes.append(chosen)
            seqs = [self._apply(s, chosen) for s in seqs]
        self.ranks = {ab: 0x10000 + k for k, ab in enumerate(self.merge)}
        freq = Counter(x for s in seqs for x in s) + Counter({END: len(seqs)})
        for k, (a, b) in enumerate(self.merge):  # keep every merge's halves in the alphabet
            for x in (a, b):
                freq.setdefault(x, 1)
            freq.setdefault(0x10000 + k, 1)
        self.lens = _lengths(freq)
        self.maxlen = max(self.lens.values())
        assert self.maxlen <= 24
        self.order = sorted(self.lens, key=lambda s: (self.lens[s], (1 << 20) if s == END else s))
        self.codes, code, prev = {}, 0, self.lens[self.order[0]]
        for s in self.order:
            code <<= self.lens[s] - prev
            prev = self.lens[s]
            self.codes[s] = code
            code += 1

    @staticmethod
    def _apply(s, chosen):
        out, i = [], 0
        while i < len(s):
            if i + 1 < len(s) and (s[i], s[i + 1]) in chosen:
                out.append(chosen[(s[i], s[i + 1])])
                i += 2
            else:
                out.append(s[i])
                i += 1
        return out

    def tokens(self, evs):
        s = list(evs)
        for chosen in self.passes:  # the training passes, in order
            s = self._apply(s, chosen)
        return s + [END]

    def pack(self, evs):
        """Bytes of one string (padded to an even length)."""
        bits = "".join(format(self.codes[s], "0%db" % self.lens[s]) for s in self.tokens(evs))
        bits += "0" * (-len(bits) % 16)
        return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))

    def blob(self):
        ids = {s: i for i, s in enumerate(self.order)}
        counts = Counter(self.lens.values())
        words = [self.maxlen] + [counts[n] for n in range(1, self.maxlen + 1)]
        for s in self.order:
            if s >= 0x10000:
                a, b = self.merge[s - 0x10000]
                words += [ids[a], ids[b]]
            else:
                words += [0 if s == END else s, LEAF]
        return struct.pack("<%dH" % len(words), *words)


def unpack(blob, data, at=0):
    """Reference unpacker (mirrors asm/vwf.asm msys_unpack): pair codes of the string at data[at:]."""
    w = struct.unpack("<%dH" % (len(blob) // 2), blob)
    maxlen = w[0]
    counts, tab = w[1:1 + maxlen], 1 + maxlen
    out, pend, bit = [], 0, at * 8
    while True:
        code = first = index = 0
        for n in range(maxlen):
            code |= data[bit >> 3] >> (7 - (bit & 7)) & 1
            bit += 1
            if code - first < counts[n]:
                break
            index += counts[n]
            first = (first + counts[n]) << 1
            code <<= 1
        else:
            raise ValueError("bad code")
        stack = [index + code - first]
        while stack:
            i = stack.pop()
            l, r = w[tab + 2 * i], w[tab + 2 * i + 1]
            if r != LEAF:
                stack += [r, l]
            elif l == 0:
                if pend:
                    out.append(enfont.PAIR + (pend << 7))
                return out
            elif l < 0x80:
                if pend:
                    out.append(enfont.PAIR + (pend << 7) + l)
                    pend = 0
                else:
                    pend = l
            else:
                if pend:
                    out.append(enfont.PAIR + (pend << 7))
                    pend = 0
                out.append(l)


def build(strings, merges=MERGES):
    """strings: encoded word lists (each with its terminator). -> (Model, [packed bytes]); checks the round trip."""
    evs = [events(w) for w in strings]
    for w, e in zip(strings, evs):
        if pairs(e) != list(w):
            raise ValueError("not EnCodec pairing: %s" % [hex(x) for x in w])
    m = Model(evs, merges)
    packed = [m.pack(e) for e in evs]
    blob = m.blob()
    for w, p in zip(strings, packed):
        assert unpack(blob, p) == list(w)
    return m, packed


def main():
    import extract
    import insert
    enc = insert.Encoder("en")
    pools = {doc["entries"][0]["id"].split(".")[1]: [enc.words(e) + [extract.TERM_W[e["term"]]]
                                                     for e in doc["entries"]]
             for doc in insert.docs() if doc["file"] == "MSYS.DAT"}
    allstr = [s for v in pools.values() for s in v]
    for nm in [int(a) for a in sys.argv[1:]] or [MERGES]:
        m, packed = build(allstr, nm)
        it = iter(packed)
        sizes = {k: sum(len(next(it)) + 2 for _ in v) + 4 for k, v in pools.items()}
        print(nm, "maxlen", m.maxlen, "model", len(m.blob()), sizes, "max out", max(2 * len(s) for s in allstr))


if __name__ == "__main__":
    main()
