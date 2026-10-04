# edgar-ghg-countries

A reproducible download of the country tables of EDGAR 2026 GHG (EDGAR_2026_GHG), the 2026 release of the
EDGAR Community GHG database from the European Commission's Joint Research Centre (JRC). The tables give
annual and monthly emissions by country and IPCC sector, 1970-2025 (F-gases 1990-2025), as xlsx inside zip
files. Only the substances the publisher licenses under CC BY 4.0 are taken: CH4, N2O, F-gases and
biogenic CO2.

- Dataset page: <https://edgar.jrc.ec.europa.eu/dataset_ghg2026>
- Files: <https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/EDGAR_2026_GHG/>
- Dataset DOI: [10.2905/JRC.2W3HH78](https://doi.org/10.2905/JRC.2W3HH78)

## What is taken and what is not

| Directory | Files | Content |
|---|---|---|
| `CH4/` | `EDGAR_CH4_1970_2025.zip`, `EDGAR_CH4_m_1970_2025.zip` | CH4, annual and monthly, kt |
| `N2O/` | `EDGAR_N2O_1970_2025.zip`, `EDGAR_N2O_m_1970_2025.zip` | N2O, annual and monthly, kt |
| `CO2bio/` | `EDGAR_CO2bio_1970_2025.zip`, `EDGAR_CO2bio_m_1970_2025.zip` | biogenic CO2, annual and monthly, kt |
| `Fgases/` | `EDGAR_F-gases_1990_2025.zip`, `EDGAR_AR5g_F-gases_1990_2025.zip` | F-gases by gas, and grouped in CO2eq (GWP100 AR5), annual |

Not taken:

- Fossil CO2 (`IEA_EDGAR_CO2_*`): the dataset page licenses IEA-EDGAR CO2 under CC BY-NC-ND 4.0.
- Total GHG in CO2eq (`EDGAR_AR5_GHG_*`): it includes fossil CO2, and the page states no separate licence for it.
- All gridded maps (NetCDF and text, annual and monthly) and all earlier releases.

The download script reads the links from the dataset page, keeps only zips directly in the release directory
(country tables), checks the page's Conditions of use and the directory's `copyright.txt`, and records every
excluded file with its reason in the manifest.

## Licence

CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>): "Unless otherwise noted, all material owned by the
European Union is licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0) licence", per the
dataset page and the `copyright.txt` kept next to the data. Reuse is allowed provided appropriate credit is given
and any changes are indicated.

Cite the data and the report:

> EDGAR (Emissions Database for Global Atmospheric Research) Community GHG Database, a collaboration between the
> European Commission, Joint Research Centre (JRC), the International Energy Agency (IEA), and comprising IEA-EDGAR
> CO2, EDGAR CH4, EDGAR N2O, EDGAR F-GASES version EDGAR_2026_GHG (2026) European Commission, JRC (Datasets).
> doi:10.2905/JRC.2W3HH78

> Crippa, M., Guizzardi, D., Pagani, F., Banja, M., Ciarlantini, S., Muntean, M., Amici, L., Luini, C., Honavar
> Melo Pires, R., Quadrelli, R., Carvalho, P., Ruiz Ponsoda, D., Andrews, S., Köykkä, J., Grassi, G., Rossi, S.,
> Melo, J., Branco, A., Suárez-Moreno, M., Sedano, F., Manca, G., Pisoni, E., Pekar, F., GHG emissions of all world
> countries - 2026 Report, Publications Office of the European Union, Luxembourg, 2026, doi:10.2760/7717504,
> JRC147815.

## How to run

```sh
uv run python scripts/01_download.py   # fetch into data/raw/ghg2026/
uv run python scripts/02_verify.py     # re-hash and test every file
uv run python -m pytest                # unit tests for the page and listing parsing
```

The download is idempotent: a file whose sha256 matches its manifest entry is not fetched again.

## Layout

```
scripts/01_download.py         fetch the country tables of the release named on the dataset page
scripts/02_verify.py           check files against the manifest, test zips (and the xlsx inside)
tests/                         unit tests; tests/fixtures/ holds trimmed copies of the page, listing and copyright.txt
data/raw/ghg2026/              not in git
  MANIFEST.json                per file: url, bytes, sha256, Last-Modified, fetch time, listed date and size;
                               plus the release, DOI, citation, Conditions of use text and excluded files
  copyright.txt                the release directory's copyright notice (CC BY 4.0)
  CH4/ N2O/ CO2bio/ Fgases/    the zips as served
```
