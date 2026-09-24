# Ранхигс-Кино

Сайт кинотеатра "Ранхигс-Кино". Включает в себя: главную страницу, афишу, страница фильма, расписание и контакты.


## Состав группы

- Портнягин Д.
- Кутузов Р.
- Загоруйко Б.

## Распределение страниц

- Кутузов Р. - Главная (`/`), Расписание (`/schedule`), Контакты (`/contacts`)
- Портнягин Д. - Афиша (`/films`), Фильм (`/films/<id>`)

## Технологии

![Python](https://img.shields.io/badge/Python-3-grey?logo=python&logoColor=white) ![Flask](https://img.shields.io/badge/Flask-grey?logo=flask&logoColor=white) ![Jinja2](https://img.shields.io/badge/Jinja2-grey?logo=jinja&logoColor=white) ![orjson](https://img.shields.io/badge/orjson-grey)

## Установка и запуск
```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py run.py
```

## Маршруты

- `/` - главная
- `/films` - афиша
- `/films/<id>` - страница фильма
- `/schedule` - расписание
- `/contacts` - контакты

# ToDo лист
- [ ] Мобильная адаптива
- [ ] Регистрация/Авторизация
- [ ] Поиск
- [ ] Отображение карточек плавающим скроллером на главной странице заместо изображения экземпля
- [ ] Переписать базу данных с JSON хранения фильмов и сессий на Sqlite3
- [ ] Заполнить пустоту сайта
- [ ] Добавить футер
- [ ] Добавить возможность сменить на темную тему
- [ ] Добавить поддержку других языков
- [ ] Добавить возможность ставить напоминание
- [ ] Отображение свободных мест на сеанс 

## Скриншоты

**Главная**

![Главная](.github/home.jpeg)

**Афиша**

![Афиша](.github/films.jpeg)

**Информация о фильме**

![Информация о фильме](.github/film_detail.jpeg)

**Расписание**

![Расписание](.github/schedule.jpeg)

**Контакты**

![Контакты](.github/contacts.jpeg)
