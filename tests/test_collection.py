import numpy as np
import pytest

from astrolcquery.collection import LightCurveCollection


def test_empty_allowed():
    col = LightCurveCollection([])
    assert len(col) == 0
    assert col.target_name == "unknown_target"


def test_len_and_iter(col):
    assert len(col) == 2
    assert sum(1 for _ in col) == 2


def test_align_time_jd(col):
    col.align_time("jd")
    all_jd = np.concatenate([lc.jd for lc in col])
    assert np.all(all_jd > 2400000)


def test_align_time_invalid(col):
    with pytest.raises(ValueError):
        col.align_time("nonsense")


def test_binning_subset(col):
    mapped = []
    for lc in col:
        lc.meta.facility.survey = "ZTF"
    col.lcs[1].meta.facility.survey = "WISE"
    col.binning(surveys=["WISE"], binsize=2.0)
    assert len(col.lcs[1]) < 200
    assert len(col.lcs[0]) == 200


def test_merge(col):
    merged = col.merge()
    assert "survey" in merged.columns
    assert len(merged) == len(col.lcs[0]) + len(col.lcs[1])


def test_plot_atlas(col):
    import matplotlib.pyplot as plt

    fig = col.plot_atlas(split_bands=True)
    assert fig is not None
    plt.close(fig)
