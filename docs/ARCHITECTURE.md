# Architecture

How the report is built, and why it is built this way.

---

## 1. The build chain

Five scripts, run in order. Each writes files; none of them mutate state anywhere else.

| Script | Lines | Writes | Responsibility |
|---|---:|---|---|
| `gen_data.py` | 323 | `Donnees/*.csv` | The data, with the source of every figure in a comment |
| `gen_model.py` | 595 | `FedEx.SemanticModel/` | TMDL: 24 tables, 14 relationships, 183 measures |
| `gen_report.py` | 592 | `FedEx.Report/` | The 7 pages, 502 visuals, and the 66 generated assets |
| `check.py` | 321 | *nothing* | 12 quality gates; exits non-zero on any failure |
| `render_pages.py` | 463 | `apercus/*.png` | A headless approximation of each page, no Desktop needed |

Two supporting libraries carry the reusable logic:

- **`pbir_lib.py`** (658 lines) provides the PBIR primitives (`card`, `table`, `bar`, `col`, `line`,
  `donut`, `scatter`, `slicer`, `image`, `textbox`, `actionButton`) plus the layout solver.
- **`brand.py`** (716 lines) draws every pixel the report displays that is not data: the
  planisphere, the route arcs, 29 KPI pictograms, five aircraft silhouettes, the MERIDIAN
  mark, the tile and rail textures.

### Determinism

Two consecutive builds produce **632 byte-identical files**. This is verified, not assumed:

```bash
python gen_report.py && cp -r ../proj /tmp/a
rm -rf ../proj/FedEx.Report && python gen_report.py && cp -r ../proj /tmp/b
diff -r /tmp/a /tmp/b      # silent
```

Getting there required removing the last source of randomness: visual-level filter names
were `uuid4()`, which made every rebuild show phantom diffs in git. They are now derived
from the filter's own definition:

```python
"name": "f" + hashlib.sha1(f'{ref}|{kind}|{value}'.encode()).hexdigest()[:8]
```

---

## 2. The semantic model

### Shape

Four conformed dimensions, nineteen fact tables, and one measure table.

| Dimension | Grain | Feeds |
|---|---|---|
| `D_FiscalYear` | one row per fiscal year, FY2015–FY2026 | 10 fact tables |
| `D_Aircraft` | one row per aircraft type (10) | `F_Fleet`, `F_FleetPlan` |
| `D_Hub` | one row per sorting facility (15) | hub metrics, map coordinates |
| `D_Target` | one row per published commitment (9) | climate page |

All 14 relationships are **single-direction, many-to-one**. No bidirectional filters, no
many-to-many, no ambiguous paths. Every fact table joins a dimension on a surrogate-free
natural key (`FiscalYear`, `AircraftKey`, `HubKey`).

`Metrics` is a measure-only table: it holds all 183 measures and no columns, so the field
list reads as a menu of answers rather than a pile of raw columns.

### The fiscal-year flags

`D_FiscalYear` carries four hidden boolean columns: `IsFinancial`, `IsFleet`, `IsClimate`,
`IsEnergy`. Each page's year slicer is filtered on the flag that matches its subject, so a
page only ever offers years for which data actually exists. Climate has FY2019–FY2025,
Energy FY2022–FY2025, Financials FY2015–FY2026. The reader never selects a year that
returns blanks.

### The universal measure pattern

Every fact table holds several fiscal years. A bare `SUM` therefore returns the sum of all
of them: 2 796 aircraft instead of 700, $900bn of revenue instead of $94.7bn. One pattern
solves it everywhere:

```dax
Aircraft =
VAR y = MAX ( F_Fleet[FiscalYear] )
RETURN
    CALCULATE ( SUM ( F_Fleet[Aircraft] ), F_Fleet[FiscalYear] = y )
```

- **Unfiltered**, `MAX` returns the latest loaded year → the measure shows the current state.
- **Inside a year slicer**, `MAX` returns the selected year → the measure follows the user.
- **Inside a chart sliced by year**, `MAX` returns each column's own year → the series is correct.

