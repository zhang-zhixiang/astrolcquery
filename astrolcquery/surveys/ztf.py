import io

import requests
import pandas as pd
import astropy.units as u
from astropy.coordinates import SkyCoord

from .base import SurveyBase, make_lc

LC_URL = "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves"

_BAND_TO_AB = {"g": "ZTF_g", "r": "ZTF_r", "i": "ZTF_i"}


def standardize_ztf(df):
    df = df.copy()
    df = df.rename(columns={"mjd": "time", "mag": "mag", "magerr": "mag_err"})
    df["band"] = df["filtercode"].str.replace("z", "", regex=False)
    return df.dropna(subset=["time", "mag"])


def _split_bands(df):
    groups = []
    for band, sub in df.groupby("band"):
        system = "AB"
        groups.append((sub, _BAND_TO_AB.get(str(band), f"ZTF_{band}"), system))
    return groups


class ZTFSurvey(SurveyBase):
    name = "ZTF"
    default_band = "ZTF_g"
    band_system = "AB"

    def __init__(self, cache_dir=None, collection=None, **kwargs):
        super().__init__(cache_dir=cache_dir, **kwargs)
        self.collection = collection

    def query(self, coord, radius=5 * u.arcsec, bands=None, **kwargs):
        radius_deg = float(radius.to_value(u.deg))
        if radius_deg > 0.1667:
            raise ValueError("ZTF lightcurve API radius is limited to 0.1667 deg.")
        bandname = ",".join(bands) if bands else "g,r,i"
        url = f"{LC_URL}?POS=CIRCLE {coord.ra.deg} {coord.dec.deg} {radius_deg}&BANDNAME={bandname}&FORMAT=csv"
        if self.collection:
            url += f"&COLLECTION={self.collection}"
        return url

    def parse(self, raw, coord=None, target_name="ZTF-source", **kwargs):
        url = raw if isinstance(raw, str) else str(raw)
        response = requests.get(url, timeout=180)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
        if df.empty:
            return []
        df = standardize_ztf(df)
        lcs = []
        for sub, band, system in _split_bands(df):
            sub = sub.drop(columns=["band"]).reset_index(drop=True)
            lcs.append(make_lc(sub, target_name, coord, self.name, band, system))
        return lcs
