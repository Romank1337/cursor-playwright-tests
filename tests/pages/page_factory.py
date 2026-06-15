"""
PageFactory: единая точка создания Page Object / Page Component.
"""

from playwright.sync_api import Page

from tests.pages.components.machine_state_form_component import MachineStateFormComponent
from tests.pages.ipm_login_page import IpmLoginPage
from tests.pages.login_page import LoginPage
from tests.pages.machine_params_page import MachineParamsPage
from tests.pages.roles_page import RolesPage


class PageFactory:
    @staticmethod
    def login_page(page: Page, login_url: str) -> LoginPage:
        return LoginPage(page=page, login_url=login_url)

    @staticmethod
    def machine_params_page(page: Page, machine_params_url: str) -> MachineParamsPage:
        return MachineParamsPage(page=page, machine_params_url=machine_params_url)

    @staticmethod
    def roles_page(page: Page, roles_url: str) -> RolesPage:
        return RolesPage(page=page, roles_url=roles_url)

    @staticmethod
    def ipm_login_page(page: Page, ipm_url: str) -> IpmLoginPage:
        return IpmLoginPage(page=page, ipm_url=ipm_url)

    @staticmethod
    def machine_state_form_component(page: Page) -> MachineStateFormComponent:
        return MachineStateFormComponent(page=page)
