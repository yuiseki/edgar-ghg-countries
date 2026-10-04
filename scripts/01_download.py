#!/usr/bin/env python3
"""Fetch the CC BY 4.0 country tables of the latest EDGAR GHG release.

The release is the one the dataset page DATASET_PAGE describes (EDGAR_2026_GHG,
published September 2026). Releases are not overwritten in place: each has its
own directory on the JRC distribution server, so the version is the release
name, EDGAR_2026_GHG -> "ghg2026", and files go to data/raw/ghg2026/<substance>/.

What is taken, and how it is decided:

* The download links are read from the dataset page. Only zips directly in the
  release directory are country tables (annual and monthly xlsx by sector and
  country); everything under a subdirectory is a gridded map and is not taken.
* The page's "Conditions of use" must state CC BY 4.0 and must confine the
  CC BY-NC-ND 4.0 clause to IEA-EDGAR CO2. The copyright.txt in the release
  directory must state CC BY 4.0 (it is kept next to the data). If it said
  NC or ND, nothing would be taken and the reason would be recorded.
* Taken: CH4, N2O, F-gases (by gas, and grouped in CO2eq) and biogenic CO2
  (CO2bio). Not taken: fossil CO2 (IEA_EDGAR_CO2_*, CC BY-NC-ND 4.0) and the
  total GHG table (EDGAR_AR5_GHG_*), which adds fossil CO2 in. Exclusions are
  listed in the manifest.
* Every taken file must also appear in the server's directory listing; its
  listed date and size are recorded.

Each file is downloaded to a .part file, checked against Content-Length, then
renamed. data/raw/ghg2026/MANIFEST.json records url, bytes, sha256,
Last-Modified and fetch time per file. A file whose local sha256 matches its
manifest entry is not fetched again. The total is checked against SIZE_LIMIT
before anything is downloaded.

    uv run python scripts/01_download.py
"""

import hashlib
import html
import json
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
UA = "edgar-ghg-countries/1 (+https://github.com/yuiseki/edgar-ghg-countries)"
DATASET_PAGE = "https://edgar.jrc.ec.europa.eu/dataset_ghg2026"
SERVER = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/"
# The dataset page does not print the dataset DOI. It is registered at DataCite
# (issued 2026-09-24) and resolves to the JRC Data Catalogue record; the script
# re-reads that record through the public DataCite REST API and checks the title.
DATASET_DOI = "10.2905/JRC.2W3HH78"
DATACITE = "https://api.datacite.org/dois/"
REPORT = (
    "Crippa, M., Guizzardi, D., Pagani, F., Banja, M., Ciarlantini, S., Muntean, M., Amici, L., "
    "Luini, C., Honavar Melo Pires, R., Quadrelli, R., Carvalho, P., Ruiz Ponsoda, D., Andrews, S., "
    "Köykkä, J., Grassi, G., Rossi, S., Melo, J., Branco, A., Suárez-Moreno, M., Sedano, F., "
    "Manca, G., Pisoni, E., Pekar, F., GHG emissions of all world countries - 2026 Report, "
    "Publications Office of the European Union, Luxembourg, 2026, doi:10.2760/7717504, JRC147815."
)
LICENCE_URL = "https://creativecommons.org/licenses/by/4.0/"
SIZE_LIMIT = 1_000_000_000
PAUSE = 1.0

TAKEN = [
    (re.compile(r"^EDGAR_CH4(_m)?_\d{4}_\d{4}\.zip$"), "CH4"),
    (re.compile(r"^EDGAR_N2O(_m)?_\d{4}_\d{4}\.zip$"), "N2O"),
    (re.compile(r"^EDGAR_CO2bio(_m)?_\d{4}_\d{4}\.zip$"), "CO2bio"),
    (re.compile(r"^EDGAR_(AR5g_)?F-gases(_m)?_\d{4}_\d{4}\.zip$"), "Fgases"),
]
EXCLUDED = [
    (
        re.compile(r"^IEA_EDGAR_CO2"),
        "fossil CO2 (IEA-EDGAR CO2): licensed under CC BY-NC-ND 4.0 per the dataset page",
    ),
    (
        re.compile(r"^EDGAR_AR5_GHG"),
        "total GHG in CO2eq: includes fossil CO2 (CC BY-NC-ND 4.0); the page states no licence for the total",
    ),
]


