"""Тести моделі академічної групи."""

import inspect

import pytest

from student_portal.exceptions import (
    DuplicateStudentError,
    InvalidGradeError,
    StudentNotFoundError,
)
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student


def test_group_len_and_iter_preserve_order(group: Group) -> None:
    students = list(group)

    assert len(group) == 3
    assert [s.id for s in students] == [1, 2, 3]


def test_group_add_rejects_duplicate_id(group: Group) -> None:
    duplicate = Student(1, "Тест", "Дубль")

    with pytest.raises(DuplicateStudentError, match="id=1"):
        group.add(duplicate)

    assert len(group) == 3
    assert group.get(1).last_name == "Коваль"


def test_group_get_unknown_id_raises(group: Group) -> None:
    with pytest.raises(StudentNotFoundError, match="id=99"):
        group.get(99)


def test_group_remove_returns_student_and_deletes(group: Group) -> None:
    removed = group.remove(2)

    assert removed.last_name == "Мельник"
    assert len(group) == 2
    with pytest.raises(StudentNotFoundError, match="id=2"):
        group.get(2)


def test_group_remove_unknown_id_raises(group: Group) -> None:
    with pytest.raises(StudentNotFoundError, match="id=99"):
        group.remove(99)


@pytest.mark.parametrize(
    ("ids", "expected"),
    [
        pytest.param([], 1, id="empty"),
        pytest.param([1, 2, 3], 4, id="sequential"),
        pytest.param([1, 7], 8, id="with-gap"),
    ],
)
def test_group_next_id(ids: list[int], expected: int) -> None:
    grp = Group("КН-11")
    for student_id in ids:
        grp.add(Student(student_id, "Ім'я", "Прізвище"))

    assert grp.next_id() == expected


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        pytest.param("Коваль", ["Коваль"], id="exact"),
        pytest.param("коваль", ["Коваль"], id="lowercase"),
        pytest.param(" Мельник ", ["Мельник"], id="spaces"),
        pytest.param("ко", ["Коваль", "Бойко"], id="substring"),
        pytest.param("Шевчук", [], id="not-found"),
    ],
)
def test_find_by_last_name(group: Group, query: str, expected: list[str]) -> None:
    assert [s.last_name for s in group.find(query)] == expected


def test_ranking_puts_best_first_and_ungraded_last(make_student) -> None:
    grp = Group("КН-11")
    s_ungraded = make_student("Яковенко")
    s_low = make_student("Бондар", 70)
    s_tie_b = make_student("Савченко", 90)
    s_tie_a = make_student("Антоненко", 90)
    for student in (s_ungraded, s_low, s_tie_b, s_tie_a):
        grp.add(student)

    ranked = grp.ranking()

    assert [s.last_name for s in ranked] == [
        "Антоненко",
        "Савченко",
        "Бондар",
        "Яковенко",
    ]


def test_group_average_ignores_ungraded(group: Group) -> None:
    assert group.average() == pytest.approx((91.5 + 61) / 2)


def test_empty_group_average_is_none() -> None:
    grp = Group("Порожня")

    assert grp.average() is None


def test_iter_grades_returns_generator_and_pairs(group: Group) -> None:
    gen = group.iter_grades()

    assert inspect.isgenerator(gen)
    pairs = [(s.id, g.course, g.score) for s, g in gen]
    assert pairs == [
        (1, "Python", 95),
        (1, "Git", 88),
        (2, "Python", 61),
    ]


def test_group_courses_and_ects_distribution(group: Group) -> None:
    courses = group.courses()
    distribution = group.ects_distribution()

    assert courses == {"Python", "Git"}
    assert list(distribution.items()) == [("A", 1), ("B", 1), ("E", 1)]


def test_transaction_commits_changes_when_no_error(group: Group) -> None:
    with group.transaction():
        group.remove(2)
        group.get(3).add_grade(Grade("Python", 80))

    assert len(group) == 2
    assert group.get(3).average() == pytest.approx(80.0)


def test_transaction_restores_group_after_error(group: Group) -> None:
    before = [(s.id, s.average()) for s in group]

    with pytest.raises(InvalidGradeError), group.transaction():
        group.remove(2)
        group.get(3).add_grade(Grade("Python", 70))
        group.get(1).add_grade(Grade("Python", 105))

    assert [(s.id, s.average()) for s in group] == before
