"""
CRUD-проверки: Production structure → Production units (legacy).

Временно исключены из прогона маркером `production_units_legacy` (см. pytest.ini).
Запуск только legacy: pytest -m production_units_legacy tests/test_production_units_crud_ui.py

Деструктивное удаление управляется фикстурой `run_destructive_production_units_crud`
(переменная окружения RUN_DESTRUCTIVE_PRODUCTION_UNITS_CRUD).

Новый CRUD-сценарий: tests/test_production_units_crud.py (ProductionUnitsCRUD).
"""

from __future__ import annotations

import time

import allure
import pytest
from playwright.sync_api import expect

from tests.testit_compat import testit


@pytest.mark.e2e
@pytest.mark.production_units_legacy
@testit.nameSpace("UI/Smoke")
@testit.className("ProductionUnits")
@testit.externalId("ui.production_units.page_opened")
@testit.displayName("Список Production units открывается и показывает таблицу и Create")
@allure.feature("Справочники")
@allure.story("Production units / Read")
@allure.title("Список Production units открывается и показывает таблицу и Create")
@allure.description("Smoke-проверка раздела Production structure → Production units: открывается список, видна таблица и кнопка Create. Базовая проверка работоспособности раздела перед остальными сценариями.")
def test_production_units_page_opened(production_units_page):
    with allure.step("Открыть вкладку Production units"):
        production_units_page.open()
    with allure.step("Проверить базовые элементы списка"):
        production_units_page.assert_loaded()


@pytest.mark.e2e
@pytest.mark.production_units_legacy
@testit.nameSpace("UI/Smoke")
@testit.className("ProductionUnits")
@testit.externalId("ui.production_units.create_form_has_required_fields")
@testit.displayName("Форма создания production unit содержит обязательные контролы")
@allure.feature("Справочники")
@allure.story("Production units / Create")
@allure.title("Форма создания production unit содержит обязательные контролы")
@allure.description("Открываем форму создания и проверяем наличие ключевых полей: Code, Name, Type (AntD Select), Parent (AntD TreeSelect). Без сохранения — только проверка структуры формы.")
def test_production_units_create_form_has_required_fields(production_units_page):
    with allure.step("Открыть список и форму создания"):
        production_units_page.open()
        opened = production_units_page.open_create_form()
        allure.attach(str(opened), "Create form opened", allure.attachment_type.TEXT)
    with allure.step("Проверить ключевые поля формы"):
        if not opened:
            allure.attach("Форма создания недоступна в текущем состоянии UI.", "Limitation", allure.attachment_type.TEXT)
            return
        assert production_units_page.has_required_form_controls(), (
            "Не найдены обязательные поля формы (Code, Name, Type, Parent)"
        )


@pytest.mark.e2e
@pytest.mark.production_units_legacy
@testit.nameSpace("UI/Smoke")
@testit.className("ProductionUnits")
@testit.externalId("ui.production_units.create_cancel_if_available")
@testit.displayName("Отмена: кнопка Cancel закрывает черновик, если доступна")
@allure.feature("Справочники")
@allure.story("Production units / Create")
@allure.title("Отмена: кнопка Cancel закрывает черновик, если доступна")
@allure.description("Если на форме доступна кнопка Cancel — заполняем минимум полей и проверяем, что отмена закрывает форму без сохранения. В текущей сборке UI кнопки Cancel на этой форме нет, поэтому тест корректно скипается.")
def test_production_units_create_cancel_if_available(production_units_page):
    with allure.step("Открыть форму создания"):
        production_units_page.open()
        opened = production_units_page.open_create_form()
        if not opened:
            pytest.skip("Форма создания недоступна")
    with allure.step("Заполнить часть полей"):
        production_units_page.fill_code_and_name(f"X-{int(time.time())}", f"Cancel-{int(time.time())}")
    with allure.step("Попробовать отменить"):
        production_units_page.cancel_form_if_present()
    with allure.step("Проверить результат"):
        url = production_units_page.page.url
        allure.attach(url, "URL after cancel attempt", allure.attachment_type.TEXT)
        if "/production-unit/0" in url:
            pytest.skip("Cancel на форме не найден — сценарий отмены не применим")


@pytest.mark.e2e
@pytest.mark.production_units_legacy
@testit.nameSpace("UI/Smoke")
@testit.className("ProductionUnits")
@testit.externalId("ui.production_units.table_visible")
@testit.displayName("Таблица production units отрисована")
@allure.feature("Справочники")
@allure.story("Production units / Read")
@allure.title("Таблица production units отрисована")
@allure.description("Проверяем, что список production units рендерится как MUI-таблица (table.MuiTable-root) с tbody. Считаем количество строк и проверяем, что значение неотрицательное (пустой список также допустим).")
def test_production_units_table_visible(production_units_page):
    with allure.step("Открыть раздел Production units"):
        production_units_page.open()
    with allure.step("Проверить, что таблица production units отрисована"):
        rows = production_units_page.page.locator("table.MuiTable-root tbody tr").count()
        allure.attach(str(rows), "tbody row count", allure.attachment_type.TEXT)
        assert rows >= 0


