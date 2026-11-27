"""Тести функції main та пункту меню 11."""

from pathlib import Path

import pytest

from student_portal import cli
from student_portal.cli import main, run
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student
from student_portal.storage import load_group, save_group


@pytest.fixture
def data_file(monkeypatch, tmp_path: Path) -> Path:
    """Підміняє файл даних застосунку тимчасовим."""
    path = tmp_path / "group.json"
    monkeypatch.setattr(cli, "DATA_FILE", path)
    return path


def test_main_loads_group_prints_summary_and_saves_changes(
    data_file: Path, group: Group, answers, capsys
) -> None:
    save_group(group, data_file)
    answers("4", "Марія", "Шевчук", "0")

    main()

    out = capsys.readouterr().out
    assert "Група КН-11: студентів - 3, середній бал - 76.2" in out
    assert load_group(data_file).get(4).full_name == "Шевчук Марія"


def test_main_creates_new_group_when_file_missing(
    data_file: Path, answers, capsys
) -> None:
    answers("КН-12", "0")

    main()

    out = capsys.readouterr().out
    assert "Група КН-12: студентів - 0, середній бал - -" in out
    assert data_file.exists()
    assert load_group(data_file).name == "КН-12"


def test_main_exits_on_corrupted_file(data_file: Path) -> None:
    data_file.write_text("{невалідний json", encoding="utf-8")

    with pytest.raises(SystemExit, match="Не вдалося завантажити дані"):
        main()


@pytest.mark.parametrize(
    ("confirm", "expected_name", "expected_message"),
    [
        pytest.param("т", "КН-99", "Групу замінено", id="replace-confirmed"),
        pytest.param("н", "КН-11", "На сервері: група КН-99", id="replace-declined"),
    ],
)
def test_menu_11_downloads_group_from_dekanat(
    mocker,
    monkeypatch,
    group: Group,
    answers,
    capsys,
    confirm: str,
    expected_name: str,
    expected_message: str,
) -> None:
    custom_url = "https://custom.dekanat.edu/groups/kn-99.json"
    monkeypatch.setenv("DEKANAT_URL", custom_url)
    remote_group = Group("КН-99")
    remote_group.add(Student(10, "Олег", "Сидоренко", [Grade("Python", 90)]))
    fetch = mocker.patch(
        "student_portal.cli.fetch_group",
        autospec=True,
        return_value=remote_group,
    )
    answers("11", confirm, "0")

    run(group)

    fetch.assert_called_once_with(custom_url)
    assert group.name == expected_name
    assert expected_message in capsys.readouterr().out
