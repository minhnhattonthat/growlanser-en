"""warp_all.py: run every (or the named) tools/debug/scenes.txt entry from a cold boot and prove it with a shot.

    python -X utf8 tools/debug/warp_all.py [NAME ..] [--cue CUE] [--jobs 4] [--states] [--out work/qa/warp]

Each entry runs `emu.py CUE --script tools/debug/warp.lua --var SCENE='NAME'` into OUT/NAME (final.png = the
proof, log.txt has the "landed" line). --states also saves work/states/NAME.sstate at the end (regenerate them
all after engine, font or graphics changes). Writes OUT/sheet.png of every final shot and OUT/results.tsv.
Exit 1 if any entry failed to land, errored or timed out.
"""
import argparse
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402

DEFAULT_CUE = ROOT / "rom" / "Growlanser (Japan) (Disc 1).cue"


def scenes():
    out = []
    for line in (ROOT / "tools" / "debug" / "scenes.txt").read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        name, rest = line.split(None, 1)
        body = rest.split(" then ", 1)[0]
        m = re.search(r"frames\s+(\d+)", body)
        out.append((name, int(m.group(1)) if m else 4500))
    return out


def run(cue, out, name, frames, states):
    d = out / name
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), str(cue), "--out", str(d),
           "--script", str(ROOT / "tools" / "debug" / "warp.lua"), "--var", f"SCENE='{name}'",
           "--frames", str(frames), "--shot-every", "500", "--timeout", str(120 + frames // 20)]
    if states:
        cmd += ["--state-out", str(ROOT / "work" / "states" / f"{name}.sstate")]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = (d / "log.txt").read_text(encoding="utf-8", errors="replace") if (d / "log.txt").exists() else ""
    landed = re.search(r"landed .* at f(\d+)", log)
    err = (d / "lua_error.txt").read_text(encoding="utf-8", errors="replace").strip() if (d / "lua_error.txt").exists() else ""
    ok = p.returncode == 0 and landed and not err and (d / "final.png").exists()
    return name, bool(ok), p.returncode, landed.group(1) if landed else "-", err[:120]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*")
    ap.add_argument("--cue", default=str(DEFAULT_CUE), help="disc 1 cue (New Game needs disc 1)")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--states", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "work" / "qa" / "warp"))
    a = ap.parse_args()
    todo = [s for s in scenes() if not a.names or s[0] in a.names]
    missing = set(a.names) - {s[0] for s in todo}
    if missing:
        sys.exit(f"not in scenes.txt: {' '.join(sorted(missing))}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda s: run(a.cue, out, s[0], s[1], a.states), todo))
    with open(out / "results.tsv", "w", encoding="utf-8") as f:
        f.write("name\tok\texit\tlanded_frame\terror\n")
        for r in res:
            f.write("\t".join(map(str, r)) + "\n")
            print(("ok  " if r[1] else "FAIL") + f" {r[0]} exit={r[2]} landed=f{r[3]} {r[4]}")
    shots = [str(out / r[0] / "final.png") for r in res if (out / r[0] / "final.png").exists()]
    if shots:
        subprocess.run([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "sheet.py"), *shots,
                        "--cols", "4", "--out", str(out / "sheet.png")], check=False)
    bad = [r[0] for r in res if not r[1]]
    print(f"{len(res) - len(bad)}/{len(res)} landed" + (f"; failed: {' '.join(bad)}" if bad else ""))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
