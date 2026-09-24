from pathlib import Path
from threading import RLock

import orjson


_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_ALLOWED_FILES = {"reviews.json", "reminders.json"}
_LOCK = RLock()


class JsonStoreError(RuntimeError):
    pass


def _path_for(name):
    if name not in _ALLOWED_FILES:
        raise JsonStoreError("Недопустимое имя хранилища")
    return _DATA_DIR / name


def read_list(name):
    path = _path_for(name)
    with _LOCK:
        if not path.exists():
            return []
        try:
            data = orjson.loads(path.read_bytes())
        except (OSError, orjson.JSONDecodeError) as error:
            raise JsonStoreError(f"Не удалось прочитать {name}") from error
        if not isinstance(data, list):
            raise JsonStoreError(f"Хранилище {name} должно содержать список")
        return data


def write_list(name, items):
    if not isinstance(items, list):
        raise JsonStoreError("Хранилище принимает только список")
    path = _path_for(name)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    payload = orjson.dumps(items, option=orjson.OPT_INDENT_2 | orjson.OPT_APPEND_NEWLINE)
    with _LOCK:
        try:
            temporary_path.write_bytes(payload)
            temporary_path.replace(path)
        except OSError as error:
            raise JsonStoreError(f"Не удалось записать {name}") from error
