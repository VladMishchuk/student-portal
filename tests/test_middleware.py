"""Проміжні компоненти (middleware), Server-Timing, CSP та сторінка 503."""

from django.db import OperationalError
from django.http import HttpResponse
from django.test import RequestFactory, override_settings

from config.middleware import TimingMiddleware


def ok_view(request):
    return HttpResponse("ok")


def test_timing_header_is_added():
    response = TimingMiddleware(ok_view)(RequestFactory().get("/"))
    assert response["Server-Timing"].startswith("app;dur=")


@override_settings(SLOW_REQUEST_MS=-1)
def test_slow_request_is_logged(caplog):
    TimingMiddleware(ok_view)(RequestFactory().get("/students/"))
    assert "Повільний запит /students/" in caplog.text


def test_empty_database_shows_503_page(client, db):
    response = client.get("/students/")
    assert response.status_code == 503
    assert "Сервіс тимчасово недоступний" in response.text


def test_database_error_shows_503_page(client, monkeypatch):
    def broken():
        raise OperationalError("database is locked")

    monkeypatch.setattr("students.views.get_group", broken)
    response = client.get("/students/")
    assert response.status_code == 503
    assert "Сервіс тимчасово недоступний" in response.text


def test_csp_header_present(client, db_group):
    response = client.get("/students/")
    assert response.status_code == 200
    assert "default-src 'self'" in response["Content-Security-Policy"]
    assert "img-src 'self' data:" in response["Content-Security-Policy"]
