---
license: cc-by-4.0
license_name: cc-by-4.0
license_link: https://creativecommons.org/licenses/by/4.0/
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
---

# edgar-ghg-countries

The country tables of EDGAR_2026_GHG, the 2026 release of the EDGAR Community GHG database
of the European Commission's Joint Research Centre (JRC): annual and monthly emissions by
country and IPCC sector, 1970-2025 (F-gases 1990-2025), as xlsx inside zip files, exactly as
the JRC serves them. Only the substances the publisher licenses under CC BY 4.0 are here:
CH4, N2O, F-gases and biogenic CO2.

- Dataset page: <https://edgar.jrc.ec.europa.eu/dataset_ghg2026>
- Dataset DOI: [10.2905/JRC.2W3HH78](https://doi.org/10.2905/JRC.2W3HH78) (EDGAR 2026 Greenhouse Gas Emissions, issued 2026-09-24)

## Files

| path | bytes | substance |
|---|---:|---|
| `raw/ghg2026/CH4/EDGAR_CH4_1970_2025.zip` | 5,719,692 | CH4 |
| `raw/ghg2026/CH4/EDGAR_CH4_m_1970_2025.zip` | 76,656,977 | CH4 |
| `raw/ghg2026/CO2bio/EDGAR_CO2bio_1970_2025.zip` | 1,495,905 | CO2bio |
| `raw/ghg2026/CO2bio/EDGAR_CO2bio_m_1970_2025.zip` | 22,303,337 | CO2bio |
| `raw/ghg2026/Fgases/EDGAR_AR5g_F-gases_1990_2025.zip` | 471,126 | Fgases |
| `raw/ghg2026/Fgases/EDGAR_F-gases_1990_2025.zip` | 1,467,444 | Fgases |
| `raw/ghg2026/N2O/EDGAR_N2O_1970_2025.zip` | 6,241,014 | N2O |
| `raw/ghg2026/N2O/EDGAR_N2O_m_1970_2025.zip` | 76,382,662 | N2O |
| `raw/ghg2026/copyright.txt` | 540 |  |

`raw/ghg2026/MANIFEST.json` gives each file's URL, size, sha256, Last-Modified and fetch
time, and records the excluded files with the reason. `copyright.txt` is the publisher's
notice kept next to the data. A new EDGAR release is a different edition, so it would be a
new directory beside this one.

## Not included

- `IEA_EDGAR_CO2_1970_2025.zip`: fossil CO2 (IEA-EDGAR CO2): licensed under CC BY-NC-ND 4.0 per the dataset page
- `EDGAR_AR5_GHG_1970_2025.zip`: total GHG in CO2eq: includes fossil CO2 (CC BY-NC-ND 4.0); the page states no licence for the total
- `IEA_EDGAR_CO2_m_1970_2025.zip`: fossil CO2 (IEA-EDGAR CO2): licensed under CC BY-NC-ND 4.0 per the dataset page
- All gridded maps (NetCDF and text) and all earlier releases (the gridded maps are collected
  separately, as `edgar-ghg-grids`).

## Licence

CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/): "Unless otherwise noted, all material owned by the European Union is licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0) licence."
Reuse is allowed provided appropriate credit is given and any changes are indicated.

Cite the data:

> EDGAR (Emissions Database for Global Atmospheric Research) Community GHG Database, a
> collaboration between the European Commission, Joint Research Centre (JRC), the International
> Energy Agency (IEA), and comprising IEA-EDGAR CO2, EDGAR CH4, EDGAR N2O, EDGAR F-GASES
> version EDGAR_2026_GHG (2026) European Commission, JRC (Datasets). doi:10.2905/JRC.2W3HH78

and the report:

> Crippa, M., Guizzardi, D., Pagani, F., Banja, M., Ciarlantini, S., Muntean, M., Amici, L., Luini, C., Honavar Melo Pires, R., Quadrelli, R., Carvalho, P., Ruiz Ponsoda, D., Andrews, S., Köykkä, J., Grassi, G., Rossi, S., Melo, J., Branco, A., Suárez-Moreno, M., Sedano, F., Manca, G., Pisoni, E., Pekar, F., GHG emissions of all world countries - 2026 Report, Publications Office of the European Union, Luxembourg, 2026, doi:10.2760/7717504, JRC147815.

Collection code: <https://github.com/yuiseki/edgar-ghg-countries> (MIT).
