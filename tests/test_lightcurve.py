import numpy as np
import pandas as pd
import pytest

from astrolcquery.lightcurve import LightCurve


def test_requires_time(small_lc):
    with pytest.raises(ValueError):
        LightCurve(pd.DataFrame({"mag": [1, 2]}), small_lc.meta)


def test_requires_mag_or_flux(small_lc):
    with pytest.raises(ValueError):
        LightCurve(pd.DataFrame({"time": [1, 2]}), small_lc.meta)


def test_sorted_by_time(meta):
    data = pd.DataFrame({"time": [59002.0, 59000.0, 59001.0], "mag": [16.9, 17.0, 17.1]})
    lc = LightCurve(data, meta)
    assert lc.time[0] == 59000.0
    assert np.all(np.diff(lc.time) > 0)


def test_mag_from_flux_roundtrip(small_lc):
    flux = small_lc.flux
    lc2 = LightCurve(pd.DataFrame({"time": small_lc.time, "flux": flux}), small_lc.meta)
    assert np.allclose(lc2.mag, small_lc.mag, atol=1e-6)


def test_flux_from_mag_roundtrip(small_lc):
    mags = small_lc.flux
    lc2 = LightCurve(pd.DataFrame({"time": small_lc.time, "flux": mags}), small_lc.meta)
    assert np.allclose(lc2.flux, small_lc.flux, atol=1e-20)


def test_jd_property(small_lc):
    jd = small_lc.jd
    assert np.all(jd > 2400000)
    assert np.allclose(jd - 2400000.5, small_lc.time, atol=1e-8)


def test_hjd_requires_coord(meta):
    from astrolcquery.lcmeta import TargetInfo
    target = TargetInfo("no_coord")
    meta.target = target
    data = pd.DataFrame({"time": [59000.0], "mag": [17.0]})
    lc = LightCurve(data, meta)
    with pytest.raises(ValueError):
        lc.to_hjd()


def test_copy_independent(small_lc):
    lc2 = small_lc.copy()
    assert lc2 is not small_lc
    assert np.array_equal(lc2.time, small_lc.time)


def test_binning_reduces_points(small_lc):
    binned = small_lc.binning(binsize=0.5)
    assert isinstance(binned, LightCurve)
    assert "time" in binned.df.columns


def test_apply_mask(small_lc):
    masked = small_lc.apply_mask([True, False, True, False])
    assert len(masked) == 2


def test_to_pandas_copy(small_lc):
    df = small_lc.to_pandas()
    df["time"] = 0
    assert not np.allclose(small_lc.time, 0)
