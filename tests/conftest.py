import numpy as np
import pandas as pd
import pytest
import astropy.units as u
from astropy.coordinates import SkyCoord

from astrolcquery.lcmeta import TargetInfo, FacilityInfo, LCMeta
from astrolcquery.phot_utils import get_band_info


def pytest_addoption(parser):
    parser.addoption(
        "--website",
        action="store_true",
        default=False,
        help="run live network integration tests against real survey APIs",
    )


def pytest_collection_modifyitems(config, items):
    run_website = config.getoption("--website")
    if run_website:
        return
    for item in items:
        if "website" in item.keywords:
            item.add_marker(
                pytest.mark.skip(reason="live API test; run with pytest --website")
            )


@pytest.fixture
def coord():
    return SkyCoord(150.0, 2.0, unit=u.deg)


@pytest.fixture
def lc(coord):
    from astrolcquery.surveys.synthetic import SyntheticSurvey

    return SyntheticSurvey().generate(coord=coord, n=200, period=12.0, seed=42)


@pytest.fixture
def meta(coord):
    target = TargetInfo(name="test_target", coord=coord)
    facility = FacilityInfo(survey="ZTF")
    band = get_band_info("ZTF_g", system="AB")
    return LCMeta(target, facility, band)


@pytest.fixture
def col(coord):
    from astrolcquery.collection import LightCurveCollection
    from astrolcquery.surveys.synthetic import SyntheticSurvey

    svy = SyntheticSurvey()
    a = svy.generate(seed=1, period=10.0, coord=coord)
    b = svy.generate(seed=2, period=8.0, coord=coord)
    return LightCurveCollection([a, b])


@pytest.fixture
def small_lc(meta):
    time = np.array([59000.0, 59001.0, 59002.0, 59003.0])
    mag = np.array([17.0, 17.1, 16.9, 17.2])
    mag_err = np.full(4, 0.05)
    data = pd.DataFrame({"time": time, "mag": mag, "mag_err": mag_err})
    from astrolcquery.lightcurve import LightCurve

    return LightCurve(data, meta)
