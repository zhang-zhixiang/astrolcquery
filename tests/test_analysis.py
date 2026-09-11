import numpy as np

from astrolcquery.analysis import fold, find_period, periodogram, plot_folded


def test_find_period_recovers(coord):
    from astrolcquery.surveys.synthetic import SyntheticSurvey

    lc = SyntheticSurvey().generate(coord=coord, n=400, period=13.0, noise=0.02, seed=1)
    period = find_period(lc, 5.0, 30.0)
    assert abs(period - 13.0) < 0.2


def test_periodogram_shape(lc):
    freq, power = periodogram(lc, 2.0, 40.0)
    assert len(freq) == len(power)
    assert np.all(np.diff(freq) > 0)


def test_fold_phase_range(lc):
    folded = fold(lc, 12.0)
    assert "phase" in folded.columns
    assert folded["phase"].min() >= 0
    assert folded["phase"].max() < 1


def test_plot_folded(lc):
    import matplotlib.pyplot as plt

    ax = plot_folded(lc, 12.0)
    assert ax is not None
    plt.close(ax.figure)
