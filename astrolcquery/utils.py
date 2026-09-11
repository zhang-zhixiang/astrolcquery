from typing import Union, Tuple, Optional

import astropy.units as u
from astropy.coordinates import EarthLocation, SkyCoord

_SURVEY_TO_SITE = {
    "ZTF": "Palomar",
    "CATALINA": "Mt. Lemmon Survey",
    "ASASSN": "Cerro Tololo",
    "SYNTHETIC": "Cerro Tololo",
}

_SPACE_SURVEYS = {"TESS", "WISE", "JWST", "SWIFT", "SDSS", "SYNTHETIC"}

_ASASSN_SITE_MAP = {
    "ct": "Cerro Tololo",
    "cl": "Cerro Tololo",
    "sa": "Sutherland",
    "hi": "Haleakala",
    "tx": "McDonald Observatory",
    "wa": "Siding Spring Observatory",
    "cn": "Teide Observatory",
}


def get_asassn_site_location(site_code: str) -> EarthLocation:
    code = site_code.lower().strip()
    full = _ASASSN_SITE_MAP.get(code)
    if full is None:
        raise ValueError(
            f"Unknown ASAS-SN site code '{site_code}'. "
            f"Valid codes: {sorted(_ASASSN_SITE_MAP)}"
        )
    return EarthLocation.of_site(full)


def _resolve_location(survey: str, site_name: Optional[str]) -> EarthLocation:
    name = survey.upper().replace("-", "").replace(" ", "")
    if name in _SPACE_SURVEYS:
        return EarthLocation.from_geocentric(0, 0, 0, unit="m")
    if name == "ASASSN":
        if site_name:
            return get_asassn_site_location(site_name)
        return EarthLocation.of_site("Cerro Tololo")
    if name in _SURVEY_TO_SITE:
        return EarthLocation.of_site(_SURVEY_TO_SITE[name])
    if site_name:
        return EarthLocation.of_site(site_name)
    raise ValueError(
        f"Cannot determine location for survey '{survey}'. Provide a site_name."
    )


_LOCATION_CACHE = {}


def get_location(survey: str, site_name: Optional[str] = None) -> EarthLocation:
    key = f"{survey}|{site_name}"
    if key not in _LOCATION_CACHE:
        _LOCATION_CACHE[key] = _resolve_location(survey, site_name)
    return _LOCATION_CACHE[key]


def parse_coord(target, unit=(u.deg, u.deg)) -> SkyCoord:
    if isinstance(target, SkyCoord):
        return target
    if isinstance(target, (list, tuple)):
        if len(target) != 2:
            raise ValueError("Coordinates must be (ra, dec).")
        return SkyCoord(target[0], target[1], unit=unit)
    if isinstance(target, str):
        pieces = [p for p in target.replace(",", " ").split() if p]
        if len(pieces) == 2:
            return SkyCoord(pieces[0], pieces[1], unit=unit)
        return SkyCoord(target)
    raise ValueError(f"Cannot parse coordinate from {target!r}.")
