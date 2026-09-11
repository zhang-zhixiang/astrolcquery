from typing import Optional, Sequence

import numpy as np
import pandas as pd


class LightCurveCollection:
    def __init__(self, lcs: Sequence, target_name: Optional[str] = None):
        self.lcs = list(lcs)
        if self.lcs:
            self.target_name = target_name or self.lcs[0].meta.target.name
        else:
            self.target_name = target_name or "unknown_target"

    def __getitem__(self, index):
        return self.lcs[index]

    def __iter__(self):
        return iter(self.lcs)

    def __len__(self):
        return len(self.lcs)

    def add(self, lc):
        self.lcs.append(lc)
        return self

    def align_time(self, reference="jd"):
        for lc in self.lcs:
            if reference == "mjd":
                lc._replace_time(lc.jd - 2400000.5, "mjd")
            elif reference == "jd":
                lc._replace_time(lc.jd, "jd")
            elif reference == "hjd":
                lc._replace_time(lc.to_hjd(), "jd")
            elif reference == "bjd":
                lc._replace_time(lc.to_bjd(), "jd")
            else:
                raise ValueError(f"Unknown time reference '{reference}'.")
        return self

    def binning(self, surveys=None, binsize=1.0):
        surveys = None if surveys is None else set(surveys)
        self.lcs = [
            lc.binning(binsize)
            if surveys is None or lc.meta.facility.survey in surveys
            else lc
            for lc in self.lcs
        ]
        return self

    def merge(self):
        rows = []
        for lc in self.lcs:
            df = lc.df
            df = df.copy()
            df["survey"] = lc.meta.facility.survey
            df["band"] = lc.meta.band.band
            rows.append(df)
        return pd.concat(rows, ignore_index=True)

    def plot_atlas(self, split_bands=True, figsize=(10, 8), system="mag", ax=None):
        import matplotlib.pyplot as plt

        bands = sorted({lc.meta.band.band for lc in self.lcs})
        if not split_bands:
            if ax is None:
                fig, ax = plt.subplots(figsize=figsize)
            for lc in self.lcs:
                lc.plot(
                    ax=ax,
                    system=system,
                    label=f"{lc.meta.facility.survey}-{lc.meta.band.band}",
                )
            ax.set_title(f"Target: {self.target_name}")
            return ax.figure

        fig, axes = plt.subplots(len(bands), 1, figsize=figsize, sharex=True)
        axes = np.atleast_1d(axes)
        for i, band in enumerate(bands):
            sub = [lc for lc in self.lcs if lc.meta.band.band == band]
            for lc in sub:
                lc.plot(
                    ax=axes[i],
                    system=system,
                    label=f"{lc.meta.facility.survey}",
                )
            axes[i].set_ylabel(f"{band}")
            axes[i].legend(loc="best", fontsize="small")
        fig.suptitle(f"Multi-band Light Curves: {self.target_name}")
        fig.tight_layout()
        return fig

    def save(self, path, **kwargs):
        from .io import save_collection

        save_collection(self, path, **kwargs)

    def __repr__(self):
        n = len(self.lcs)
        bands = sorted({lc.meta.band.band for lc in self.lcs})
        return f"<LightCurveCollection: {self.target_name}, {n} curves, bands={bands}>"
