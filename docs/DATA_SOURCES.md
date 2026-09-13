# Data sources and method

Every figure in this report comes from a document FedEx Corporation published itself. This
file says which one, and flags the places where a naive reading would be wrong.

---

## Primary sources

| Source | Filed / published | What it supplies |
|---|---|---|
| **Form 10-K FY2026** | 2026-07-20 (SEC accession 0001048911-26-000105) | Fleet by type and ownership, aircraft on order, segment revenue and operating income, facilities, headcount, capex |
| **Form 10-K FY2025** | 2025 | Prior-year comparatives, restated segment figures |
| **Statistical Book Q4 FY2026** | 2026 | Average daily volume and yield by service line, LTL shipments and revenue per shipment, revenue by service |
| **Statistical Book Q4 FY2025** | 2025 | Prior-year volumes (see restatement note below) |
| **Corporate Responsibility Reports 2022–2026** | annual | Scopes 1, 2 and 3, carbon intensity, electric vehicles, SAF, energy by source in terajoules |
| **Ernst & Young assurance statements** | with each CR report | Independent verification of the GHG figures |
| **CDP responses 2024–2025** | annual | Aviation efficiency in litres per available ton mile |
| **SEC XBRL company facts API** | continuous | Long series: revenue, operating income, net income, diluted EPS, capex FY2015–FY2026 |

---

## Table by table

| Table | Rows | Source |
|---|---:|---|
| `D_Aircraft` | 10 | 10-K FY2026 fleet table (type, max payload, owned / leased, in service, on order) |
| `F_Fleet` | 40 | 10-K FY2026 and FY2025 fleet tables, four fiscal years |
| `F_FleetPlan` | 13 | 10-K FY2026 aircraft purchase commitments and planned retirements by year |
| `D_Hub` | 15 | 10-K facility schedule + airport coordinates (WGS84) |
| `F_Network` | 19 | FY2026 annual report network figures (countries, airports, vehicles, facilities, drop-off points) |
| `F_Financial` | 12 | SEC XBRL, FY2015–FY2026 |
| `F_Segment` | 12 | 10-K segment note, FY2026 |
| `F_Geography` | 6 | 10-K revenue by geography |
| `F_Service` | 6 | Statistical Book Q4 FY2026, revenue and ADV by service line |
| `F_Freight` | 7 | Statistical Book, LTL shipments per day and revenue per shipment |
| `F_Climate` | 7 | CR reports, scope 1 and 2 by fiscal year |
| `F_Scope3` | 6 | CR report 2026, FY2025 categories only |
| `F_Intensity` | 17 | CR reports, emissions per million dollars of revenue, FY2009–FY2025 |
| `F_Energy` | 4 | CR report ESG annex, total energy and jet fuel share, FY2022–FY2025 |
| `F_EnergySource` | 24 | CR report ESG annex, six sources × four fiscal years, terajoules |
| `F_Electric` | 4 | CR reports, electric vehicles in operation |
| `F_SAF` | 2 | CR reports, sustainable aviation fuel deployed |
| `F_Efficiency` / `F_AviationIntensity` | 2 each | CDP responses 2024 and 2025 |
| `D_Target` | 9 | CR report 2026, published commitments and due years |
| `D_FiscalYear` | 12 | FY2015–FY2026, with availability flags per subject |

**23 CSV files, 235 rows of data.** Small by design: this is a curated model of published
figures, not a warehouse extract.

---

## Seven things that change how the numbers read

### 1. The fiscal year ends 31 May
FY2026 runs 1 June 2025 → 31 May 2026. Comparing a FedEx fiscal year against a calendar
year of any other company is a category error.

### 2. FY2026 is the last year consolidating FedEx Freight
The spin-off took effect 1 June 2026. Every FY2026 figure in this report includes Freight;
no later figure will. FedEx is also moving from a 31 May close to a 31 December close, so a
seven-month transition period is coming.

### 3. Scope 2 changes method mid-series
FY2019–FY2021 are **market-based**; FY2024–FY2025 are **location-based**. FY2022 and FY2023
are only published as a combined total. The report shows the break rather than smoothing a
continuous line over two different methodologies.

### 4. Scope 3 is not a time series
The published category perimeter changed three times between 2022 and 2026. Only FY2025 is
shown, broken down by its six categories. Any chart drawing scope 3 across years would be
comparing different definitions.

### 5. FedEx never publishes fuel in gallons
Energy is published in **terajoules**. The only physical volumes anywhere are litres, in the
CDP responses, and they cover FedEx Express alone, not the group. Aviation efficiency
(0.18765 L per available ton mile, CDP 2025) carries the same limitation. The number of
flights is not published at all: the CR Content Index cites confidentiality constraints.

### 6. Corporate Responsibility reports are named for their publication year
The "2026 CR Report" covers **FY2025**. Reading the title as the data year shifts every
climate figure by one year.

### 7. FY2025 volumes were restated
Average daily volume for FY2025 reads 17 001 k in the FY2025 Statistical Book and 16 231 k
in the restated FY2026 book. This model uses the **restated** figures throughout, so the
FY2025 line matches what FedEx itself now reports.

---

## What was deliberately not modelled

- **Hub coordinates are the airports', not the facilities'.** FedEx does not publish
  facility coordinates. On a world map the difference is invisible; at city scale it would
  not be, so the map is deliberately drawn at world scale.
- **No FY2026 climate data.** The CR report covering FY2026 was not published at the time
  of build. The climate page stops at FY2025 and says so; it does not extrapolate.
- **No estimated or derived metrics presented as reported.** Every figure on a KPI card is
  either published verbatim or a ratio of two published figures. Nothing is modelled,
  forecast, or benchmarked against peers.

---

## Updating at the next 10-K

1. Update the affected CSV in `Donnees/`. The usual rhythm: `F_Financial`, `F_Segment`,
   `F_Service` and `F_Geography` gain a row from the 10-K and the Q4 Statistical Book;
   `D_Aircraft` and `F_Fleet` from the fleet schedule; `F_FleetPlan` from the purchase
   commitments; the climate and energy tables later in the year, when the CR report lands.
2. Add the year to `D_FiscalYear` and set the four availability flags to match what actually
   exists.
3. Do not touch the measures. They all use the
   `VAR y = MAX ( … [FiscalYear] ) RETURN CALCULATE ( …, [FiscalYear] = y )` pattern and
   move to the new year on their own.
4. Rebuild, then check three totals before publishing: aircraft by type must equal the
   `Aircraft` KPI, segment revenue must equal consolidated revenue, and the `Of total`
   column on the Energy page must sum to 100 %.

Subtitles that name a year (*"FY2022 to FY2025"*) are text, and live in `gen_report.py`.
