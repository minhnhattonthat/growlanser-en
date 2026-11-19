"""build.py: rebuild both discs from the unpacked trees, with patched files swapped in.

  python -X utf8 build.py              -> build/disc{1,2}/ (Redump file names, original .cue copied)
  python -X utf8 build.py --marker     -> marker build (phase 5: every line = its id + filler)
  python -X utf8 build.py [--marker] --qa F.tsv --out work/qa/b --disc 1   -> stress build (id<TAB>text overrides)
  python -X utf8 build.py --identity  -> no patches into work/ident/, exit 1 unless every track's SHA-1 equals rom.sha1

Steps: check the dump (rom.sha1), unpack with dumpsxiso if work/discN/tree is missing (never written to), write a
layout with absolute paths (patched files point at build/discN/files/), run mkpsxiso, split disc 2's single image
into the Redump Track 1/Track 2 bins at track 2's INDEX 00 (Redump keeps the pregap in track 2)."""
import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402

MKPSXISO = ROOT / "tools/mkpsxiso/mkpsxiso-2.30-win64"
SECTOR = 2352
DISCS = {  # disc -> (cue, track bins in order), names as in rom/
    1: ("Growlanser (Japan) (Disc 1).cue", ["Growlanser (Japan) (Disc 1).bin"]),
    2: ("Growlanser (Japan) (Disc 2).cue", ["Growlanser (Japan) (Disc 2) (Track 1).bin",
                                            "Growlanser (Japan) (Disc 2) (Track 2).bin"]),
}


def unpack(disc):
    work = ROOT / f"work/disc{disc}"
    if not (work / "tree").is_dir():
        work.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(MKPSXISO / "dumpsxiso.exe"), "-x", "tree", "-s", "layout.xml",
                        str(ROOT / "rom" / DISCS[disc][0])], cwd=work, check=True)
    return work


def write_layout(disc, out, patched):
    """Layout with absolute sources; patched maps an ISO file name (e.g. 'SCEN.DAT') to its new bytes."""
    work = unpack(disc)
    tree = ET.parse(work / "layout.xml")
    root = tree.getroot()
    root.set("image_name", "mkpsxiso.bin")
    root.set("cue_sheet", "mkpsxiso.cue")
    for el in root.iter():
        for attr in ("file", "source"):
            if attr in el.attrib and el.tag in ("license", "track", "directory_tree"):
                el.set(attr, str((work / el.get(attr)).resolve()))
    files = out / "files"
    done = set()
    for el in root.iter("file"):
        name = el.get("name")
        if name in patched:
            files.mkdir(parents=True, exist_ok=True)
            (files / name).write_bytes(patched[name])
            el.set("source", str((files / name).resolve()))
            done.add(name)
    if set(patched) - done:
        sys.exit(f"disc {disc}: patched files not in the layout: {sorted(set(patched) - done)}")
    tree.write(out / "layout.xml", encoding="utf-8")


def msf(text):
    m, s, f = map(int, text.split(":"))
    return (m * 60 + s) * 75 + f


def build_disc(disc, out, patched):
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    write_layout(disc, out, patched)
    r = subprocess.run([str(MKPSXISO / "mkpsxiso.exe"), "-y", "-q", "layout.xml"], cwd=out,
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"mkpsxiso disc {disc} failed:\n{r.stdout}{r.stderr}")
    image = out / "mkpsxiso.bin"
    cue, bins = DISCS[disc]
    # Track starts in sectors: track 1 at 0, each later track at its INDEX 00 (pregap included, as Redump splits).
    starts = [0] + [msf(m) for m in re.findall(r"TRACK \d+ AUDIO\s+INDEX 00 (\d+:\d+:\d+)",
                                                  (out / "mkpsxiso.cue").read_text())]
    assert len(starts) == len(bins), (disc, starts)
    size = image.stat().st_size
    assert size % SECTOR == 0
    if len(bins) == 1:
        image.replace(out / bins[0])
    else:
        bounds = [s * SECTOR for s in starts] + [size]
        with open(image, "rb") as src:
            for name, a, b in zip(bins, bounds, bounds[1:]):
                with open(out / name, "wb") as dst:
                    src.seek(a)
                    left = b - a
                    while left:
                        chunk = src.read(min(left, 1 << 24))
                        dst.write(chunk)
                        left -= len(chunk)
        image.unlink()
    (out / "mkpsxiso.cue").unlink()
    shutil.copyfile(ROOT / "rom" / cue, out / cue)
    return [out / b for b in bins]


def sha1(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha1").hexdigest()


def patches(disc, mode, qa=None):
    """Patched files for this disc, {ISO name: bytes}. Both discs share data files and EXE (one translation)."""
    import insert
    if mode not in _patched:
        _patched[mode] = insert.patched(mode, overrides=insert.read_qa(qa) if qa else None)
    files = dict(_patched[mode])
    if disc == 2:
        files["SLPS_023.81"] = files.pop("SLPS_023.80")
    elif mode == "en" and not qa:  # the FMVs are on disc 1 only (G8: logo subtitle removed, tools/fmvlogo.py)
        import fmvlogo
        files.update(fmvlogo.patched())
    return files


_patched = {}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--identity", action="store_true", help="build with no patches and compare to rom.sha1")
    ap.add_argument("--marker", action="store_true", help="marker build: every line replaced by its id + filler")
    ap.add_argument("--qa", help="TSV of id<TAB>English text overriding those entries (width-gate stress lines)")
    ap.add_argument("--out", default="build", help="output directory (default build/)")
    ap.add_argument("--disc", type=int, choices=sorted(DISCS), help="build only this disc")
    args = ap.parse_args()
    check_rom.check()
    if args.identity:
        want = {Path(n.strip()).name: h for h, n in (line.split(None, 1) for line in
                (ROOT / "rom.sha1").read_text(encoding="utf-8").splitlines() if line.strip() and line[0] != "#")}
        bad = 0
        for disc in DISCS:
            for path in build_disc(disc, ROOT / f"work/ident/disc{disc}", {}):
                got = sha1(path)
                ok = got == want[path.name]
                bad += not ok
                print(f"{'ok  ' if ok else 'DIFF'} {got}  {path.name}")
        sys.exit(1 if bad else 0)
    for disc in [args.disc] if args.disc else DISCS:
        files = patches(disc, "marker" if args.marker else "en", args.qa)
        for path in build_disc(disc, ROOT / args.out / f"disc{disc}", files):
            print(f"{sha1(path)}  {path.relative_to(ROOT).as_posix()}")
    if not (args.marker or args.qa):
        import strings  # text-coverage keys for textcover.py (phase 8)
        with open(ROOT / args.out / "strings.tsv", "w", encoding="utf-8", newline="\n") as f:
            f.writelines(f"{i}\t{k:X}\n" for i, k in strings.rows())


if __name__ == "__main__":
    main()
