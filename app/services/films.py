from app.services.storage import load


def all_films():
    return load("films.json")


def get_film(film_id):
    for film in all_films():
        if film["id"] == film_id:
            return film
    return None
