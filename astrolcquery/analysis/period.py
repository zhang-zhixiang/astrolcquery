import numpy as np


def _measurements(lc):
    df = lc.df
    if "mag" in df:
        y = lc.mag
        dy = lc.mag_err if "mag_err" in df else None
    elif "flux" in df:
        y = lc.flux
        dy = lc.flux_err if "flux_err" in df else None
    else:
        raise ValueError("Light curve has neither mag nor flux.")
    return lc.time, np.asarray(y, dtype=float), None if dy is None else np.asarray(dy, dtype=float)


def periodogram(lc, min_period=1.0, max_period=100.0, n=10000, method="lombscargle"):
    if method != "lombscargle":
        raise ValueError(f"Unsupported period search method '{method}'.")
    from astropy.timeseries import LombScargle

    t, y, dy = _measurements(lc)
    ls = LombScargle(t, y, dy)
    frequency = np.linspace(1.0 / max_period, 1.0 / min_period, n)
    power = ls.power(frequency)
    return frequency, power


def find_period(lc, min_period=1.0, max_period=100.0, method="lombscargle"):
    frequency, power = periodogram(lc, min_period, max_period, method=method)
    best_freq = frequency[np.argmax(power)]
    return 1.0 / best_freq