# ---------------------------------------------------------------- parsing


def release_version(release: str) -> str:
    """EDGAR_2026_GHG -> ghg2026."""
    m = re.fullmatch(r"EDGAR_(\d{4})_GHG", release)
    if not m:
        raise ValueError(f"not a yearly GHG release name: {release}")
    return f"ghg{m.group(1)}"


def zip_links(page_html: str) -> list[str]:
    """Distinct .zip hrefs on the dataset page, in page order."""
    seen: dict[str, None] = {}
    for href in re.findall(r'href="([^"]+\.zip)"', page_html):
        seen.setdefault(html.unescape(href), None)
    return list(seen)


def release_dir(url: str) -> str:
    rest = url[len(SERVER) :] if url.startswith(SERVER) else ""
    return rest.split("/", 1)[0]


def country_tables(links: list[str]) -> list[str]:
    """Zips directly in a release directory; anything deeper is a gridded map."""
    out = []
    for u in links:
        if not u.startswith(SERVER):
            continue
        parts = u[len(SERVER) :].split("/")
        if len(parts) == 2:
            out.append(u)
    return out


def classify(name: str) -> tuple[str | None, str | None]:
    """(substance directory, None) for a file to take, (None, reason) otherwise."""
    for pat, reason in EXCLUDED:
        if pat.search(name):
            return None, reason
    for pat, substance in TAKEN:
        if pat.match(name):
            return substance, None
    return None, "not a known CC BY 4.0 country table name; left for review"


def _text(fragment: str) -> str:
    t = re.sub(r"<[^>]+>", "", fragment.replace("</p>", "\n"))
    t = html.unescape(t)
    return "\n".join(re.sub(r"\s+", " ", line).strip() for line in t.splitlines() if line.strip())


def conditions_text(page_html: str) -> str:
    """Plain text of the page's Conditions of use section."""
    m = re.search(r'<h2[^>]*id\s*=\s*"conditions"[^>]*>.*?(?=<h2|</body>)', page_html, flags=re.S)
    if not m:
        raise ValueError("no Conditions of use section on the dataset page")
    return _text(m.group(0))


def page_licence_ok(conditions: str) -> bool:
    """CC BY 4.0 is stated and every NC/ND clause is about IEA-EDGAR CO2 only."""
    if "CC BY 4.0" not in conditions:
        return False
    for sentence in re.split(r"(?<=\.)\s+(?=[A-Z])", conditions):
        if re.search(r"NC-ND|NonCommercial|NoDerivatives", sentence) and (
            "IEA-EDGAR CO2" not in sentence
        ):
            return False
    return True


def copyright_licence(text: str) -> str | None:
    m = re.search(r"CC[ -]BY-N[CD][-A-Z]*\s*4\.0", text)
    if m:
        return "CC " + m.group(0)[3:]
    if "(CC BY 4.0)" in text or re.search(r"\bCC BY 4\.0\b", text):
        return "CC BY 4.0"
    return None


def listing_entries(listing_html: str) -> dict[str, dict]:
    """File rows of an Apache directory index: name -> {modified, size}."""
    out = {}
    for href, mod, size in re.findall(
        r'<a href="([^"?/][^"]*)">[^<]*</a></td><td align="right">([\d-]+ [\d:]+)\s*</td>'
        r'<td align="right">\s*([^<]+?)\s*</td>',
        listing_html,
    ):
        if href.endswith("/"):
            continue
        out[urllib.parse.unquote(href)] = {"modified": mod, "size": size}
    return out


# ---------------------------------------------------------------- network

_last = 0.0


def _request(url: str, method: str = "GET"):
    global _last
    wait = PAUSE - (time.monotonic() - _last)
    if wait > 0:
        time.sleep(wait)
    _last = time.monotonic()
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=300)


def get_text(url: str) -> str:
    with _request(url) as r:
        return r.read().decode("utf-8")


