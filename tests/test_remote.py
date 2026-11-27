"""Тести модуля remote (завантаження групи з сервера деканату)."""

import io
import json
from urllib.error import URLError

import pytest

from student_portal.exceptions import StorageError
from student_portal.remote import fetch_group
from student_portal.storage import group_to_dict

URL = "https://dekanat.example.edu/api/groups/kn-11"


@pytest.fixture
def urlopen(mocker):
    """Підміняє urlopen там, де його шукає модуль remote."""
    return mocker.patch("student_portal.remote.urlopen", autospec=True)


def respond_with(urlopen, payload: bytes) -> None:
    urlopen.return_value.__enter__.return_value = io.BytesIO(payload)


def test_fetch_group_parses_response(urlopen, group) -> None:
    respond_with(urlopen, json.dumps(group_to_dict(group)).encode())

    fetched = fetch_group(URL)

    assert fetched == group
    urlopen.assert_called_once_with(URL, timeout=5.0)


def test_fetch_group_passes_custom_timeout(urlopen, group) -> None:
    respond_with(urlopen, json.dumps(group_to_dict(group)).encode())

    fetch_group(URL, timeout=1.5)

    assert urlopen.call_args.kwargs["timeout"] == 1.5


@pytest.mark.parametrize(
    ("error", "expected_text"),
    [
        pytest.param(
            URLError("Connection refused"),
            "сервер недоступний: Connection refused",
            id="url-error",
        ),
        pytest.param(
            TimeoutError(),
            "сервер не відповів за 5.0 с",
            id="timeout",
        ),
    ],
)
def test_fetch_group_network_errors(urlopen, error, expected_text: str) -> None:
    urlopen.side_effect = error

    with pytest.raises(StorageError, match=expected_text):
        fetch_group(URL)


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(b"<html>502 Bad Gateway</html>", id="html-error-page"),
        pytest.param(
            json.dumps({"name": "КН-11"}).encode(),
            id="missing-students-key",
        ),
    ],
)
def test_fetch_group_invalid_response(urlopen, payload: bytes) -> None:
    respond_with(urlopen, payload)

    with pytest.raises(StorageError, match="неправильному форматі"):
        fetch_group(URL)
