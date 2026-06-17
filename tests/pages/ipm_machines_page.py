"""
Page Object: список станков в ИПМ после авторизации.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from playwright.sync_api import Page, expect


@dataclass(frozen=True)
class IpmMachinesPage:
    page: Page

    def assert_machine_visible(self, machine_short_name: str) -> None:
        card = self._machine_card(machine_short_name)
        expect(card).to_be_visible(timeout=15_000)

    def select_machine(self, machine_short_name: str) -> None:
        card = self._machine_card(machine_short_name)
        expect(card).to_be_visible(timeout=15_000)
        card.click()
        self.page.wait_for_timeout(800)
        expect(card).to_have_class(re.compile(r"cardChecked"), timeout=5_000)

    def apply_selection(self) -> None:
        apply_btn = self.page.locator("#machines button").filter(
            has_text=re.compile(r"Применить|Apply", re.I)
        ).first
        if apply_btn.count() == 0 or not apply_btn.is_visible():
            apply_btn = self.page.locator("#machines button").nth(3)
        expect(apply_btn).to_be_enabled(timeout=5_000)
        apply_btn.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2500)

    def _machine_card(self, machine_short_name: str):
        return self.page.locator(".ant-card-small").filter(has_text=machine_short_name).first
