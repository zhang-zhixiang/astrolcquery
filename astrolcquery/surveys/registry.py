from .synthetic import SyntheticSurvey

SURVEY_CLASSES = {
    "ZTF": "astrolcquery.surveys.ztf:ZTFSurvey",
    "ASAS-SN": "astrolcquery.surveys.asassn:ASASNNSurvey",
    "Catalina": "astrolcquery.surveys.catalina:CatalinaSurvey",
    "TESS": "astrolcquery.surveys.tess:TESSSurvey",
    "WISE": "astrolcquery.surveys.wise:WISESurvey",
    "synthetic": SyntheticSurvey,
}


def _import_path(path):
    module, _, cls_name = path.partition(":")
    import importlib

    return getattr(importlib.import_module(module), cls_name)


def _normalize(name: str) -> str:
    cleaned = name.strip().replace("-", "").replace(" ", "").upper()
    for key in SURVEY_CLASSES:
        if key.replace("-", "").replace(" ", "").upper() == cleaned:
            return key
    return cleaned


def get_survey(name: str, **kwargs):
    key = _normalize(name)
    entry = SURVEY_CLASSES.get(key)
    if entry is None:
        raise KeyError(
            f"Unknown survey '{name}'. Available: {sorted(SURVEY_CLASSES)}"
        )
    cls = _import_path(entry) if isinstance(entry, str) else entry
    return cls(**kwargs)
