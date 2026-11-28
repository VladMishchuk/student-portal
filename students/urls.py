from django.urls import path, re_path, register_converter

from . import converters, views

register_converter(converters.EctsConverter, "ects")

app_name = "students"
urlpatterns = [
    path("", views.student_list, name="list"),
    path("new/", views.StudentCreateView.as_view(), name="create"),
    path("<int:student_id>/", views.student_detail, name="detail"),
    path("<int:student_id>/edit/", views.StudentUpdateView.as_view(), name="edit"),
    path("<int:student_id>/grades/new/", views.add_grade, name="add-grade"),
    path("<int:student_id>.json", views.student_json, name="detail-json"),
    path("ects/<ects:letter>/", views.by_ects, name="by-ects"),
    path("ranking/", views.RankingView.as_view(), name="ranking"),
    path("ranking.json", views.ranking_json, name="ranking-json"),
    path("pages/", views.StudentListView.as_view(), name="pages"),
    path("stats/", views.stats, name="stats"),
    re_path(r"^st/(?P<student_id>[0-9]{4})/$", views.legacy_student),
]
