import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation
import astropy.units as u
from .lcmeta import LCMeta


class LightCurve:
    REQUIRED_COLUMNS = ['time', 'mag', 'mag_err', 'band']

    def __init__(self, data: pd.DataFrame, meta: LCMeta):
        self.data = data.sort_values(by='time').reset_index(drop=True)
        self.meta = meta
        self.validate()

    def validate(self):
        missing = set(self.REQUIRED_COLUMNS) - set(self.data.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    @property
    def time_obj(self):
        return Time(self.data['time'], format='mjd', scale='utc')

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

    def plot(self):
        plt.errorbar(self.data['time'], self.data['mag'], yerr=self.data['mag_err'], fmt='o')
        plt.gca().invert_yaxis()
        plt.xlabel('Time')
        plt.ylabel('Magnitude')
        plt.title('Light Curve')
        plt.show()