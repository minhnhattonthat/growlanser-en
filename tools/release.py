"""release.py: build, gate and package the English patch (skill pipeline.md §Release). Stops at the first failure.

    python -X utf8 tools/release.py [--version 1.0] [--force] [--skip-build] [--skip-tests]

Steps: build.py (both discs) -> tools/check.py -> smoke boot of each disc -> no Japanese left in the script (see
leftover_jp) -> qa_gate.py check on every work/qa/**/manifest.tsv (verdicts in its folder's verdicts/) ->
textcover.py -> no unticked line in docs/polish.md -> no template placeholder in README.md -> debug tool off ->
xdelta3 patch per changed .bin (-B image size) -> re-apply to the clean original and compare sha1 -> zip
release/Growlanser_EN_v<version>.zip (patches + README.txt, ZIP_STORED). The playable image stays in build/.
--skip-build / --skip-tests reuse the current build/ or skip the 15-minute check.py (gates only: a real release
runs everything). Refuses to overwrite an existing version's files without --force.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402

PY = [sys.executable, "-X", "utf8"]
DISCS = {1: ["Growlanser (Japan) (Disc 1).bin"],
         2: ["Growlanser (Japan) (Disc 2) (Track 1).bin", "Growlanser (Japan) (Disc 2) (Track 2).bin"]}
CUES = {1: "Growlanser (Japan) (Disc 1).cue", 2: "Growlanser (Japan) (Disc 2).cue"}
JP = re.compile(r"[぀-ヺー-ヿ一-鿿ｦ-ﾟ]")  # not ・ (U+30FB): the choice bullet
CODE = re.compile(r"\{[^}\n]*\}|\[[0-9A-F]{4}\]")
PLACEHOLDER = re.compile(r"<(?:Game title|platform|publisher|year|repo|file|size|sha1|game|ext)[^>]*>|<[A-Z][a-z]+ /")


def step(name, ok, detail=""):
    print(f"[{'ok' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail else ""), flush=True)
    if not ok:
        sys.exit(1)


def run(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], cwd=ROOT, **kw).returncode


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def crc32(path):
    c = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            c = zlib.crc32(chunk, c)
    return "%08X" % c


def leftover_jp():
    """Japanese the release would still show. A byte scan (jp_left.py) is noise here: text is u16 glyph indices, so
    code and data read as kanji, and English dialogue/MSYS is dictionary/Huffman-packed. The build encodes exactly
    script/*.json, so check that: every pool string with Japanese has English with none (KEEP_JP and the unused
    exe.dict excepted). Runtime proof that each string is shown is textcover.py's job."""
    from insert import KEEP_JP
    bad = []
    for p in sorted((ROOT / "script").rglob("*.json")):
        for e in json.loads(p.read_text(encoding="utf-8"))["entries"]:
            if e["id"] in KEEP_JP or e["id"].startswith("exe.dict") or not JP.search(CODE.sub("", e["jp"])):
                continue
            if not e.get("en") or JP.search(CODE.sub("", e["en"])):
                bad.append(e["id"])
    return bad


def placeholders():
    return PLACEHOLDER.findall((ROOT / "README.md").read_text(encoding="utf-8"))


def debug_in_build():
    """The debug tool is Lua run by emu.py (tools/debug/*.lua); nothing of it may be assembled into the build."""
    return [p.name for p in (ROOT / "asm").glob("*.asm")
            if re.search(r"tools/debug|\bwarp|cheat", p.read_text(encoding="utf-8"), re.I)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--force", action="store_true", help="overwrite this version's existing release files")
    ap.add_argument("--skip-build", action="store_true", help="use the current build/ (not for a real release)")
    ap.add_argument("--skip-tests", action="store_true", help="skip tools/check.py (not for a real release)")
    a = ap.parse_args()
    out = ROOT / "release" / f"v{a.version}"
    zpath = ROOT / "release" / f"Growlanser_EN_v{a.version}.zip"
    if (out.exists() or zpath.exists()) and not a.force:
        step("release files", False, f"{out.name} exists; pass --force to overwrite")
    xdelta = shutil.which("xdelta3")
    step("xdelta3 on PATH", bool(xdelta))

    if not a.skip_build:
        step("build", run(PY + ["build.py"]) == 0)
    if not a.skip_tests:
        step("tools/check.py", run(PY + ["tools/check.py"]) == 0)
    for d, cue in CUES.items():
        rc = run(PY + [SKILL / "scripts/emu.py", ROOT / "build" / f"disc{d}" / cue, "--out", ROOT / f"work/qa/release_smoke{d}",
                       "--frames", 2400, "--mash", 30, "--mash-key", "start", "--smoke"], stdout=subprocess.DEVNULL)
        step(f"smoke disc {d}", rc == 0, f"exit {rc}")
    bad = leftover_jp()
    step("no Japanese left in the script", not bad, " ".join(bad[:20]))
    manifests = sorted((ROOT / "work/qa").rglob("manifest.tsv"))
    for m in manifests:
        rc = run(PY + [SKILL / "scripts/qa_gate.py", "check", m, m.parent / "verdicts"], stdout=subprocess.DEVNULL)
        step(f"qa_gate {m.relative_to(ROOT)}", rc == 0, f"exit {rc}")
    rc = run(PY + [SKILL / "scripts/textcover.py", "work/qa/cov", "build/strings.tsv", "--waive", "docs/text_unshown.tsv"],
             stdout=subprocess.DEVNULL)
    step("textcover", rc == 0, f"exit {rc}")
    open_polish = [ln for ln in (ROOT / "docs/polish.md").read_text(encoding="utf-8").splitlines()
                   if ln.startswith("- [ ]")]
    step("docs/polish.md all ticked", not open_polish, f"{len(open_polish)} open")
    ph = placeholders()
    step("README.md has no template placeholder", not ph, " ".join(ph[:5]))
    dbg = debug_in_build()
    step("debug tool off (none assembled)", not dbg, " ".join(dbg))

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    rows = []
    for d, bins in DISCS.items():
        for b in bins:
            orig, built = ROOT / "rom" / b, ROOT / "build" / f"disc{d}" / b
            o_sha, b_sha = sha1(orig), sha1(built)
            if o_sha == b_sha:
                rows.append((b, orig.stat().st_size, crc32(orig), o_sha, None, None))
                continue
            patch = out / (Path(b).stem + ".xdelta")
            size = max(orig.stat().st_size, built.stat().st_size)
            step(f"xdelta {b}", run([xdelta, "-e", "-9", "-f", "-B", size, "-s", orig, built, patch]) == 0)
            check = out / "reapply.tmp"
            rc = run([xdelta, "-d", "-f", "-s", orig, patch, check])
            same = rc == 0 and sha1(check) == b_sha
            check.unlink(missing_ok=True)
            step(f"re-apply {patch.name}", same, f"{patch.stat().st_size} bytes")
            rows.append((b, orig.stat().st_size, crc32(orig), o_sha, patch.name, crc32(built)))
    readme = (ROOT / "docs/release-readme.txt").read_text(encoding="utf-8").replace("{VERSION}", a.version)
    table = []
    for b, size, crc, s, patch, pcrc in rows:
        table.append(f"  {b}\n    {size} bytes, CRC32 {crc}, SHA-1 {s}\n" +
                     (f"    patch: {patch} -> patched CRC32 {pcrc}\n" if patch else "    unchanged: no patch needed\n"))
    readme = readme.replace("{FILES}", "\n".join(table))
    (out / "README.txt").write_text(readme, encoding="utf-8", newline="\r\n")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as z:
        for f in sorted(out.iterdir()):
            z.write(f, f.name)
    step("zip", True, f"{zpath.relative_to(ROOT)} ({zpath.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
