import numpy as np
from astropy import units as u

from astrolcquery.io import save_lc, load_lc, save_collection, load_collection, Cache


def test_save_load_lc_pickle(small_lc, tmp_path):
    p = tmp_path / "lc.pkl"
    save_lc(small_lc, p)
    lc = load_lc(p)
    assert np.allclose(lc.time, small_lc.time)


def test_save_load_lc_csv(small_lc, tmp_path):
    p = tmp_path / "lc.csv"
    save_lc(small_lc, p)
    lc = load_lc(p)
    assert np.allclose(lc.mag, small_lc.mag)


def test_save_load_lc_parquet(small_lc, tmp_path):
    p = tmp_path / "lc.parquet"
    save_lc(small_lc, p)
    lc = load_lc(p)
    assert np.allclose(lc.mag, small_lc.mag)


def test_save_load_collection(col, tmp_path):
    d = tmp_path / "col"
    save_collection(col, d)
    loaded = load_collection(d)
    assert len(loaded) == len(col)
    assert loaded.target_name == col.target_name


def test_cache_roundtrip(small_lc, tmp_path):
    cache = Cache(tmp_path / "cache")
    cache.put("target", small_lc)
    assert "target" in cache
    loaded = cache.get("target")
    assert np.allclose(loaded.time, small_lc.time)
