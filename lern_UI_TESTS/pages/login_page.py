import re

from playwright.sync_api import Page, expect


class LoginPage:
    # Page Object инкапсулирует знания о странице логина:
    # URL, локаторы и действия. Тесты остаются короткими и читаемыми.
    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.url = f"{base_url}/user/login?redirect={base_url}/"

        # Для этой формы наиболее стабильны id-селекторы.
        self.username_input = page.locator("#login")
        self.password_input = page.locator("#password")
        self.submit_button = page.locator(
            "button.ant-btn.css-98hip3.ant-btn-primary.ant-btn-color-primary."
            "ant-btn-variant-solid.ant-btn-lg"
        )

    def open(self) -> None:
        # Переход на страницу логина.
        self.page.goto(self.url)

    def expect_opened(self) -> None:
        # Проверяем, что действительно на странице логина.
        # Через regex, потому что query-параметры могут меняться.
        expect(self.page).to_have_url(re.compile(r".*/user/login(\?.*)?$"), timeout=10_000)

        # Базовые smoke-проверки: ключевые элементы формы видимы.
        expect(self.username_input).to_be_visible()
        expect(self.password_input).to_be_visible()
        expect(self.submit_button).to_be_visible()

    def login(self, username: str, password: str) -> None:
        # Бизнес-действие: ввод кредов и отправка формы.
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.submit_button.click()

    def expect_success_redirect(self, base_url: str) -> None:
        # После успешной авторизации ожидаем переход на realtime-страницу.
        expect(self.page).to_have_url(f"{base_url}/monitoring/realtime", timeout=15_000)
