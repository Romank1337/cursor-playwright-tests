"""
Page Object для страницы авторизации.

Зачем это нужно:
- здесь собраны все знания о странице (селекторы и действия);
- тесты используют методы этого класса и не зависят от деталей DOM;
- если поменяется верстка/селекторы, обычно достаточно правок только в этом файле.
"""

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