No `LASTDATE`, no `TREATAS`, no calculation groups. One pattern, applied without exception.

### Measure families

183 measures organised into nine display folders:

| Folder | Count | Examples |
|---|---:|---|
| `01 Fleet` | 13 | `Aircraft`, `Aircraft owned`, `Aircraft on order`, `Owned share` |
| `02 Payload & capacity` | 12 | `Fleet payload Mlbs`, `Average payload`, `Total lift` |
| `03 Fleet mix` | 8 | `Boeing share`, `Trunk share`, `Manufacturer share` |
| `04 Hubs & network` | 27 | `Sort capacity`, `Sq ft`, `Hub rank`, `Employees` |
| `05 Financial` | 17 | `Revenue`, `Operating margin`, `EPS`, `Capex intensity` |
| `06 Volumes & yield` | 11 | `Daily packages`, `Reported yield`, `Volume growth` |
| `07 Climate` | 22 | `Scope 1 and 2`, `Carbon intensity`, `SAF deployed` |
| `08 Narrative` | 46 | the one-line context strings under each KPI |
| `09 Energy & fuel` | 27 | `Terajoules`, `Of total`, `Jet fuel`, `Energy intensity` |

The 46 **narrative** measures deserve a word. Each KPI tile carries a second line that
puts its number in perspective: *"Memphis sorts 484k/h"*, *"Only 3 on lease"*,
*"−19.7% since FY2022"*. They are DAX string expressions, not static text, so they follow
every filter the reader applies.

---

## 3. The report layer

### PBIR structure

```
FedEx.Report/
├── definition.pbir                  → points at ../FedEx.SemanticModel
├── definition/
│   ├── report.json                  theme, resource manifest
│   ├── pages/pages.json             page order and active page
│   └── pages/p1..p7/
│       ├── page.json                page size, background, display name
│       └── visuals/<name>/visual.json
└── StaticResources/RegisteredResources/    66 generated PNG
```

One JSON file per visual. A change to a single chart is a single-file diff in a pull
request, which is the whole point.

### Visual naming

`p3_064_tb` = page 3, z-order 64, type `tb` (table). The suffix encodes the type: `cd`
card, `tb` table, `ch` chart, `sc` scatter, `ss` slicer, `tx` textbox, `im` image, `bt`
button, `kb` KPI tile background. Sorting a page's folder gives you its z-order.

### Layout is computed, not chosen

Three solvers replace three habits of eyeballing:

**Column widths.** `fitw()` widens any column too narrow for its header or its longest real
value. Text columns are measured against the CSV; **measure columns are measured against
strings read from the live model over XMLA** and frozen in `rendered_values.json`, because
`"56 owned · 3 leased"` exists nowhere in the source data.

**Row spacing.** Row padding is derived from the panel height so the table fills its frame:

```python
libre = (h - 8 - HDR_ZONE) / rows - size * 1.33 - 7
rowpad = int(max(0, min(20, libre / 2)))
```

`HDR_ZONE = 150` is the height Power BI gives to title, subtitle and header row. Measured on
real screenshots, not guessed; an earlier estimate of 104 px put a scrollbar on every table.

**Row height.** `size × 1.33 + 2 × rowpad + 7`. The 1.33 converts points to pixels; the 7
is Power BI's internal cell padding.

### Page grid

1600 × 900. A 120 px navigation rail on the left, then:

| Band | Y | Height |
|---|---:|---:|
| Eyebrow / title / subtitle / filter / logo | 0 | 112 |
| KPI row (5 or 6 tiles) | 112 | 202 |
| Content | 328 | 536 |
| Source line | 860 | 30 |

The content band is split either as one full-height visual plus two stacked, or as
280 / 240 when the upper block holds a short table.

---

## 4. The map

The Bing map visual was rejected: it needs a network round-trip, it renders in its own
visual language, and it cannot be styled to match. The replacement is two layers sharing
one projection constant.

```python
MAP_BOUNDS = (-170, 158, -46, 76)     # lon0, lon1, lat0, lat1
```

