from functools import lru_cache
from pathlib import Path

import orjson

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=None)
def load(name):
    with open(_DATA_DIR / name, "rb") as f:
        return orjson.loads(f.read())