def head_length(url: str) -> int:
    with _request(url, "HEAD") as r:
        return int(r.headers["Content-Length"])


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(url: str, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    with _request(url) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f, 1 << 20)
        length = r.headers.get("Content-Length")
        lm = r.headers.get("Last-Modified", "")
    got = tmp.stat().st_size
    if length is not None and got != int(length):
        tmp.unlink()
        raise SystemExit(f"{url}: got {got} bytes, the server stated {length}")
    tmp.replace(dest)
    return {
        "url": url,
        "bytes": got,
        "sha256": sha256(dest),
        "last_modified": lm,
        "fetched_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def is_current(d: Path, rel: str, manifest: dict) -> bool:
    entry = manifest.get("files", {}).get(rel)
    return bool(entry) and (d / rel).exists() and sha256(d / rel) == entry["sha256"]


# ---------------------------------------------------------------- main


def main() -> int:
    page = get_text(DATASET_PAGE)
    conditions = conditions_text(page)
    if not page_licence_ok(conditions):
        raise SystemExit(
            "the dataset page's Conditions of use no longer read as CC BY 4.0; stopping"
        )

    tables = country_tables(zip_links(page))
    releases = {release_dir(u) for u in tables}
    if len(releases) != 1:
        raise SystemExit(f"expected one release directory on the page, found {sorted(releases)}")
    release = releases.pop()
    version = release_version(release)
    base = SERVER + release + "/"

    doi = json.loads(get_text(DATACITE + DATASET_DOI.lower()))["data"]["attributes"]
    doi_title = doi["titles"][0]["title"]
    if release.split("_")[1] not in doi_title:
        raise SystemExit(f"DOI {DATASET_DOI} is titled {doi_title!r}, not release {release}")

    listing = listing_entries(get_text(base))
    d = RAW / version
    d.mkdir(parents=True, exist_ok=True)
    mpath = d / "MANIFEST.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {}
    files = manifest.setdefault("files", {})

    # copyright.txt of the directory the tables sit in
    cr_url = base + "copyright.txt"
    cr_tmp = d / "copyright.txt.new"
    cr_entry = fetch(cr_url, cr_tmp)
    cr_licence = copyright_licence(cr_tmp.read_text(encoding="utf-8"))
    if "copyright.txt" in files and files["copyright.txt"]["sha256"] == cr_entry["sha256"]:
        cr_tmp.unlink()
    else:
        cr_tmp.replace(d / "copyright.txt")
        files["copyright.txt"] = cr_entry | {"licence_stated": cr_licence}
        print(f"{version}/copyright.txt: {cr_licence}")

    excluded = []
    plan = []
    for url in tables:
        name = url.rsplit("/", 1)[1]
        substance, reason = classify(name)
        if substance is None:
            excluded.append({"url": url, "reason": reason})
        elif cr_licence != "CC BY 4.0":
            excluded.append(
                {"url": url, "reason": f"copyright.txt states {cr_licence}, not CC BY 4.0"}
            )
        elif name not in listing:
            excluded.append(
                {"url": url, "reason": "linked from the page but absent from the listing"}
            )
        else:
            plan.append((url, f"{substance}/{name}", substance))

    total = 0
    for url, rel, _ in plan:
        total += files[rel]["bytes"] if is_current(d, rel, manifest) else head_length(url)
    if total > SIZE_LIMIT:
        raise SystemExit(f"selected files total {total:,} bytes, over the {SIZE_LIMIT:,} limit")

    fetched = 0
    for url, rel, substance in plan:
        if is_current(d, rel, manifest):
            continue
        entry = fetch(url, d / rel)
        files[rel] = entry | {
            "substance": substance,
            "listing_modified": listing[url.rsplit("/", 1)[1]]["modified"],
            "listing_size": listing[url.rsplit("/", 1)[1]]["size"],
            "licence": "CC BY 4.0",
        }
        fetched += 1
        print(f"{version}/{rel}: {entry['bytes']:,} bytes, {entry['last_modified']}")

    manifest.update(
        {
            "release": release,
            "version": version,
            "dataset_page": DATASET_PAGE,
            "dataset_doi": DATASET_DOI,
            "dataset_doi_title": doi_title,
            "dataset_doi_issued": next(
                (x["date"] for x in doi.get("dates", []) if x.get("dateType") == "Issued"), ""
            ),
            "report_citation": REPORT,
            "licence": "CC BY 4.0",
            "licence_url": LICENCE_URL,
            "conditions_of_use": conditions,
            "excluded": excluded,
            "files": dict(sorted(files.items())),
        }
    )
    mpath.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(f"{fetched} fetched, {len(plan) - fetched} already present, {len(excluded)} excluded")
    for x in excluded:
        print(f"  excluded {x['url'].rsplit('/', 1)[1]}: {x['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
