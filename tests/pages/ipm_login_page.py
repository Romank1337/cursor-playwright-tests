"""
Page Object для окна авторизации ИПМ (http://localhost:8002).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from playwright.sync_api import Page, expect


@dataclass(frozen=True)
class IpmLoginPage:
    page: Page
    ipm_url: str

    _AUTH_URL_RE = re.compile(r"/imp/(login|unauthorized-device)")
    _LOGIN_URL_RE = re.compile(r"/imp/login")
    _TAB_INPUT = "input[name='worker_tabNum'], input[type='number']"
    _IPM_RADIO = "input[type='radio'][value='ipm']"
    _LOGIN_BTN = re.compile(r"Вход|Войти|OK|Enter", re.I)

    def open(self) -> None:
        self.page.goto(self.ipm_url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(1500)

    def assert_auth_window(self) -> None:
        expect(self.page).to_have_url(self._AUTH_URL_RE, timeout=15_000)
        if "/unauthorized-device" in self.page.url:
            self.page.wait_for_timeout(1500)
            self.open()
        expect(self.page).to_have_url(self._LOGIN_URL_RE, timeout=15_000)

    def select_ipm_mode(self) -> None:
        ipm_radio = self.page.locator(self._IPM_RADIO)
        if ipm_radio.count():
            ipm_radio.check(force=True)
            self.page.wait_for_timeout(400)

    def fill_tab_number(self, tab_number: str) -> None:
        tab_input = self.page.locator(self._TAB_INPUT).first
        expect(tab_input).to_be_visible(timeout=10_000)
        tab_input.fill(tab_number)

    def submit_login(self) -> None:
        login_btn = self.page.locator("button:visible").filter(has_text=self._LOGIN_BTN).first
        if login_btn.count() == 0:
            login_btn = self.page.locator("button:visible").first
        login_btn.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2500)

    def login_with_tab_number(self, tab_number: str) -> None:
        self.assert_auth_window()
        self.select_ipm_mode()
        self.fill_tab_number(tab_number)
        self.submit_login()

    def assert_logged_in(self, setup_suffix: str, *, tab_number: str | None = None) -> None:
        body = self.page.locator("body").inner_text()
        markers = (
            f"WR{setup_suffix}",
            f"M{setup_suffix}",
            tab_number or setup_suffix,
        )
        if not any(marker in body for marker in markers if marker):
            raise AssertionError(
                "После входа в ИПМ не найдены маркеры персонала/станка на экране: "
                f"{', '.join(m for m in markers if m)}"
            )
