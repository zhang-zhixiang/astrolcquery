from dataclasses import dataclass
from astropy import units as u
from pyphot.sandbox import get_library
import numpy as np


@dataclass(frozen=True)
class BandInfo:
    band: str
    leff: u.Quantity
    lmin: u.Quantity
    lmax: u.Quantity
    width: u.Quantity
    zp_flux_vega: u.Quantity
    zp_flux_AB: u.Quantity


def get_band_info(filter_name: str) -> BandInfo:
    lib = get_library()
    filt = lib[filter_name]
    return BandInfo(
        band=filter_name,
        leff=filt.leff,
        lmin=filt.lmin,
        lmax=filt.lmax,
        width=filt.width,
        zp_flux_vega=filt.Vega_zero_flux,
        zp_flux_AB=filt.AB_zero_flux
    )


def mag_to_flux(mag, zp_flux: u.Quantity, given_unit, mag_err=None):
    """
    Convert magnitude to flux using the zero point flux.
    """
    zvalue = zp_flux.to_value(given_unit)
    flux = zvalue * 10 ** (-0.4 * mag)
    if mag_err is not None:
        flux_err = flux * (10 ** (0.4 * mag_err) - 1)
        return flux, flux_err
    return flux


def flux_to_mag(flux, zp_flux: u.Quantity, given_unit, flux_err=None):
    """
    Convert flux to magnitude using the zero point flux.
    """
    zvalue = zp_flux.to_value(given_unit)
    mag = -2.5 * (flux / zvalue).log10()
    if flux_err is not None:
        mag_err = -2.5 * np.log10(1 - flux_err / flux)
        return mag, mag_err
    return mag