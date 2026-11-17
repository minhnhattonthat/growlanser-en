"""vmops.py: event-VM op lengths from vmtrace.lua logs (docs/re/debug.md).

    python -X utf8 tools/vmops.py work/qa/vt*/log.txt

A log line "op XX PTR" is one dispatch; PTR points past the op byte. The next dispatch's PTR minus this one is the
op's length when no jump happened in between, so each op's most common delta is its length. Prints op, length,
how often that delta was seen out of all, the other deltas, and for each log the first op's offset into entry N.
"""
import re
import sys
from collections import Counter, defaultdict


def deltas(paths):
    d = defaultdict(Counter)
    starts = []
    for p in paths:
        prev, base = None, None
        for line in open(p, encoding="utf-8", errors="replace"):
            m = re.match(r"load (\d+) 1 ([0-9A-F]{8})", line)
            if m:
                base = int(m.group(2), 16)
                prev = None
                continue
            m = re.match(r"op ([0-9A-F]{2}) ([0-9A-F]{8})", line)
            if not m:
                continue
            op, ptr = int(m.group(1), 16), int(m.group(2), 16)
            if prev:
                d[prev[0]][ptr - prev[1]] += 1
            elif base:
                starts.append((p, op, ptr - 1 - base))
            prev = (op, ptr)
    return d, starts


if __name__ == "__main__":
    d, starts = deltas(sys.argv[1:])
    for op in sorted(d):
        c = d[op]
        best, n = c.most_common(1)[0]
        print(f"{op:02X} len {best:4d}  {n}/{sum(c.values())}  {dict(c.most_common(4))}")
    for p, op, off in starts:
        print(f"# {p}: first op {op:02X} at entry N +0x{off:X}")
