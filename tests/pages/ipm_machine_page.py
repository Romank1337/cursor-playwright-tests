"""
Page Object: страница станка в ИПМ (вкладка «Причина простоя»).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from playwright.sync_api import Page, expect


@dataclass(frozen=True)
class IpmMachinePage:
    page: Page

    _DOWNTIME_TAB = re.compile(r"Причина простоя|Downtime cause", re.I)
    _SELECT_BTN = re.compile(r"Выбрать|Select", re.I)

    @property
    def downtime_panel(self):
        return self.page.locator('[id*="panel-downtime"]').first

    def open_downtime_cause_tab(self) -> None:
        tab = self.page.get_by_role("tab", name=self._DOWNTIME_TAB).first
        expect(tab).to_be_visible(timeout=10_000)
        tab.click()
        self.page.wait_for_timeout(1200)
        expect(self.downtime_panel).to_be_visible(timeout=10_000)

    def select_downtime_cause(self, cause_name: str | None = None) -> str:
        reasons = self.downtime_panel.locator("[class*='reasonItem']")
        expect(reasons.first).to_be_visible(timeout=10_000)
        if cause_name:
            reason = reasons.filter(has_text=cause_name).first
            expect(reason).to_be_visible(timeout=10_000)
        else:
            reason = reasons.first
        selected_name = reason.inner_text().strip()
        reason.click()
        self.page.wait_for_timeout(500)
        return selected_name

    def confirm_downtime_cause_selection(self, cause_name: str) -> str:
        select_btn = self.downtime_panel.get_by_role("button", name=self._SELECT_BTN).first
        expect(select_btn).to_be_visible(timeout=5_000)
        expect(select_btn).to_be_enabled(timeout=5_000)
        select_btn.click()
        notice = self.page.locator(".ant-notification-notice, .ant-message-notice").filter(
            has_text=cause_name
        ).first
        expect(notice).to_be_visible(timeout=5_000)
        return notice.inner_text().strip()

    def assert_downtime_cause_displayed_above_table(self, cause_name: str) -> None:
        expect(self.downtime_panel).to_contain_text(cause_name, timeout=10_000)
