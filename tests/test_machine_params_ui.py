"""
UI-тесты страницы machineParams.
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
@allure.feature("Параметры оборудования")
@allure.story("Создание состояния")
@allure.title("Пользователь может создать новое состояние на странице machineParams")
def test_create_new_machine_state(login_page, machine_params_page, credentials):
    username, password = credentials
    unique_state_name = f"auto-{int(time.time())}"
    allure.dynamic.parameter("state_name", unique_state_name)
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
            login_page.page.wait_for_timeout(2_000)

        with allure.step("Проверить, что вход выполнен"):
            if "/user/login" in login_page.page.url.lower():
                # Фолбэк только если действительно остались на форме логина.
                expect(login_page.login_input).to_be_visible(timeout=2_000)
                expect(login_page.password_input).to_be_visible(timeout=2_000)
                with allure.step("Повторить вход c логином admin"):
                    login_page.login("admin", password)
                    login_page.page.wait_for_timeout(2_000)
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

    with allure.step("Создание нового состояния"):
        with allure.step("Открыть форму создания"):
            state_form = machine_params_page.open_create_state_form()
            _attach_ui_state(machine_params_page.page, "create_form_opened")

        with allure.step("Заполнить форму и нажать Сохранить"):
            state_form.create_state(unique_state_name)
            machine_params_page.page.wait_for_timeout(2_000)
            _attach_ui_state(machine_params_page.page, "after_save")

    with allure.step("Проверка нового состояния на текущей странице"):
        with allure.step("Проверить, что список состояний отображается после сохранения"):
            machine_params_page.assert_loaded()
            _attach_ui_state(machine_params_page.page, "before_assert_state")

        with allure.step(f"Проверить наличие состояния '{unique_state_name}' в таблице"):
            machine_params_page.assert_state_visible(unique_state_name)

    edited_state_name = f"redact-{unique_state_name}"
    allure.dynamic.parameter("edited_state_name", edited_state_name)

    with allure.step("Редактирование созданного состояния"):
        with allure.step(f"Открыть форму редактирования для '{unique_state_name}'"):
            edit_form = machine_params_page.open_edit_state_form(unique_state_name)
            _attach_ui_state(machine_params_page.page, "edit_form_opened")

        with allure.step(f"Изменить имя состояния на '{edited_state_name}' и сохранить"):
            edit_form.edit_state_name(edited_state_name)
            machine_params_page.page.wait_for_timeout(2_000)
            _attach_ui_state(machine_params_page.page, "after_edit_save")

    with allure.step("Проверка отредактированного состояния"):
        machine_params_page.assert_loaded()
        _attach_ui_state(machine_params_page.page, "before_assert_edited_state")
        machine_params_page.assert_state_visible(edited_state_name)

    with allure.step("Удаление отредактированного состояния"):
        with allure.step(f"Выделить '{edited_state_name}' и нажать Удалить"):
            machine_params_page.delete_state(edited_state_name)
            _attach_ui_state(machine_params_page.page, "after_delete_click")

        with allure.step("Подтвердить удаление кнопкой Да и проверить отсутствие состояния"):
            machine_params_page.assert_loaded()
            machine_params_page.assert_state_not_visible(edited_state_name)
            _attach_ui_state(machine_params_page.page, "after_delete_confirm")
