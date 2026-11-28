from student_portal.grades import ECTS_LETTERS


class EctsConverter:
    """Конвертер URL для літер шкали ECTS."""

    regex = "|".join(ECTS_LETTERS)

    def to_python(self, value: str) -> str:
        return value

    def to_url(self, value: str) -> str:
        return value
