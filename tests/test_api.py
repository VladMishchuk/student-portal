import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from students.models import Group, Student

pytestmark = pytest.mark.django_db


def test_api_anonymous_is_forbidden(db_group):
    api_client = APIClient()
    response = api_client.get("/api/students/")
    assert response.status_code == 403
    assert "detail" in response.json()


def test_api_student_list_and_query_count(
    db_group, role_user, django_assert_num_queries
):
    api_client = APIClient()
    teacher = role_user("teacher", "Викладачі")
    api_client.force_authenticate(user=teacher)

    with django_assert_num_queries(3):
        response = api_client.get("/api/students/")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    first = data["results"][0]
    assert first["average"] == pytest.approx(91.5)
    assert first["grades"][0]["ects"] == "A"


def test_api_teacher_creates_grade_and_validates_score(db_group, role_user):
    api_client = APIClient()
    teacher = role_user("teacher", "Викладачі")
    api_client.force_authenticate(user=teacher)

    student = Student.objects.get(pk=2)
    response = api_client.post(
        "/api/grades/",
        {
            "student": student.pk,
            "course": "Git",
            "score": 81,
            "graded_on": timezone.localdate().isoformat(),
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["ects"] == "C"

    detail = api_client.get(f"/api/students/{student.pk}/").json()
    assert detail["average"] == pytest.approx(71.0)

    bad = api_client.post(
        "/api/grades/",
        {
            "student": student.pk,
            "course": "Git",
            "score": 101,
            "graded_on": timezone.localdate().isoformat(),
        },
        format="json",
    )
    assert bad.status_code == 400
    assert set(bad.json()) == {"score"}


def test_api_user_without_role_cannot_create_grade(db_group, django_user_model):
    api_client = APIClient()
    viewer = django_user_model.objects.create_user("viewer", password="pass-12345")
    api_client.force_authenticate(user=viewer)

    response = api_client.post(
        "/api/grades/",
        {
            "student": 1,
            "course": "Git",
            "score": 80,
            "graded_on": timezone.localdate().isoformat(),
        },
        format="json",
    )
    assert response.status_code == 403


def test_api_dean_creates_student_and_teacher_cannot_delete(db_group, role_user):
    api_client = APIClient()
    dean = role_user("dean", "Деканат")
    api_client.force_authenticate(user=dean)

    group = Group.objects.first()
    created = api_client.post(
        "/api/students/",
        {"first_name": "Марія", "last_name": "Лисенко", "group": group.pk},
        format="json",
    )
    assert created.status_code == 201
    assert created.json()["average"] is None
    student_id = created.json()["id"]

    teacher = role_user("teacher", "Викладачі")
    api_client.force_authenticate(user=teacher)
    deleted = api_client.delete(reverse("student-detail", args=[student_id]))
    assert deleted.status_code == 403


def test_api_filter_students_by_last_name(db_group, role_user):
    api_client = APIClient()
    teacher = role_user("teacher", "Викладачі")
    api_client.force_authenticate(user=teacher)

    filtered = api_client.get("/api/students/", {"last_name": "Ков"})
    assert filtered.status_code == 200
    assert filtered.json()["count"] == 1
    assert filtered.json()["results"][0]["last_name"] == "Коваль"

    unfiltered = api_client.get("/api/students/")
    assert unfiltered.status_code == 200
    assert unfiltered.json()["count"] == 3
