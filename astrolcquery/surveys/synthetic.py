from typing import Optional

import numpy as np
import pandas as pd
import astropy.units as u
from astropy.coordinates import SkyCoord

from .base import SurveyBase, make_lc


class SyntheticSurvey(SurveyBase):
    name = "synthetic"
    default_band = "ZTF_g"
    band_system = "AB"

    def generate(
        self,
        target_name="synthetic_target",
        coord=None,
        n=200,
        period=12.0,
        amplitude=0.4,
        seed=42,
        noise=0.05,
        t0=59000.0,
        **kwargs,
    ):
        rng = np.random.default_rng(seed)
        time = np.sort(rng.uniform(t0, t0 + 4 * period, n))
        mag = 17.0 + amplitude * np.sin(2 * np.pi * (time - t0) / period)
        mag += noise * rng.standard_normal(n)
        df = pd.DataFrame({"time": time, "mag": mag, "mag_err": noise})
        return make_lc(df, target_name, coord, self.name, self.default_band)

    def query(self, coord: SkyCoord, radius: u.Quantity = 5 * u.arcsec, **kwargs):
        return {"coord": coord, **kwargs}

    def parse(self, raw, coord=None, **kwargs):
        coord = coord or raw.get("coord")
        return [self.generate(coord=coord, **kwargs)]
