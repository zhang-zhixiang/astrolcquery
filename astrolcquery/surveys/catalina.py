import astropy.units as u
from astropy.coordinates import SkyCoord

from .base import SurveyBase, make_lc

_COLUMN_MAP = {
    "time": "time",
    "mag": "mag",
    "magerr": "mag_err",
    "mag_err": "mag_err",
    "filter": "band",
}


def standardize_catalina(df):
    df = df.copy()
    if "MJD" in df.columns:
        df = df.rename(columns={"MJD": "time"})
    return df.rename(columns=_COLUMN_MAP)


class CatalinaSurvey(SurveyBase):
    name = "Catalina"
    default_band = "CSS_V"
    band_system = "Vega"

    def query(self, coord: SkyCoord, radius: u.Quantity = 5 * u.arcsec, **kwargs):
        # CSS/CRTS photometry is distributed as per-object files (e.g.
        # nunuku.caltech.edu CSV), not as a region/catalog query. This adapter is
        # not available via a public no-auth API; see AGENTS.md.
        raise NotImplementedError(
            "Catalina/CRTS light curves have no public programmatic region query. "
            "The CRTS data is distributed per-object; provide a catalog ID/file."
        )

    def parse(self, raw, coord=None, target_name="Catalina-source", band=None, **kwargs):
        table = raw
        df = standardize_catalina(table.to_pandas())
        band = band or self.default_band
        return make_lc(df, target_name, coord, self.name, band, self.band_system)
