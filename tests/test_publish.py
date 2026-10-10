import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("publish", ROOT / "src" / "publish.py")
p = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p)


def _tree(
    tmp_path,
    names=("CH4/EDGAR_CH4_1970_2025.zip",),
    card="license: cc-by-4.0\nraw/ghg2026/",
    tamper=False,
):
    d = tmp_path / "data"
    run = d / "raw" / "ghg2026"
    files = {}
    for n in names:
        (run / n).parent.mkdir(parents=True, exist_ok=True)
        (run / n).write_bytes(n.encode())
        files[n] = {"sha256": hashlib.sha256(n.encode()).hexdigest(), "bytes": len(n)}
    (run / "MANIFEST.json").write_text(json.dumps({"files": files}))
    if tamper:
        (run / names[0]).write_bytes(b"x")
    for f in ("LICENSE", "provenance.yaml"):
        (d / f).write_text("x")
    (d / "README.md").write_text(card)
    return d


def test_collect_lists_the_card_and_the_release(tmp_path):
    files = p.collect(_tree(tmp_path))
    assert files[-1] in {"raw/ghg2026/CH4/EDGAR_CH4_1970_2025.zip", "raw/ghg2026/MANIFEST.json"}
    assert "raw/ghg2026/CH4/EDGAR_CH4_1970_2025.zip" in files


@pytest.mark.parametrize("name", ["CO2/IEA_EDGAR_CO2_1970_2025.zip", "EDGAR_AR5_GHG_1970_2025.zip"])
def test_a_file_not_under_cc_by_stops_the_push(tmp_path, name):
    with pytest.raises(SystemExit, match="not under CC BY"):
        p.collect(_tree(tmp_path, names=(name,)))


def test_a_changed_file_stops_the_push(tmp_path):
    with pytest.raises(SystemExit, match="not the file in its manifest"):
        p.collect(_tree(tmp_path, tamper=True))


def test_a_card_that_does_not_name_the_release_is_refused(tmp_path):
    with pytest.raises(SystemExit, match="name the release"):
        p.collect(_tree(tmp_path, card="license: cc-by-4.0"))
