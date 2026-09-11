import pytest
import astropy.units as u

from astrolcquery.client import LCQueryClient


def test_get_lightcurve_synthetic(coord):
    client = LCQueryClient(surveys=["synthetic"])
    col = client.get_lightcurve(coord, radius=5 * u.arcsec)
    assert len(col) == 1
    assert col.lcs[0].meta.facility.survey == "synthetic"


def test_get_lightcurve_name(coord):
    client = LCQueryClient(surveys=["synthetic"])
    col = client.get_lightcurve(coord, target_name="my_target")
    assert col.target_name == "my_target"


def test_invalid_survey():
    with pytest.raises(KeyError):
        LCQueryClient(surveys=["NOTASURVEY"])


def test_get_list(coord):
    client = LCQueryClient(surveys=["synthetic"])
    result = client.get_list([coord, (150.1, 2.0)])
    assert len(result) == 2
