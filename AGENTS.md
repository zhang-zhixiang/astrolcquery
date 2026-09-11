# ASTROLCQUERY — Agent Guide

This document is the **single source of truth** for the `astrolcquery` package: its
goals, architecture, module layout, naming conventions, constraints, and the
step-by-step build plan. Read it before touching any code.

---

## 1. Project Goal

`astrolcquery` is a Python package that lets a user query and download light curves
for a given celestial target from several public photometric **surveys** (ZTF,
ASAS-SN, Catalina, TESS, WISE), normalize them into one consistent format, analyse
them, and plot them — from a simple Python API **or** a terminal command.

The three design pillars (from the design discussions):

1. **Simple entry point** — give a coordinate (`RA Dec`), a `SkyCoord`, or a target
   name; get back one or more `LightCurve` objects with a uniform time axis and
   interchangeable `mag`/`flux`.
2. **Consistent container** — every survey's data is wrapped in the same `LightCurve`
   object backed by a pandas `DataFrame`.
3. **Consumable** — plotting, multi-band composition (`LightCurveCollection`),
   phase folding, period search, local caching, and a `lcquery` CLI.

---

## 2. Design Principles (decision log)

These were the decisions reached across the design conversations; do not relitigate
them without a strong reason:

- **`LightCurve` is a thin, clean data container.** It stores a sorted pandas
  `DataFrame` plus an `LCMeta` object. It does **not** own help text or survey
  logic. Help/schema text lives in the config-driven **`FieldHelper`**.
- **Metadata is hierarchical and dataclass-based** — `LCMeta` wraps
  `TargetInfo` / `FacilityInfo` / `BandInfo`. Never flatten metadata into a plain
  dict.
- **Units & coordinates use astropy** — `SkyCoord`, `EarthLocation`, `Time`,
  `astropy.units`. Time is stored internally as **MJD** (`float`); the `.time_obj`
  property converts lazily to an astropy `Time` object. Do not hand-roll time math.
- **Conversion formulas live in `phot_utils`** (a `filters`/`photometry` module).
  Bands come from a **curated, built-in registry** (`_BAND_PARAMS`): the AB
  zero-point is *derived exactly* from the 3631 Jy definition via astropy's
  `spectral_density` equivalency, and the Vega zero-points are curated published
  values. No silent wrong-value fallback — an unknown band raises `KeyError`.
  `LightCurve` only *proxies* these conversions. (pyphot is not a hard dependency;
  its HDF filter library needs PyTables.)
- **Field descriptions are config-driven** (`config/fields_schema.yaml`), not
  hardcoded in Python, and are consumed through `FieldHelper`.
- **Location lookup is lazy + singleton-cached** (`utils.get_location`). It is
  computed only when needed (e.g. when computing `hjd`/`bjd`), because astropy's
  `EarthLocation.of_site` is slow. Never query it eagerly in constructors.
- **Third-party survey access is wrapped with the adapter pattern.** The package
  lazy-imports `astroquery`, `lightkurve`, and `pyasassn` inside the survey
  adapters. The package must stay importable even if those are missing.
- **Survey backends are verified live** (see §4.11); adapters must match the real
  API, not assume a schema. There is an opt-in `--website` integration test suite.
- **Everything must work offline for tests.** All tests use synthetic/generated
  data (see the `synthetic` survey). No test hits the network.

---

## 3. Package Structure

