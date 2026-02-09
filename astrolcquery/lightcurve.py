import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation
import astropy.units as u
from .lcmeta import LCMeta


class LightCurve:
    _default_unit_time = 'MJD'
    _default_unit_mag = 'VEGA'
    _default_unit_flux = u.erg / (u.cm**2 * u.s * u.AA)
    # REQUIRED_COLUMNS = ['time', 'mag', 'mag_err', 'band']

    def __init__(self, data: pd.DataFrame, meta: LCMeta):
        self._data = data.sort_values(by='time').reset_index(drop=True)
        self.meta = meta
        self._validate()

    def _validate(self):
        # missing = set(self.REQUIRED_COLUMNS) - set(self._data.columns)
        cols = self._data.columns
        if 'time' not in cols:
            raise ValueError("The 'time' column is required in the data.")
        if 'mag' not in cols and 'flux' not in cols:
            raise ValueError("Data must contain at least 'mag' or 'flux' column.")

    @property
    def time(self):
        return self._data['time'].values

    @property
    def time_obj(self):
        if hasattr(self, '_time_obj'):
            return self._time_obj
        self._time_obj = Time(self._data['time'], format=self._default_unit_time, scale='utc')
        return self._time_obj

    @property
    def jd(self):
        return self.time_obj.jd

    @property
    def hjd(self):
        location = self.meta.facility.location
        coord = self.meta.target.coord
        if location is None or coord is None:
            raise ValueError("Location and target coordinates must be set.")
        times = self.time_obj
        ltt_helio = times.light_travel_time(coord, 'heliocentric', location=location)
        hjd_time = times + ltt_helio
        return hjd_time.jd

    def _get_quantity(self, primary, secondary, convert):
        cols = self._data.columns

        if primary in cols:
            return self._data[primary].values
        elif secondary in cols:
            return convert(self._data[secondary].values)
        else:
            raise ValueError(
                f"Data must contain '{primary}' or '{secondary}' column."
            )

    @property
    def flux(self):
        return self._get_quantity('flux', 'mag', self._mag_to_flux)

    @property
    def flux_err(self):
        return self._get_quantity('flux_err', 'mag_err', self._mag_to_flux)

    @property
    def mag(self):
        return self._get_quantity('mag', 'flux', self._flux_to_mag)

    def plot(self):
        plt.errorbar(self._data['time'], self.mag, yerr=self._data['mag_err'], fmt='o')
        plt.gca().invert_yaxis()
        plt.xlabel('Time')
        plt.ylabel('Magnitude')
        plt.title('Light Curve')
        plt.show()