import numpy as np
import pandas as pd
import astropy.units as u
from astropy.time import Time

from .lcmeta import LCMeta
from .phot_utils import mag_to_flux, flux_to_mag


class LightCurve:
    _default_unit_flux = u.erg / (u.cm**2 * u.s * u.AA)

    def __init__(self, data: pd.DataFrame, meta: LCMeta, time_format="mjd"):
        self.meta = meta
        self._time_format = time_format
        self._validate(data)
        self._data = data.sort_values("time").reset_index(drop=True)

    @property
    def _astropy_format(self):
        return "jd" if self._time_format == "jd" else "mjd"

    def _validate(self, data):
        cols = data.columns
        if "time" not in cols:
            raise ValueError("Data must contain a 'time' column.")
        if "mag" not in cols and "flux" not in cols:
            raise ValueError("Data must contain at least 'mag' or 'flux' column.")

    @property
    def time(self):
        return self._data["time"].values

    @property
    def time_obj(self):
        return Time(self._data["time"], format=self._astropy_format, scale="utc")

    @property
    def jd(self):
        return self.time_obj.jd

    @property
    def band(self):
        return self.meta.band.band

    @property
    def df(self):
        return self._data.copy()

    @property
    def mag(self):
        if "mag" in self._data:
            return self._data["mag"].values
        zp = self.meta.band.zero_point()
        return flux_to_mag(self._data["flux"].values, zp, self._default_unit_flux)

    @property
    def mag_err(self):
        if "mag_err" in self._data:
            return self._data["mag_err"].values
        if "flux_err" not in self._data:
            raise ValueError("No uncertainty available (mag_err or flux_err).")
        zp = self.meta.band.zero_point()
        _, err = flux_to_mag(
            self._data["flux"].values,
            zp,
            self._default_unit_flux,
            self._data["flux_err"].values,
        )
        return err

    @property
    def flux(self):
        if "flux" in self._data:
            return self._data["flux"].values
        zp = self.meta.band.zero_point()
        return mag_to_flux(self._data["mag"].values, zp, self._default_unit_flux)

    @property
    def flux_err(self):
        if "flux_err" in self._data:
            return self._data["flux_err"].values
        if "mag_err" not in self._data:
            raise ValueError("No uncertainty available (flux_err or mag_err).")
        zp = self.meta.band.zero_point()
        _, err = mag_to_flux(
            self._data["mag"].values,
            zp,
            self._default_unit_flux,
            self._data["mag_err"].values,
        )
        return err

    def _hjd(self, kind: str, location=None):
        if self.meta.target.coord is None:
            raise ValueError("Target coordinate required for time correction.")
        loc = location or self.meta.facility.location
        times = self.time_obj
        ltt = times.light_travel_time(self.meta.target.coord, kind, location=loc)
        return (times + ltt).jd

    def to_hjd(self, location=None):
        return self._hjd("heliocentric", location)

    def to_bjd(self, location=None):
        return self._hjd("barycentric", location)

    def _replace_time(self, values, fmt="jd"):
        self._data = self._data.copy()
        self._data["time"] = np.asarray(values)
        self._data = self._data.sort_values("time").reset_index(drop=True)
        self._time_format = fmt

    def copy(self):
        return LightCurve(self._data.copy(), self.meta, self._time_format)

    def apply_mask(self, mask):
        mask = np.asarray(mask, dtype=bool)
        return LightCurve(self._data[mask].reset_index(drop=True), self.meta)

    def binning(self, binsize=1.0):
        col = "mag" if "mag" in self._data else "flux"
        value = self._data[col].values
        time = self._data["time"].values
        err_col = f"{col}_err"
        err = self._data.get(err_col)
        bins = np.arange(time.min() - binsize / 2, time.max() + binsize / 2, binsize)
        idx = np.digitize(time, bins)
        binned_time, binned_val, binned_err = [], [], []
        for g in np.unique(idx):
            sel = idx == g
            w = None
            if err is not None:
                w = 1.0 / err.values[sel] ** 2
            v = np.average(value[sel], weights=w) if w is not None else value[sel].mean()
            binned_time.append(time[sel].mean())
            binned_val.append(v)
            if err is not None:
                binned_err.append(np.sqrt(1.0 / np.sum(w)))
            else:
                err_col = f"{col}_err"
                binned_err.append(err.values[sel].mean() if err is not None else np.nan)
        out = pd.DataFrame({"time": np.asarray(binned_time), col: np.asarray(binned_val)})
        if binned_err and not all(np.isnan(binned_err)):
            out[err_col] = np.asarray(binned_err)
        return LightCurve(out, self.meta)

    def fold(self, period, t0=0.0):
        from .analysis.folding import fold

        return fold(self, period, t0)

    def periodogram(self, min_period=1.0, max_period=100.0, method="lombscargle"):
        from .analysis.period import periodogram

        return periodogram(self, min_period, max_period, method)

    def find_period(self, min_period=1.0, max_period=100.0, method="lombscargle"):
        from .analysis.period import find_period

        return find_period(self, min_period, max_period, method)

    def plot(self, ax=None, system="mag", **kwargs):
        import matplotlib.pyplot as plt

        if ax is None:
            fig, ax = plt.subplots()
        if system == "mag":
            y = self.mag
            yerr = self.mag_err if "mag_err" in self._data else None
            ax.invert_yaxis()
            ylabel = f"{self.meta.band.band} magnitude"
        else:
            y = self.flux
            yerr = self.flux_err if "flux_err" in self._data else None
            ylabel = f"{self.meta.band.band} flux"
        ax.errorbar(self.time, y, yerr=yerr, fmt="o", **kwargs)
        ax.set_xlabel("Time (MJD)")
        ax.set_ylabel(ylabel)
        return ax

    def to_pandas(self):
        return self.df

    def save(self, path, **kwargs):
        from .io import save_lc

        save_lc(self, path, **kwargs)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return (
            f"<LightCurve: {self.meta.target.name} "
            f"({self.meta.facility.survey}/{self.meta.band.band}), "
            f"N={len(self)}>"
        )