```
astrolcquery/
├── pyproject.toml              # build config, deps, [project.scripts] → lcquery
├── README.md                   # short description + usage
├── AGENTS.md                   # this file
├── astrolcquery/
│   ├── __init__.py             # public API re-exports
│   ├── _version.py             # __version__
│   ├── base.py                 # BaseDownloader / BaseSurvey / BaseCollection ABCs
│   ├── cli.py                  # `lcquery` entry point (argparse)
│   ├── client.py               # LCQueryClient — main user-facing orchestrator
│   ├── collection.py           # LightCurveCollection
│   ├── io.py                   # local cache + save/load (parquet/csv/pickle)
│   ├── helper.py               # FieldHelper (config-driven field docs)
│   ├── lcmeta.py               # LCMeta, TargetInfo, FacilityInfo, BandInfo
│   ├── lightcurve.py           # LightCurve
│   ├── phot_utils.py           # BandInfo pyphot wrapper, mag<->flux
│   ├── utils.py                # get_location, get_asassn_site_location, coord parsing
│   ├── config/
│   │   └── fields_schema.yaml  # GLOBAL + per-survey field descriptions
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── folding.py          # phase folding
│   │   └── period.py           # Lomb-Scargle period search
│   └── surveys/
│       ├── __init__.py         # registry import surface
│       ├── base.py             # SurveyBase(ABC) — query/download/parse template
│       ├── registry.py         # SURVEY_REGISTRY + get_survey()
│       ├── synthetic.py        # offline synthetic survey (tests/demos)
│       ├── ztf.py              # astroquery.irsa adapter
│       ├── asassn.py           # ASAS-SN sky-patrol adapter
│       ├── catalina.py         # Catalina/CSS adapter
│       ├── tess.py             # lightkurve adapter
│       └── wise.py             # timewise adapter
└── tests/
    ├── conftest.py             # fixtures: synthetic LightCurve(s), tmp dirs
    ├── test_lcmeta.py
    ├── test_lightcurve.py
    ├── test_phot.py
    ├── test_helper.py
    ├── test_utils.py
    ├── test_collection.py
    ├── test_io.py
    ├── test_analysis.py
    └── test_client.py
```

---

## 4. Module Responsibilities & Key Contracts

### 4.1 `lcmeta.py` — metadata
- `TargetInfo(name, coord=None, redshift=None, extra_params=dict)`
- `FacilityInfo(survey, telescope="", site_name="")`
  - `survey` is constrained to `Literal["ZTF","ASAS-SN","Catalina","TESS","WISE"]`
    (case/hyphen-insensitive, normalized at `__post_init__`).
  - `.location` → lazy `EarthLocation` via `utils.get_location`.
- `BandInfo(band, unit_system="AB")` — intentionally lightweight here; full
  physical band data (wavelengths, zero-point flux) comes from `phot_utils`.
- `LCMeta(target, facility, band)` with `__repr__`.

### 4.2 `phot_utils.py` — photometry
- `get_band_info(band, system='AB') -> BandInfo` from the built-in band registry.
  The AB zero-point is computed exactly from `3631 * u.Jy` using astropy's
  `spectral_density` equivalency at the band's effective wavelength; Vega
  zero-points are curated for ASAS-SN V, CSS V, TESS and WISE W1/W2.
- `mag_to_flux(mag, zp_flux, given_unit, mag_err=None)`
- `flux_to_mag(flux, zp_flux, given_unit, flux_err=None)`
- `BandInfo` dataclass stores `band`, `system`, `leff`, `lmin`, `lmax`, `width`,
  `zp_flux_AB`, `zp_flux_vega`; `BandInfo.zero_point(system=None)` returns the
  zero-point for the given (or native) system and raises for missing ones.
- `LightCurve` uses `meta.band.zero_point()` to convert `mag <-> flux` in the
  default flux unit `erg / (cm**2 s AA)`.

### 4.3 `helper.py` — field docs
- `FieldHelper.get_info(survey_name, field=None)` reads
  `config/fields_schema.yaml` and merges `GLOBAL` with per-survey entries.
- Return a dict (no `field`) or a single description string.
- Caches the config with a lazy class-level cache.

### 4.4 `utils.py` — infrastructure
- `get_location(survey, site_name=None)` → eager `EarthLocation`, singleton-cached.
- `get_asassn_site_location(site_code)` → `EarthLocation` from ASAS-SN site code.
- `parse_coord(x)` → `SkyCoord`, accepting strings / tuples / `SkyCoord`.

### 4.5 `lightcurve.py` — `LightCurve`
- `LightCurve(data: pd.DataFrame, meta: LCMeta)`; sorts by `time`, validates:
  `time` present; at least one of `mag`/`flux` present.
- Properties: `time`, `time_obj`, `jd`, `hjd`, `mag`, `mag_err`, `flux`,
  `flux_err`, `band`, `df`.
- Methods: `to_hjd`, `to_jd`, `fits_mask`, `binning`, `plot`, `fold`, `periodogram`,
  `to_pandas`, `save`, `copy`.
- `mag`/`flux` convert lazily using `meta.band` + `phot_utils`.

### 4.6 `collection.py` — `LightCurveCollection`
- Holds `list[LightCurve]` for one target across surveys/bands.
- `align_time(reference='jd'|'hjd'|'bjd'|'mjd')`
- `binning(surveys=None, binsize=1.0)` → weighted-mean binning per LC.
- `plot_atlas(split_bands=True, ...)` → multi-axes figure.
- `merge()` → single DataFrame.
- `save(path)`, `load(path)`.

