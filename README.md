# Система управління студентами

Навчальний вебзастосунок для обліку студентів, груп, дисциплін і оцінок.
Наскрізний проєкт дисципліни «Технології проєктування та розробки мережевих ресурсів».

## Автор

Міщук Владислав Михайлович, група КНІТ-53М

## Технології

- Python 3.13 або новіший, менеджер проєкту uv
- Django, Django REST Framework
- FastAPI
- Vue.js
- PostgreSQL (продакшен), SQLite (розробка), Docker, Docker Compose
suggestion
## Запуск

Потрібен менеджер проєктів [uv](https://docs.astral.sh/uv/).

```bash
uv sync                  # створити середовище і встановити залежності
uv run student-portal    # запустити консольний застосунок
```

Рівень журналювання керується змінною середовища `LOG_LEVEL` (за замовчуванням `WARNING`). Для перегляду діагностичних повідомлень (зокрема часу виконання операцій) запустіть із `LOG_LEVEL=INFO`:

```powershell
$env:LOG_LEVEL="INFO"; uv run student-portal
```

## Вебзастосунок Django

Проєкт містить вебзастосунок Django (`config/` та `students/`). Перед запуском створіть файл `.env` на основі `.env.example` і згенеруйте власний `DJANGO_SECRET_KEY`:

```powershell
Copy-Item .env.example .env
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

| Змінна середовища | Призначення / приклад значення | Значення за замовчуванням |
| :--- | :--- | :--- |
| `DJANGO_SECRET_KEY` | Секретний ключ Django (обов'язковий) | — (викидає `KeyError`) |
| `DJANGO_DEBUG` | Режим налагодження (`1` — увімкнено) | `"0"` (вимкнено) |
| `DJANGO_ALLOWED_HOSTS` | Дозволені хости через пробіл (`"127.0.0.1 localhost"`) | `""` (порожній список) |

Основні команди керування:

```bash
uv run --env-file .env python manage.py migrate                    # створити таблиці вбудованих застосунків і моделей
uv run --env-file .env python manage.py load_group data/group.json # завантажити групу з JSON у базу даних
uv run --env-file .env python manage.py runserver                  # запустити сервер розробки (http://127.0.0.1:8000/students/)
uv run --env-file .env python manage.py group_stats data/group.json # статистика групи з JSON-файлу
```

### Сторінки

| Адреса | Що показує | Представлення / маршрут |
| :--- | :--- | :--- |
| `/` | Перенаправлення (302) на список студентів | `RedirectView` (`home`) |
| `/students/` | Список студентів із пошуком (`?q=`) | `student_list` (FBV) |
| `/students/<id>/` | Картка студента з оцінками та шкалою ECTS | `student_detail` (FBV) |
| `/students/<id>.json` | Дані студента у форматі JSON | `student_json` (FBV) |
| `/students/ects/<letter>/` | Студенти із середнім балом за літерою ECTS | `by_ects` (FBV) |
| `/students/ranking/` | Рейтинг групи за середнім балом | `RankingView` (`TemplateView`) |
| `/students/ranking.json` | Рейтинг групи у форматі JSON | `ranking_json` (FBV) |
| `/students/pages/` | Рейтинг групи з пагінацією по 2 студенти | `StudentListView` (`ListView`) |
| `/students/stats/` | Статистика групи та розподіл ECTS | `stats` (FBV) |
| `/students/st/<id:4>/` | Перенаправлення (301) зі старої адреси на картку | `legacy_student` (FBV) |
| `/archive/2025/` | Архівний екземпляр застосунку (`archive-2025`) | `students.urls` (`include`) |

### Вхід, ролі і REST API

Увесь сайт закрито обов’язковим входом через `LoginRequiredMiddleware` (сторінка входу `/accounts/login/` відкрита, вихід `/accounts/logout/` приймає лише `POST`).

Для створення груп і призначення прав застосунку `students` виконайте:

```bash
uv run --env-file .env python manage.py setup_roles
```

| Роль (група) | Права (`students`) | Доступні дії |
| :--- | :--- | :--- |
| `Викладачі` | `view_student`, `view_grade`, `add_grade` | Перегляд студентів і оцінок, додавання оцінок (`/students/<id>/grades/new/`) |
| `Деканат` | `view_student`, `add_student`, `change_student`, `delete_student` | Перегляд, створення (`/students/new/`), зміна (`/students/<id>/edit/`) і видалення студентів |

REST API побудовано на Django REST Framework (`DjangoModelPermissions`, пагінація по 20 записів):

- `/api/students/` (`GET`, `POST`) та `/api/students/<id>/` (`GET`, `PUT`, `PATCH`, `DELETE`), підтримується фільтр `?last_name=<частина прізвища>`;
- `/api/grades/` (`GET`, `POST`) — створення та перегляд оцінок (зміна й видалення через API заборонені).

Приклад запиту до API з HTTP Basic автентифікацією:

```bash
curl -s -u teacher:<пароль> http://127.0.0.1:8000/api/students/
```

### База даних і адмінпанель

Усі сторінки вебзастосунку беруть дані з бази даних SQLite (`db.sqlite3`) через сервісний шар `students/services.py`, який перетворює ORM-записи (`Group`, `Student`, `Grade`) на об’єкти ядра `student_portal`. Якщо база порожня або недоступна, користувач отримує сторінку `503`.

1. **Завантаження даних у базу** (повторний запуск оновлює записи без дублювання):

   ```bash
   uv run --env-file .env python manage.py load_group data/group.json
   ```

2. **Створення адміністратора** для доступу до `/admin/`:

   ```bash
   uv run --env-file .env python manage.py createsuperuser
   ```

3. **Після зміни моделей** у `students/models.py` необхідно створити та застосувати міграцію:

   ```bash
   uv run --env-file .env python manage.py makemigrations students
   uv run --env-file .env python manage.py migrate
   ```

Збирання статичних файлів для розгортання:

```bash
uv run --env-file .env python manage.py collectstatic --noinput
```

## Журнал оцінок

Застосунок підтримує пакетний імпорт оцінок із CSV-файлу з роздільником `;` (крапка з комою, кодування `UTF-8` або `UTF-8 with BOM`). Заголовок файлу: `student_id;course;score;graded_on`.

Приклад рядка:

```csv
student_id;course;score;graded_on
1;Вебтехнології;91;2026-10-20
```

Імпорт працює за правилом **«все або нічого»**: якщо хоча б один рядок містить помилку формату, оцінку поза діапазоном `0–100` або неіснуючий `student_id`, жодна оцінка з журналу не зберігається в групі.

## Перевірки

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

## Тести

Модульні тести знаходяться у теці `tests/`. Вони використовують тимчасові директорії (`tmp_path`) і не змінюють файли в `data/`.

```bash
uv run --env-file .env pytest                  # запустити всі тести
uv run --env-file .env pytest -v               # докладний вивід кожного тесту
uv run --env-file .env pytest -k ranking       # запустити тести за фільтром назви
```

## Сервер деканату

Пункт меню `11` завантажує список групи у форматі `group.json` з сервера деканату. Адреса задається змінною середовища `DEKANAT_URL` (за замовчуванням `https://dekanat.example.edu/api/groups/kn-11`).

Для локальної перевірки можна роздати каталог `data/` вбудованим вебсервером Python:

```bash
uv run python -m http.server 8001 -d data
```

В іншому терміналі (PowerShell):

```powershell
$env:DEKANAT_URL="http://127.0.0.1:8001/group.json"; uv run student-portal
```

## Покриття і CI

Покриття коду (оператори та розгалуження, мінімальний поріг — `90 %`) перевіряється через `pytest-cov`:

```bash
uv run --env-file .env pytest --cov
uv run --env-file .env pytest --cov --cov-report=term-missing --cov-report=html
```

Конвеєр GitHub Actions (`.github/workflows/ci.yml`) автоматично запускається для кожного pull request та push у `main` і виконує два незалежні завдання:
- `checks` — `uv sync --locked`, `ruff check`, `ruff format --check`, `mypy src`, `manage.py check`, `manage.py makemigrations --check --dry-run`;
- `tests` — `uv sync --locked`, `pytest --cov --cov-report=term-missing --cov-report=html` із завантаженням артефакту `coverage-html`.

## Планування

Задачі та їхній статус ведуться на дошці GitHub Projects.

## Асинхронний API (FastAPI)

Окремий пакет `portal_api` на базі **FastAPI** надає асинхронний REST API з ключем доступу для інших систем університету (системи дистанційного навчання, яка передає оцінки за тести, та системи деканату, яка отримує рейтинг для стипендій).

- **База даних:** API працює з тим самим файлом `db.sqlite3`, що й сайт Django. Схемою бази даних володіють міграції Django, а моделі SQLAlchemy у `portal_api/orm.py` лише описують наявні таблиці (відповідність перевіряється тестом `test_orm_matches_django`).
- **Запуск у режимі розробки:**
  ```bash
  uv run fastapi dev portal_api/main.py --port 8001
  ```
- **Документація:** Swagger UI — `http://127.0.0.1:8001/docs`, ReDoc — `http://127.0.0.1:8001/redoc`, схема OpenAPI — `http://127.0.0.1:8001/openapi.json`.

### Змінні середовища (`PORTAL_*`)

| Змінна | За замовчуванням | Опис |
| :--- | :--- | :--- |
| `PORTAL_API_KEY` | *(обов'язкова, ≥ 16 символів)* | Ключ доступу, що передається у заголовку `X-API-Key` |
| `PORTAL_DATABASE_URL` | `sqlite+aiosqlite:///db.sqlite3` | Рядок підключення до бази даних для асинхронного SQLAlchemy |
| `PORTAL_ECHO_SQL` | `false` | Виведення SQL-запитів у журнал (`true`/`1` для налагодження) |

### Маршрути API

| Метод | Адреса | Дія |
| :--- | :--- | :--- |
| `GET` | `/students` | Список студентів з оцінками та середнім балом (пагінація `limit`, `offset`) |
| `GET` | `/students/{student_id}` | Картка студента з оцінками, літерами ECTS та середнім балом |
| `POST` | `/students/{student_id}/grades` | Додавання нової оцінки студенту з валідацією Pydantic |
| `PATCH` | `/grades/{grade_id}` | Часткове оновлення оцінки за ідентифікатором (варіант 3) |
| `GET` | `/ranking` | Рейтинг студентів за правилами ядра `Group.ranking()` (`limit`) |
