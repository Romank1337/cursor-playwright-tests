"""
Функциональные тесты ИПМ.
"""

from __future__ import annotations

import json
import os
import re

os.environ.setdefault("HEADLESS", "true")

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


def _attach_backend_setup(setup) -> None:
    payload = {
        "suffix": setup.suffix,
        "tab_number": setup.tab_number,
        "personnel_id": setup.personnel_id,
        "worker_id": setup.worker_id,
        "machine_id": setup.machine_id,
        "machine_code": setup.machine_code,
        "machine_short_name": setup.machine_short_name,
        "protocol_id": setup.protocol_id,
        "protocol_ip": setup.protocol_ip,
        "worker_role_id": setup.worker_role_id,
    }
    allure.attach(
        json.dumps(payload, ensure_ascii=False, indent=2),
        name="ipm_backend_setup",
        attachment_type=allure.attachment_type.JSON,
    )


@pytest.mark.e2e
@pytest.mark.ipm
@testit.nameSpace("UI/Smoke")
@testit.className("Ipm")
@testit.externalId("ui.ipm.downtime_cause_select")
@testit.displayName("ИПМ: выбрать причину простоя на станке")
@allure.feature("ИПМ")
@allure.story("Причина простоя")
@allure.title("ИПМ: выбрать причину простоя на станке")
@allure.description(
    "После подготовки и входа в ИПМ: выбрать карточку станка → Применить → "
    "вкладка «Причина простоя» → выбрать причину → «Выбрать» → "
    "проверить уведомление и отображение причины в панели."
)
@allure.severity(allure.severity_level.CRITICAL)
def test_ipm_select_downtime_cause(
    ipm_ready,
    ipm_machines_page,
    ipm_machine_page,
    ipm_login_page,
):
    setup = ipm_ready
    page = ipm_login_page.page

    allure.dynamic.parameter("tab_number", setup.tab_number)
    allure.dynamic.parameter("machine_id", setup.machine_id)
    allure.dynamic.parameter("machine_short_name", setup.machine_short_name)
    allure.dynamic.parameter("worker_id", setup.worker_id)

    with allure.step("Подготовка: API + автоподключение + вход в ИПМ"):
        _attach_backend_setup(setup)
        expect(page).to_have_url(re.compile(r"/imp/(login)?/?$"), timeout=5_000)
        expect(page.locator("body")).to_contain_text(setup.machine_short_name, timeout=10_000)
        _attach_ui_state(page, "ipm_ready")

    machine_card = page.locator(".ant-card-small").filter(has_text=setup.machine_short_name).first

    with allure.step("Список станков: выбрать карточку созданного станка"):
        with allure.step("Проверить, что карточка станка видна"):
            ipm_machines_page.assert_machine_visible(setup.machine_short_name)

        with allure.step("Кликнуть по карточке и проверить выделение (cardChecked)"):
            ipm_machines_page.select_machine(setup.machine_short_name)
            expect(machine_card).to_have_class(re.compile(r"cardChecked"), timeout=5_000)
            _attach_ui_state(page, "machine_card_selected")

    with allure.step("Перейти на страницу станка"):
        with allure.step("Нажать «Применить» (кнопка активна после выбора карточки)"):
            apply_btn = page.locator("#machines button").nth(3)
            expect(apply_btn).to_be_enabled(timeout=5_000)
            ipm_machines_page.apply_selection()

        with allure.step("Проверить переход на страницу станка (/imp/)"):
            expect(page).to_have_url(re.compile(r"/imp/?$"), timeout=10_000)
            expect(page.locator("body")).to_contain_text(setup.machine_short_name, timeout=10_000)
            _attach_ui_state(page, "machine_page_opened")

    downtime_tab = page.get_by_role("tab", name=re.compile(r"Причина простоя|Downtime cause", re.I))

    with allure.step("Открыть вкладку «Причина простоя»"):
        with allure.step("Проверить наличие вкладки и открыть её"):
            expect(downtime_tab).to_be_visible(timeout=10_000)
            ipm_machine_page.open_downtime_cause_tab()

        with allure.step("Проверить, что панель причин простоя отображается"):
            expect(ipm_machine_page.downtime_panel).to_be_visible(timeout=10_000)
            expect(ipm_machine_page.downtime_panel.locator("[class*='reasonItem']").first).to_be_visible(
                timeout=10_000
            )
            _attach_ui_state(page, "downtime_tab_opened")

    with allure.step("Выбрать причину простоя и подтвердить"):
        with allure.step("Выбрать причину из списка"):
            cause_name = ipm_machine_page.select_downtime_cause()
            allure.dynamic.parameter("downtime_cause_name", cause_name)
            allure.attach(cause_name, name="selected_downtime_cause", attachment_type=allure.attachment_type.TEXT)
            select_btn = ipm_machine_page.downtime_panel.get_by_role(
                "button", name=re.compile(r"Выбрать|Select", re.I)
            ).first
            expect(select_btn).to_be_enabled(timeout=5_000)

        with allure.step("Нажать «Выбрать» и проверить уведомление"):
            notification_text = ipm_machine_page.confirm_downtime_cause_selection(cause_name)
            allure.attach(
                notification_text,
                name="downtime_notification",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert cause_name in notification_text, (
                f"Уведомление не содержит имя причины: {notification_text!r}"
            )
            _attach_ui_state(page, "downtime_cause_confirmed")

    with allure.step("Проверить отображение выбранной причины в панели"):
        ipm_machine_page.assert_downtime_cause_displayed_above_table(cause_name)
        expect(ipm_machine_page.downtime_panel).to_contain_text(cause_name, timeout=10_000)
        _attach_ui_state(page, "downtime_cause_verified")
