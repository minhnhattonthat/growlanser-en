"""straddr.py: RAM address of EXE-table strings in the built EXE (for read-watch probes).

    python -X utf8 tools/straddr.py Man Woman        print id, RAM address and `en` of every EXE entry whose en matches
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import extract  # noqa: E402
import insert  # noqa: E402

BUILT = insert.ROOT / "build" / "disc1" / "files" / insert.EXE


def main(names):
    exe, seen = BUILT.read_bytes(), set()
    for doc in insert.docs():
        if doc["file"] != insert.EXE:
            continue
        table, base = int(doc["table"], 16), int(doc["base"], 16)
        for slot, (i, d) in enumerate(extract._refs_parse(doc["refs"])):
            e = doc["entries"][i]
            p = base + 2 * struct.unpack_from("<H", exe, table + 2 * slot)[0] - d
            if e.get("en") in names and p not in seen:
                seen.add(p)
                print("%s  0x%08X  %r" % (e["id"], p + insert.RAM, e["en"]))


if __name__ == "__main__":
    main(set(sys.argv[1:]))
