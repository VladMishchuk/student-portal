"""Схеми Pydantic: що API приймає і що повертає."""

from datetime import date
from statistics import fmean
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, computed_field

from student_portal.grades import MAX_SCORE, MIN_SCORE, ects_grade


def _not_in_future(value: date) -> date:
    if value > date.today():
        raise ValueError("дата оцінки не може бути в майбутньому")
    return value


CourseStr = Annotated[str, Field(min_length=1, max_length=100)]
ScoreInt = Annotated[int, Field(ge=MIN_SCORE, le=MAX_SCORE)]
PastOrTodayDate = Annotated[date, AfterValidator(_not_in_future)]


class GradeIn(BaseModel):
    """Нова оцінка: ті самі правила, що у формі Django і серіалізаторі DRF."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [{"course": "Git", "score": 74, "graded_on": "2026-11-02"}]
        },
    )

    course: CourseStr
    score: ScoreInt
    graded_on: PastOrTodayDate


class GradeUpdate(BaseModel):
    """Часткове оновлення оцінки: ті самі правила, що й у GradeIn."""

    model_config = ConfigDict(str_strip_whitespace=True)

    course: CourseStr | None = None
    score: ScoreInt | None = None
    graded_on: PastOrTodayDate | None = None


class GradeOut(BaseModel):
    """Вихідна схема оцінки з обчислюваною літерою ECTS."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course: str
    score: int
    graded_on: date

    @computed_field
    @property
    def ects(self) -> str:
        return ects_grade(self.score)


class StudentOut(BaseModel):
    """Вихідна схема студента з оцінками та середнім балом."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    grades: list[GradeOut]

    @computed_field
    @property
    def average(self) -> float | None:
        return fmean(g.score for g in self.grades) if self.grades else None


class StudentPage(BaseModel):
    """Сторінка списку студентів."""

    count: int
    items: list[StudentOut]


class RankingItem(BaseModel):
    """Елемент рейтингу студентів."""

    place: int
    id: int
    full_name: str
    average: float | None
