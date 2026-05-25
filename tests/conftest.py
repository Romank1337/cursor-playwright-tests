"""
Общие фикстуры для UI-тестов страницы авторизации.
"""

import os
import re

import pytest
from playwright.sync_api import sync_playwright

from tests.pages.login_page import LoginPage
from tests.pages.machine_params_page import MachineParamsPage
from tests.pages.page_factory import PageFactory
from tests.pages.roles_page import RolesPage


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


@pytest.fixture(scope="session")
def browser_context_args() -> dict:
    # Для локального https со self-signed сертификатом.
    return {
        "ignore_https_errors": True,
        "viewport": {"width": 1920, "height": 1080},
    }


@pytest.fixture(scope="session")
def browser():
    # Локальная замена pytest-playwright browser fixture.
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        yield browser
        browser.close()


@pytest.fixture()
def context(browser, browser_context_args: dict):
    context = browser.new_context(**browser_context_args)
    yield context
    context.close()


@pytest.fixture()
def page(context):
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="session")
def login_url() -> str:
    return _env("LOGIN_URL", "https://localhost:8001/user/login")  # type: ignore[return-value]


@pytest.fixture(scope="session")
def machine_params_url() -> str:
    return _env("MACHINE_PARAMS_URL", "https://localhost:8001/list/machineParams")  # type: ignore[return-value]


@pytest.fixture(scope="session")
def roles_url() -> str:
    return _env("ROLES_URL", "https://localhost:8001/list/workerRoles")  # type: ignore[return-value]


@pytest.fixture(scope="session")
def credentials() -> tuple[str, str]:
    username = _env("TEST_USER_LOGIN", "Admin")
    password = _env("TEST_USER_PASSWORD", "123")
    return username or "", password or ""


@pytest.fixture(scope="session")
def success_url_regex() -> re.Pattern[str]:
    pattern = _env(
        "SUCCESS_URL_REGEX",
        r".*monitoring/realtime\?deptId=\d+&presetId=\d+.*",
    )
    return re.compile(pattern or r".*monitoring/realtime.*")


@pytest.fixture()
def login_page(page, login_url: str) -> LoginPage:
    return PageFactory.login_page(page=page, login_url=login_url)


@pytest.fixture()
def machine_params_page(page, machine_params_url: str) -> MachineParamsPage:
    return PageFactory.machine_params_page(page=page, machine_params_url=machine_params_url)


@pytest.fixture()
def roles_page(page, roles_url: str) -> RolesPage:
    return PageFactory.roles_page(page=page, roles_url=roles_url)

