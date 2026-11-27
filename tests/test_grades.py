"""Тести шкали ECTS і класу Grade."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from student_portal.exceptions import InvalidGradeError
from student_portal.grades import Grade, ects_grade


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (100, "A"),
        (90, "A"),
        (89, "B"),
        (82, "B"),
        (81, "C"),
        (75, "C"),
        (74, "D"),
        (67, "D"),
        (66, "E"),
        (60, "E"),
        (59, "Fx"),
        (1, "Fx"),
        (0, "Fx"),
    ],
)
def test_ects_grade_boundaries(score: int, expected: str) -> None:
    assert ects_grade(score) == expected


@pytest.mark.parametrize(
    "score",
    [
        pytest.param(0, id="min"),
        pytest.param(100, id="max"),
    ],
)
def test_grade_accepts_boundary_scores(score: int) -> None:
    grade = Grade("Python", score)

    assert grade.score == score


@pytest.mark.parametrize(
    "score",
    [
        pytest.param(-1, id="below-min"),
        pytest.param(101, id="above-max"),
    ],
)
def test_grade_rejects_score_out_of_range(score: int) -> None:
    with pytest.raises(InvalidGradeError, match="від 0 до 100"):
        Grade("Python", score)


def test_grade_ects_property() -> None:
    grade = Grade("Python", 85)

    assert grade.ects == "B"


def test_grade_defaults_to_today() -> None:
    before = date.today()

    grade = Grade("Python", 85)
    after = date.today()

    assert before <= grade.graded_on <= after


def test_grade_is_immutable() -> None:
    grade = Grade("Python", 85)

    with pytest.raises(FrozenInstanceError):
        grade.score = 100  # type: ignore[misc]
