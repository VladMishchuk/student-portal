"""Тести збереження та завантаження групи у JSON."""

import json
from pathlib import Path

import pytest

from student_portal.exceptions import StorageError
from student_portal.group import Group
from student_portal.storage import atomic_write, load_group, save_group


def test_save_and_load_roundtrip(group: Group, tmp_path: Path) -> None:
    path = tmp_path / "nested" / "group.json"

    save_group(group, path)
    loaded = load_group(path)

    assert loaded == group


def test_save_writes_utf8_cyrillic_without_escaping(
    group: Group, tmp_path: Path
) -> None:
    path = tmp_path / "group.json"

    save_group(group, path)
    raw = path.read_text(encoding="utf-8")

    assert "Коваль" in raw


def test_load_missing_file_raises_storage_error(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"

    with pytest.raises(StorageError, match="не знайдено"):
        load_group(path)


@pytest.mark.parametrize(
    "content",
    [
        pytest.param("{not valid json", id="invalid-json"),
        pytest.param(json.dumps({"name": "КН-11"}), id="missing-students"),
        pytest.param(
            json.dumps(
                {
                    "name": "КН-11",
                    "students": [
                        {
                            "id": 1,
                            "first_name": "Олена",
                            "last_name": "Коваль",
                            "grades": [
                                {
                                    "course": "Python",
                                    "score": 105,
                                    "graded_on": "2026-10-01",
                                }
                            ],
                        }
                    ],
                }
            ),
            id="score-105",
        ),
        pytest.param(
            json.dumps(
                {
                    "name": "КН-11",
                    "students": [
                        {
                            "id": 1,
                            "first_name": "Олена",
                            "last_name": "Коваль",
                            "grades": [
                                {
                                    "course": "Python",
                                    "score": 90,
                                    "graded_on": "01.10.2026",
                                }
                            ],
                        }
                    ],
                }
            ),
            id="bad-date",
        ),
    ],
)
def test_load_corrupted_file_raises_storage_error(tmp_path: Path, content: str) -> None:
    path = tmp_path / "broken.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(StorageError, match="неправильний формат"):
        load_group(path)


def test_atomic_write_replaces_content(tmp_path: Path) -> None:
    path = tmp_path / "data.txt"
    path.write_text("старий вміст", encoding="utf-8")

    with atomic_write(path) as file:
        file.write("новий вміст")

    assert path.read_text(encoding="utf-8") == "новий вміст"
    assert list(tmp_path.iterdir()) == [path]


def test_atomic_write_keeps_old_content_on_error(tmp_path: Path) -> None:
    path = tmp_path / "data.txt"
    path.write_text("старий вміст", encoding="utf-8")

    with pytest.raises(RuntimeError), atomic_write(path) as file:
        file.write("неповний запис")
        raise RuntimeError("збій запису")

    assert path.read_text(encoding="utf-8") == "старий вміст"
    assert list(tmp_path.iterdir()) == [path]
