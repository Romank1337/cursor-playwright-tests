"""
Page Object для страницы авторизации.

Зачем это нужно:
- здесь собраны все знания о странице (селекторы и действия);
- тесты используют методы этого класса и не зависят от деталей DOM;
- если поменяется верстка/селекторы, обычно достаточно правок только в этом файле.
"""

import re
from dataclasses import dataclass

from playwright.sync_api import Page, expect


@dataclass(frozen=True)
class LoginPage:
    page: Page
    login_url: str

    @property
    def login_input(self):
        # Селектор поля логина из реальной формы.
        return self.page.locator("#login")

    @property
    def password_input(self):
        # Селектор поля пароля.
        return self.page.locator("#password")

    @property
    def submit_button(self):
        # Кнопка отправки формы авторизации.
        return self.page.locator("button[type='submit']")

    @property
    def settings_button(self):
        # Кнопка настроек на форме логина (обычно открывает параметры языка).
        return self.page.locator(
            "button:has([aria-label='setting']), button:has(.anticon-setting), .button___SpWF4"
        ).first

    @property
    def language_badge(self):
        # Текущий язык на форме (например, RU/EN).
        return self.page.locator("text=/\\b(RU|EN)\\b/").first

    def open(self) -> None:
        # Переходим на URL логина и ждём базовой готовности DOM.
        self.page.goto(self.login_url, wait_until="domcontentloaded")

    def assert_loaded(self) -> None:
        # Проверяем видимость ключевых элементов формы входа.
        expect(self.login_input).to_be_visible()
        expect(self.password_input).to_be_visible()
        expect(self.submit_button).to_be_visible()

    def login(self, username: str, password: str) -> None:
        # Унифицированное действие "войти в систему".
        self.login_input.fill(username)
        self.password_input.fill(password)
        self.submit_button.click()

    def submit_empty(self) -> None:
        # Отправка пустой формы (проверка валидации/блокировки входа).
        self.submit_button.click()

    def assert_still_on_login_page(self) -> None:
        # После неуспешной авторизации URL должен оставаться в зоне /login.
        expect(self.page).to_have_url(re.compile(r".*/user/login.*"), timeout=10_000)

    def has_auth_error_message(self) -> bool:
        # Проверка на типовое сообщение об ошибке авторизации.
        # В разных сборках это может быть toast/alert и текст может немного отличаться.
        self.page.wait_for_timeout(700)
        error_candidates = [
            self.page.get_by_text(re.compile(r"неверн.*(парол|имя|данн)", re.I)),
            self.page.get_by_text(re.compile(r"(invalid|wrong).*(password|user|credential)", re.I)),
            self.page.locator("[role='alert'], .ant-notification-notice, .ant-message-notice").first,
        ]
        for loc in error_candidates:
            if loc.count() > 0 and loc.first.is_visible():
                return True
        return False

    def has_language_control(self) -> bool:
        # На некоторых конфигурациях язык видно сразу, на некоторых — через кнопку настроек.
        self.page.wait_for_timeout(200)
        return self.language_badge.count() > 0 or self.settings_button.count() > 0

    def switch_language(self, target: str) -> bool:
        """
        Пытается переключить язык на target (`RU` или `EN`).
        Возвращает True, если удалось кликнуть по нужной опции.
        """
        if self.settings_button.count() > 0:
            self.settings_button.click()
            self.page.wait_for_timeout(200)

        option = self.page.get_by_text(target, exact=True).first
        if option.count() == 0:
            return False

        option.click()
        self.page.wait_for_timeout(300)
        return True

