import warnings
from typing import Optional, Sequence

import astropy.units as u

from .collection import LightCurveCollection
from .surveys import get_survey
from .utils import parse_coord


class LCQueryClient:
    def __init__(self, surveys=None, cache_dir=None):
        self.cache_dir = cache_dir
        self.survey_names = list(surveys) if surveys else self._default_surveys()
        self._cache = None
        if cache_dir is not None:
            from .io import Cache

            self._cache = Cache(cache_dir)
        self._handlers = {
            name: get_survey(name, cache_dir=cache_dir) for name in self.survey_names
        }

    @staticmethod
    def _default_surveys():
        return ["ZTF", "ASAS-SN", "TESS", "WISE"]

    def get_lightcurve(
        self,
        target,
        radius: u.Quantity = 5 * u.arcsec,
        surveys=None,
        target_name=None,
        use_cache: bool = True,
    ) -> LightCurveCollection:
        coord = parse_coord(target)
        names = list(surveys) if surveys else self.survey_names
        tc = target_name or str(target)
        lcs = []
        for name in names:
            handler = self._handlers.get(name) or get_survey(name, cache_dir=self.cache_dir)
            try:
                batch = handler.download(coord, radius)
            except Exception as exc:
                warnings.warn(f"[{handler.name}] skipped ({exc})")
                continue
            for lc in batch or []:
                lc.meta.target.name = tc
                if use_cache and self._cache is not None:
                    key = f"{handler.name}_{lc.band}_{coord.ra.deg:.5f}_{coord.dec.deg:.5f}"
                    self._cache.put(key, lc)
                lcs.append(lc)
        if not lcs:
            warnings.warn("No light curves were retrieved.")
        return LightCurveCollection(lcs, target_name=tc)

    def get_list(self, targets, radius: u.Quantity = 5 * u.arcsec, **kwargs):
        return {str(t): self.get_lightcurve(t, radius=radius, **kwargs) for t in targets}
