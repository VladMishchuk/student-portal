"""Маршрути, конвертери, перенаправлення та простори імен."""

import pytest
from django.urls import NoReverseMatch, resolve, reverse
from pytest_django.asserts import assertContains, assertNotContains

from students import views


def test_ects_route_resolves_letter():
    match = resolve("/students/ects/Fx/")
    assert match.func is views.by_ects
    assert match.kwargs == {"letter": "Fx"}


@pytest.mark.parametrize(
    "path",
    ["/students/ects/F/", "/students/ects/a/", "/students/st/3/"],
)
def test_invalid_routes_return_404(client, path):
    assert client.get(path).status_code == 404


def test_unknown_ects_letter_cannot_be_reversed():
    with pytest.raises(NoReverseMatch):
        reverse("students:by-ects", args=["F"])


def test_by_ects_page_filters_students(client, db_group):
    response_a = client.get(reverse("students:by-ects", args=["A"]))
    assert response_a.status_code == 200
    assertContains(response_a, "Коваль Олена")
    assertNotContains(response_a, "Мельник Андрій")

    response_fx = client.get(reverse("students:by-ects", args=["Fx"]))
    assert response_fx.status_code == 200
    assertContains(response_fx, "Таких студентів немає")


def test_legacy_url_redirects_permanently(client):
    response = client.get("/students/st/0003/")
    assert response.status_code == 301
    assert response["Location"] == reverse("students:detail", args=[3])


def test_home_redirects_to_student_list(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response["Location"] == reverse("students:list")


def test_student_detail_ects_link(client, db_group):
    melnyk = client.get(reverse("students:detail", args=[2]))
    assertContains(melnyk, 'href="/students/ects/E/"')

    boyko = client.get(reverse("students:detail", args=[3]))
    assertNotContains(boyko, "/students/ects/")


def test_archive_instance_namespace_links(client, db_group):
    response = client.get("/archive/2025/")
    assert response.status_code == 200
    assertContains(response, 'href="/archive/2025/1/"')
    assertContains(response, 'href="/archive/2025/ranking/"')
    assert reverse("students:list") == "/students/"
    assert reverse("archive-2025:list") == "/archive/2025/"
