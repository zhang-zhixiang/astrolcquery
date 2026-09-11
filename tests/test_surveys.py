import pandas as pd
import pytest

from astrolcquery.surveys import get_survey, SurveyBase
from astrolcquery.surveys.ztf import standardize_ztf
from astrolcquery.surveys.asassn import standardize_asassn
from astrolcquery.surveys.catalina import standardize_catalina
from astrolcquery.surveys.tess import standardize_tess


def test_get_survey_case_insensitive():
    assert get_survey("ztf").name == "ZTF"
    assert get_survey("asassn").name == "ASAS-SN"


def test_get_survey_all_available():
    for name in ["ZTF", "ASAS-SN", "Catalina", "TESS", "WISE", "synthetic"]:
        assert isinstance(get_survey(name), SurveyBase)


def test_get_survey_unknown():
    with pytest.raises(KeyError):
        get_survey("Hubble")


def test_ztf_standardize():
    raw = pd.DataFrame({"mjd": [59000], "mag": [17.0], "magerr": [0.1], "filtercode": ["zg"]})
    out = standardize_ztf(raw)
    assert "time" in out.columns
    assert "mag_err" in out.columns
    assert out["band"].iloc[0] == "g"  # canonical ZTF filtercode, mapped to ZTF_g later
    assert out["time"].iloc[0] == 59000


def test_asassn_standardize():
    raw = pd.DataFrame({"jd": [2459000], "mag": [17.0], "magerr": [0.1]})
    out = standardize_asassn(raw)
    assert "time" in out.columns
    assert "mag_err" in out.columns


def test_catalina_standardize():
    raw = pd.DataFrame({"MJD": [59000], "mag": [17.0], "magerr": [0.1], "filter": ["V"]})
    out = standardize_catalina(raw)
    assert "time" in out.columns


def test_tess_standardize_and_btjd_offset():
    class FakeLC:
        def __init__(self, df):
            self._df = df

        def to_pandas(self):
            return self._df

    raw = FakeLC(pd.DataFrame({"time": [1400.0], "pdcsap_flux": [1.0], "pdcsap_flux_err": [0.1]}))
    out = standardize_tess(raw)
    assert 50000 < out["time"].iloc[0] < 100000  # normalized to MJD
    assert set(["time", "flux", "flux_err"]).issubset(out.columns)


def test_tess_standardize_jd_scale():
    # lightkurve may hand back values already on the Julian date scale
    class FakeLC:
        def __init__(self, df):
            self._df = df

        def to_pandas(self):
            return self._df

    raw = FakeLC(pd.DataFrame({"time": [2458790.0], "flux": [1.0], "flux_err": [0.1]}))
    out = standardize_tess(raw)
    assert 50000 < out["time"].iloc[0] < 100000
