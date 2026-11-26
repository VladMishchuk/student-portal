"""Декоратори та контекстні менеджери застосунку."""

import functools
import logging
import time
from collections.abc import Callable
from contextlib import ContextDecorator
from types import TracebackType
from typing import Self

logger = logging.getLogger(__name__)


def timed[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Записує в журнал час виконання функції."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start
            logger.info("%s: %.1f мс", func.__qualname__, elapsed * 1000)

    return wrapper


class Timer(ContextDecorator):
    """Контекстний менеджер і декоратор для вимірювання часу виконання."""

    def __init__(self, label: str = "") -> None:
        self.label = label
        self.elapsed: float = 0.0
        self._start: float = 0.0

    def __enter__(self) -> Self:
        self._start = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.elapsed = time.perf_counter() - self._start
        logger.info("%s: %.1f мс", self.label or "timer", self.elapsed * 1000)
