import pytest
import astropy.units as u
from astropy.coordinates import SkyCoord

from astrolcquery.utils import parse_coord, get_location, get_asassn_site_location


def test_parse_coord_skycoord():
    c = SkyCoord(10, 20, unit=u.deg)
    assert parse_coord(c) is c


def test_parse_coord_tuple():
    c = parse_coord((10, 20))
    assert c.ra.deg == 10


def test_parse_coord_string():
    c = parse_coord("10 20")
    assert c.ra.deg == 10


def test_parse_coord_invalid():
    with pytest.raises(ValueError):
        parse_coord({})


def test_get_location_space_survey():
    loc = get_location("TESS")
    assert loc.x.value == 0


def test_get_location_ground_survey():
    loc = get_location("ZTF")
    assert loc.lat != 0


def test_asassn_site():
    loc = get_asassn_site_location("ct")
    assert loc.lat != 0


def test_asassn_unknown_site():
    with pytest.raises(ValueError):
        get_asassn_site_location("zz")
