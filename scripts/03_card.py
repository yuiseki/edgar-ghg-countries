#!/usr/bin/env python3
"""Write data/README.md (the Hub card), data/LICENSE and data/provenance.yaml.

Everything comes from the manifest of the newest release under data/raw/.

    uv run python scripts/03_card.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CC = "https://creativecommons.org/licenses/by/4.0/"


def facts() -> dict:
    d = sorted((DATA / "raw").glob("*/MANIFEST.json"))[-1].parent
    m = json.loads((d / "MANIFEST.json").read_text())
    return {"dir": d.name, "m": m, "bytes": sum(e["bytes"] for k, e in m["files"].items())}


def table(f: dict) -> str:
    return "\n".join(
        f"| `raw/{f['dir']}/{k}` | {e['bytes']:,} | {e.get('substance', '')} |"
        for k, e in sorted(f["m"]["files"].items())
    )


def excluded(f: dict) -> str:
    return "\n".join(f"- `{Path(x['url']).name}`: {x['reason']}" for x in f["m"]["excluded"])


def card(f: dict) -> str:
    m = f["m"]
    return f"""---
license: cc-by-4.0
license_name: cc-by-4.0
license_link: {CC}
language:
- en
tags:
- edgar
- jrc
- greenhouse-gas
- emissions
- methane
- nitrous-oxide
- f-gases
size_categories:
- 100M<n<1B
---

# edgar-ghg-countries

The country tables of {m["release"]}, the 2026 release of the EDGAR Community GHG database
of the European Commission's Joint Research Centre (JRC): annual and monthly emissions by
country and IPCC sector, 1970-2025 (F-gases 1990-2025), as xlsx inside zip files, exactly as
the JRC serves them. Only the substances the publisher licenses under CC BY 4.0 are here:
CH4, N2O, F-gases and biogenic CO2.

- Dataset page: <{m["dataset_page"]}>
- Dataset DOI: [{m["dataset_doi"]}](https://doi.org/{m["dataset_doi"]}) ({m["dataset_doi_title"]}, issued {m["dataset_doi_issued"]})

## Files

| path | bytes | substance |
|---|---:|---|
{table(f)}

`raw/{f["dir"]}/MANIFEST.json` gives each file's URL, size, sha256, Last-Modified and fetch
time, and records the excluded files with the reason. `copyright.txt` is the publisher's
notice kept next to the data. A new EDGAR release is a different edition, so it would be a
new directory beside this one.

## Not included

{excluded(f)}
- All gridded maps (NetCDF and text) and all earlier releases (the gridded maps are collected
  separately, as `edgar-ghg-grids`).

## Licence

CC BY 4.0 ({CC}): "Unless otherwise noted, {m["conditions_of_use"].split("Unless otherwise noted, ")[1].split(" This means")[0]}"
Reuse is allowed provided appropriate credit is given and any changes are indicated.

Cite the data:

> EDGAR (Emissions Database for Global Atmospheric Research) Community GHG Database, a
> collaboration between the European Commission, Joint Research Centre (JRC), the International
> Energy Agency (IEA), and comprising IEA-EDGAR CO2, EDGAR CH4, EDGAR N2O, EDGAR F-GASES
> version {m["release"]} (2026) European Commission, JRC (Datasets). doi:{m["dataset_doi"]}

and the report:

> {m["report_citation"]}

Collection code: <https://github.com/yuiseki/edgar-ghg-countries> (MIT).
"""


def licence_file(f: dict) -> str:
    m = f["m"]
    return f"""The contents of data/raw/ are the country tables of {m["release"]}, © European
Union 2026, European Commission, Joint Research Centre (JRC), unchanged.

{m["conditions_of_use"].split("Disclaimer:")[0].split(chr(10), 1)[1].split(chr(10))[0]}

Licensed under CC BY 4.0 ({CC}): reuse is allowed provided appropriate credit is given and
any changes are indicated. IEA-EDGAR CO2 (fossil CO2), which the publisher licenses under
CC BY-NC-ND 4.0, and the total in CO2eq that includes it are not included.

The code of the repository this dataset was built from is MIT licensed.
"""


def provenance(f: dict) -> str:
    m = f["m"]
    return f"""# Where this data comes from and what was done to it.

source:
  name: {m["dataset_doi_title"]} ({m["release"]}), country tables
  publisher: European Commission, Joint Research Centre (JRC)
  dataset_page: {m["dataset_page"]}
  doi: {m["dataset_doi"]}  # issued {m["dataset_doi_issued"]}
  licence:
    applied: CC BY 4.0 ({CC}), from the dataset page's conditions of use and copyright.txt
    card: "license: cc-by-4.0"
    attribution_required: true
    left_out: fossil CO2 (CC BY-NC-ND 4.0) and the total in CO2eq that includes it
  citation: >-
    EDGAR Community GHG Database version {m["release"]} (2026) European Commission, JRC (Datasets).
    doi:{m["dataset_doi"]}

processing:
  - none: the zips are as served, each checked against the sha256 in MANIFEST.json
"""


def main() -> int:
    f = facts()
    (DATA / "README.md").write_text(card(f), encoding="utf-8")
    (DATA / "LICENSE").write_text(licence_file(f), encoding="utf-8")
    (DATA / "provenance.yaml").write_text(provenance(f), encoding="utf-8")
    print(f"{len(f['m']['files'])} files, {f['bytes']:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