**Layer 1, the backdrop.** A PNG drawn in `brand.py`:
- land mass sampled at 1° from the `global-land-mask` package, plotted as dots whose colour
  shifts with latitude;
- route arcs as quadratic Béziers with travelling dots;
- hub labels placed by **collision avoidance**: eight candidate positions at four
  increasing distances, largest hub first, rejecting any box that overlaps a placed label
  or another hub;
- gradient bands top and bottom so the legend sits on a legible ground.

**Layer 2, the live bubbles.** A `scatterChart` with no background and no axes, whose
`categoryAxis.start/end` and `valueAxis.start/end` are set to the same four bounds. Since
the drawn projection is linear in longitude and latitude, a linear scatter aligns exactly.

Result: hubs are real data points. They resize with sort capacity, respond to the continent
slicer, carry tooltips, and cross-filter the page on click. No tiles, no telemetry.

The title sits in its own 82 px band **above** the image, never on top of it. Otherwise a
northern hub (Anchorage, 61°N) lands underneath the subtitle.

---

## 4 bis. Three PBIR behaviours that cost a version each

**A visual-level filter on a measure is silently ignored.** `THE FIVE BIGGEST` carried
`filterConfig` on a `RANKX` measure with `ComparisonKind: 4` (≤ 5). Power BI accepted the
file, showed no error, and displayed all fifteen hubs with a scrollbar. The same filter
shape on a *column* works perfectly. It is what limits `THE NETWORK IN NUMBERS` to its
eleven key indicators. The fix was to precompute `CapacityRank` in the dimension and filter
on that column. **Rule: filter on columns, never on measures.**

**A table needs about 8 % of headroom or it scrolls.** The height model says a table filling
97 % of its panel fits. In the real renderer it gets a scrollbar. The build now reserves
40 px below the last row, which lands tables at 87 to 96 % fill, enough that Power BI never
adds the bar.

**`wordWrap` has no effect on a card's value.** A context line longer than the tile is
truncated, not wrapped. Every narrative measure is therefore written to fit on one line, and
`check.py` measures each one against its tile before delivery.

These were all found by exporting the report to PDF and reading it. `render_pages.py` draws
the layout but not Power BI's own rendering rules, so it cannot see them. That is why the
PDF export is part of the release procedure, not an afterthought.

---

## 5. The quality gate

`check.py` runs before every delivery. Twelve checks; any failure exits non-zero.

| Check | What it prevents |
|---|---|
| DAX reference validation | a measure silently returning blank after a column rename |
| Visual reference coverage | a visual pointing at a measure that no longer exists |
| Card text width | a truncated KPI context line (`wordWrap` has no effect on card values) |
| Visual title width | a title overflowing its panel |
| Table column width | a truncated header or value, measured against real data |
| Table height | a scrollbar where all rows should be visible |
| Panel fill | a short table floating in an oversized panel (< 88 % fill fails) |
| Table horizontal overflow | columns summing past the visual width |
| Integer font sizes | Power BI silently ignores decimal sizes on axes |
| Image manifest | a resource used but not registered renders as a blank rectangle |
| Apostrophe escaping | an unescaped `'` in a DAX string literal breaks the model |
| Navigation targets | a button pointing at a deleted page |

Every one of these exists because the corresponding defect shipped once and had to be found
by eye. That is the argument for the gate: the eye misses things, the measurement does not.

---

## 6. Known constraints

- The model reads local CSV through the `DossierDonnees` parameter. There is **no automated
  refresh from SEC EDGAR**. Figures are transcribed from filings and updated by hand at each
  10-K. The procedure is in the README.
- `render_pages.py` is an *approximation*. It draws the layout faithfully enough to catch
  overflow and empty space, but it does not evaluate DAX and its font metrics are DejaVu,
  roughly 10 % wider than Segoe UI. It is a smoke test, not a substitute for Desktop.
- PBIR is still evolving. This project targets `visualContainer` schema 2.12.0, page 2.1.0,
  report 3.3.0, and TMDL compatibility level 1606.
