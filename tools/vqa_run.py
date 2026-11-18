"""vqa_run.py: visual-QA verdicts for a tour through `codex exec` (no subagents in an Orca worker).

    python -X utf8 tools/vqa_run.py work/qa/tour [--size 12] [-j 4] [--jp work/qa/tour_jp]

Runs `qa_gate.py todo` on TOUR/manifest.tsv (chunks in TOUR/chunks), then one read-only codex run per chunk with
docs/visual-qa-brief.md. Codex can't write in read-only mode, so its final message (one `id<TAB>ok|issue<TAB>note`
line per sheet) is parsed and written to TOUR/verdicts/<chunk>.tsv; a chunk missing any id is not written (re-run).
Logs: TOUR/vqa_log/. Afterwards: `qa_gate.py check TOUR/manifest.tsv TOUR/verdicts`.
"""
import argparse
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from skill import SKILL  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ROW = re.compile(r"^(\S+)\t(ok|issue)\t?(.*)$")


def chunk_prompt(chunk, tour, jp):
    ids = chunk.read_text(encoding="utf-8")
    return f"""{(ROOT / 'docs/visual-qa-brief.md').read_text(encoding='utf-8')}

## This dispatch
- You run read-only: you can't write files or run sheet.py --out. Look at images with your image viewer instead:
  the sheets, and the single full-size frames `fNNNNNN.png` in the same folder as a sheet when you need detail.
- $SKILL = {SKILL}. Original disc's tour (same folder names): {jp}.
- Don't write a verdict file: return the verdict lines as your final message, one per id below, exactly
  `id<TAB>ok|issue<TAB>note`, nothing else (no code fences, no headings).

Chunk ({chunk.name}), `id<TAB>path`:
{ids}"""


def run(chunk, tour, jp):
    log = tour / "vqa_log"
    log.mkdir(exist_ok=True)
    out = log / f"{chunk.stem}.out.md"
    want = [ln.split("\t")[0] for ln in chunk.read_text(encoding="utf-8").splitlines() if ln.strip()]
    r = subprocess.run([shutil.which("codex"), "exec", "-s", "read-only", "--skip-git-repo-check", "-o", str(out),
                        "-"], input=chunk_prompt(chunk, tour, jp), text=True, encoding="utf-8", cwd=ROOT,
                       capture_output=True, timeout=3600)
    (log / f"{chunk.stem}.stderr.txt").write_text((r.stderr or "")[-4000:], encoding="utf-8")
    got = {}
    for ln in (out.read_text(encoding="utf-8") if out.exists() else "").splitlines():
        m = ROW.match(ln.strip())
        if m:
            got[m.group(1)] = f"{m.group(1)}\t{m.group(2)}\t{m.group(3).strip()}"
    missing = [i for i in want if i not in got]
    if missing:
        return f"{chunk.stem}: FAILED, {len(missing)} ids missing (see {out})"
    (tour / "verdicts").mkdir(exist_ok=True)
    (tour / "verdicts" / f"{chunk.stem}.tsv").write_text("".join(got[i] + "\n" for i in want), encoding="utf-8",
                                                          newline="\n")
    issues = [got[i] for i in want if got[i].split("\t")[1] == "issue"]
    return f"{chunk.stem}: {len(want) - len(issues)} ok, {len(issues)} issue" + "".join("\n  " + s for s in issues)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tour")
    ap.add_argument("--size", type=int, default=12)
    ap.add_argument("-j", type=int, default=4)
    ap.add_argument("--jp", default=str(ROOT / "work/qa/tour_jp"))
    a = ap.parse_args()
    tour = Path(a.tour).resolve()
    chunks_dir = tour / "chunks"
    for old in chunks_dir.glob("chunk_*.txt"):
        old.unlink()
    subprocess.run([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts/qa_gate.py"), "todo",
                    str(tour / "manifest.tsv"), str(tour / "verdicts"), "--size", str(a.size), "--out-dir",
                    str(chunks_dir)], check=True)
    chunks = sorted(chunks_dir.glob("chunk_*.txt"))
    with ThreadPoolExecutor(a.j) as ex:
        for res in ex.map(lambda c: run(c, tour, a.jp), chunks):
            print(res, flush=True)


if __name__ == "__main__":
    main()
