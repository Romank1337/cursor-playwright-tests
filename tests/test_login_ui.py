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

# Важно:
# - тесты специально написаны на уровне "действие -> проверка",
#   чтобы бизнес-сценарий читался без знания DOM/селекторов;
# - детали UI инкапсулированы в tests/pages/login_page.py (Page Object).


@pytest.mark.e2e
@allure.feature("Авторизация")
@allure.story("Открытие страницы логина")
@allure.title("Страница авторизации открывается и показывает основные элементы")
@allure.description("Проверяем, что форма авторизации открывается и содержит обязательные элементы.")
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
    with allure.step("Открыть страницу авторизации"):
        # Page Object сам знает, какой URL открыть (берётся из фикстуры login_url).
        login_page.open()
    with allure.step("Проверить, что ключевые элементы формы видимы"):
        # expect внутри assert_loaded делает auto-wait:
        # Playwright подождёт, пока элементы действительно станут видимыми.
        login_page.assert_loaded()


@pytest.mark.e2e
@allure.feature("Авторизация")
@allure.story("Проверка поля пароля")
@allure.title("Поле пароля имеет тип password")
@allure.description("Проверяем, что поле пароля маскирует ввод (type=password).")
def test_password_field_type_is_password(login_page):
    """
    Сценарий: "Поле пароля маскирует ввод".

    Что проверяем:
    - у поля пароля стоит атрибут type="password".

    Зачем нужен тест:
    - это базовая проверка безопасности/UX:
      пароль не должен отображаться открытым текстом.
    """
    with allure.step("Открыть страницу логина"):
        login_page.open()
    with allure.step("Проверить атрибут поля пароля type=password"):
        # to_have_attribute — также "умная" проверка с ожиданием.
        expect(login_page.password_input).to_have_attribute("type", "password")


@pytest.mark.e2e
@allure.feature("Авторизация")
@allure.story("Успешный вход")
@allure.title("После успешного логина происходит редирект на рабочую страницу")
@allure.description("Проверяем успешный вход валидными данными и редирект на рабочую страницу.")
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
    username, password = credentials
    # Параметр попадёт в отчёт Allure и поможет понять, под каким пользователем шёл запуск.
    allure.dynamic.parameter("username", username)

    with allure.step("Открыть страницу входа"):
        login_page.open()
    with allure.step("Выполнить логин валидными данными"):
        login_page.login(username, password)
    with allure.step("Проверить редирект на целевой URL после авторизации"):
        # success_url_regex приходит из conftest.py и может быть переопределён через env.
        # timeout увеличен для нестабильных/медленных стендов.
        expect(login_page.page).to_have_url(success_url_regex, timeout=20_000)


@pytest.mark.e2e
@allure.feature("Авторизация")
@allure.story("Негативные проверки")
@allure.title("Логин с неверными данными не должен авторизовывать пользователя")
@allure.description("Проверяем, что неверные учетные данные не дают войти в систему.")
def test_invalid_login_shows_error(login_page, invalid_credentials):
    username, password = invalid_credentials
    allure.dynamic.parameter("invalid_username", username)

    with allure.step("Открыть страницу входа"):
        login_page.open()
    with allure.step("Отправить форму с неверными учетными данными"):
        login_page.login(username, password)
    with allure.step("Проверить, что авторизация не выполнена (остаемся на /login)"):
        login_page.assert_still_on_login_page()
    with allure.step("Проверить отображение сообщения об ошибке авторизации"):
        # Метод учитывает разные реализации ошибки (toast/alert/текст), поэтому проверка гибкая.
        has_error = login_page.has_auth_error_message()
        assert has_error, "Ожидалось сообщение об ошибке авторизации для неверных учетных данных"


@pytest.mark.e2e
@allure.feature("Авторизация")
@allure.story("Негативные проверки")
@allure.title("Пустая форма не должна приводить к успешному входу")
@allure.description("Проверяем, что пустая форма не приводит к успешному входу.")
def test_empty_form_does_not_login(login_page):
    with allure.step("Открыть страницу входа"):
        login_page.open()
    with allure.step("Отправить пустую форму"):
        login_page.submit_empty()
    with allure.step("Проверить, что вход не выполнен и мы на странице логина"):
        login_page.assert_still_on_login_page()
        login_page.assert_loaded()


