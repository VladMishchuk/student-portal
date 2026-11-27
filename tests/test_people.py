"""Тести моделей осіб: Person, Student, Teacher."""

import pytest

from student_portal.grades import Grade
from student_portal.people import Person, Student, Teacher


def test_person_is_abstract() -> None:
    with pytest.raises(TypeError):
        Person(1, "Олена", "Коваль")  # type: ignore[abstract]


def test_full_name_starts_with_last_name(make_student) -> None:
    student = make_student("Коваль")

    assert student.full_name == "Коваль Студент"


@pytest.mark.parametrize(
    ("person", "expected_role"),
    [
        pytest.param(Student(1, "Олена", "Коваль"), "студент", id="student"),
        pytest.param(Teacher(1, "Віталій", "Іванов"), "викладач", id="teacher"),
    ],
)
def test_person_str_contains_role(person: Person, expected_role: str) -> None:
    text = str(person)

    assert expected_role in text
    assert person.full_name in text


def test_student_without_grades_has_none_average(make_student) -> None:
    student = make_student("Бойко")

    assert student.average() is None


def test_student_average_calculation(make_student) -> None:
    student = make_student("Коваль", 95, 88)

    assert student.average() == pytest.approx(91.5)


def test_add_grade_updates_average(make_student) -> None:
    student = make_student("Мельник", 60)

    student.add_grade(Grade("Git", 80))

    assert student.average() == pytest.approx(70.0)


def test_grades_for_filters_by_course() -> None:
    student = Student(
        1,
        "Олена",
        "Коваль",
        [Grade("Python", 95), Grade("Git", 88), Grade("Python", 90)],
    )

    python_grades = student.grades_for("Python")

    assert [g.score for g in python_grades] == [95, 90]
