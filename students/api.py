from statistics import fmean

from rest_framework import mixins, serializers, viewsets

from student_portal.grades import ects_grade

from .models import Grade, Student


class GradeSerializer(serializers.ModelSerializer):
    ects = serializers.SerializerMethodField()

    class Meta:
        model = Grade
        fields = ["id", "student", "course", "score", "ects", "graded_on"]

    def get_ects(self, grade: Grade) -> str:
        return ects_grade(grade.score)


class StudentSerializer(serializers.ModelSerializer):
    average = serializers.SerializerMethodField()
    grades = GradeSerializer(many=True, read_only=True)

    class Meta:
        model = Student
        fields = ["id", "first_name", "last_name", "group", "average", "grades"]

    def get_average(self, student: Student) -> float | None:
        scores = [g.score for g in student.grades.all()]
        return fmean(scores) if scores else None


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer

    def get_queryset(self):
        queryset = Student.objects.prefetch_related("grades").order_by("id")
        last_name = self.request.query_params.get("last_name")
        if last_name:
            queryset = queryset.filter(last_name__icontains=last_name)
        return queryset


class GradeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = GradeSerializer
    queryset = Grade.objects.order_by("id")
