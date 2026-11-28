from typing import Any

from django import forms
from django.utils import timezone

from .models import Grade


class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ["course", "score", "graded_on"]
        widgets = {
            "graded_on": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_course(self) -> str:
        return self.cleaned_data["course"].strip()

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        graded_on = cleaned_data.get("graded_on")
        if graded_on is not None and graded_on > timezone.localdate():
            self.add_error("graded_on", "Дата оцінки не може бути в майбутньому")
        return cleaned_data
