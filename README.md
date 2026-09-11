# astrolcquery

Query and download multi-survey astronomical light curves with a unified API.

`astrolcquery` normalizes photometric time series from several public surveys
(ZTF, ASAS-SN, Catalina, TESS, WISE) into a consistent `LightCurve` container
so that every survey's data shares one time axis and interchangeable `mag` /
`flux` columns.

## Installation

```bash
pip install -e .
```

Requires Python >= 3.10 with `numpy`, `pandas`, `astropy`, `matplotlib`,
`pyyaml`. Optional real-survey adapters use `astroquery`, `lightkurve` and
`pyasassn` (lazy imports). `pyarrow` enables parquet storage.

## Python API

```python
import astropy.units as u
from astropy.coordinates import SkyCoord
from astrolcquery import LCQueryClient

client = LCQueryClient(surveys=["ZTF", "WISE"])
coord = SkyCoord(150.0, 2.0, unit=u.deg)
collection = client.get_lightcurve(coord, radius=5 * u.arcsec)

print(collection)          # <LightCurveCollection: ..., 2 curves>
for lc in collection:
    print(lc)              # <LightCurve: ... (ZTF/ZTF_g), N=...>
    print(lc.mag[:5])      # magnitudes
    print(lc.flux[:5])     # fluxes (erg / (cm^2 s AA))
    print(lc.jd[:5], lc.hjd[:5])   # Julian / Heliocentric JD

collection.plot_atlas()              # multi-band figure
period = collection[0].find_period(1.0, 100.0)   # Lomb-Scargle
folded = collection[0].fold(period)              # phase-folded DataFrame
```

## Command line

```bash
lcquery --survey ztf asassn --plot 150.0 2.0
lcquery --target "150.0 2.0" --surveys ZTF WISE --cache
```

## Offline / synthetic data

For demos and tests (no network) use the built-in `synthetic` survey:

```python
client = LCQueryClient(surveys=["synthetic"])
collection = client.get_lightcurve(SkyCoord(150, 2, unit=u.deg))
```

Run the offline test suite:

```bash
/Users/zzx/.pyenv/shims/python3.11 -m pytest -q
```

## Survey support

| survey | backend | band / system | status |
|--------|---------|---------------|--------|
| ZTF    | IRSA ZTF-LC-API (`nph_light_curves`) | ZTF_g/r/i (AB) | verified |
| ASAS-SN| `pyasassn`                          | V (Vega)       | verified |
| TESS   | `lightkurve`                        | TESS           | verified |
| WISE   | IRSA GATOR (`neowiser_p1bs_psd`)    | W1/W2 (Vega)   | verified |
| Catalina | — (no public no-auth API)         | CSS_V (Vega)   | unavailable |
| synthetic | built-in generator              | ZTF_g          | offline |

The real survey adapters are lazily imported and verified against live services
(see `tests/test_integration.py`, run with `pytest --website`). Unavailable
surveys raise or are marked expected-failure rather than silently returning bad
data.

## Notes

- Time is stored internally as MJD; `jd`, `hjd`, `bjd` are derived properties.
- Magnitudes default to the survey's native system (AB or Vega) as recorded in
  the band registry; `get_band_info` exposes wavelength/zero-point metadata.
- Field descriptions for every survey column are config-driven and available
  via `FieldHelper.get_info("ZTF", "seeing")`.
- Offline tests never hit the network; live tests are opt-in via `--website`.
