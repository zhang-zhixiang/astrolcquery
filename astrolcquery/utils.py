from astropy.coordinates import EarthLocation


def get_asassn_site_location(site_code: str):
    code = site_code.lower().strip()
    ASASSN_SITE_MAP = {
        "ct": "Cerro Tololo",          # 智利 (Chile)
        "cl": "Cerro Tololo",          # 智利常用别名
        "sa": "Sutherland",            # 南非 (South Africa)
        "hi": "Haleakala",             # 夏威夷 (Hawaii, Maui)
        "tx": "McDonald Observatory",  # 德克萨斯 (Texas)
        "wa": "Siding Spring Observatory", # 澳洲 (Western Australia/NSW)
        "cn": "Teide Observatory",     # 加那利群岛 (Canary Islands, Tenerife)
    }

    site_full_name = ASASSN_SITE_MAP.get(code)

    if not site_full_name:
        import warnings
        warnings.warn(f"Unknown ASASSN site code: {site_code}. Defaulting to Cerro Tololo.")
        code = "ct"  # Default to Cerro Tololo if unknown code is provided
        site_full_name = ASASSN_SITE_MAP[code]

    return EarthLocation.of_site(site_full_name)


def _actually_query_astropy(survey, site_name=None):
    name = survey.upper().replace("-", "")
    survey_to_site = {
        "ZTF": "Palomar",
        "CATALINA": "Mt. Lemmon Survey",
        "PANSTARRS": "Haleakala",
        "SDSS": "Apache Point",
    }

    if name in ["TESS", "WISE", "SWIFT", "JWST"]:
        return EarthLocation.from_geocentric(0, 0, 0, unit='m')
    
    if name == 'ASASSN':
        if site_name:
            try:
                return get_asassn_site_location(site_name)
            except Exception:
                pass
        return EarthLocation.of_site("Cerro Tololo")

    if name in survey_to_site:
        return EarthLocation.of_site(survey_to_site[name])

    raise ValueError(f"Unknown survey: {survey}. Please provide a valid survey name.")


_GLOBAL_SITE_CACHE = {}


def get_location(survey, site_name=None):
    key = f"{survey}_{site_name}"
    if key not in _GLOBAL_SITE_CACHE:
        _GLOBAL_SITE_CACHE[key] = _actually_query_astropy(survey, site_name)
    return _GLOBAL_SITE_CACHE[key]