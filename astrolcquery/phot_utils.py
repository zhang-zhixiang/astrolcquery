from dataclasses import dataclass
from typing import Literal, Optional

from astropy import units as u
import numpy as np

System = Literal["AB", "Vega"]

_FLUX_UNIT = u.erg / (u.cm**2 * u.s * u.AA)
_AB_ZERO_FLUX = 3631.0 * u.Jy


def _ab_zp_flam(leff: float) -> u.Quantity:
    return _AB_ZERO_FLUX.to(_FLUX_UNIT, equivalencies=u.spectral_density(leff * u.AA))


_BAND_PARAMS = {
    "ZTF_g": (4810, 4200, 5400, 1400),
    "ZTF_r": (6230, 5480, 6980, 1500),
    "ZTF_i": (7510, 6720, 8300, 1580),
    "ASASSN_V": (5470, 4880, 6180, 1300),
    "ASASSN_g": (4810, 4200, 5400, 1400),
    "CSS_V": (5470, 4880, 6180, 1300),
    "TESS": (7865, 6000, 10000, 4000),
    "WISE_W1": (33526, 29400, 39500, 10100),
    "WISE_W2": (46028, 41000, 51000, 10000),
}

_VEGA_ZP_FLAM = {
    "ASASSN_V": 3.63e-9,
    "CSS_V": 3.63e-9,
    "TESS": 1.94e-23,
    "WISE_W1": 8.18e-12,
    "WISE_W2": 2.42e-12,
}


@dataclass(frozen=True)
class BandInfo:
    band: str
    system: System = "AB"
    leff: Optional[u.Quantity] = None
    lmin: Optional[u.Quantity] = None
    lmax: Optional[u.Quantity] = None
    width: Optional[u.Quantity] = None
    zp_flux_AB: Optional[u.Quantity] = None
    zp_flux_vega: Optional[u.Quantity] = None

    def zero_point(self, system: Optional[System] = None) -> u.Quantity:
        system = system or self.system
        if system == "AB":
            if self.zp_flux_AB is None:
                raise ValueError(f"No AB zero point available for band '{self.band}'.")
            return self.zp_flux_AB
        if self.zp_flux_vega is None:
            raise ValueError(f"No Vega zero point available for band '{self.band}'.")
        return self.zp_flux_vega


def get_band_info(band: str, system: System = "AB") -> BandInfo:
    if band not in _BAND_PARAMS:
        raise KeyError(
            f"Unknown band '{band}'. Available bands: {sorted(_BAND_PARAMS)}"
        )
    leff, lmin, lmax, width = _BAND_PARAMS[band]
    zp_ab = _ab_zp_flam(leff)
    zp_vega = (
        u.Quantity(_VEGA_ZP_FLAM[band], _FLUX_UNIT)
        if band in _VEGA_ZP_FLAM
        else None
    )
    return BandInfo(
        band=band,
        system=system,
        leff=u.Quantity(leff, u.AA),
        lmin=u.Quantity(lmin, u.AA),
        lmax=u.Quantity(lmax, u.AA),
        width=u.Quantity(width, u.AA),
        zp_flux_AB=zp_ab,
        zp_flux_vega=zp_vega,
    )


def mag_to_flux(mag, zp_flux: u.Quantity, given_unit, mag_err=None):
    zvalue = zp_flux.to_value(given_unit)
    mag = np.asarray(mag, dtype=float)
    flux = zvalue * 10 ** (-0.4 * mag)
    if mag_err is not None:
        flux_err = 0.4 * np.log(10) * flux * np.asarray(mag_err, dtype=float)
        return flux, flux_err
    return flux


def flux_to_mag(flux, zp_flux: u.Quantity, given_unit, flux_err=None):
    zvalue = zp_flux.to_value(given_unit)
    flux = np.asarray(flux, dtype=float)
    mag = -2.5 * np.log10(flux / zvalue)
    if flux_err is not None:
        mag_err = 2.5 / np.log(10) * np.asarray(flux_err, dtype=float) / flux
        return mag, mag_err
    return mag
