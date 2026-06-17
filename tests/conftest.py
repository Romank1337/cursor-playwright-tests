"""
Общие фикстуры для UI-тестов страницы авторизации.
"""

import os
import re

import pytest
from playwright.sync_api import sync_playwright

from tests.api.ipm_setup_client import IpmBackendSetup, prepare_ipm_backend
from tests.helpers.ipm_flow import prepare_and_login_ipm
from tests.pages.devices_page import DevicesPage
from tests.pages.ipm_login_page import IpmLoginPage
from tests.pages.ipm_machine_page import IpmMachinePage
from tests.pages.ipm_machines_page import IpmMachinesPage
from tests.pages.login_page import LoginPage
from tests.pages.machine_params_page import MachineParamsPage
from tests.pages.page_factory import PageFactory
from tests.pages.personnel_page import PersonnelPage
from tests.pages.production_units_page import ProductionUnitsPage
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
    # HEADLESS=false | 0 | no — видимый браузер (для отладки на стенде).
    headless = (_env("HEADLESS", "true") or "true").lower() not in {"0", "false", "no"}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
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
def web_client_api_url() -> str:
    return _env("WEB_CLIENT_API_URL", "http://127.0.0.1:8089")  # type: ignore[return-value]


@pytest.fixture(scope="session")
def web_api_user_id() -> str:
    return _env("WEB_API_USER_ID", "1")  # type: ignore[return-value]


@pytest.fixture(scope="session")
def ipm_url() -> str:
    return _env("IPM_URL", "http://localhost:8002")  # type: ignore[return-value]


@pytest.fixture(scope="session")
def ipm_dept_id() -> int:
    return int(_env("IPM_MACHINE_DEPT_ID", "2") or "2")


@pytest.fixture(scope="session")
def ipm_worker_role_id() -> int:
    return int(_env("IPM_WORKER_ROLE_ID", "1") or "1")


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
    return PageFactory.login_page(page=page, login_url=login_url)


@pytest.fixture()
def machine_params_page(page, machine_params_url: str) -> MachineParamsPage:
    return PageFactory.machine_params_page(page=page, machine_params_url=machine_params_url)


@pytest.fixture()
def roles_page(page, roles_url: str) -> RolesPage:
    return PageFactory.roles_page(page=page, roles_url=roles_url)


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


@pytest.fixture()
def ipm_login_page(page, ipm_url: str) -> IpmLoginPage:
    return IpmLoginPage(page=page, ipm_url=ipm_url)


@pytest.fixture()
def ipm_machines_page(page) -> IpmMachinesPage:
    return IpmMachinesPage(page=page)


@pytest.fixture()
def ipm_machine_page(page) -> IpmMachinePage:
    return IpmMachinePage(page=page)


@pytest.fixture()
def ipm_ready(
    login_page,
    devices_page,
    ipm_login_page,
    credentials,
    web_client_api_url: str,
    web_api_user_id: str,
    ipm_dept_id: int,
    ipm_worker_role_id: int,
) -> IpmBackendSetup:
    """API-подготовка + автоподключение устройств + вход в ИПМ."""
    username, password = credentials
    return prepare_and_login_ipm(
        login_page=login_page,
        devices_page=devices_page,
        ipm_login_page=ipm_login_page,
        username=username,
        password=password,
        web_client_api_url=web_client_api_url,
        web_api_user_id=web_api_user_id,
        ipm_dept_id=ipm_dept_id,
        ipm_worker_role_id=ipm_worker_role_id,
    )


@pytest.fixture()
def ipm_backend_setup(
    web_client_api_url: str,
    web_api_user_id: str,
    ipm_dept_id: int,
    ipm_worker_role_id: int,
) -> IpmBackendSetup:
    """API-подготовка персонала/станка/протокола/роли для сценариев ИПМ."""
    return prepare_ipm_backend(
        base_url=web_client_api_url,
        user_id=web_api_user_id,
        dept_id=ipm_dept_id,
        worker_role_id=ipm_worker_role_id,
    )


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