### 4.7 `analysis/period.py` + `folding.py`
- `find_period(lc, min_p, max_p, method='lombscargle')` → best period + power
  spectrum (astropy `LombScargle`).
- `fold_lc(lc, period, t0=0)` → phased DataFrame; `plot_folded(...)` helper.

### 4.8 `io.py` — storage
- `save_lc(lc, path)`, `load_lc(path)`, `save_collection(col, path)`,
  `load_collection(path)`, and a `Cache` class with `~/.astrolcquery/cache/`
  default. Uses parquet when `pyarrow` is available, else CSV + pickle for meta.

### 4.9 `surveys/`
- `SurveyBase(ABC)` (`surveys/base.py`): contract for
  `query(coord, radius=..., **kw)`, `download(...)`, `parse(...) -> LightCurve`,
  `name`, `default_band`, `field_docs`.
- Each concrete adapter maps raw survey output → standard columns:
  `time`, `mag`, `mag_err` **or** `flux`, `flux_err`, `band`, and optional
  extras (`seeing`, `apt_ra`, `catflags`, `quality`, …).
- **One `LightCurve` per band.** `SurveyBase.download` / `parse` return a
  `list[LightCurve]` — one per distinct band — so a multi-band survey (ZTF g/r/i,
  ASAS-SN V/g, WISE W1/W2) yields several single-band curves that the client
  collects into a `LightCurveCollection`. `make_lc(...)` still builds a single
  `LightCurve`; the adapters group the raw rows by band first.
- Time is always normalized to **MJD** at ingest (ASAS-SN JD is converted by
  `mjd = jd - 2400000.5`), so mixed-survey plots/`merge()` share a common axis.
- `registry.get_survey(name)` (case-insensitive) returns an adapter instance.
- `synthetic.py`: deterministic synthetic generator used by tests and demos —
  works offline, no third-party deps.

### 4.11 Survey backends (verified live)
Every adapter talks to the real service (do not assume a schema):

| survey | backend | band(s) / system        | time           |
|--------|---------|-------------------------|----------------|
| ZTF    | IRSA ZTF-LC-API `nph_light_curves` | ZTF_g/r/i (AB) | MJD (also HJD) |
| ASAS-SN| `pyasassn.SkyPatrolClient`        | ASASSN_V/g (Vega) | JD        |
| Catalina| none (per-object CRTS files only) | CSS_V (Vega) | MJD / JD |
| TESS   | `lightkurve.search_lightcurve`    | TESS (Vega-ish) | BTJD→MJD |
| WISE   | IRSA GATOR `neowiser_p1bs_psd` / `allwise_p3as_mep` | WISE_W1/W2 (Vega) | MJD |

- `query(...)` returns the raw service result; `parse(...)` maps it to standard
  columns and builds one `LightCurve` per band via `make_lc(...)` (survey base).
- ZTF: `BANDNAME` and `POS=CIRCLE ra dec radius` (radius ≤ 0.1667°). Time column
  is `mjd`; `catflags` is carried as an extra column.
- ASAS-SN: cone search then `query_list`; the closest target to the requested
  coordinate is selected. Rows are grouped by `phot_filter` (V/g) into separate
  bands; JD is converted to MJD at ingest.
- WISE: `standardize_wise` picks `w{n}mpro`/`w{n}sigmpro` (Vega); W1 and W2 are
  returned as two separate single-band curves.
- TESS: lightkurve `to_pandas()` uses `time` as the index; `time` is BTJD so it
  is offset by `2457000` into a MJD-like range. Flux is PDC-SAP (relative).
- Catalina: no public no-auth region API; `query` raises `NotImplementedError`.
  The client catches per-survey errors and warns instead of crashing. The CRTS
  data is distributed per object; a future adapter should fetch by catalog ID.
- Live verification: `/Users/zzx/.pyenv/shims/python3.11 -m pytest --website tests/test_integration.py`.

### 4.10 `client.py` + `cli.py`
- `LCQueryClient(surveys=None, cache_dir=None)`; `get_lightcurve(target, radius)`
  → `LightCurveCollection`; `get_list(targets, radius)` for batches.
