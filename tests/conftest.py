"""
Общие фикстуры для UI-тестов страницы авторизации.
"""

import os
import re

import pytest

from tests.pages.login_page import LoginPage


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


@pytest.fixture(scope="session")
def browser_context_args() -> dict:
    # Для локального https со self-signed сертификатом.
    return {"ignore_https_errors": True}


@pytest.fixture(scope="session")
def login_url() -> str:
    return _env("LOGIN_URL", "https://localhost:8001/user/login")  # type: ignore[return-value]


@pytest.fixture(scope="session")
def credentials() -> tuple[str, str]:
    username = _env("TEST_USER_LOGIN", "Admin")
    password = _env("TEST_USER_PASSWORD", "123")
    return username or "", password or ""


@pytest.fixture(scope="session")
def invalid_credentials() -> tuple[str, str]:
    username = _env("TEST_INVALID_LOGIN", "wrong_user")
    password = _env("TEST_INVALID_PASSWORD", "wrong_pass")
    return username or "wrong_user", password or "wrong_pass"


@pytest.fixture(scope="session")
def success_url_regex() -> re.Pattern[str]:
    pattern = _env(
        "SUCCESS_URL_REGEX",
        r".*monitoring/realtime\?deptId=\d+&presetId=\d+.*",
    )
    return re.compile(pattern or r".*monitoring/realtime.*")


@pytest.fixture()
def login_page(page, login_url: str) -> LoginPage:
    return LoginPage(page=page, login_url=login_url)


@pytest.fixture(scope="session")
def language_login_placeholder_en_regex() -> re.Pattern[str]:
    pattern = _env("LANG_LOGIN_PLACEHOLDER_EN_REGEX", r".*(login|username|user name|email).*")
    return re.compile(pattern, re.I)


@pytest.fixture(scope="session")
def language_login_placeholder_ru_regex() -> re.Pattern[str]:
    pattern = _env("LANG_LOGIN_PLACEHOLDER_RU_REGEX", r".*(логин|пользоват|введите).*")
    return re.compile(pattern, re.I)

