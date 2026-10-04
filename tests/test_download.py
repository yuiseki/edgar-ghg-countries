import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures"

spec = importlib.util.spec_from_file_location("dl", ROOT / "scripts" / "01_download.py")
dl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dl)

PAGE = (FIX / "dataset_ghg2026_trimmed.html").read_text(encoding="utf-8")
LISTING = (FIX / "listing_EDGAR_2026_GHG.html").read_text(encoding="utf-8")
COPYRIGHT = (FIX / "copyright.txt").read_text(encoding="utf-8")
BASE = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/EDGAR_2026_GHG/"


def test_release_version():
    assert dl.release_version("EDGAR_2026_GHG") == "ghg2026"
    assert dl.release_version("EDGAR_2025_GHG") == "ghg2025"
    with pytest.raises(ValueError):
        dl.release_version("v80_FT2022_GHG")


def test_zip_links_from_page():
    links = dl.zip_links(PAGE)
    assert BASE + "EDGAR_CH4_1970_2025.zip" in links
    assert BASE + "monthly/CH4/bkl_AGRICULTURE/bkl_AGRICULTURE_emi_nc.zip" in links
    assert len(links) == len(set(links))


def test_country_tables_only_top_level():
    tables = dl.country_tables(dl.zip_links(PAGE))
    assert all(u.startswith(BASE) and "/" not in u[len(BASE) :] for u in tables)
    assert BASE + "monthly/CH4/bkl_AGRICULTURE/bkl_AGRICULTURE_emi_nc.zip" not in tables
    assert dl.release_dir(tables[0]) == "EDGAR_2026_GHG"


@pytest.mark.parametrize(
    "name,substance",
    [
        ("EDGAR_CH4_1970_2025.zip", "CH4"),
        ("EDGAR_CH4_m_1970_2025.zip", "CH4"),
        ("EDGAR_N2O_1970_2025.zip", "N2O"),
        ("EDGAR_N2O_m_1970_2025.zip", "N2O"),
        ("EDGAR_CO2bio_1970_2025.zip", "CO2bio"),
        ("EDGAR_CO2bio_m_1970_2025.zip", "CO2bio"),
        ("EDGAR_F-gases_1990_2025.zip", "Fgases"),
        ("EDGAR_AR5g_F-gases_1990_2025.zip", "Fgases"),
    ],
)
def test_classify_taken(name, substance):
    assert dl.classify(name) == (substance, None)


@pytest.mark.parametrize(
    "name",
    ["IEA_EDGAR_CO2_1970_2025.zip", "IEA_EDGAR_CO2_m_1970_2025.zip", "EDGAR_AR5_GHG_1970_2025.zip"],
)
def test_classify_excluded(name):
    substance, reason = dl.classify(name)
    assert substance is None
    assert "fossil CO2" in reason


def test_classify_unknown_is_skipped():
    substance, reason = dl.classify("EDGAR_NOx_1970_2025.zip")
    assert substance is None and "not a known" in reason


def test_conditions_text():
    text = dl.conditions_text(PAGE)
    assert text.startswith("Conditions of use")
    assert "Creative Commons Attribution 4.0 International (CC BY 4.0)" in text
    assert "IEA-EDGAR CO2 (v5)" in text  # <sub> markup collapsed


def test_page_licence_ok():
    assert dl.page_licence_ok(dl.conditions_text(PAGE))
    # an NC-ND clause that is not confined to IEA-EDGAR CO2 fails
    assert not dl.page_licence_ok(
        "licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0) licence. "
        "EDGAR CH4 data are licensed under CC BY-NC-ND 4.0."
    )
    assert not dl.page_licence_ok("All rights reserved.")


def test_copyright_licence():
    assert dl.copyright_licence(COPYRIGHT) == "CC BY 4.0"
    assert dl.copyright_licence("licensed under CC BY-NC-ND 4.0") == "CC BY-NC-ND 4.0"
    assert dl.copyright_licence("All rights reserved") is None


def test_listing_entries():
    entries = dl.listing_entries(LISTING)
    assert entries["EDGAR_CH4_1970_2025.zip"] == {"modified": "2026-09-18 08:02", "size": "5.5M"}
    assert entries["copyright.txt"]["size"] == "540"
    assert "CH4/" not in entries
