"""Спільні фікстури тестів."""

import io
from collections.abc import Callable

import pytest
from django.contrib.auth.models import Group as AuthGroup
from django.core.management import call_command
from django.test import Client
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from portal_api import orm
from portal_api.main import create_app
from portal_api.settings import Settings
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student
from student_portal.storage import save_group
from students.services import store_group

API_KEY = "test-key-0123456789"

type StudentFactory = Callable[..., Student]


@pytest.fixture
def group() -> Group:
    """Група з трьох студентів: відмінниця, студент з оцінкою E і без оцінок."""
    group = Group("КН-11")
    group.add(Student(1, "Олена", "Коваль", [Grade("Python", 95), Grade("Git", 88)]))
    group.add(Student(2, "Андрій", "Мельник", [Grade("Python", 61)]))
    group.add(Student(3, "Ірина", "Бойко"))
    return group


@pytest.fixture
def data_file(tmp_path, settings, group):
    """Файл групи з трьох студентів замість data/group.json."""
    path = tmp_path / "group.json"
    save_group(group, path)
    settings.STUDENT_PORTAL_DATA = path
    return path


@pytest.fixture
def db_group(db, group):
    """Та сама група з трьох студентів, збережена в тестовій базі даних."""
    store_group(group)
    return group


@pytest.fixture
def make_student() -> StudentFactory:
    """Фабрика студентів з оцінками з Python і унікальними ідентифікаторами."""
    next_id = 100

    def make(last_name: str = "Тестовий", *scores: int) -> Student:
        nonlocal next_id
        next_id += 1
        grades = [Grade("Python", score) for score in scores]
        return Student(next_id, "Студент", last_name, grades)

    return make


@pytest.fixture
def answers(monkeypatch):
    """Підміняє input(): кожен виклик повертає наступну відповідь зі списку."""

    def set_answers(*values: str) -> None:
        replies = iter(values)
        monkeypatch.setattr("builtins.input", lambda prompt="": next(replies))

    return set_answers


@pytest.fixture
def client(client, django_user_model):
    """Тестовий клієнт Django від імені користувача, що увійшов (без особливих прав)."""
    user = django_user_model.objects.create_user("viewer", password="pass-12345")
    client.force_login(user)
    return client


@pytest.fixture
def anonymous():
    """Клієнт без входу: для перевірки LoginRequiredMiddleware."""
    return Client()


@pytest.fixture
def role_user(db, django_user_model):
    """Фабрика користувачів із роллю («Викладачі» або «Деканат»)."""
    call_command("setup_roles", stdout=io.StringIO())

    def make(username: str, role: str):
        user = django_user_model.objects.create_user(username, password="pass-12345")
        user.groups.add(AuthGroup.objects.get(name=role))
        return user

    return make


@pytest.fixture
def api_db(tmp_path, group):
    """Файл SQLite з таблицями, як у Django, і тією самою групою з трьох студентів."""
    path = tmp_path / "api.sqlite3"
    engine = create_engine(f"sqlite:///{path}")
    orm.Base.metadata.create_all(engine)
    with Session(engine) as session:
        record = orm.Group(name=group.name)
        session.add_all(
            orm.Student(
                id=s.id,
                group=record,
                first_name=s.first_name,
                last_name=s.last_name,
                grades=[
                    orm.Grade(course=g.course, score=g.score, graded_on=g.graded_on)
                    for g in s.grades
                ],
            )
            for s in group
        )
        session.commit()
    engine.dispose()
    return path


@pytest.fixture
def api(api_db):
    """Клієнт FastAPI з ключем API; with запускає і зупиняє застосунок (lifespan)."""
    settings = Settings(database_url=f"sqlite+aiosqlite:///{api_db}", api_key=API_KEY)
    with TestClient(create_app(settings), headers={"X-API-Key": API_KEY}) as client:
        yield client
