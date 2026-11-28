"""Моделі Django, сервіс збереження/читання, load_group та адмінпанель."""

from datetime import date

import pytest
from django.core.management import CommandError, call_command
from django.db import IntegrityError

from students.models import Grade, Group, Student
from students.services import get_group, store_group

pytestmark = pytest.mark.django_db


def test_store_group_is_idempotent_and_preserves_ranking(group):
    count1 = store_group(group)
    count2 = store_group(group)

    assert count1 == (3, 3)
    assert count2 == (3, 3)
    assert Group.objects.count() == 1
    assert Student.objects.count() == 3
    assert Grade.objects.count() == 3

    loaded = get_group()
    assert [s.id for s in loaded.ranking()] == [s.id for s in group.ranking()]


def test_model_str_representations(db_group):
    grp = Group.objects.get(name="КН-11")
    student = Student.objects.get(id=1)
    grade = student.grades.order_by("id").first()

    assert str(grp) == "КН-11"
    assert str(student) == "Коваль Олена"
    assert str(grade) == "Коваль Олена: Python 95"


def test_grade_score_above_100_rejected_by_database(db_group):
    student = Student.objects.get(id=1)
    with pytest.raises(IntegrityError):
        Grade.objects.create(
            student=student,
            course="Python",
            score=101,
            graded_on=date.today(),
        )


def test_load_group_command_imports_json(data_file, capsys):
    call_command("load_group", str(data_file))
    out = capsys.readouterr().out
    assert "Група КН-11: студентів - 3, оцінок - 3" in out


def test_load_group_missing_file_raises_command_error(tmp_path):
    missing = tmp_path / "nope.json"
    with pytest.raises(CommandError, match="не знайдено"):
        call_command("load_group", str(missing))


def test_admin_student_list_and_change_page(admin_client, db_group):
    list_response = admin_client.get("/admin/students/student/")
    assert list_response.status_code == 200

    change_response = admin_client.get("/admin/students/student/1/change/")
    assert change_response.status_code == 200
    assert "grades-0-course" in change_response.text
