"""Тести імпорту журналу оцінок CSV."""

from collections.abc import Callable
from pathlib import Path

import pytest

from student_portal.exceptions import JournalFormatError, StorageError
from student_portal.group import Group
from student_portal.journal import import_journal, parse_entries, read_rows

HEADER = "student_id;course;score;graded_on"

type JournalWriter = Callable[..., Path]


@pytest.fixture
def write_journal(tmp_path: Path) -> JournalWriter:
    """Фабрика файлів журналу: рядки даних додаються після заголовка."""

    def write(*rows: str, header: str = HEADER, encoding: str = "utf-8") -> Path:
        path = tmp_path / "journal.csv"
        path.write_text("\n".join([header, *rows]) + "\n", encoding=encoding)
        return path

    return write


def test_import_valid_journal_strips_course_and_adds_grades(
    group: Group, write_journal: JournalWriter
) -> None:
    path = write_journal(
        "1;  Вебтехнології  ;92;2026-10-20",
        "3;Python;78;2026-10-21",
    )

    count = import_journal(group, path)

    assert count == 2
    assert group.get(1).grades_for("Вебтехнології")[0].score == 92
    assert group.get(3).grades_for("Python")[0].score == 78


def test_import_journal_with_bom(group: Group, write_journal: JournalWriter) -> None:
    path = write_journal(
        "3;Git;85;2026-10-20",
        encoding="utf-8-sig",
    )

    count = import_journal(group, path)

    assert count == 1
    assert group.get(3).grades_for("Git")[0].score == 85


@pytest.mark.parametrize(
    ("row", "message"),
    [
        pytest.param("1;Python;105;2026-10-20", "від 0 до 100", id="score"),
        pytest.param("1;Python;abc;2026-10-20", "invalid literal", id="text"),
        pytest.param("1;Python;90;20.10.2026", "Invalid isoformat", id="date"),
        pytest.param("1;Python;90", "argument must be str", id="missing-column"),
        pytest.param("x;Python;90;2026-10-20", "invalid literal", id="id"),
        pytest.param(
            "42;Python;90;2026-10-20",
            "студента з id=42 немає",
            id="unknown-id",
        ),
    ],
)
def test_bad_row_is_reported_with_line_number(
    group: Group, write_journal: JournalWriter, row: str, message: str
) -> None:
    path = write_journal("1;Python;90;2026-10-20", row)

    with pytest.raises(JournalFormatError, match=f"^рядок 3: .*{message}"):
        import_journal(group, path)


def test_import_journal_is_atomic_on_error(
    group: Group, write_journal: JournalWriter
) -> None:
    before = {s.id: len(s.grades) for s in group}
    path = write_journal(
        "1;Вебтехнології;90;2026-10-20",
        "2;Вебтехнології;105;2026-10-20",
    )

    with pytest.raises(JournalFormatError, match="^рядок 3:"):
        import_journal(group, path)

    assert {s.id: len(s.grades) for s in group} == before


def test_import_rejects_invalid_header(
    group: Group, write_journal: JournalWriter
) -> None:
    path = write_journal("1;Python;90;2026-10-20", header="id;course;score;date")

    with pytest.raises(JournalFormatError, match="заголовок має бути"):
        import_journal(group, path)


def test_read_rows_is_lazy(tmp_path: Path) -> None:
    rows = read_rows(tmp_path / "missing.csv")

    with pytest.raises(StorageError, match="не знайдено"):
        next(rows)


def test_parse_entries_preserves_line_numbers() -> None:
    raw_rows = [
        (
            2,
            {
                "student_id": "1",
                "course": "Python",
                "score": "95",
                "graded_on": "2026-10-01",
            },
        ),
        (
            3,
            {
                "student_id": "2",
                "course": "Git",
                "score": "88",
                "graded_on": "2026-10-02",
            },
        ),
    ]

    entries = list(parse_entries(raw_rows))

    assert [entry.line for entry in entries] == [2, 3]
