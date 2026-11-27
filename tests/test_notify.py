"""Тести асинхронної розсилки результатів."""

import asyncio

import pytest

from student_portal import notify
from student_portal.notify import notify_all, notify_sequentially, send_result
from student_portal.people import Student


@pytest.fixture(autouse=True)
def no_delay(monkeypatch) -> None:
    """Тести не чекають «поштовий сервер»."""
    monkeypatch.setattr(notify, "SEND_DELAY", 0)


def test_send_result_with_and_without_grades(group) -> None:
    with_grades = group.get(1)
    without_grades = Student(10, "Тарас", "Шевченко")

    assert asyncio.run(send_result(with_grades)) == "Коваль Олена: середній бал 91.5"
    assert asyncio.run(send_result(without_grades)) == "Шевченко Тарас: оцінок немає"


def test_notify_sequentially_preserves_order(group) -> None:
    messages = asyncio.run(notify_sequentially(group))

    assert messages == [
        "Коваль Олена: середній бал 91.5",
        "Мельник Андрій: середній бал 61.0",
        "Бойко Ірина: оцінок немає",
    ]


@pytest.mark.parametrize("limit", [1, 2, 3])
def test_notify_all_respects_limit_and_order(mocker, group, limit: int) -> None:
    active = 0
    peak = 0

    async def fake_send(student: Student) -> str:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        return student.last_name

    send = mocker.patch("student_portal.notify.send_result", side_effect=fake_send)

    messages = asyncio.run(notify_all(group, limit=limit))

    assert messages == ["Коваль", "Мельник", "Бойко"]
    assert peak == limit
    assert send.await_count == 3