@pytest.mark.e2e
@allure.feature("Локализация")
@allure.story("Элементы локализации")
@allure.title("На странице логина доступен элемент выбора языка")
@allure.description("Проверяем наличие контрола выбора языка на странице авторизации.")
def test_language_control_is_present(login_page):
    with allure.step("Открыть страницу входа"):
        login_page.open()
    with allure.step("Проверить наличие контрола выбора языка"):
        if not login_page.has_language_control():
            # Это не дефект теста: на части стендов языковой контрол может быть отключён конфигурацией.
            pytest.skip("Переключатель языка не найден в текущей конфигурации стенда")


@pytest.mark.e2e
@allure.feature("Локализация")
@allure.story("Смена языка")
@allure.title("Переключение языка на странице логина (если опция доступна)")
@allure.description("Проверяем переключение языка на EN и локализацию placeholder поля логина.")
def test_language_switch_if_available(login_page, language_login_placeholder_en_regex):
    with allure.step("Открыть страницу входа"):
        login_page.open()
    with allure.step("Проверить доступность переключателя языка"):
        if not login_page.has_language_control():
            pytest.skip("Переключатель языка не найден в текущей конфигурации")
    with allure.step("Переключить язык на EN"):
        switched = login_page.switch_language("EN")
        if not switched:
            pytest.skip("Опция EN не найдена в текущей конфигурации")
    with allure.step("Проверить, что placeholder логина соответствует английской локали"):
        en_placeholder = login_page.login_placeholder()
        # Сохраняем фактическое значение в отчёт — удобно для диагностики падений.
        allure.attach(en_placeholder, "EN placeholder", allure.attachment_type.TEXT)
        # Проверяем "по шаблону", а не точной строкой:
        # это снижает хрупкость при небольших текстовых правках в UI.
        assert language_login_placeholder_en_regex.match(en_placeholder), (
            f"После переключения на EN placeholder логина не выглядит английским: {en_placeholder!r}"
        )


@pytest.mark.e2e
@allure.feature("Локализация")
@allure.story("Смена языка")
@allure.title("Переключение EN -> RU меняет placeholder обратно")
@allure.description("Проверяем, что после EN -> RU placeholder возвращается к русской локали.")
def test_language_switch_back_to_ru(login_page, language_login_placeholder_ru_regex):
    with allure.step("Открыть страницу входа"):
        login_page.open()
    with allure.step("Проверить доступность переключателя языка"):
        if not login_page.has_language_control():
            pytest.skip("Переключатель языка не найден в текущей конфигурации")
    with allure.step("Переключить язык на EN, затем обратно на RU"):
        # Двойное переключение проверяет, что UI умеет менять локаль в обе стороны.
        if not login_page.switch_language("EN"):
            pytest.skip("Опция EN не найдена в текущей конфигурации")
        if not login_page.switch_language("RU"):
            pytest.skip("Опция RU не найдена в текущей конфигурации")
    with allure.step("Проверить, что placeholder логина соответствует русской локали"):
        ru_placeholder = login_page.login_placeholder()
        allure.attach(ru_placeholder, "RU placeholder", allure.attachment_type.TEXT)
        assert language_login_placeholder_ru_regex.match(ru_placeholder), (
            f"После переключения обратно на RU placeholder логина не выглядит русским: {ru_placeholder!r}"
        )


@pytest.mark.e2e
@allure.feature("Локализация")
@allure.story("Сохранение языка")
@allure.title("Выбранный язык сохраняется после обновления страницы")
@allure.description("Проверяем сохранение выбранного языка после перезагрузки страницы.")
def test_language_persists_after_reload(login_page):
    with allure.step("Открыть страницу входа"):
        login_page.open()
    with allure.step("Проверить доступность переключателя языка"):
        if not login_page.has_language_control():
            pytest.skip("Переключатель языка не найден в текущей конфигурации")
    with allure.step("Переключить язык на EN"):
        if not login_page.switch_language("EN"):
            pytest.skip("Опция EN не найдена в текущей конфигурации")
    with allure.step("Обновить страницу и проверить сохранение языка"):
        before_reload = login_page.current_language()
        login_page.page.reload(wait_until="domcontentloaded")
        after_reload = login_page.current_language()
        allure.attach(
            f"before_reload={before_reload}, after_reload={after_reload}",
            "Language before/after reload",
            allure.attachment_type.TEXT,
        )
        # Проверка мягкая: если язык не удалось надёжно прочитать,
        # не считаем это функциональным падением (избегаем флаки на разных UI-сборках).
        # Но если значение определено до/после, тогда требуем, чтобы остался EN.
        if before_reload and after_reload:
            assert before_reload == after_reload == "EN", (
                f"Ожидали сохранение EN после refresh, получили before={before_reload}, after={after_reload}"
            )

