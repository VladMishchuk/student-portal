"""Django-частина: сторінка рейтингу, статистика, команда group_stats, налаштування."""

import pytest
from django.core.management import CommandError, call_command
from django.urls import reverse
from pytest_django.asserts import assertContains, assertTemplateUsed


def test_ranking_page_lists_best_student_first(client, db_group):
    response = client.get(reverse("students:ranking"))

    assertTemplateUsed(response, "students/ranking.html")
    assert response.context["group"].name == "КН-11"
    assertContains(response, "<li>Коваль Олена: 91,5</li>", html=True)


def test_ranking_page_shows_student_without_grades_last(client, db_group):
    response = client.get(reverse("students:ranking"))

    text = response.text
    assertContains(response, "<li>Бойко Ірина: немає оцінок</li>", html=True)
    assert (
        text.index("Коваль Олена")
        < text.index("Мельник Андрій")
        < text.index("Бойко Ірина")
    )


def test_unknown_url_returns_404(client):
    response = client.get("/students/unknown/")

    assert response.status_code == 404


def test_group_stats_prints_group_and_distribution(data_file, capsys):
    call_command("group_stats", str(data_file))

    out = capsys.readouterr().out
    assert "Група КН-11: 3 студентів" in out
    assert "A: 1" in out
    assert "E: 1" in out
    assert "Готово" in out


def test_group_stats_missing_file_raises_command_error(tmp_path):
    missing = tmp_path / "nope.json"

    with pytest.raises(CommandError, match="не знайдено"):
        call_command("group_stats", str(missing))


def test_django_settings(settings):
    assert settings.LANGUAGE_CODE == "uk"
    assert settings.TIME_ZONE == "Europe/Kyiv"
    assert "students" in settings.INSTALLED_APPS


def test_stats_page_shows_summary_and_ects_table(client, db_group):
    response = client.get(reverse("students:stats"))

    assert response.status_code == 200
    assertTemplateUsed(response, "students/stats.html")
    assertTemplateUsed(response, "base.html")
    assert response.context["student_count"] == 3
    assert response.context["group_average"] == pytest.approx((91.5 + 61.0) / 2)
    assert response.context["ects_distribution"] == [("A", 1), ("B", 1), ("E", 1)]
    assert "Кількість студентів: 3" in response.text
    assert "<tr><td>A</td><td>1</td></tr>" in response.text
