from dataclasses import dataclass, field
from astropy.coordinates import SkyCoord, EarthLocation
from typing import Optional, Dict, Any, Literal, get_args
from .utils import get_location
from .phot_utils import BandInfo


SURVEY_LITERAL = Literal["ZTF", "ASAS-SN", "Catalina", "TESS", "WISE"]


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
    _location_cache: Optional['EarthLocation'] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        valid_surveys = get_args(SURVEY_LITERAL)
        lookup = {s.upper(): s for s in valid_surveys}
        input_cleaned = str(self.survey).upper().replace(" ", "").replace("-", "")

        matched = None

        for k, v in lookup.items():
            if k.replace("-", "") == input_cleaned:
                matched = v
                break

        if not matched:
            raise ValueError(f"Invalid survey: {self.survey}. Valid options are: {', '.join(valid_surveys)}")

        self.survey = matched

    @property
    def location(self) -> EarthLocation:
        if self._location_cache is None:
            self._location_cache = get_location(self.survey, self.telescope)
        return self._location_cache


class LCMeta:
    def __init__(self, target: TargetInfo, facility: FacilityInfo, band: BandInfo):
        self.target = target
        self.facility = facility
        self.band = band

    def __repr__(self):
        return f"<LCMeta: {self.target.name}@{self.facility.survey}({self.band.band})>"