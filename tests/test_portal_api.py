"""Тести асинхронного API на FastAPI (portal_api)."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from portal_api import orm
from portal_api.main import create_app
from portal_api.settings import Settings
from students import models


@pytest.mark.parametrize(
    ("table", "model"),
    [
        (orm.Group, models.Group),
        (orm.Student, models.Student),
        (orm.Grade, models.Grade),
    ],
)
def test_orm_matches_django(table, model):
    """Схемою володіють міграції Django; моделі SQLAlchemy мають їй відповідати."""
    assert table.__tablename__ == model._meta.db_table
    columns = {column.name for column in table.__table__.columns}
    assert columns == {field.column for field in model._meta.concrete_fields}


def test_auth_required_and_invalid_key(api):
    """Без ключа або з неправильним ключем API повертає 401."""
    bad_response = api.get("/students", headers={"X-API-Key": "wrong-key"})
    assert bad_response.status_code == 401

    api.headers.pop("X-API-Key")
    no_key_response = api.get("/students")
    assert no_key_response.status_code == 401


def test_docs_and_openapi_public(api):
    """/docs та /openapi.json доступні без ключа і містять схему безпеки."""
    api.headers.pop("X-API-Key")
    assert api.get("/docs").status_code == 200

    openapi_resp = api.get("/openapi.json")
    assert openapi_resp.status_code == 200
    schema = openapi_resp.json()
    assert {
        "/students",
        "/students/{student_id}",
        "/students/{student_id}/grades",
        "/ranking",
    }.issubset(schema["paths"].keys())
    assert schema["components"]["securitySchemes"]["APIKeyHeader"] == {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "Ключ з PORTAL_API_KEY",
    }


def test_list_students_and_student_detail(api):
    """Список студентів і картка студента містять оцінки, ECTS та середній бал."""
    response = api.get("/students")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    items = data["items"]
    assert [item["id"] for item in items] == [1, 2, 3]
    assert items[0]["average"] == 91.5
    assert [g["ects"] for g in items[0]["grades"]] == ["A", "B"]
    assert items[2]["average"] is None

    detail = api.get("/students/1")
    assert detail.status_code == 200
    assert detail.json()["last_name"] == "Коваль"


@pytest.mark.parametrize(
    ("query", "expected_ids"),
    [
        ("limit=2", [1, 2]),
        ("limit=2&offset=2", [3]),
        ("offset=5", []),
    ],
)
def test_list_students_pagination(api, query, expected_ids):
    """Пагінація повертає потрібний зріз, а count залишається загальним."""
    response = api.get(f"/students?{query}")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    assert [item["id"] for item in data["items"]] == expected_ids


@pytest.mark.parametrize(
    "query",
    ["limit=0", "limit=101", "offset=-1", "limit=abc"],
)
def test_list_students_invalid_query(api, query):
    """Некоректні параметри запиту повертають 422 з loc=['query', ...]."""
    response = api.get(f"/students?{query}")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][0] == "query"


def test_student_invalid_path_param(api):
    """Нечисловий student_id повертає 422 з loc=['path', 'student_id']."""
    response = api.get("/students/abc")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "student_id"]


def test_student_not_found(api):
    """Неіснуючий студент повертає 404."""
    response = api.get("/students/99")
    assert response.status_code == 404
    assert response.json() == {"detail": "Студента з id=99 немає"}


def test_add_grade_success(api):
    """Додавання оцінки повертає 201, обчислює ECTS і оновлює середній бал."""
    response = api.post(
        "/students/2/grades",
        json={"course": " Git ", "score": 74, "graded_on": "2026-11-02"},
    )
    assert response.status_code == 201
    created = response.json()
    assert created["course"] == "Git"
    assert created["score"] == 74
    assert created["ects"] == "D"

    student = api.get("/students/2").json()
    assert student["average"] == 67.5


@pytest.mark.parametrize(
    ("payload", "error_loc"),
    [
        (
            {"course": "Git", "score": 101, "graded_on": "2026-11-02"},
            ["body", "score"],
        ),
        (
            {"course": "Git", "score": -1, "graded_on": "2026-11-02"},
            ["body", "score"],
        ),
        (
            {"course": "Git", "score": "abc", "graded_on": "2026-11-02"},
            ["body", "score"],
        ),
        (
            {"course": "   ", "score": 80, "graded_on": "2026-11-02"},
            ["body", "course"],
        ),
        (
            {"course": "x" * 101, "score": 80, "graded_on": "2026-11-02"},
            ["body", "course"],
        ),
        (
            {
                "course": "Git",
                "score": 80,
                "graded_on": (date.today() + timedelta(days=1)).isoformat(),
            },
            ["body", "graded_on"],
        ),
        (
            {"course": "Git", "score": 80, "graded_on": "20.11.2026"},
            ["body", "graded_on"],
        ),
    ],
)
def test_add_grade_validation_errors(api, payload, error_loc):
    """Помилки валідації повертають 422 і не додають оцінку в базу."""
    before = len(api.get("/students/2").json()["grades"])
    response = api.post("/students/2/grades", json=payload)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert len(detail) == 1
    assert detail[0]["loc"] == error_loc
    after = len(api.get("/students/2").json()["grades"])
    assert after == before


def test_add_grade_missing_fields_and_not_found(api):
    """Відсутні поля дають кілька помилок 422, а неіснуючий студент — 404."""
    missing = api.post("/students/2/grades", json={"course": "Git"})
    assert missing.status_code == 422
    assert len(missing.json()["detail"]) == 2

    not_found = api.post(
        "/students/99/grades",
        json={"course": "Git", "score": 74, "graded_on": "2026-11-02"},
    )
    assert not_found.status_code == 404


def test_ranking(api):
    """Рейтинг повертає місця, ПІБ та середні бали, а limit обмежує список."""
    response = api.get("/ranking")
    assert response.status_code == 200
    assert response.json() == [
        {"place": 1, "id": 1, "full_name": "Коваль Олена", "average": 91.5},
        {"place": 2, "id": 2, "full_name": "Мельник Андрій", "average": 61.0},
        {"place": 3, "id": 3, "full_name": "Бойко Ірина", "average": None},
    ]

    limited = api.get("/ranking?limit=1")
    assert limited.status_code == 200
    assert len(limited.json()) == 1


def test_settings_from_env_and_validation(monkeypatch, api_db):
    """Налаштування читаються зі змінних середовища; ключ приховано в repr."""
    monkeypatch.setenv("PORTAL_API_KEY", "secret-env-key-123456")
    monkeypatch.setenv("PORTAL_DATABASE_URL", f"sqlite+aiosqlite:///{api_db}")

    cfg = Settings(_env_file=None)
    assert "secret-env-key-123456" not in repr(cfg)

    with TestClient(create_app(), headers={"X-API-Key": "secret-env-key-123456"}) as c:
        assert c.get("/students").status_code == 200

    for bad_key in [None, "", "short"]:
        if bad_key is None:
            monkeypatch.delenv("PORTAL_API_KEY", raising=False)
        else:
            monkeypatch.setenv("PORTAL_API_KEY", bad_key)
        with pytest.raises(ValidationError):
            Settings(_env_file=None)


def test_patch_grade_partial_update_and_errors(api):
    """PATCH /grades/{grade_id}: часткова зміна балів не змінює дату; 422 і 404."""
    before = api.get("/students/1").json()["grades"][0]
    grade_id = before["id"]

    updated = api.patch(f"/grades/{grade_id}", json={"score": 74})
    assert updated.status_code == 200
    body = updated.json()
    assert body["score"] == 74
    assert body["ects"] == "D"
    assert body["course"] == before["course"]
    assert body["graded_on"] == before["graded_on"]

    invalid = api.patch(f"/grades/{grade_id}", json={"score": 101})
    assert invalid.status_code == 422
    assert invalid.json()["detail"][0]["loc"] == ["body", "score"]

    not_found = api.patch("/grades/999", json={"score": 80})
    assert not_found.status_code == 404
    assert not_found.json() == {"detail": "Оцінку з id=999 не знайдено"}
