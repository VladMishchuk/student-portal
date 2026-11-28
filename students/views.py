from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.generic import ListView, TemplateView

from student_portal.grades import ects_grade

from .services import get_group, get_student_or_404


def student_list(request):
    group = get_group()
    query = request.GET.get("q", "").strip()
    students = group.find(query) if query else list(group)
    context = {"group": group, "students": students, "query": query}
    return render(request, "students/student_list.html", context)


def student_detail(request, student_id):
    student = get_student_or_404(get_group(), student_id)
    return render(request, "students/student_detail.html", {"student": student})


def student_json(request, student_id):
    student = get_student_or_404(get_group(), student_id)
    return JsonResponse(
        {
            "id": student.id,
            "full_name": student.full_name,
            "average": student.average(),
        },
        json_dumps_params={"ensure_ascii": False},
    )


class RankingView(TemplateView):
    template_name = "students/ranking.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = get_group()
        context["group"] = group
        context["ranking"] = group.ranking()
        return context


def ranking_json(request):
    group = get_group()
    data = [
        {
            "place": place,
            "full_name": student.full_name,
            "average": student.average(),
        }
        for place, student in enumerate(group.ranking(), start=1)
    ]
    return JsonResponse(
        data,
        safe=False,
        json_dumps_params={"ensure_ascii": False},
    )


class StudentListView(ListView):
    template_name = "students/student_pages.html"
    context_object_name = "students"
    paginate_by = 2

    def get_queryset(self):
        return get_group().ranking()


def stats(request):
    group = get_group()
    return render(
        request,
        "students/stats.html",
        {
            "group": group,
            "student_count": len(group),
            "group_average": group.average(),
            "ects_distribution": list(group.ects_distribution().items()),
        },
    )


def by_ects(request, letter):
    students = [
        s
        for s in get_group()
        if s.average() is not None and ects_grade(round(s.average())) == letter
    ]
    return render(
        request,
        "students/by_ects.html",
        {"letter": letter, "students": students},
    )


def legacy_student(request, student_id):
    return redirect("students:detail", student_id=int(student_id), permanent=True)
