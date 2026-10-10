#!/usr/bin/env python3
"""Push the card, the licence, the provenance and the release's files to the Hub.

Each EDGAR release is a different edition of the database, so the Hub holds the release
under data/raw/<version>/ (today ghg2026). Each file goes up unchanged after its sha256 is
checked against MANIFEST.json. The card must name the release directory. Only substances the
publisher licenses under CC BY 4.0 are in the manifest at all (the script records the others
under "excluded"), and the push refuses a manifest that lists one of those.

    uv run python src/publish.py             # dry run: list the files and their total size
    uv run python src/publish.py --push
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPO = "yuiseki/edgar-ghg-countries"
DELETE_PATTERNS = ["raw/**"]
NOT_CC_BY = ("IEA_EDGAR_CO2", "EDGAR_AR5_GHG")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def collect(data: Path) -> list[str]:
    """The files to upload, relative to data/; stops on anything the card or a manifest refutes."""
    card = (data / "README.md").read_text(encoding="utf-8")
    if "license: cc-by-4.0" not in card:
        raise SystemExit("the card does not declare license: cc-by-4.0")
    runs = sorted((data / "raw").glob("*/MANIFEST.json"))
    if not runs:
        raise SystemExit("no release under data/raw/; run scripts/01_download.py")
    d = runs[-1].parent
    if f"raw/{d.name}/" not in card:
        raise SystemExit(f"the card does not name the release raw/{d.name}/")
    manifest = json.loads((d / "MANIFEST.json").read_text())
    files = ["README.md", "LICENSE", "provenance.yaml", f"raw/{d.name}/MANIFEST.json"]
    for name, e in manifest["files"].items():
        if Path(name).name.startswith(NOT_CC_BY):
            raise SystemExit(f"{name} is not under CC BY 4.0 and must not be in the manifest")
        if sha256(d / name) != e["sha256"]:
            raise SystemExit(f"raw/{d.name}/{name} is not the file in its manifest")
        files.append(f"raw/{d.name}/{name}")
    stray = {p.relative_to(data).as_posix() for p in d.rglob("*") if p.is_file()} - set(files)
    if stray:
        raise SystemExit(
            f"files in the release that the manifest does not list: {sorted(stray)[:5]}"
        )
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()

    files = collect(DATA)
    total = sum((DATA / f).stat().st_size for f in files)
    print(f"{a.repo}\n  {len(files)} files, {total:,} bytes ({total / 1e6:.1f} MB)")
    print(f"  remote files matching {DELETE_PATTERNS} and not uploaded are deleted")
    if not a.push:
        print("\ndry run. pass --push to upload")
        return 0

    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(a.repo, repo_type="dataset", exist_ok=True, private=False)
    api.upload_folder(
        folder_path=str(DATA), repo_id=a.repo, repo_type="dataset", allow_patterns=files,
        delete_patterns=DELETE_PATTERNS,
    )  # fmt: skip
    print(f"\npushed to https://huggingface.co/datasets/{a.repo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
