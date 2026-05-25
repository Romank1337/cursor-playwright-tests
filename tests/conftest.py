"""
Общие фикстуры для UI-тестов страницы авторизации.
"""

import os
import re

import pytest

from tests.pages.devices_page import DevicesPage
from tests.pages.login_page import LoginPage
from tests.pages.personnel_page import PersonnelPage
from tests.pages.production_units_page import ProductionUnitsPage


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


@pytest.fixture()
def devices_page(page, login_url: str, credentials: tuple[str, str]) -> DevicesPage:
    username, password = credentials
    return DevicesPage(page=page, login_url=login_url, username=username, password=password)


@pytest.fixture()
def personnel_page(page, login_url: str, credentials: tuple[str, str]) -> PersonnelPage:
    username, password = credentials
    return PersonnelPage(page=page, login_url=login_url, username=username, password=password)


@pytest.fixture()
def production_units_page(page, login_url: str, credentials: tuple[str, str]) -> ProductionUnitsPage:
    username, password = credentials
    return ProductionUnitsPage(page=page, login_url=login_url, username=username, password=password)


@pytest.fixture(scope="session")
def language_login_placeholder_en_regex() -> re.Pattern[str]:
    pattern = _env("LANG_LOGIN_PLACEHOLDER_EN_REGEX", r".*(login|username|user name|email).*")
    return re.compile(pattern, re.I)


@pytest.fixture(scope="session")
def language_login_placeholder_ru_regex() -> re.Pattern[str]:
    pattern = _env("LANG_LOGIN_PLACEHOLDER_RU_REGEX", r".*(логин|пользоват|введите).*")
    return re.compile(pattern, re.I)


@pytest.fixture(scope="session")
def run_destructive_devices_crud() -> bool:
    # По умолчанию выключено: чтобы не удалить реальные данные на стенде.
    return (_env("RUN_DESTRUCTIVE_DEVICES_CRUD", "false") or "false").lower() in {"1", "true", "yes"}


@pytest.fixture(scope="session")
def run_destructive_personnel_crud() -> bool:
    # По умолчанию выключено: чтобы не удалить реальные данные на стенде.
    return (_env("RUN_DESTRUCTIVE_PERSONNEL_CRUD", "false") or "false").lower() in {"1", "true", "yes"}


@pytest.fixture(scope="session")
def run_destructive_production_units_crud() -> bool:
    # По умолчанию выключено: создание/удаление production unit затрагивает справочник.
    return (_env("RUN_DESTRUCTIVE_PRODUCTION_UNITS_CRUD", "false") or "false").lower() in {"1", "true", "yes"}

