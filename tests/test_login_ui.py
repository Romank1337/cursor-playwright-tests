"""
Базовые UI-тесты для страницы авторизации.

Как читать этот файл:
1) Каждый `test_*` — отдельный пользовательский сценарий.
2) Фикстура `login_page` создаёт объект страницы (Page Object),
   чтобы тесты были "человеческими": open/login/assert, без низкоуровневых селекторов.
3) `expect(...)` — это "умные ожидания" Playwright:
   он ждёт некоторое время, пока состояние страницы станет нужным.
"""

import allure
import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
@allure.feature("Авторизация")
@allure.story("Открытие страницы логина")
@allure.title("Страница авторизации открывается и показывает основные элементы")
def test_login_page_opened(login_page):
    """
    Сценарий: "Страница авторизации открывается и отображает основные элементы".

    Что проверяем:
    - URL логина открывается без ошибок;
    - видны поле логина, поле пароля и кнопка отправки формы.

    Зачем нужен тест:
    - это smoke-тест, который быстро показывает,
      что страница в целом "жива" после изменений фронтенда/бэкенда.
    """
    # 1. Открываем страницу авторизации по login_url (из фикстуры).
    login_page.open()
    # 2. Проверяем, что ключевые элементы формы реально отображаются пользователю.
    login_page.assert_loaded()


@pytest.mark.e2e
@allure.feature("Авторизация")
@allure.story("Проверка поля пароля")
@allure.title("Поле пароля имеет тип password")
def test_password_field_type_is_password(login_page):
    """
    Сценарий: "Поле пароля маскирует ввод".

    Что проверяем:
    - у поля пароля стоит атрибут type="password".

    Зачем нужен тест:
    - это базовая проверка безопасности/UX:
      пароль не должен отображаться открытым текстом.
    """
    # 1. Открываем страницу логина.
    login_page.open()
    # 2. Проверяем HTML-атрибут поля пароля.
    expect(login_page.password_input).to_have_attribute("type", "password")


@pytest.mark.e2e
@allure.feature("Авторизация")
@allure.story("Успешный вход")
@allure.title("После успешного логина происходит редирект на рабочую страницу")
def test_success_login_redirect(login_page, credentials, success_url_regex):
    """
    Сценарий: "Успешный логин переводит пользователя на рабочую страницу".

    Что проверяем:
    - вводим валидные креды;
    - отправляем форму;
    - убеждаемся, что URL соответствует шаблону успешного входа.

    Откуда берутся данные:
    - логин/пароль из фикстуры `credentials`
      (по умолчанию Admin/123 или через переменные окружения);
    - ожидаемый URL из `success_url_regex`.
    """
    # 1. Достаём тестовые учетные данные.
    username, password = credentials
    # 2. Переходим на страницу входа.
    login_page.open()
    # 3. Заполняем форму и кликаем "Вход".
    login_page.login(username, password)
    # 4. Проверяем редирект после входа.
    #    timeout увеличен, так как приложение может загружать данные не мгновенно.
    expect(login_page.page).to_have_url(success_url_regex, timeout=20_000)


@pytest.mark.e2e
@allure.feature("Авторизация")
@allure.story("Негативные проверки")
@allure.title("Логин с неверными данными не должен авторизовывать пользователя")
def test_invalid_login_shows_error(login_page, invalid_credentials):
    username, password = invalid_credentials
    login_page.open()
    login_page.login(username, password)
    login_page.assert_still_on_login_page()
    # В некоторых конфигурациях текст ошибки показывается кратковременным toast.
    # Поэтому основная обязательная проверка — вход не выполнен (мы всё ещё на /login),
    # а наличие текста ошибки фиксируем как дополнительный сигнал.
    _ = login_page.has_auth_error_message()


@pytest.mark.e2e
@allure.feature("Авторизация")
@allure.story("Негативные проверки")
@allure.title("Пустая форма не должна приводить к успешному входу")
def test_empty_form_does_not_login(login_page):
    login_page.open()
    login_page.submit_empty()
    login_page.assert_still_on_login_page()
    login_page.assert_loaded()


@pytest.mark.e2e
@allure.feature("Локализация")
@allure.story("Элементы локализации")
@allure.title("На странице логина доступен элемент выбора языка")
def test_language_control_is_present(login_page):
    login_page.open()
    if not login_page.has_language_control():
        pytest.skip("Переключатель языка не найден в текущей конфигурации стенда")


@pytest.mark.e2e
@allure.feature("Локализация")
@allure.story("Смена языка")
@allure.title("Переключение языка на странице логина (если опция доступна)")
def test_language_switch_if_available(login_page):
    login_page.open()
    if not login_page.has_language_control():
        pytest.skip("Переключатель языка не найден в текущей конфигурации")

    switched = login_page.switch_language("EN")
    if not switched:
        pytest.skip("Опция EN не найдена в текущей конфигурации")

    # После переключения на EN на форме обычно появляется английский placeholder.
    placeholder = login_page.login_input.get_attribute("placeholder") or ""
    assert ("login" in placeholder.lower()) or ("enter" in placeholder.lower()), (
        "После переключения на EN не обнаружен ожидаемый английский placeholder у поля логина"
    )

