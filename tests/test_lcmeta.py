import pytest
from astropy.coordinates import SkyCoord
import astropy.units as u

from astrolcquery.lcmeta import TargetInfo, FacilityInfo, LCMeta
from astrolcquery.phot_utils import get_band_info


def test_facility_normalizes_survey_names():
    assert FacilityInfo(survey="ztf").survey == "ZTF"
    assert FacilityInfo(survey="ASASSN").survey == "ASAS-SN"
    assert FacilityInfo(survey="asas-sn").survey == "ASAS-SN"
    assert FacilityInfo(survey="TESS").survey == "TESS"


def test_facility_invalid_survey():
    with pytest.raises(ValueError):
        FacilityInfo(survey="Tycho")


def test_target_info_defaults():
    t = TargetInfo("target")
    assert t.coord is None
    assert t.extra_params == {}


def test_lcmeta_repr():
    target = TargetInfo("src", coord=SkyCoord(10, 20, unit=u.deg))
    facility = FacilityInfo("ZTF")
    band = get_band_info("ZTF_g", system="AB")
    meta = LCMeta(target, facility, band)
    assert "src" in repr(meta)
    assert "ZTF" in repr(meta)
