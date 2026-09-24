import re
import time
import unicodedata
from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

from flask import abort, jsonify, render_template, request, session

from app.services.films import all_films, get_film
from app.services.json_store import JsonStoreError, read_list, write_list
from app.services.sessions import get_schedule


_TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
_RATE_BUCKETS = defaultdict(deque)
_RATE_LOCK = Lock()


def _clean_text(value, minimum, maximum, multiline=False):
    if not isinstance(value, str):
        return None
    value = unicodedata.normalize("NFKC", value).replace("\r\n", "\n").replace("\r", "\n")
    if any(unicodedata.category(character).startswith("C") and character not in "\n\t" for character in value):
        return None
    if multiline:
        value = "\n".join(line.strip() for line in value.splitlines()).strip()
    else:
        value = " ".join(value.split())
    if not minimum <= len(value) <= maximum:
        return None
    return value


def _valid_name(value):
    return value is not None and all(character.isalnum() or character in " .'-" for character in value)


def _normalize_review_record(record):
    if not isinstance(record, dict):
        return None
    film_id = record.get("film_id")
    rating = record.get("rating")
    name = _clean_text(record.get("name"), 2, 40)
    text = _clean_text(record.get("text"), 10, 500, multiline=True)
    if type(film_id) is not int or type(rating) is not int or not 1 <= rating <= 5:
        return None
    if not _valid_name(name) or text is None:
        return None
    normalized = {"film_id": film_id, "name": name, "text": text, "rating": rating}
    if isinstance(record.get("id"), str):
        normalized["id"] = record["id"][:64]
    if isinstance(record.get("created_at"), str):
        normalized["created_at"] = record["created_at"][:64]
    return normalized


def _json_payload(allowed_keys):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not set(payload).issubset(allowed_keys):
        return None
    return payload


def _rate_limited(action, limit, window=60):
    key = (request.remote_addr or "unknown", action)
    now = time.monotonic()
    with _RATE_LOCK:
        bucket = _RATE_BUCKETS[key]
        while bucket and now - bucket[0] >= window:
            bucket.popleft()
        if len(bucket) >= limit:
            return True
        bucket.append(now)
    return False


def register_routes(app):
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Ресурс не найден"}), 404
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def request_too_large(error):
        return jsonify({"error": "Запрос слишком большой"}), 413

    @app.errorhandler(JsonStoreError)
    def storage_error(error):
        app.logger.exception("Ошибка JSON-хранилища")
        if request.path.startswith("/api/"):
            return jsonify({"error": "Ошибка хранилища данных"}), 500
        return render_template("500.html"), 500

    @app.errorhandler(500)
    def server_error(error):
        return render_template("500.html"), 500

    @app.route("/")
    def index():
        return render_template("index.html", films=all_films(), schedule=get_schedule())

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

    @app.route("/api/films/<int:film_id>/reviews", methods=["GET", "POST"])
    def film_reviews(film_id):
        if get_film(film_id) is None:
            abort(404)
        reviews = [
            normalized
            for item in read_list("reviews.json")
            if (normalized := _normalize_review_record(item)) is not None
        ]
        if request.method == "GET":
            film_reviews_list = [review for review in reviews if review.get("film_id") == film_id]
            return jsonify(film_reviews_list[-200:])

        if _rate_limited("review", limit=8):
            return jsonify({"error": "Слишком много отзывов. Попробуйте позже"}), 429
        payload = _json_payload({"name", "text", "rating"})
        if payload is None:
            return jsonify({"error": "Некорректная структура запроса"}), 400
        name = _clean_text(payload.get("name"), 2, 40)
        text = _clean_text(payload.get("text"), 10, 500, multiline=True)
        rating = payload.get("rating")
        if not _valid_name(name) or text is None or type(rating) is not int or not 1 <= rating <= 5:
            return jsonify({"error": "Проверьте имя, оценку и текст отзыва"}), 400
        if any(
            review.get("film_id") == film_id
            and review.get("name", "").casefold() == name.casefold()
            and review.get("text", "").casefold() == text.casefold()
            for review in reviews[-200:]
        ):
            return jsonify({"error": "Такой отзыв уже существует"}), 409

        review = {
            "id": uuid4().hex,
            "film_id": film_id,
            "name": name,
            "text": text,
            "rating": rating,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        reviews.append(review)
        write_list("reviews.json", reviews[-2000:])
        return jsonify(review), 201

    @app.route("/api/reminders", methods=["GET", "POST", "DELETE"])
    def reminders():
        owner_id = session.setdefault("client_id", uuid4().hex)
        all_reminders = [item for item in read_list("reminders.json") if isinstance(item, dict)]
        reminders_list = [item for item in all_reminders if item.get("owner_id") == owner_id]
        if request.method == "GET":
            return jsonify([{key: value for key, value in item.items() if key != "owner_id"} for item in reminders_list])
        if _rate_limited("reminder", limit=30):
            return jsonify({"error": "Слишком много запросов. Попробуйте позже"}), 429
        payload = _json_payload({"film_id", "time"})
        if payload is None:
            return jsonify({"error": "Некорректная структура запроса"}), 400
        film_id = payload.get("film_id")
        session_time = _clean_text(payload.get("time"), 5, 5)
        if type(film_id) is not int or not session_time or not _TIME_PATTERN.fullmatch(session_time):
            return jsonify({"error": "Некорректный фильм или время"}), 400
        session_row = next(
            (
                row
                for row in get_schedule()
                if row["film"]["id"] == film_id and row["time"] == session_time
            ),
            None,
        )
        if session_row is None:
            return jsonify({"error": "Такого сеанса нет в расписании"}), 404

        reminder_id = f"{film_id}:{session_time}"
        if request.method == "DELETE":
            updated = [
                item
                for item in all_reminders
                if not (item.get("owner_id") == owner_id and item.get("id") == reminder_id)
            ]
            if len(updated) == len(all_reminders):
                return jsonify({"error": "Напоминание не найдено"}), 404
            write_list("reminders.json", updated)
            return jsonify({"ok": True})

        reminder = {
            "id": reminder_id,
            "film_id": film_id,
            "title": session_row["film"]["title"],
            "time": session_time,
            "owner_id": owner_id,
        }
        if not any(item.get("id") == reminder_id for item in reminders_list):
            all_reminders.append(reminder)
            write_list("reminders.json", all_reminders)
        return jsonify({key: value for key, value in reminder.items() if key != "owner_id"}), 201
