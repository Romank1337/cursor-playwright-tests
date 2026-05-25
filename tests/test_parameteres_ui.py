"""
Отдельный UI-тест для перехода на вкладку "Параметры" страницы machineParams.
"""

import time
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import allure
import pytest
from playwright.sync_api import expect


def _attach_ui_state(page, name: str) -> None:
    allure.attach(page.url, name=f"{name}:url", attachment_type=allure.attachment_type.TEXT)
    allure.attach(
        page.screenshot(full_page=True),
        name=f"{name}:screenshot",
        attachment_type=allure.attachment_type.PNG,
    )


@pytest.mark.e2e
@pytest.mark.parameteres
@allure.feature("Параметры оборудования")
@allure.story("Вкладка Параметры")
@allure.title("Пользователь может открыть вкладку Параметры на странице machineParams")
def test_parameteres(login_page, machine_params_page, credentials):
    username, password = credentials
    unique_parameter_name = f"auto-param-{int(time.time())}"
    edited_parameter_name = f"redact-{unique_parameter_name}"
    allure.dynamic.parameter("parameter_name", unique_parameter_name)
    allure.dynamic.parameter("edited_parameter_name", edited_parameter_name)
    allure.dynamic.parameter("login", username)

    with allure.step("Авторизация"):
        with allure.step("Открыть страницу логина"):
            login_page.open()
            _attach_ui_state(login_page.page, "login_page_opened")

        with allure.step("Переключить язык интерфейса на русский"):
            login_page.switch_language_to_russian()
            _attach_ui_state(login_page.page, "language_switched")

        with allure.step("Выполнить вход под тестовым пользователем"):
            login_page.login(username, password)
            login_page.page.wait_for_timeout(10_000)

        with allure.step("Проверить, что вход выполнен"):
            if "/user/login" in login_page.page.url.lower():
                # Фолбэк только если действительно остались на форме логина.
                expect(login_page.login_input).to_be_visible(timeout=20_000)
                expect(login_page.password_input).to_be_visible(timeout=20_000)
                with allure.step("Повторить вход c логином admin"):
                    login_page.login("admin", password)
                    login_page.page.wait_for_timeout(10_000)
            _attach_ui_state(login_page.page, "after_login")

    with allure.step("Открытие страницы machineParams"):
        with allure.step("Подготовить URL с auth query-параметрами"):
            current_url = login_page.page.url
            parsed_current = urlparse(current_url)
            auth_query = dict(parse_qsl(parsed_current.query))

        with allure.step("Перейти на страницу machineParams"):
            if auth_query:
                parsed_target = urlparse(machine_params_page.machine_params_url)
                merged_query = dict(parse_qsl(parsed_target.query))
                merged_query.update(auth_query)
                target_url = urlunparse(
                    (
                        parsed_target.scheme,
                        parsed_target.netloc,
                        parsed_target.path,
                        parsed_target.params,
                        urlencode(merged_query),
                        parsed_target.fragment,
                    )
                )
                machine_params_page.page.goto(target_url, wait_until="domcontentloaded")
            else:
                machine_params_page.open()

        with allure.step("Проверить, что таблица состояний загружена"):
            machine_params_page.assert_loaded()
            _attach_ui_state(machine_params_page.page, "machine_params_loaded")

    with allure.step("Переход во вкладку Параметры"):
        machine_params_page.open_parameters_tab()
        expect(
            machine_params_page.page.locator("span.dx-tab-text", has_text="Параметры").first
        ).to_be_visible(timeout=20_000)
        _attach_ui_state(machine_params_page.page, "parameters_tab_opened")

    with allure.step("Создание нового параметра"):
        with allure.step("Открыть форму создания параметра"):
            parameter_form = machine_params_page.open_create_parameter_form()
            _attach_ui_state(machine_params_page.page, "parameter_form_opened")

        with allure.step("Заполнить форму и сохранить параметр"):
            parameter_form.create_parameter(unique_parameter_name)
            machine_params_page.page.wait_for_timeout(10_000)
            _attach_ui_state(machine_params_page.page, "after_parameter_save")

    with allure.step("Проверка нового параметра"):
        machine_params_page.open_parameters_tab()
        machine_params_page.assert_parameter_visible(unique_parameter_name)
        _attach_ui_state(machine_params_page.page, "parameter_visible")

    with allure.step("Редактирование созданного параметра"):
        with allure.step(f"Открыть форму редактирования для '{unique_parameter_name}'"):
            edit_form = machine_params_page.open_edit_parameter_form(unique_parameter_name)
            _attach_ui_state(machine_params_page.page, "parameter_edit_form_opened")

        with allure.step(f"Изменить имя параметра на '{edited_parameter_name}' и сохранить"):
            edit_form.edit_parameter_name(edited_parameter_name)
            machine_params_page.page.wait_for_timeout(10_000)
            _attach_ui_state(machine_params_page.page, "after_parameter_edit_save")

    with allure.step("Проверка отредактированного параметра"):
        machine_params_page.open_parameters_tab()
        machine_params_page.assert_parameter_visible(edited_parameter_name)
        _attach_ui_state(machine_params_page.page, "edited_parameter_visible")

    with allure.step("Удаление отредактированного параметра"):
        with allure.step(f"Выделить '{edited_parameter_name}' и нажать Удалить"):
            machine_params_page.open_parameters_tab()
            machine_params_page.delete_state(edited_parameter_name)
            _attach_ui_state(machine_params_page.page, "after_parameter_delete_click")

        with allure.step("Проверить, что параметр удален"):
            machine_params_page.open_parameters_tab()
            machine_params_page.assert_state_not_visible(edited_parameter_name)
            _attach_ui_state(machine_params_page.page, "after_parameter_delete_confirm")
