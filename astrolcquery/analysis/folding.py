import numpy as np
import pandas as pd


def fold(lc, period, t0=0.0):
    period = float(period)
    t0 = float(t0)
    out = lc.df
    out["phase"] = ((lc.time - t0) / period) % 1.0
    return out


def plot_folded(lc, period, t0=0.0, ax=None, system="mag", **kwargs):
    import matplotlib.pyplot as plt

    folded = fold(lc, period, t0)
    if ax is None:
        fig, ax = plt.subplots()
    if system == "mag":
        y = lc.mag
        yerr = lc.mag_err if "mag_err" in lc.df else None
        ax.invert_yaxis()
        ylabel = f"{lc.meta.band.band} magnitude"
    else:
        y = lc.flux
        yerr = lc.flux_err if "flux_err" in lc.df else None
        ylabel = f"{lc.meta.band.band} flux"
    ax.errorbar(folded["phase"], y, yerr=yerr, fmt="o", **kwargs)
    ax.set_xlabel(f"Phase ({period:g} d)")
    ax.set_ylabel(ylabel)
    return ax
