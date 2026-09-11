import astropy.units as u
from astropy.coordinates import SkyCoord

from .base import SurveyBase, make_lc

VEGA_BAND = {"W1": "WISE_W1", "W2": "WISE_W2"}


def standardize_wise(df, band="W1"):
    df = df.copy()
    band = band.upper()
    mag_col = f"w{band[1]}mpro"
    if "mjd" in df.columns and mag_col in df.columns:
        err_col = f"w{band[1]}sigmpro"
        df = df[["mjd", mag_col, err_col]].rename(
            columns={"mjd": "time", mag_col: "mag", err_col: "mag_err"}
        )
    elif "time" in df.columns and mag_col in df.columns:
        err_col = f"w{band[1]}sigmpro"
        df = df[["time", mag_col, err_col]].rename(
            columns={mag_col: "mag", err_col: "mag_err"}
        )
    return df.dropna(subset=["time", "mag"])


class WISESurvey(SurveyBase):
    name = "WISE"
    default_band = "WISE_W1"
    band_system = "Vega"

    def query(self, coord: SkyCoord, radius: u.Quantity = 5 * u.arcsec, catalog="neowiser_p1bs_psd", **kwargs):
        from astroquery.ipac.irsa import Irsa

        return Irsa.query_region(coord, catalog=catalog, radius=radius)

    def parse(self, raw, coord=None, target_name="WISE-source", band=None, **kwargs):
        df_all = raw.to_pandas()
        wanted = [band] if band else ["W1", "W2"]
        wanted = [w.replace("WISE_", "").upper() for w in wanted]
        lcs = []
        for key in wanted:
            key = key.upper()
            if key not in VEGA_BAND:
                continue
            sub = standardize_wise(df_all, band=key)
            if sub.empty:
                continue
            lcs.append(make_lc(sub, target_name, coord, self.name, VEGA_BAND[key], self.band_system))
        return lcs
