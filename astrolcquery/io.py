import os
import pickle
from pathlib import Path
from typing import Dict

import pandas as pd


def _pyarrow_available() -> bool:
    try:
        import pyarrow  # noqa: F401
    except Exception:
        return False
    return True


def _meta_path(path: Path) -> Path:
    return Path(str(path) + ".meta.pkl")


def save_lc(lc, path):
    path = Path(path)
    payload = {"meta": lc.meta, "time_format": lc._time_format}
    ext = path.suffix.lower()
    if ext in (".pkl", ".pickle", ".lc"):
        with open(path, "wb") as f:
            pickle.dump({"data": lc.df, **payload}, f)
        return path
    df = lc.df
    if ext == ".parquet":
        df.to_parquet(path, index=False)
    else:
        df.to_csv(path, index=False)
    with open(_meta_path(path), "wb") as f:
        pickle.dump(payload, f)
    return path


def load_lc(path):
    from .lightcurve import LightCurve

    path = Path(path)
    ext = path.suffix.lower()
    if ext in (".pkl", ".pickle", ".lc"):
        with open(path, "rb") as f:
            data = pickle.load(f)
        return LightCurve(data["data"], data["meta"], data["time_format"])
    if ext == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)
    with open(_meta_path(path), "rb") as f:
        payload = pickle.load(f)
    return LightCurve(df, payload["meta"], payload["time_format"])


_COLLECTION_MANIFEST = "collection.pkl"


def save_collection(col, path):
    from .collection import LightCurveCollection

    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    ext = ".parquet" if _pyarrow_available() else ".csv"
    files = {}
    for i, lc in enumerate(col.lcs):
        name = f"{i:04d}{ext}"
        save_lc(lc, path / name)
        files[name] = _lc_id(lc)
    with open(path / _COLLECTION_MANIFEST, "wb") as f:
        pickle.dump({"target_name": col.target_name, "files": files}, f)
    return path


def _lc_id(lc) -> Dict:
    bands = getattr(lc.meta.band, "band", None)
    survey = getattr(lc.meta.facility, "survey", None)
    return {"survey": survey, "band": bands}


def load_collection(path):
    from .collection import LightCurveCollection

    path = Path(path)
    manifest = None
    if (path / _COLLECTION_MANIFEST).exists():
        with open(path / _COLLECTION_MANIFEST, "rb") as f:
            manifest = pickle.load(f)
    data_files = sorted(
        p
        for p in path.iterdir()
        if p.suffix.lower() in (".parquet", ".csv", ".pkl", ".pickle")
        and p.name != _COLLECTION_MANIFEST
        and not p.name.endswith(".meta.pkl")
    )
    lcs = [load_lc(p) for p in data_files]
    target = manifest.get("target_name") if manifest else None
    return LightCurveCollection(lcs, target_name=target)


class Cache:
    def __init__(self, root=None):
        self.root = Path(root or os.path.expanduser("~/.astrolcquery/cache"))
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        clean = key.strip("/")
        return self.root / f"{clean}.pkl"

    def has(self, key: str) -> bool:
        return self._path_for(key).exists()

    def get(self, key: str):
        return load_lc(self._path_for(key))

    def put(self, key: str, lc) -> Path:
        return save_lc(lc, self._path_for(key))

    def __contains__(self, key):
        return self.has(key)
