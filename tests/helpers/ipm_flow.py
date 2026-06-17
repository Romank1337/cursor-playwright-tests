"""Общие шаги подготовки и входа в ИПМ."""

from __future__ import annotations

from tests.api.ipm_setup_client import IpmBackendSetup, prepare_ipm_backend
from tests.pages.devices_page import DevicesPage
from tests.pages.ipm_login_page import IpmLoginPage
from tests.pages.login_page import LoginPage


def prepare_and_login_ipm(
    *,
    login_page: LoginPage,
    devices_page: DevicesPage,
    ipm_login_page: IpmLoginPage,
    username: str,
    password: str,
    web_client_api_url: str,
    web_api_user_id: str,
    ipm_dept_id: int,
    ipm_worker_role_id: int,
) -> IpmBackendSetup:
    setup = prepare_ipm_backend(
        base_url=web_client_api_url,
        user_id=web_api_user_id,
        dept_id=ipm_dept_id,
        worker_role_id=ipm_worker_role_id,
    )
    login_page.open()
    login_page.login(username, password)
    login_page.page.wait_for_timeout(1_500)
    devices_page.open()
    devices_page.assert_loaded()
    devices_page.enable_auto_connect_new_devices()
    ipm_login_page.open()
    ipm_login_page.login_with_tab_number(setup.tab_number)
    ipm_login_page.assert_logged_in(setup.suffix, tab_number=setup.tab_number)
    return setup
