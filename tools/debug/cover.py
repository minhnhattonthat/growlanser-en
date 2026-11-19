"""cover.py: text-coverage runs: every scene's messages through the real printer (msgforce.lua loop + textlog.lua).

    python -X utf8 tools/debug/cover.py [N-M] [--cue CUE] [--jobs 4] [--out work/qa/cov]

Per scene N: cold boot, warp to scene 0 (the host: most scenes warped to directly hang or idle on the wrong map),
mash Circle; msgforce.lua (HOST = N's text section from the build's SCEN.DAT, OUT/sec_NNN.bin) copies message 1, 2,
... of N into scene 0's text area in a loop of scene 0's message op, then cycles N's speaker strings through the
name tags; textlog.lua logs every printer call (`TEXT <hash>`). A run ends when the section is done or stalls (a message that never
closes): the next run starts after the stalled message (FROM=k), up to --reruns times. Run folders
OUT/scene_NNN_rK, OUT/results_N-M.tsv (scene, messages, reached, done|stalled|timeout|reruns, last rerun).
Then: `textcover.py OUT build/strings.tsv`.
"""
import argparse
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import dat  # noqa: E402
import scen  # noqa: E402
from skill import SKILL  # noqa: E402

CUE = ROOT / "build" / "disc1" / "Growlanser (Japan) (Disc 1).cue"
END = re.compile(r"FORCE end f\d+ (done|stalled) forced (\d+)")


def section(scen_dat, n, path):
    """Write scene n's text section (from the built SCEN.DAT) to path; return its unique string count (messages
    first, then the speaker strings msgforce.lua cycles after them), 0 when the scene has none."""
    e = dat.entry(scen_dat, 280 + n)
    ts = e and scen.text_section(e)
    if not ts:
        return 0
    path.write_bytes(e[ts[0]:ts[0] + ts[1]])
    return len(set(ts[2]))


def run(cue, scen_dat, out, n, frm, reruns):
    sec = out / f"sec_{n:03d}.bin"
    total = section(scen_dat, n, sec)
    if not total:
        return n, 0, 0, "none", 0
    for r in range(reruns + 1):
        d = out / f"scene_{n:03d}_r{r}"
        frames = 7200 + 60 * max(total - frm, 0)  # + room for the speaker strings after the messages
        cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), str(cue), "--out", str(d),
               "--debugger", "--frames", str(frames),
               "--script", str(ROOT / "tools" / "debug" / "warp.lua"), "--var", "SCENE='scene 0'",
               "--var", "THEN='4 circle*4000/8'",
               "--script", str(ROOT / "tools" / "debug" / "msgforce.lua"), "--var", "SHOTS_ON=0", "--var", f"FROM={frm}",
               "--var", "HOST='%s'" % sec.resolve().as_posix(),
               "--script", str(ROOT / "tools" / "debug" / "textlog.lua")]
        subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        log = (d / "log.txt").read_text(encoding="utf-8", errors="replace") if (d / "log.txt").exists() else ""
        m = END.search(log)
        forced = int(m.group(2)) if m else 0
        state = m.group(1) if m else "timeout"
        if state == "done" or forced == 0 or frm + forced >= total:
            return n, total, frm + forced, state, r
        frm += forced  # skip the message that stalled (it was shown)
    return n, total, frm, "reruns", reruns


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("range", nargs="?", default="0-279")
    ap.add_argument("--cue", default=str(CUE))
    ap.add_argument("--scen", default=str(ROOT / "work" / "qa" / "btree" / "tree" / "SCEN.DAT"),
                    help="the build's SCEN.DAT (dumpsxiso -x work/qa/btree/tree <build cue>)")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--reruns", type=int, default=6)
    ap.add_argument("--out", default=str(ROOT / "work" / "qa" / "cov"))
    a = ap.parse_args()
    lo, hi = map(int, a.range.split("-"))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    scen_dat = Path(a.scen).read_bytes()
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda n: run(a.cue, scen_dat, out, n, 0, a.reruns), range(lo, hi + 1)))
    with open(out / f"results_{lo}-{hi}.tsv", "w", encoding="utf-8") as f:
        f.write("scene\tmessages\treached\tend\treruns\n")
        for r in res:
            f.write("\t".join(map(str, r)) + "\n")
            print("\t".join(map(str, r)))


if __name__ == "__main__":
    main()
