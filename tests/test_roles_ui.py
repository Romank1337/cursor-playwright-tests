"""
Отдельный UI-тест для справочника ролей.
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
@allure.feature("Справочники")
@allure.story("Справочник ролей")
@allure.title("Пользователь может создать новую роль через модальное окно")
def test_create_role(login_page, roles_page, credentials):
    username, password = credentials
    unique_role_name = f"auto-role-{int(time.time())}"
    edited_role_name = f"edited-{unique_role_name}"
    allure.dynamic.parameter("role_name", unique_role_name)
    allure.dynamic.parameter("edited_role_name", edited_role_name)
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
                expect(login_page.login_input).to_be_visible(timeout=2_000)
                expect(login_page.password_input).to_be_visible(timeout=2_000)
                with allure.step("Повторить вход c логином admin"):
                    login_page.login("admin", password)
                    login_page.page.wait_for_timeout(2_000)
            _attach_ui_state(login_page.page, "after_login")

    with allure.step("Открытие страницы справочника ролей"):
        with allure.step("Подготовить URL с auth query-параметрами"):
            current_url = login_page.page.url
            parsed_current = urlparse(current_url)
            auth_query = dict(parse_qsl(parsed_current.query))

        with allure.step("Перейти на страницу ролей"):
            if auth_query:
                parsed_target = urlparse(roles_page.roles_url)
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
                roles_page.page.goto(target_url, wait_until="domcontentloaded")
            else:
                roles_page.open()

        with allure.step("Проверить, что страница ролей загружена"):
            roles_page.assert_loaded()
            _attach_ui_state(roles_page.page, "roles_page_loaded")

    with allure.step("Создание новой роли"):
        with allure.step("Нажать кнопку Добавить"):
            _attach_ui_state(roles_page.page, "before_add_role")

        with allure.step("Заполнить название роли и нажать Сохранить"):
            roles_page.create_role(unique_role_name)
            roles_page.page.wait_for_timeout(2_000)
            _attach_ui_state(roles_page.page, "after_role_save")

    with allure.step("Проверка, что новая роль отображается в списке"):
        roles_page.assert_role_visible(unique_role_name)
        _attach_ui_state(roles_page.page, "role_visible")

    with allure.step("Редактирование созданной роли"):
        with allure.step("Выбрать роль и нажать кнопку Редактировать"):
            roles_page.edit_role(unique_role_name, edited_role_name)
            _attach_ui_state(roles_page.page, "after_role_edit_save")

    with allure.step("Проверка, что роль обновлена в списке"):
        roles_page.assert_role_visible(edited_role_name)
        _attach_ui_state(roles_page.page, "edited_role_visible")

    with allure.step("Удаление отредактированной роли"):
        with allure.step("Выбрать роль и нажать кнопку Удалить"):
            roles_page.delete_role(edited_role_name)
            _attach_ui_state(roles_page.page, "after_role_delete")

    with allure.step("Проверка, что роль удалена из списка"):
        roles_page.assert_role_not_visible(edited_role_name)
        _attach_ui_state(roles_page.page, "role_deleted")
