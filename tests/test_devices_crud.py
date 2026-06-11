"""
Новый CRUD-сценарий: Directories → Devices (DevicesCRUD).

UI устройств — список .ant-list-item (не таблица как в Production units).
Сценарий повторяет проверенные шаги из test_devices_crud_ui.
"""

from __future__ import annotations

import os
import time

os.environ["HEADLESS"] = "true"

import allure
import pytest
from playwright.sync_api import expect

from tests.testit_compat import testit


def _attach_ui_state(page, name: str) -> None:
    allure.attach(page.url, name=f"{name}:url", attachment_type=allure.attachment_type.TEXT)
    allure.attach(
        page.screenshot(full_page=True),
        name=f"{name}:screenshot",
        attachment_type=allure.attachment_type.PNG,
    )


@pytest.mark.e2e
@pytest.mark.devices_crud
@testit.nameSpace("UI/Smoke")
@testit.className("DevicesCRUD")
@testit.externalId("ui.devices_crud.full_crud")
@testit.displayName("Создать устройство, переименовать и удалить")
@allure.feature("Справочники")
@allure.story("Devices / Full CRUD")
@allure.title("Создать устройство, переименовать и удалить")
@allure.description(
    "Полный CRUD устройства (Devices): логин → переключение языка на RU → "
    "/list/devices → Name/UID/Type → Save + Apply → проверка в списке и форме → "
    "переименовать Name → проверить → удалить из списка/карточки → подтвердить → "
    "запись отсутствует в списке."
)
def test_devices_crud(login_page, devices_page, credentials):
    username, password = credentials
    suffix = str(int(time.time()))
    unique_name = f"auto-device-{suffix}"
    unique_uid = f"auto-uid-{suffix}"
    renamed_name = f"redact-auto-device-{suffix}"
    allure.dynamic.parameter("device_name", unique_name)
    allure.dynamic.parameter("device_uid", unique_uid)
    allure.dynamic.parameter("renamed_device_name", renamed_name)
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

    with allure.step("Открыть раздел Devices"):
        devices_page.open()
        devices_page.assert_loaded()
        _attach_ui_state(devices_page.page, "devices_list_opened")

    with allure.step("Создать новое устройство"):
        assert devices_page.open_create_form(), "Не удалось открыть форму создания"
        _attach_ui_state(devices_page.page, "create_form_opened")
        devices_page.fill_device_form(
            name=unique_name,
            uid=unique_uid,
            comment=f"auto-comment-{suffix}",
        )
        devices_page.select_device_type_if_needed()
        devices_page.save_and_apply(refresh_list=True)
        _attach_ui_state(devices_page.page, "after_create_save")

    with allure.step("Проверить создание устройства в списке"):
        assert devices_page.wait_until_device_found_by_search(unique_name), (
            f"Устройство не найдено в списке: name={unique_name}"
        )
        _attach_ui_state(devices_page.page, "created_device_list_verified")

    with allure.step("Проверить создание устройства в форме"):
        assert devices_page.open_device_edit_form_by_name(unique_name, search=False), (
            f"Не удалось открыть форму редактирования: {unique_name}"
        )
        expect(devices_page.name_input).to_have_value(unique_name, timeout=15_000)
        expect(devices_page.uid_input).to_have_value(unique_uid, timeout=15_000)
        _attach_ui_state(devices_page.page, "created_device_form_verified")

    with allure.step(f"Переименовать устройство: '{unique_name}' → '{renamed_name}'"):
        devices_page.name_input.fill(renamed_name)
        devices_page.save_and_apply(refresh_list=True)
        _attach_ui_state(devices_page.page, "after_rename_save")

    with allure.step("Проверить новое имя устройства в списке"):
        assert devices_page.wait_until_device_found_by_search(renamed_name), (
            f"Переименованное устройство не найдено в списке: name={renamed_name}"
        )
        _attach_ui_state(devices_page.page, "renamed_device_verified")

    with allure.step("Удалить устройство"):
        assert devices_page.delete_device_and_confirm(renamed_name, search=False), (
            "Не удалось удалить устройство (⋯ → Удалить → Подтвердить удаление)"
        )
        _attach_ui_state(devices_page.page, "after_delete_confirmed")

    with allure.step("Проверить, что устройство удалено"):
        devices_page.refresh_list_once()
        devices_page.search_device_in_list(renamed_name)
        assert not devices_page.device_exists_in_list(renamed_name), (
            f"Устройство всё ещё в списке после удаления: name={renamed_name}"
        )
        _attach_ui_state(devices_page.page, "deleted_device_verified")
