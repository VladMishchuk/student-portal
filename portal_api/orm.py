"""Моделі SQLAlchemy для таблиць, які створили міграції Django (ЛР 8)."""

from datetime import date

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from student_portal import grades, people


class Base(DeclarativeBase):
    """Базовий клас декларативних моделей SQLAlchemy."""


class Group(Base):
    """Академічна група (таблиця students_group)."""

    __tablename__ = "students_group"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20), unique=True)


class Student(Base):
    """Студент (таблиця students_student)."""

    __tablename__ = "students_student"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("students_group.id"))
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))

    group: Mapped[Group] = relationship(lazy="raise")
    grades: Mapped[list[Grade]] = relationship(
        lazy="raise",
        order_by=lambda: (Grade.graded_on, Grade.id),
    )


class Grade(Base):
    """Оцінка з дисципліни (таблиця students_grade)."""

    __tablename__ = "students_grade"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students_student.id"))
    course: Mapped[str] = mapped_column(String(100))
    score: Mapped[int]
    graded_on: Mapped[date]


def to_core(student: Student) -> people.Student:
    """Студент з бази даних як об’єкт ядра; оцінки мають бути вже завантажені."""
    marks = [grades.Grade(g.course, g.score, g.graded_on) for g in student.grades]
    return people.Student(student.id, student.first_name, student.last_name, marks)
