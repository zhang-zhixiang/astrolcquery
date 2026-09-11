"""Live integration tests against real survey APIs.

These tests hit the network and are skipped by default. Run with:

    pytest --website tests/test_integration.py

Verification matrix (verified live in this environment):
  - ZTF   : works via IRSA ZTF-LC-API (nph_light_curves)
  - TESS  : works via lightkurve
  - WISE  : works via IRSA multi-epoch catalogs
  - ASAS-SN: works via pyasassn SkyPatrolClient
  - Catalina: no public region API (see test_catalina_live)
"""

import astropy.units as u
import pytest
from astropy.coordinates import SkyCoord

from astrolcquery.surveys import get_survey

COORD = SkyCoord(260.0, 42.6, unit=u.deg)


@pytest.mark.website
def test_ztf_live_splits_bands():
    lcs = get_survey("ZTF").download(COORD, radius=5 * u.arcsec)
    assert len(lcs) >= 1
    for lc in lcs:
        assert "time" in lc.df.columns
        assert "mag" in lc.df.columns
        assert lc.meta.band.system == "AB"
        assert len(lc) > 0


@pytest.mark.website
def test_wise_live_splits_bands():
    lcs = get_survey("WISE").download(COORD, radius=1 * u.arcmin)
    assert len(lcs) >= 1
    for lc in lcs:
        assert lc.meta.band.system == "Vega"
        assert lc.time.max() < 2400000  # native MJD
        assert len(lc) > 0


@pytest.mark.website
def test_tess_live():
    survey = get_survey("TESS")
    raw = survey.query(SkyCoord(45.67, 52.39, unit=u.deg))
    if raw is None:
        pytest.skip("No TESS data for this field")
    lcs = survey.parse(raw, coord=None, target_name="tess_target")
    assert len(lcs) >= 1
    # TESS time must be normalized to MJD (not JD/BTJD) to align with other surveys
    assert 50000 < lcs[0].time.min() < 100000


@pytest.mark.website
def test_asassn_live_splits_bands():
    lcs = get_survey("ASAS-SN").download(COORD, radius=1 * u.arcmin)
    assert len(lcs) >= 1
    for lc in lcs:
        assert lc.meta.band.system in ("Vega", "AB")
        assert len(lc) > 0


@pytest.mark.website
@pytest.mark.xfail(
    strict=False,
    reason="Catalina/CRTS photometry has no public no-auth region query API.",
)
def test_catalina_live():
    get_survey("Catalina").download(COORD, radius=1 * u.arcmin)
