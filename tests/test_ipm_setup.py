"""
Предварительная подготовка стенда для тестирования ИПМ.

Сценарий объединяет API-подготовку (Web Client API :8089) и UI-шаги:
- создание персонала, станка, разблокировка протокола, назначение роли;
- включение автоподключения устройств в /list/devices;
- вход в ИПМ по табельному номеру на http://localhost:8002.
"""

from __future__ import annotations

import json
import os

os.environ.setdefault("HEADLESS", "true")

import allure
import pytest

from tests.api.ipm_setup_client import prepare_ipm_backend
from tests.testit_compat import testit


def _attach_ui_state(page, name: str) -> None:
    allure.attach(page.url, name=f"{name}:url", attachment_type=allure.attachment_type.TEXT)
    allure.attach(
        page.screenshot(full_page=True),
        name=f"{name}:screenshot",
        attachment_type=allure.attachment_type.PNG,
    )


def _attach_backend_setup(setup) -> None:
    payload = {
        "suffix": setup.suffix,
        "tab_number": setup.tab_number,
        "personnel_id": setup.personnel_id,
        "worker_id": setup.worker_id,
        "machine_id": setup.machine_id,
        "machine_code": setup.machine_code,
        "protocol_id": setup.protocol_id,
        "protocol_ip": setup.protocol_ip,
        "worker_role_id": setup.worker_role_id,
    }
    allure.attach(
        json.dumps(payload, ensure_ascii=False, indent=2),
        name="ipm_backend_setup",
        attachment_type=allure.attachment_type.JSON,
    )


@pytest.mark.e2e
@pytest.mark.ipm_setup
@testit.nameSpace("UI/Smoke")
@testit.className("IpmSetup")
@testit.externalId("ui.ipm_setup.preparation")
@testit.displayName("Подготовка стенда для тестирования ИПМ")
@allure.feature("ИПМ")
@allure.story("Подготовка стенда")
@allure.title("Подготовка стенда для тестирования ИПМ")
@allure.description(
    "Предварительные шаги перед тестами ИПМ: API-цикл (персонал → станок → "
    "разблокировка протокола → роль) → автоподключение устройств на :8001 → "
    "авторизация в ИПМ на :8002 по табельному номеру."
)
def test_ipm_preparation_full_setup(
    login_page,
    devices_page,
    ipm_login_page,
    credentials,
    web_client_api_url: str,
    web_api_user_id: str,
    ipm_dept_id: int,
    ipm_worker_role_id: int,
):
    username, password = credentials
    allure.dynamic.parameter("login", username)
    allure.dynamic.parameter("web_client_api_url", web_client_api_url)

    with allure.step("API: подготовить персонал, станок, протокол и роль"):
        setup = prepare_ipm_backend(
            base_url=web_client_api_url,
            user_id=web_api_user_id,
            dept_id=ipm_dept_id,
            worker_role_id=ipm_worker_role_id,
        )
        allure.dynamic.parameter("tab_number", setup.tab_number)
        allure.dynamic.parameter("machine_id", setup.machine_id)
        allure.dynamic.parameter("protocol_id", setup.protocol_id)
        _attach_backend_setup(setup)

    with allure.step("UI: авторизация в web-client (:8001)"):
        login_page.open()
        login_page.login(username, password)
        login_page.page.wait_for_timeout(1_500)
        _attach_ui_state(login_page.page, "web_client_logged_in")

    with allure.step("UI: включить автоподключение новых устройств (/list/devices)"):
        devices_page.open()
        devices_page.assert_loaded()
        devices_page.enable_auto_connect_new_devices()
        _attach_ui_state(devices_page.page, "devices_auto_connect_enabled")

    with allure.step("UI: открыть ИПМ и проверить окно авторизации (:8002)"):
        ipm_login_page.open()
        ipm_login_page.assert_auth_window()
        _attach_ui_state(ipm_login_page.page, "ipm_auth_window")

    with allure.step("UI: войти в ИПМ по табельному номеру"):
        ipm_login_page.login_with_tab_number(setup.tab_number)
        ipm_login_page.assert_logged_in(setup.suffix, tab_number=setup.tab_number)
        _attach_ui_state(ipm_login_page.page, "ipm_logged_in")
