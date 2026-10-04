#!/usr/bin/env python3
"""Check every file under data/raw/<version>/ against its MANIFEST.json.

Re-hashes each file listed in the manifest, tests every zip (and every zip
inside it, since the xlsx tables are themselves zip containers), reads gzip
files to the end and counts CSV rows. Prints one ok/FAIL line per check and
exits non-zero if any check fails.

    uv run python scripts/02_verify.py
"""

import csv
import gzip
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check_zip(source, label: str) -> list[tuple[bool, str]]:
    out = []
    with zipfile.ZipFile(source) as z:
        bad = z.testzip()
        names = z.namelist()
        out.append(
            (bad is None, f"{label}: zip {len(names)} members" + (f", bad {bad}" if bad else ""))
        )
        for n in names:
            low = n.lower()
            if low.endswith((".xlsx", ".zip")):
                out += check_zip(io.BytesIO(z.read(n)), f"{label}!{n}")
            elif low.endswith(".csv"):
                with z.open(n) as f:
                    rows = sum(1 for _ in csv.reader(io.TextIOWrapper(f, "utf-8", newline="")))
                out.append((True, f"{label}!{n}: {rows:,} csv rows"))
    return out


def check_file(path: Path) -> list[tuple[bool, str]]:
    name = path.name.lower()
    if name.endswith(".zip"):
        return check_zip(path, str(path.relative_to(RAW)))
    if name.endswith(".gz"):
        with gzip.open(path) as f:
            while f.read(1 << 20):
                pass
        return [(True, f"{path.relative_to(RAW)}: gzip read to end")]
    if name.endswith(".csv"):
        with open(path, newline="", encoding="utf-8") as f:
            rows = sum(1 for _ in csv.reader(f))
        return [(True, f"{path.relative_to(RAW)}: {rows:,} csv rows")]
    return []


def main() -> int:
    failed = 0
    manifests = sorted(RAW.glob("*/MANIFEST.json"))
    if not manifests:
        print("FAIL no MANIFEST.json under data/raw/")
        return 1
    for mpath in manifests:
        d = mpath.parent
        files = json.loads(mpath.read_text())["files"]
        for rel, entry in files.items():
            p = d / rel
            label = f"{d.name}/{rel}"
            if not p.exists():
                print(f"FAIL {label}: missing")
                failed += 1
                continue
            ok = p.stat().st_size == entry["bytes"] and sha256(p) == entry["sha256"]
            print(f"{'ok  ' if ok else 'FAIL'} {label}: {entry['bytes']:,} bytes sha256")
            failed += not ok
            try:
                results = check_file(p)
            except Exception as e:  # a broken archive is a failure, not a crash
                results = [(False, f"{label}: {type(e).__name__}: {e}")]
            for good, msg in results:
                print(f"{'ok  ' if good else 'FAIL'} {msg}")
                failed += not good
        stray = [
            p
            for p in d.rglob("*")
            if p.is_file() and p != mpath and str(p.relative_to(d)) not in files
        ]
        for p in stray:
            print(f"FAIL {d.name}/{p.relative_to(d)}: not in MANIFEST")
            failed += 1
    print(f"{failed} failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
