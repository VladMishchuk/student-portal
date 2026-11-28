"""Тести сторінки /app/ та ендпоінта /api/me/ для клієнта Vue."""

import pytest


def test_app_redirects_anonymous(anonymous):
    response = anonymous.get("/app/")
    assert response.status_code == 302
    assert response["Location"] == "/accounts/login/?next=/app/"


def test_app_renders_for_authenticated(client):
    response = client.get("/app/")
    assert response.status_code == 200
    body = response.content.decode()
    assert '<div id="app"></div>' in body
    assert 'src="/static/frontend/app.js"' in body
    assert "csrftoken" in response.cookies


def test_api_me_anonymous(anonymous):
    response = anonymous.get("/api/me/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_api_me_teacher(anonymous, role_user):
    teacher = role_user("teacher_vue", "Викладачі")
    anonymous.force_login(teacher)
    response = anonymous.get("/api/me/")
    assert response.status_code == 200
    assert response.json() == {
        "username": "teacher_vue",
        "permissions": ["add_grade", "view_grade", "view_student"],
    }
