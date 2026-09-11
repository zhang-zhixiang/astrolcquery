from astrolcquery.helper import FieldHelper


def test_global_merged():
    info = FieldHelper.get_info("ZTF")
    assert "time" in info


def test_survey_specific_field():
    desc = FieldHelper.get_info("ZTF", "seeing")
    assert isinstance(desc, str)
    assert "FWHM" in desc


def test_missing_field_message():
    desc = FieldHelper.get_info("ZTF", "not_a_field")
    assert "not_a_field" in desc


def test_case_insensitive_survey():
    assert FieldHelper.get_info("ztf", "catflags") == FieldHelper.get_info("ZTF", "catflags")