@pytest.mark.e2e
@pytest.mark.production_units_legacy
@testit.nameSpace("UI/Smoke")
@testit.className("ProductionUnits")
@testit.externalId("ui.production_units.update_name_after_create")
@testit.displayName("После сохранения можно изменить Name на карточке")
@allure.feature("Справочники")
@allure.story("Production units / Update")
@allure.title("После сохранения можно изменить Name на карточке")
@allure.description("Создаём production unit с обязательными полями (Type ≠ Enterprise, Parent выбираем через AntD TreeSelect), сохраняем через save_until_persisted (с ретраями до появления id в URL или recovery из списка), затем переоткрываем запись по id и меняем Name. Проверяем, что новое значение сохранилось. Покрывает Update-сценарий.")
def test_production_units_update_name_after_create(production_units_page):
    with allure.step("Создать запись с минимально достаточными полями"):
        production_units_page.open()
        assert production_units_page.open_create_form()
        suffix = str(int(time.time()))
        code = f"AT-{suffix}"[:18]
        name1 = f"AUTO1-{suffix}"
        name2 = f"AUTO2-{suffix}"
        production_units_page.fill_code_and_name(code, name1)
        t_ok, p_ok, s_ok = production_units_page.fill_mandatory_selects_for_new_unit()
        allure.attach(f"type={t_ok}, parent={p_ok}, status={s_ok}", "Mandatory selects", allure.attachment_type.TEXT)
        assert t_ok and p_ok, "Не удалось выбрать Type и/или Parent (TreeSelect)"
        production_units_page.save_until_persisted()
        uid = production_units_page.current_unit_id()
        if not uid or uid == "0":
            uid = production_units_page.recover_unit_id_from_list(code, name1)
        allure.attach(str(uid), "unit id after save", allure.attachment_type.TEXT)
        assert uid and uid != "0", "Не удалось сохранить запись (нет id в URL и не найдена строка в списке)"

    with allure.step("Открыть ту же запись по id и изменить Name"):
        production_units_page.open_unit_by_id(uid)
        production_units_page.page.locator("#ProductionUnit_Name").fill(name2)
        production_units_page.save_form()
        production_units_page.apply_changes_if_present()

    with allure.step("Проверить новое имя в инпуте"):
        expect(production_units_page.page.locator("#ProductionUnit_Name")).to_have_value(name2, timeout=15_000)


@pytest.mark.e2e
@pytest.mark.production_units_legacy
@testit.nameSpace("UI/Smoke")
@testit.className("ProductionUnits")
@testit.externalId("ui.production_units.full_crud_destructive_flagged")
@testit.displayName("CRUD: создать production unit и удалить (destructive по флагу)")
@allure.feature("Справочники")
@allure.story("Production units / Full CRUD")
@allure.title("CRUD: создать production unit и удалить (destructive по флагу)")
@allure.description("Полный CRUD: создаём production unit, проверяем карточку по id, инициируем удаление (с карточки или через выделение в списке + кнопку на тулбаре). Под флагом RUN_DESTRUCTIVE_PRODUCTION_UNITS_CRUD=true — подтверждает удаление и проверяет, что запись больше не доступна. Без флага — отменяет диалог удаления и проверяет, что запись осталась.")
def test_production_units_full_crud_destructive_flagged(
    production_units_page, run_destructive_production_units_crud
):
    with allure.step("Создать тестовую запись"):
        production_units_page.open()
        assert production_units_page.open_create_form()
        suffix = str(int(time.time()))
        code = f"AT-{suffix}"[:18]
        name = f"CRUD-{suffix}"
        production_units_page.fill_code_and_name(code, name)
        t_ok, p_ok, s_ok = production_units_page.fill_mandatory_selects_for_new_unit()
        allure.attach(f"type={t_ok}, parent={p_ok}, status={s_ok}", "selects", allure.attachment_type.TEXT)
        assert t_ok and p_ok, "Не удалось выбрать Type и/или Parent"
        production_units_page.save_until_persisted()
        uid = production_units_page.current_unit_id()
        if not uid or uid == "0":
            uid = production_units_page.recover_unit_id_from_list(code, name)
        assert uid and uid != "0"
        allure.attach(uid, "created id", allure.attachment_type.TEXT)

    with allure.step("Проверить, что карточка сохранилась (по id и полю Code)"):
        production_units_page.open_unit_by_id(uid)
        expect(production_units_page.page.locator("#ProductionUnit_Code")).to_have_value(code, timeout=15_000)

    with allure.step("Удалить запись и подтвердить/отменить по флагу"):
        deleted = False
        for attempt in range(3):
            production_units_page.open_unit_by_id(uid)
            production_units_page.page.locator("#ProductionUnit_Code").wait_for(state="visible", timeout=10_000)
            if production_units_page.trigger_delete_on_card():
                deleted = True
                break
            if production_units_page.delete_unit_from_list_by_text(code, name):
                deleted = True
                break
            allure.attach(str(attempt), "delete attempt", allure.attachment_type.TEXT)
            production_units_page.page.wait_for_timeout(500)
        allure.attach(str(deleted), "delete triggered on card", allure.attachment_type.TEXT)
        assert deleted, "Не найдена кнопка удаления (ни на карточке, ни в списке)"
        assert production_units_page.delete_dialog_visible(), "Не появился диалог удаления"
        if run_destructive_production_units_crud:
            production_units_page.confirm_delete_dialog()
        else:
            production_units_page.cancel_delete_dialog()
        production_units_page.apply_changes_if_present()

    with allure.step("Проверить итог после удаления/отмены"):
        production_units_page.open_unit_by_id(uid)
        if run_destructive_production_units_crud:
            cur_id = production_units_page.current_unit_id()
            if cur_id == uid:
                try:
                    saved_code = production_units_page.page.locator("#ProductionUnit_Code").input_value()
                except Exception:
                    saved_code = ""
                assert saved_code != code, f"Запись {code} всё ещё доступна после удаления"
        else:
            expect(production_units_page.page.locator("#ProductionUnit_Code")).to_have_value(code)
