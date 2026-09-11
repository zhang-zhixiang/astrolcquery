import astropy.units as u
from astropy.coordinates import SkyCoord

from .base import SurveyBase, make_lc

_BTJD_OFFSET = 2457000.0


def _to_mjd(times):
    times = times.astype(float)
    # lightkurve TESS time is labelled 'btjd' but the stored values are on the
    # Julian/Barycentric date scale (e.g. ~2458790). Normalize everything to MJD.
    if times.max() > 2400000.0:
        mjd = times - 2400000.5
    else:
        mjd = times + _BTJD_OFFSET - 2400000.5
    return mjd


def standardize_tess(lc, flux_column="flux"):
    df = lc.to_pandas().copy()
    if "time" not in df.columns:
        df = df.reset_index()
    if "time" in df.columns:
        df["time"] = _to_mjd(df["time"])
    if flux_column not in df.columns:
        aliases = ["sap_flux", "pdcsap_flux"]
        for alias in aliases:
            if alias in df.columns:
                flux_column = alias
                break
        df = df.rename(columns={flux_column: "flux", f"{flux_column}_err": "flux_err"})
    keep = ["time", "flux", "flux_err"]
    df = df[[c for c in keep if c in df.columns]]
    return df.dropna(subset=["time", "flux"])


class TESSSurvey(SurveyBase):
    name = "TESS"
    default_band = "TESS"
    band_system = "Vega"

    def query(self, coord: SkyCoord, radius: u.Quantity = 5 * u.arcsec, **kwargs):
        from lightkurve import search_lightcurve

        try:
            result = search_lightcurve(coord, radius=float(radius.to_value(u.deg)))
        except Exception:
            return None
        if len(result) == 0:
            return None
        return result[0].download()

    def parse(self, raw, coord=None, target_name="TESS-source", flux_column="flux", **kwargs):
        if raw is None:
            return []
        df = standardize_tess(raw, flux_column=flux_column)
        return [make_lc(df, target_name, coord, self.name, self.default_band, self.band_system)]
