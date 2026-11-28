from datetime import timedelta

import pytest
from django.utils import timezone

from students.forms import GradeForm

pytestmark = pytest.mark.django_db


def test_grade_form_valid_and_strips_course():
    form = GradeForm(
        data={
            "course": "  Git  ",
            "score": 85,
            "graded_on": timezone.localdate().isoformat(),
        }
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["course"] == "Git"


@pytest.mark.parametrize(
    ("score", "expected_error"),
    [
        (101, "Переконайтеся, що це значення менше чи дорівнює 100."),
        (-1, "Переконайтеся, що це значення більше чи дорівнює 0."),
        ("abc", "Введіть ціле число."),
    ],
)
def test_grade_form_invalid_scores(score, expected_error):
    form = GradeForm(
        data={
            "course": "Git",
            "score": score,
            "graded_on": timezone.localdate().isoformat(),
        }
    )
    assert not form.is_valid()
    assert form.errors["score"] == [expected_error]


@pytest.mark.parametrize("score", [0, 100])
def test_grade_form_boundary_scores(score):
    form = GradeForm(
        data={
            "course": "Git",
            "score": score,
            "graded_on": timezone.localdate().isoformat(),
        }
    )
    assert form.is_valid(), form.errors


def test_grade_form_future_date_is_invalid():
    tomorrow = timezone.localdate() + timedelta(days=1)
    form = GradeForm(
        data={
            "course": "Git",
            "score": 80,
            "graded_on": tomorrow.isoformat(),
        }
    )
    assert not form.is_valid()
    assert form.errors["graded_on"] == ["Дата оцінки не може бути в майбутньому"]


def test_grade_form_required_fields():
    form = GradeForm(data={})
    assert not form.is_valid()
    assert set(form.errors) == {"course", "score", "graded_on"}
