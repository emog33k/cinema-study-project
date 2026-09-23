from functools import lru_cache

from app.services.films import get_film
from app.services.storage import load


def all_sessions():
    return load("sessions.json")


@lru_cache(maxsize=1)
def get_schedule():
    rows = []
    for s in all_sessions():
        film = get_film(s["film_id"])
        if film is not None:
            rows.append({"time": s["time"], "film": film})
    rows.sort(key=lambda r: r["time"])
    return rows
