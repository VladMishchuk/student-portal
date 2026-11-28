"""Представлення і шаблони застосунку students."""

import pytest
from django.template.loader import render_to_string
from django.urls import reverse
from pytest_django.asserts import assertContains, assertNotContains, assertTemplateUsed

from student_portal.people import Student
from students.services import store_group
from students.templatetags.grades import ects


def test_student_list_shows_all_students_and_uses_templates(client, db_group):
    response = client.get(reverse("students:list"))

    assert response.status_code == 200
    assertTemplateUsed(response, "students/student_list.html")
    assertTemplateUsed(response, "base.html")
    assert [s.last_name for s in response.context["students"]] == [
        "Коваль",
        "Мельник",
        "Бойко",
    ]


def test_search_uses_query_string(client, db_group):
    response = client.get(reverse("students:list"), {"q": "кова"})

    assert [s.last_name for s in response.context["students"]] == ["Коваль"]
    assertContains(response, 'value="кова"')


def test_search_without_results_shows_empty_message(client, db_group):
    response = client.get(reverse("students:list"), {"q": "zzz"})

    assert response.context["students"] == []
    assertContains(response, "Нікого не знайдено за запитом «zzz»")


def test_student_detail_shows_grades_and_average(client, db_group):
    response = client.get(reverse("students:detail", args=[1]))

    assertContains(response, "<td>B</td>", html=True)
    assertContains(response, "Середній бал: 91,5 A")


def test_student_detail_without_grades(client, db_group):
    response = client.get(reverse("students:detail", args=[3]))

    assertContains(response, "Оцінок ще немає")
    assertContains(response, "Середній бал: -")


def test_unknown_student_is_404(client, db_group):
    assert client.get(reverse("students:detail", args=[42])).status_code == 404


def test_student_json_returns_expected_dict(client, db_group):
    response = client.get(reverse("students:detail-json", args=[1]))

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "full_name": "Коваль Олена",
        "average": 91.5,
    }


def test_ranking_uses_student_line_three_times(client, db_group):
    response = client.get(reverse("students:ranking"))

    assertTemplateUsed(response, "students/_student_line.html", count=3)
    assertContains(response, "Бойко Ірина: немає оцінок")


def test_ranking_post_returns_405(client, db_group):
    response = client.post(reverse("students:ranking"))

    assert response.status_code == 405


@pytest.mark.parametrize(("page", "first"), [(1, "Коваль"), (2, "Бойко")])
def test_ranking_pages(client, db_group, page, first):
    response = client.get(reverse("students:pages"), {"page": page})

    assert response.status_code == 200
    assert response.context["students"][0].last_name == first


def test_ranking_pages_out_of_range_is_404(client, db_group):
    response = client.get(reverse("students:pages"), {"page": 9})

    assert response.status_code == 404


@pytest.mark.parametrize(
    "url_name",
    ["students:list", "students:ranking", "students:pages"],
)
def test_pages_link_stylesheet(client, db_group, url_name):
    response = client.get(reverse(url_name))

    assertContains(response, 'href="/static/students/style.css"')


def test_student_row_partial_renders_alone(group):
    html = render_to_string(
        "students/student_list.html#student-row", {"student": group.get(3)}
    )

    assert '<a href="/students/3/">Бойко Ірина</a>' in html
    assert "<td>-</td>" in html


def test_names_are_escaped(client, db, group):
    group.add(Student(4, "Марко", "<script>alert(1)</script>"))
    store_group(group)

    response = client.get(reverse("students:list"))

    assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt; Марко")
    assertNotContains(response, "<script>")


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (95, "A"),
        (89.9, "B"),
        (60, "E"),
        (59.5, "Fx"),
        (None, ""),
    ],
)
def test_ects_filter(score, expected):
    assert ects(score) == expected


def test_ranking_json_returns_ordered_list(client, db_group):
    response = client.get(reverse("students:ranking-json"))

    assert response.status_code == 200
    data = response.json()
    assert data[0] == {"place": 1, "full_name": "Коваль Олена", "average": 91.5}
    assert data[-1] == {"place": 3, "full_name": "Бойко Ірина", "average": None}
    assert "Коваль Олена" in response.text
