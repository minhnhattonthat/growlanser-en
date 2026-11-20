"""warp_all.py: run every (or the named) tools/debug/scenes.txt entry from a cold boot and prove it with a shot.

    python -X utf8 tools/debug/warp_all.py [NAME ..] [--cue CUE] [--jobs 4] [--states] [--out work/qa/warp]

Each entry runs `emu.py CUE --script tools/debug/warp.lua --var SCENE='NAME'` into OUT/NAME (final.png = the
proof, log.txt has the "landed" line). --states also saves work/states/NAME.sstate at the end (regenerate them
all after engine, font or graphics changes). Writes OUT/sheet.png of every final shot and OUT/results.tsv.
Exit 1 if any entry failed to land, errored or timed out.
"""
import argparse
import re
import shutil
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
        j = re.search(r"\bjump\s+(\d+):(0x[0-9A-Fa-f]+)", body)
        if j:
            JUMP[name] = j.groups()
        k = re.search(r"\bkill\s+(\d+)", body)
        if k:
            KILL[name] = int(k.group(1))
        if re.search(r"\bstress\b", body):
            STRESS.add(name)
        out.append((name, int(m.group(1)) if m else 4500, 2 if re.search(r"\bdisc\s+2\b", body) else 1,
                    bool(re.search(r"\bcard\b", body))))
    return out


CARD = ROOT / "work" / "states" / "save1.mcd"  # memory card with one save: `warp_all.py card_save` writes it
JUMP = {}  # name -> (SCEN entry, script offset): "jump E:0xOFF" runs tools/debug/vmjump.lua after landing
KILL = {}  # name -> frame: "kill F" runs tools/debug/kill.lua (hero HP held at 1 from frame F)
STRESS = set()  # "stress": tools/debug/stress.lua fills every item list (full lists, x9, max money)


def run(cue, out, name, frames, states, probes=(), every=500, then=None, disc=1, card=False):
    d = out / name
    raw = re.fullmatch(r"scene_(\d+)", name)  # --raw: a bare scene id, run on the New Game map
    if disc == 2:  # same folder, Redump name: "... (Disc 1).cue" -> "... (Disc 2).cue"
        cue = Path(cue).with_name(Path(cue).name.replace("(Disc 1)", "(Disc 2)"))
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), str(cue), "--out", str(d),
           "--script", str(ROOT / "tools" / "debug" / "warp.lua"),
           "--var", f"SCENE='scene {int(raw.group(1))}'" if raw else f"SCENE='{name}'",
           "--frames", str(frames), "--shot-every", str(every), "--timeout", str(120 + frames // 20)]
    if raw and then:
        cmd += ["--var", f"THEN='{then}'"]
    if every < 500:
        cmd.append("--sheet")  # tour mode: per-warp contact sheets for visual QA
    if disc == 2:  # New Game on disc 2: hold the expected-disc index at disc 2 (docs/re/debug.md "Disc 2")
        cmd += ["--script", str(ROOT / "tools" / "debug" / "disc2.lua")]
    if card:
        if not CARD.exists():
            return name, False, -1, "-", f"no {CARD.name}: run warp_all.py card_save first"
        cmd += ["--sav", str(CARD)]
    elif name in ("card_save", "stress_save"):  # routes that save: a fresh copy of the blank card, never the shared one
        cmd += ["--sav", str(ROOT / "tools" / "pcsx" / "memcard1.mcd")]
    if name in KILL:  # hold the hero's HP at 1 so the next hit is a defeat (game over screen)
        cmd += ["--script", str(ROOT / "tools" / "debug" / "kill.lua"), "--var", f"KILL_AT={KILL[name]}"]
    if name in STRESS:
        cmd += ["--script", str(ROOT / "tools" / "debug" / "stress.lua")]
    for p in probes:
        cmd += ["--script", str(Path(p).resolve())]
    if name in JUMP:
        cmd += ["--script", str(ROOT / "tools" / "debug" / "vmjump.lua"), "--var", f"ENTRY={JUMP[name][0]}",
                "--var", f"OFF={JUMP[name][1]}", "--var", "AT=1600"]
    if probes or name in JUMP or name in STRESS:
        cmd.append("--debugger")  # probes, vmjump and stress.lua (spell filter) use L.on_exec
    if states:
        cmd += ["--state-out", str(ROOT / "work" / "states" / f"{name}.sstate")]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = (d / "log.txt").read_text(encoding="utf-8", errors="replace") if (d / "log.txt").exists() else ""
    landed = re.search(r"landed .* at f(\d+)", log)
    err = (d / "lua_error.txt").read_text(encoding="utf-8", errors="replace").strip() if (d / "lua_error.txt").exists() else ""
    ok = p.returncode == 0 and landed and not err and (d / "final.png").exists()
    if name == "card_save" and ok:
        shutil.copy(d / "memcard1.mcd", CARD)
    return name, bool(ok), p.returncode, landed.group(1) if landed else "-", err[:120]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*")
    ap.add_argument("--cue", default=str(DEFAULT_CUE), help="disc 1 cue (New Game needs disc 1)")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--states", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "work" / "qa" / "warp"))
    ap.add_argument("--script", action="append", default=[], help="extra probe Lua for every run (repeatable)")
    ap.add_argument("--shot-every", type=int, default=500, help="below 500 = tour mode: --sheet per warp")
    ap.add_argument("--raw", help="scene id range N-M instead of scenes.txt names (folders scene_NNN)")
    ap.add_argument("--then", default="6 circle*250", help="route after landing for --raw runs")
    ap.add_argument("--frames", type=int, default=11000, help="run length for --raw runs")
    a = ap.parse_args()
    if a.raw:
        lo, hi = map(int, a.raw.split("-"))
        a.names = [f"scene_{i:03d}" for i in range(lo, hi + 1)]
    todo = [s for s in scenes() if not a.names or s[0] in a.names]
    todo += [(n, a.frames, 1, False) for n in a.names if n.startswith("scene_")]
    missing = set(a.names) - {s[0] for s in todo}
    if missing:
        sys.exit(f"not in scenes.txt: {' '.join(sorted(missing))}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda s: run(a.cue, out, s[0], s[1], a.states, a.script, a.shot_every, a.then, *s[2:]),
                          todo))
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
