from flask import abort, render_template

from app.services.films import all_films, get_film
from app.services.sessions import get_schedule


def register_routes(app):
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/films")
    def films():
        return render_template("films.html", films=all_films())

    @app.route("/films/<int:film_id>")
    def film(film_id):
        movie = get_film(film_id)
        if movie is None:
            abort(404)
            
        return render_template("film.html", movie=movie)

    @app.route("/schedule")
    def schedule():
        return render_template("schedule.html", schedule=get_schedule())

    @app.route("/contacts")
    def contacts():
        return render_template("contacts.html")
