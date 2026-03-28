# TeamFinder — Вариант 2 (Навыки пользователей)

Платформа для поиска единомышленников для совместной работы над pet-проектами.

## Вариант проекта

**Вариант 2** — навыки пользователей и фильтрация участников по навыкам.

На странице пользователя отображается блок «Навыки» со списком тегов. Владелец профиля может
добавлять и удалять навыки без перезагрузки страницы (AJAX), с автодополнением и возможностью
создания новых навыков. На странице списка пользователей (`/users/list/`) реализована фильтрация
по навыкам через GET-параметр `?skill=<Название>`.

## Запуск через Docker Compose

1. Скопируйте `.env_example` в `.env` и при необходимости отредактируйте параметры:

```bash
cp .env_example .env
```

2. Запустите проект:

```bash
docker compose up -d --build
```

При запуске автоматически выполняются миграции и сбор статики.

3. Создайте суперпользователя:

```bash
docker compose exec web python manage.py createsuperuser
```

4. Заполните базу тестовыми данными:

```bash
docker compose exec web python manage.py seed
```

Команда `seed` создаёт трёх пользователей (maria@yandex.ru, alex@yandex.ru, elena@yandex.ru,
пароль у всех: `password`), набор навыков и по одному проекту у каждого пользователя.

5. Приложение доступно по адресу: http://localhost:8000

## Локальный запуск (без Docker)

Требуется запущенный PostgreSQL. В `.env` укажите `POSTGRES_HOST=localhost` (в Docker используется `db`).

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py seed
python manage.py createsuperuser
python manage.py runserver
```

## Тестовый аккаунт

- Email: `maria@yandex.ru`
- Пароль: `password`

## Тесты

```bash
python manage.py test main
```

## Технологии

- Python 3.12, Django 5.2
- PostgreSQL 16
- Pillow (генерация аватаров)
- Docker, Docker Compose
