import logging
import time

from django.conf import settings
from django.db import DatabaseError
from django.shortcuts import render

from student_portal.exceptions import StorageError

logger = logging.getLogger("student_portal.requests")


class TimingMiddleware:
    """Вимірює час обробки запиту та додає заголовок Server-Timing."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response["Server-Timing"] = f"app;dur={elapsed_ms:.1f}"
        if elapsed_ms > settings.SLOW_REQUEST_MS:
            logger.warning("Повільний запит %s: %.0f мс", request.path, elapsed_ms)
        return response


class StorageErrorMiddleware:
    """Перетворює StorageError і DatabaseError на відповідь 503."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, StorageError | DatabaseError):
            logger.error("Сховище недоступне: %s", exception)
            return render(request, "503.html", status=503)
        return None
