import io

import pytest
from django.contrib.messages import get_messages
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects

from students.models import Grade, Group, Student

pytestmark = pytest.mark.django_db


def test_anonymous_redirected_to_login(anonymous, db_group):
    response = anonymous.get(reverse("students:list"))
    assertRedirects(response, "/accounts/login/?next=/students/")


def test_login_page_accessible_and_redirects_after_login(
    anonymous, db_group, django_user_model
):
    login_url = reverse("login")
    assert anonymous.get(login_url).status_code == 200

    django_user_model.objects.create_user("user1", password="secret-password-1")
    response = anonymous.post(
        login_url,
        {"username": "user1", "password": "secret-password-1"},
    )
    assertRedirects(response, reverse("students:list"))


def test_logout_requires_post(client):
    logout_url = reverse("logout")
    assert client.get(logout_url).status_code == 405
    response = client.post(logout_url)
    assertRedirects(response, reverse("login"))


def test_setup_roles_is_idempotent():
    call_command("setup_roles", stdout=io.StringIO())
    call_command("setup_roles", stdout=io.StringIO())


def test_add_grade_permissions_and_links(client, db_group, role_user):
    student = Student.objects.first()
    add_url = reverse("students:add-grade", args=[student.pk])

    assert client.get(add_url).status_code == 403

    teacher = role_user("teacher", "Викладачі")
    client.force_login(teacher)
    assert client.get(add_url).status_code == 200
    detail_response = client.get(reverse("students:detail", args=[student.pk]))
    assertContains(detail_response, "Нова оцінка")
    assertNotContains(detail_response, "Змінити")


def test_add_grade_post_invalid_and_valid(client, db_group, role_user):
    student = Student.objects.first()
    add_url = reverse("students:add-grade", args=[student.pk])
    teacher = role_user("teacher", "Викладачі")
    client.force_login(teacher)

    before_count = Grade.objects.count()
    invalid_response = client.post(
        add_url,
        {
            "course": "Git",
            "score": 101,
            "graded_on": timezone.localdate().isoformat(),
        },
    )
    assert invalid_response.status_code == 200
    assert "score" in invalid_response.context["form"].errors
    assert Grade.objects.count() == before_count

    valid_response = client.post(
        add_url,
        {
            "course": "  Git  ",
            "score": 74,
            "graded_on": timezone.localdate().isoformat(),
        },
    )
    assertRedirects(valid_response, reverse("students:detail", args=[student.pk]))
    assert Grade.objects.count() == before_count + 1
    msgs = [str(m) for m in get_messages(valid_response.wsgi_request)]
    assert "Оцінку 74 з Git збережено" in msgs


def test_dean_creates_and_updates_student_teacher_forbidden(
    client, db_group, role_user
):
    create_url = reverse("students:create")
    student = Student.objects.first()
    edit_url = reverse("students:edit", args=[student.pk])
    group = Group.objects.first()

    teacher = role_user("teacher", "Викладачі")
    client.force_login(teacher)
    assert client.get(create_url).status_code == 403
    assert client.get(edit_url).status_code == 403

    dean = role_user("dean", "Деканат")
    client.force_login(dean)
    create_response = client.post(
        create_url,
        {"first_name": "Тарас", "last_name": "Шевченко", "group": group.pk},
    )
    assertRedirects(create_response, reverse("students:list"))
    created = Student.objects.get(last_name="Шевченко")

    update_response = client.post(
        reverse("students:edit", args=[created.pk]),
        {"first_name": "Тарас", "last_name": "Франко", "group": group.pk},
    )
    assertRedirects(update_response, reverse("students:detail", args=[created.pk]))
    created.refresh_from_db()
    assert created.last_name == "Франко"
