"""Django-частина: сторінка рейтингу, статистика, команда group_stats, налаштування."""

import pytest
from django.core.management import CommandError, call_command
from django.urls import reverse

from student_portal.storage import save_group


@pytest.fixture
def data_file(tmp_path, settings, group):
    """Файл групи з трьох студентів замість data/group.json."""
    path = tmp_path / "group.json"
    save_group(group, path)
    settings.STUDENT_PORTAL_DATA = path
    return path


def test_ranking_page_lists_best_student_first(client, data_file):
    response = client.get(reverse("students:ranking"))

    assert response.status_code == 200
    assert [t.name for t in response.templates] == ["students/ranking.html"]
    assert response.context["group"].name == "КН-11"
    assert "<li>Коваль Олена: 91,5</li>" in response.text


def test_ranking_page_shows_student_without_grades_last(client, data_file):
    response = client.get(reverse("students:ranking"))

    text = response.text
    assert "<li>Бойко Ірина: немає оцінок</li>" in text
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


def test_stats_page_shows_summary_and_ects_table(client, data_file):
    response = client.get(reverse("students:stats"))

    assert response.status_code == 200
    assert [t.name for t in response.templates] == ["students/stats.html"]
    assert response.context["student_count"] == 3
    assert response.context["group_average"] == pytest.approx((91.5 + 61.0) / 2)
    assert response.context["ects_distribution"] == [("A", 1), ("B", 1), ("E", 1)]
    assert "Кількість студентів: 3" in response.text
    assert "<tr><td>A</td><td>1</td></tr>" in response.text
