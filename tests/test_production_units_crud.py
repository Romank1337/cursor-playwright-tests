"""
Новый CRUD-сценарий: Production structure → Production units (ProductionUnitsCRUD).

Сценарий: создать подразделение → проверить создание → переименовать → удалить.
"""

from __future__ import annotations

import time

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
@pytest.mark.production_units_crud
@testit.nameSpace("UI/Smoke")
@testit.className("ProductionUnitsCRUD")
@testit.externalId("ui.production_units_crud.full_crud")
@testit.displayName("Создать подразделение, переименовать и удалить production unit")
@allure.feature("Справочники")
@allure.story("Production units / Full CRUD")
@allure.title("Создать подразделение, переименовать и удалить production unit")
@allure.description(
    "Полный CRUD подразделения (Production unit): логин → переключение языка на RU → "
    "/list/production-structure?tab=productionUnits → Code/Name/Type/Parent → Save + Apply → "
    "проверка на карточке и в списке → переименовать Name → проверить новое имя → "
    "открыть карточку по id → Delete на карточке → подтвердить «Удалить» → запись отсутствует в списке."
)
def test_production_units_crud(login_page, production_units_page, credentials):
    username, password = credentials
    suffix = str(int(time.time()))
    unique_code = f"APU-{suffix}"[:18]
    unique_name = f"auto-pu-{suffix}"
    renamed_name = f"redact-auto-pu-{suffix}"
    allure.dynamic.parameter("production_unit_code", unique_code)
    allure.dynamic.parameter("production_unit_name", unique_name)
    allure.dynamic.parameter("renamed_production_unit_name", renamed_name)
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

    with allure.step("Открыть раздел Production units"):
        production_units_page.open()
        production_units_page.assert_loaded()
        _attach_ui_state(production_units_page.page, "production_units_list_opened")

    with allure.step("Создать новое подразделение"):
        assert production_units_page.open_create_form(), "Не удалось открыть форму создания"
        _attach_ui_state(production_units_page.page, "create_form_opened")
        production_units_page.fill_code_and_name(unique_code, unique_name)
        t_ok, p_ok, s_ok = production_units_page.fill_mandatory_selects_for_new_unit()
        allure.attach(
            f"type={t_ok}, parent={p_ok}, status={s_ok}",
            "Mandatory selects",
            allure.attachment_type.TEXT,
        )
        assert t_ok and p_ok, "Не удалось выбрать Type и/или Parent (TreeSelect)"
        unit_id = production_units_page.save_until_persisted()
        if not unit_id or unit_id == "0":
            unit_id = production_units_page.recover_unit_id_from_list(unique_code, unique_name)
        allure.attach(str(unit_id), "unit id after create", allure.attachment_type.TEXT)
        assert unit_id and unit_id != "0", (
            "Не удалось сохранить подразделение (нет id в URL и не найдена строка в списке)"
        )
        _attach_ui_state(production_units_page.page, "after_create_save")

    with allure.step("Проверить создание подразделения на карточке"):
        production_units_page.open_unit_by_id(unit_id)
        expect(production_units_page.page.locator("#ProductionUnit_Code")).to_have_value(
            unique_code, timeout=15_000
        )
        expect(production_units_page.page.locator("#ProductionUnit_Name")).to_have_value(
            unique_name, timeout=15_000
        )
        _attach_ui_state(production_units_page.page, "created_unit_card_verified")

    with allure.step("Проверить создание подразделения в списке"):
        assert production_units_page.wait_until_unit_in_table(unit_id, unique_code, unique_name), (
            f"Подразделение не найдено в списке: id={unit_id}, code={unique_code}, name={unique_name}"
        )
        _attach_ui_state(production_units_page.page, "created_unit_list_verified")

    with allure.step(f"Переименовать подразделение: '{unique_name}' → '{renamed_name}'"):
        production_units_page.open_unit_by_id(unit_id)
        production_units_page.page.locator("#ProductionUnit_Name").fill(renamed_name)
        production_units_page.save_form()
        production_units_page.apply_changes_if_present()
        _attach_ui_state(production_units_page.page, "after_rename_save")

    with allure.step("Проверить новое имя подразделения"):
        production_units_page.open_unit_by_id(unit_id)
        expect(production_units_page.page.locator("#ProductionUnit_Name")).to_have_value(
            renamed_name, timeout=15_000
        )
        assert production_units_page.wait_until_unit_in_table(unit_id, unique_code, renamed_name), (
            f"Переименованное подразделение не найдено в списке: id={unit_id}, code={unique_code}, name={renamed_name}"
        )
        _attach_ui_state(production_units_page.page, "renamed_unit_verified")

    with allure.step("Удалить подразделение с карточки"):
        assert production_units_page.delete_unit_from_card_and_confirm(unit_id), (
            "Не удалось удалить подразделение с карточки (Delete → подтверждение)"
        )
        _attach_ui_state(production_units_page.page, "after_delete_confirmed")

    with allure.step("Проверить, что подразделение удалено"):
        assert production_units_page.wait_until_unit_not_in_table(
            unit_id, unique_code, renamed_name
        ), f"Подразделение всё ещё в списке после удаления: id={unit_id}, code={unique_code}"
        production_units_page.open_unit_by_id(unit_id)
        if production_units_page.current_unit_id() == unit_id:
            try:
                saved_code = production_units_page.page.locator("#ProductionUnit_Code").input_value()
            except Exception:
                saved_code = ""
            assert saved_code != unique_code, (
                f"Карточка подразделения {unique_code} всё ещё доступна после удаления"
            )
        _attach_ui_state(production_units_page.page, "deleted_unit_verified")
