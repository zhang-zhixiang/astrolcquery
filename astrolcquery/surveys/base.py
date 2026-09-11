from abc import ABC, abstractmethod
from typing import Optional

import astropy.units as u
from astropy.coordinates import SkyCoord

from ..helper import FieldHelper


def make_lc(df, target_name, coord, survey, band, system="AB", time_format="mjd"):
    from ..lcmeta import TargetInfo, FacilityInfo, LCMeta
    from ..phot_utils import get_band_info
    from ..lightcurve import LightCurve

    target = TargetInfo(name=target_name, coord=coord)
    facility = FacilityInfo(survey=survey)
    bandinfo = get_band_info(band, system=system)
    return LightCurve(df, LCMeta(target, facility, bandinfo), time_format=time_format)


class SurveyBase(ABC):
    name: str = ""
    default_band: str = ""
    band_system: str = "AB"

    def __init__(self, cache_dir: Optional[str] = None, **kwargs):
        self.cache_dir = cache_dir

    @abstractmethod
    def query(self, coord: SkyCoord, radius: u.Quantity = 5 * u.arcsec, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def parse(self, raw, coord=None, **kwargs):
        raise NotImplementedError

    def download(self, coord: SkyCoord, radius: u.Quantity = 5 * u.arcsec, **kwargs):
        raw = self.query(coord, radius, **kwargs)
        return self.parse(raw, coord=coord)

    @property
    def field_docs(self):
        return FieldHelper.get_info(self.name)
