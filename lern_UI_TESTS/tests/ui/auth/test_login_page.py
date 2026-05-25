from pages.login_page import LoginPage


def test_login_page_smoke(page, base_url: str) -> None:
    # Arrange: создаем объект страницы.
    login_page = LoginPage(page=page, base_url=base_url)

    # Act: открываем логин.
    login_page.open()

    # Assert: убеждаемся, что форма отображается корректно.
    login_page.expect_opened()


def test_login_with_admin_credentials(page, base_url: str) -> None:
    # Первый практический сценарий: вводим логин/пароль и жмем кнопку входа.
    login_page = LoginPage(page=page, base_url=base_url)
    login_page.open()
    login_page.expect_opened()
    login_page.login(username="admin", password="123")
    login_page.expect_success_redirect(base_url=base_url)