- The client **collects per-band LCs and skips failed/empty surveys with a
  warning** instead of crashing (so a missing survey never aborts a run).
- `cli.main()` (`lcquery`) with argparse:
  `lcquery --survey ztf asassn RA DEC [--plot] [--cache] [--all]`.
  `--plot` plots the collection; a survey with no data (e.g. TESS in an
  unobserved field) produces a warning and is skipped.

---

## 5. Standard Column Names & Units

| column        | type       | meaning                                            |
|---------------|------------|----------------------------------------------------|
| `time`        | float      | MJD (internal); property `.jd`/`.hjd` derived      |
| `mag`         | float      | apparent magnitude in `band`                       |
| `mag_err`     | float      | 1-sigma magnitude uncertainty                      |
| `flux`        | float      | flux in `flux_unit`                                |
| `flux_err`    | float      | 1-sigma flux uncertainty                           |
| `band`        | str        | band / filter code                                 |

- Time units: `MJD` internally; `jd`, `hjd`, `bjd` exposed via properties.
- Magnitude system: `AB` by default; `Vega` available through `BandInfo`.
- Flux unit: `erg / (cm**2 s AA)` default (`LightCurve._default_unit_flux`).
  `.flux`/`.flux_err` return values in that unit.

---

## 6. Constraints & Rules

- **Python ≥ 3.10.** Run everything with
  `/Users/zzx/.pyenv/shims/python3.11` (the interpreter that has `numpy`,
  `pandas`, `astropy`, `matplotlib`, `pytest`, `yaml`, `pyarrow`). The default
  `python` shim resolves to 3.14 and is missing these deps.
- **No comments** unless the code genuinely needs them. Match existing style.
- **Lazy-import third-party libs** (`astroquery`, `lightkurve`, `pyasassn`)
  inside survey methods; never at module top level of `__init__`.
- **Never hit the network in offline tests.** Use `surveys.synthetic`. Live API
  tests live in `tests/test_integration.py` and are gated behind `--website`
  (skipped by default).
- **Keep `LightCurve` clean** — no survey logic, no help text.
- **Editable install** via `pip install -e .` with `pyproject.toml`.
- **CLI entry point** name: `lcquery`.
- Unit system consistency: magnitudes default to `AB`; document overrides clearly.

---

## 7. Step-by-step Build Plan

1. **Write this AGENTS.md.** (done)
2. **Scaffold the package**: `pyproject.toml`, `__init__.py`, `_version.py`.
3. **Core data layer** (no deps beyond numpy/pandas/astropy/yaml):
   - `phot_utils.py` — band registry + conversion.
   - `utils.py` — location + coordinate parsing.
   - `lcmeta.py` — metadata dataclasses.
   - `lightcurve.py` — `LightCurve` container (existing file, extend & fix).
   - `helper.py` + `config/fields_schema.yaml` (existing, extend schema entries).
4. **Collection & analysis**: `collection.py`, `analysis/period.py`,
   `analysis/folding.py`.
5. **Storage**: `io.py` (save/load + `Cache`).
6. **Synthetic survey + registry**: `surveys/synthetic.py`, `surveys/base.py`,
   `surveys/registry.py`. Wire into `__init__`.
7. **Client + CLI**: `client.py`, `cli.py`.
8. **Tests** (offline, synthetic data): `tests/conftest.py` + the per-module
   test files. Run `python3.11 -m pytest -q`.
9. **Real adapters** (ZTF/ASAS-SN/Catalina/TESS/WISE) as lazy adapters against
   their live backends (see §4.11); unit-test the column-mapping parts offline
   and the live paths with the opt-in `--website` suite.
10. **Polish**: README, `python3.11 -m pytest`, verify `lcquery --help`.

---

## 8. Verification commands

```bash
# environment (use python3.11, NOT plain `python`)
PY=/Users/zzx/.pyenv/shims/python3.11

$PY -c "import astrolcquery; print(astrolcquery.__version__)"

# run the full offline test suite (live tests skipped by default)
$PY -m pytest -q

# run the LIVE integration tests against real survey APIs
$PY -m pytest -q --website

# smoke check the CLI
$PY -m astrolcquery.cli --help
```

### Live verification status

Verified working against the real services (see `tests/test_integration.py`):
ZTF, ASAS-SN, TESS, WISE. `Catalina` has no public no-auth region API and is
`xfailed` (documented) in the live suite.
