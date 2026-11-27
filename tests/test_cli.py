"""Тести консольного меню, декораторів та індивідуальних розширень (Timer)."""

import logging
from pathlib import Path

import pytest

from student_portal import cli
from student_portal.cli import command, run
from student_portal.decorators import Timer, timed
from student_portal.group import Group


@pytest.fixture
def answers(monkeypatch):
    """Підміняє input(): кожен виклик повертає наступну відповідь зі списку."""

    def set_answers(*values: str) -> None:
        replies = iter(values)
        monkeypatch.setattr("builtins.input", lambda prompt="": next(replies))

    return set_answers


def test_menu_adds_student(group: Group, answers, capsys) -> None:
    answers("4", "Марія", "Шевчук", "0")

    run(group)

    assert "Додано: Шевчук Марія (студент)" in capsys.readouterr().out
    assert group.get(4).full_name == "Шевчук Марія"


def test_menu_adds_grade(group: Group, answers, capsys) -> None:
    answers("5", "3", "Python", "74", "0")

    run(group)

    assert "Бойко Ірина: 74 (D)" in capsys.readouterr().out
    assert group.get(3).grades_for("Python")[0].score == 74


@pytest.mark.parametrize(
    ("inputs", "expected_message"),
    [
        pytest.param(
            ("5", "3", "Python", "сто", "0"),
            "Помилка введення",
            id="non-numeric-score",
        ),
        pytest.param(
            ("5", "3", "Python", "105", "0"),
            "Помилка введення",
            id="score-out-of-range",
        ),
        pytest.param(
            ("6", "42", "0"),
            "Помилка: студента з id=42 немає",
            id="unknown-student",
        ),
        pytest.param(
            ("99", "0"),
            "Невідома команда",
            id="unknown-command",
        ),
    ],
)
def test_menu_handles_invalid_input(
    group: Group,
    answers,
    capsys,
    inputs: tuple[str, ...],
    expected_message: str,
) -> None:
    answers(*inputs)

    run(group)

    assert expected_message in capsys.readouterr().out
    assert len(group) == 3


def test_menu_exports_ranking_csv(
    group: Group,
    answers,
    capsys,
    monkeypatch,
    tmp_path: Path,
) -> None:
    export_path = tmp_path / "ranking.csv"
    monkeypatch.setattr(cli, "RANKING_FILE", export_path)
    answers("8", "0")

    run(group)

    assert f"Рейтинг експортовано у {export_path}" in capsys.readouterr().out
    assert export_path.exists()


def test_command_rejects_duplicate_key(monkeypatch) -> None:
    monkeypatch.setattr(cli, "COMMANDS", {})

    @command("1", "перша")
    def first(group: Group) -> None:
        pass

    with pytest.raises(ValueError, match="уже зайнято"):

        @command("1", "друга")
        def second(group: Group) -> None:
            pass


def test_timed_logs_duration_and_keeps_name(caplog) -> None:
    @timed
    def add(a: int, b: int) -> int:
        return a + b

    with caplog.at_level(logging.INFO):
        assert add(2, 3) == 5

    assert add.__name__ == "add"
    assert "add: " in caplog.text
    assert caplog.text.rstrip().endswith("мс")


def test_timer_as_context_manager_records_elapsed_and_logs(caplog) -> None:
    with caplog.at_level(logging.INFO), Timer("експорт") as timer:
        total = sum(range(100))

    assert total == 4950
    assert timer.elapsed >= 0.0
    assert "експорт: " in caplog.text
    assert caplog.text.rstrip().endswith("мс")


@pytest.mark.parametrize(
    ("label", "expected_prefix"),
    [
        pytest.param("custom_op", "custom_op: ", id="named"),
        pytest.param("", "timer: ", id="default-empty"),
    ],
)
def test_timer_as_decorator_logs_label_and_keeps_name(
    caplog, label: str, expected_prefix: str
) -> None:
    @Timer(label)
    def multiply(a: int, b: int) -> int:
        return a * b

    with caplog.at_level(logging.INFO):
        assert multiply(3, 4) == 12

    assert multiply.__name__ == "multiply"
    assert expected_prefix in caplog.text


def test_timer_records_elapsed_after_exception(caplog) -> None:
    with (
        caplog.at_level(logging.INFO),
        pytest.raises(RuntimeError, match="збій"),
        Timer("помилка") as timer,
    ):
        raise RuntimeError("збій")

    assert timer.elapsed >= 0.0
    assert "помилка: " in caplog.text
