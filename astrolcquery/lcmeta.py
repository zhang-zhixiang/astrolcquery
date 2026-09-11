from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Literal, get_args

from astropy.coordinates import SkyCoord, EarthLocation

from .utils import get_location
from .phot_utils import BandInfo

SURVEY_LITERAL = Literal["ZTF", "ASAS-SN", "Catalina", "TESS", "WISE", "synthetic"]


@dataclass
class TargetInfo:
    name: str
    coord: Optional[SkyCoord] = None
    redshift: Optional[float] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FacilityInfo:
    survey: SURVEY_LITERAL
    telescope: Optional[str] = None
    site_name: Optional[str] = None
    _location_cache: Optional[EarthLocation] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        valid_surveys = get_args(SURVEY_LITERAL)
        lookup = {s.upper(): s for s in valid_surveys}
        cleaned = str(self.survey).upper().replace(" ", "").replace("-", "")
        self.survey = next(
            (v for k, v in lookup.items() if k.replace("-", "") == cleaned),
            None,
        )
        if self.survey is None:
            raise ValueError(
                f"Invalid survey '{self.survey}'. Valid options: {', '.join(valid_surveys)}"
            )

    @property
    def location(self) -> EarthLocation:
        if self._location_cache is None:
            self._location_cache = get_location(self.survey, self.site_name)
        return self._location_cache


class LCMeta:
    def __init__(self, target: TargetInfo, facility: FacilityInfo, band: BandInfo):
        self.target = target
        self.facility = facility
        self.band = band

    def __repr__(self):
        band = self.band.band
        return (
            f"<LCMeta: {self.target.name}@{self.facility.survey}"
            f"({band}/{self.band.system})>"
        )
