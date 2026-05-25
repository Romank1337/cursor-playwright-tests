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
    def language_menu_button(self):
        # Кнопка вызова меню выбора языка на странице авторизации.
        return self.page.locator(
            "#root > div > div > div > form > div.header___uFci3 > button"
        )

    @property
    def language_select_button(self):
        # Вторая кнопка, которая появляется после первого клика.
        return self.page.locator(
            "#root > div > div > div > form > div.selectVisible___LSabj > div"
        )

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
        expect(self.language_menu_button).to_be_visible()
        expect(self.login_input).to_be_visible()
        expect(self.password_input).to_be_visible()
        expect(self.submit_button).to_be_visible()

    def switch_language_to_russian(self) -> None:
        # 1) Открываем блок выбора языка первой кнопкой.
        expect(self.language_menu_button).to_be_visible(timeout=20_000)
        self.language_menu_button.click()
        # 2) Нажимаем вторую кнопку, которая раскрывает список языков.
        expect(self.language_select_button).to_be_visible(timeout=20_000)
        self.language_select_button.click()
        # 3) Выбираем русский язык в выпадающем меню.
        ru_option = self.page.locator(
            "[role='menuitem']:has-text('Русский'), "
            ".ant-dropdown-menu-item:has-text('Русский'), "
            ".ant-select-item-option:has-text('Русский'), "
            "[role='menuitem']:has-text('Russian'), "
            ".ant-dropdown-menu-item:has-text('Russian'), "
            ".ant-select-item-option:has-text('Russian')"
        ).first
        expect(ru_option).to_be_visible(timeout=20_000)
        ru_option.click()

    def login(self, username: str, password: str) -> None:
        # Унифицированное действие "войти в систему".
        self.login_input.fill(username)
        self.password_input.fill(password)
        self.submit_button.click()

