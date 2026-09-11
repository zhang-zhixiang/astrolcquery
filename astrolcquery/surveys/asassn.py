import astropy.units as u
from astropy.coordinates import SkyCoord

from .base import SurveyBase, make_lc

_MJD_OFFSET = 2400000.5

_BAND_INFO = {
    "V": ("ASASSN_V", "Vega"),
    "g": ("ASASSN_g", "AB"),
    "BG": ("ASASSN_g", "AB"),
}


def standardize_asassn(df):
    df = df.copy()
    if "jd" in df.columns and "time" not in df.columns:
        df = df.rename(columns={"jd": "time"})
    if "time" in df.columns and df["time"].min() > _MJD_OFFSET:
        df["time"] = df["time"] - _MJD_OFFSET
    if "magerr" in df.columns and "mag_err" not in df.columns:
        df = df.rename(columns={"magerr": "mag_err"})
    return df.dropna(subset=["time", "mag"])


def _split_bands(df):
    groups = []
    if "phot_filter" in df.columns:
        for filt, sub in df.groupby("phot_filter"):
            band, system = _BAND_INFO.get(str(filt), _BAND_INFO["V"])
            groups.append((sub, band, system))
    else:
        groups.append((df, "ASASSN_V", "Vega"))
    return groups


class ASASNNSurvey(SurveyBase):
    name = "ASAS-SN"
    default_band = "ASASSN_V"
    band_system = "Vega"

    def query(self, coord: SkyCoord, radius: u.Quantity = 5 * u.arcsec, catalog="stellar_main", **kwargs):
        from pyasassn.client import SkyPatrolClient

        client = SkyPatrolClient(verbose=False)
        index = client.cone_search(
            coord.ra.deg,
            coord.dec.deg,
            float(radius.to_value(u.deg)),
            units="deg",
            catalog=catalog,
            download=False,
        )
        return {"client": client, "index": index}

    def parse(self, raw, coord=None, target_name="ASAS-SN-source", band=None, id_col="asas_sn_id", **kwargs):
        client = raw["client"]
        index = raw["index"]
        if index is None or len(index) == 0:
            return []
        if coord is not None and {"ra_deg", "dec_deg"}.issubset(index.columns):
            import numpy as np

            idx_ra = index["ra_deg"].values
            idx_dec = index["dec_deg"].values
            sep = np.sqrt(
                ((idx_ra - coord.ra.deg) * np.cos(np.deg2rad(coord.dec.deg))) ** 2
                + (idx_dec - coord.dec.deg) ** 2
            )
            row = index.iloc[int(np.argmin(sep))]
        else:
            row = index.iloc[0]
        target_id = row[id_col]
        collection = client.query_list([target_id], catalog="stellar_main", download=True)
        curve = collection[target_id]
        df = standardize_asassn(curve.data)
        b = band or self.default_band
        lcs = []
        for sub, bname, system in _split_bands(df):
            sub = sub.drop(columns=["phot_filter"], errors="ignore").reset_index(drop=True)
            lcs.append(make_lc(sub, target_name, coord, self.name, bname, system))
        return lcs if lcs else [make_lc(df, target_name, coord, self.name, b, self.band_system)]
