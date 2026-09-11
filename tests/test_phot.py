import numpy as np
import pytest
from astropy import units as u

from astrolcquery.phot_utils import (
    get_band_info,
    mag_to_flux,
    flux_to_mag,
    BandInfo,
)

FLUX_UNIT = u.erg / (u.cm**2 * u.s * u.AA)


def test_get_band_info_returns_metadata():
    info = get_band_info("ZTF_g")
    assert info.band == "ZTF_g"
    assert info.leff.unit == u.AA
    assert info.zp_flux_AB.unit == FLUX_UNIT
    assert info.system == "AB"
    assert info.lmax > info.lmin


def test_get_band_info_unknown():
    with pytest.raises(KeyError):
        get_band_info("NOSUCH")


def test_mag_flux_roundtrip():
    zp = get_band_info("ZTF_g").zp_flux_AB
    mags = np.array([15.0, 16.0, 17.0])
    flux = mag_to_flux(mags, zp, FLUX_UNIT)
    back = flux_to_mag(flux, zp, FLUX_UNIT)
    assert np.allclose(back, mags, atol=1e-9)


def test_mag_flux_monotonic():
    zp = get_band_info("ZTF_g").zp_flux_AB
    flux = mag_to_flux(np.array([15.0, 17.0, 19.0]), zp, FLUX_UNIT)
    assert (np.diff(flux) < 0).all()


def test_flux_err_propagation():
    zp = get_band_info("ZTF_g").zp_flux_AB
    flux, flux_err = mag_to_flux(np.array([15.0]), zp, FLUX_UNIT, np.array([0.1]))
    assert flux_err[0] > 0
    mag, mag_err = flux_to_mag(flux, zp, FLUX_UNIT, flux_err)
    assert np.isclose(mag[0], 15.0)


def test_band_zero_point_raises_for_unknown_system():
    info = BandInfo(band="X", system="AB", zp_flux_AB=u.Quantity(1.0, FLUX_UNIT))
    with pytest.raises(ValueError):
        info.zero_point("Vega")


def test_subset_zero_point():
    info = get_band_info("ASASSN_V", system="Vega")
    assert info.zp_flux_vega is not None
    assert info.zero_point().unit == FLUX_UNIT
