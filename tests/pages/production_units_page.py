"""
Page Object: Production structure → вкладка Production units.

Форма создания: `/list/production-structure/production-unit/0`.
Поле Parent — Ant Design TreeSelect (`ant-select ant-tree-select`), не плоский Select.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from playwright.sync_api import Page, expect


@dataclass(frozen=True)
class ProductionUnitsPage:
    page: Page
    login_url: str
    username: str
    password: str

    LIST_PATH = "/list/production-structure?tab=productionUnits"

    def _base(self) -> str:
        parsed = urlsplit(self.login_url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _login(self) -> None:
        self.page.goto(self.login_url, wait_until="domcontentloaded")
        self.page.locator("#login").fill(self.username)
        self.page.locator("#password").fill(self.password)
        self.page.locator("button[type='submit']").click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(900)

    def open(self) -> None:
        target = f"{self._base()}{self.LIST_PATH}"
        self._login()
        self.page.goto(target, wait_until="domcontentloaded")
        self.page.wait_for_timeout(1200)
        if "/user/login" in self.page.url:
            self._login()
            self.page.goto(target, wait_until="domcontentloaded")
            self.page.wait_for_timeout(1200)

    def assert_loaded(self) -> None:
        expect(self.page.locator("table.MuiTable-root, .ant-table").first).to_be_visible(timeout=15_000)
        btns = self.page.locator("button.index_button__EOmvq").filter(has_text=re.compile(r"Create|Создать"))
        any_visible = False
        for i in range(btns.count()):
            try:
                if btns.nth(i).is_visible():
                    any_visible = True
                    break
            except Exception:
                continue
        assert any_visible, "Кнопка Create/Создать не видна на списке Production units"

    def open_create_form(self) -> bool:
        self.open()
        self.page.locator("table.MuiTable-root, .ant-table").first.wait_for(state="visible", timeout=20_000)
        btns = self.page.locator("button.index_button__EOmvq").filter(has_text=re.compile(r"Create|Создать"))
        for i in range(btns.count()):
            btn = btns.nth(i)
            if btn.count() == 0:
                continue
            try:
                if not btn.is_visible():
                    continue
            except Exception:
                continue
            try:
                btn.click(timeout=5000)
            except Exception:
                btn.click(force=True)
            self.page.wait_for_timeout(1000)
            if "/production-unit/" in self.page.url:
                expect(self.page.locator("#ProductionUnit_Code")).to_be_visible(timeout=10_000)
                return True
        return False

    def _widget_for_select_input(self, input_id: str):
        return self.page.locator(".ant-select").filter(has=self.page.locator(f"#{input_id}")).first

    def pick_flat_select_first_option(self, input_id: str) -> bool:
        return self.pick_flat_select_option_matching(input_id, None)

    def pick_flat_select_option_matching(
        self, input_id: str, label_pattern: re.Pattern[str] | None
    ) -> bool:
        """Плоский Ant Select: первая опция или первая, чей текст совпадает с label_pattern."""
        inner = self.page.locator(f"#{input_id}").first
        if inner.count() == 0:
            return False
        widget = self._widget_for_select_input(input_id)
        if widget.count() == 0:
            return False
        for _ in range(40):
            cls = (widget.get_attribute("class") or "") + (
                inner.evaluate(
                    "(el) => { const r = el.closest('.ant-select'); return r ? r.className : ''; }"
                )
                or ""
            )
            if "ant-select-disabled" not in cls:
                break
            self.page.wait_for_timeout(200)

        try:
            widget.scroll_into_view_if_needed()
        except Exception:
            pass
        handle = widget.locator(".ant-select-selector").first
        if handle.count() == 0:
            return False
        try:
            handle.click(timeout=3000)
        except Exception:
            handle.click(force=True)
        self.page.wait_for_timeout(400)
        dropdown = self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
        try:
            dropdown.wait_for(state="visible", timeout=5000)
        except Exception:
            return False

        options = dropdown.locator(".ant-select-item-option:not(.ant-select-item-option-disabled)")
        count = options.count()
        chosen = None
        if label_pattern is not None:
            for i in range(count):
                opt = options.nth(i)
                try:
                    txt = (opt.inner_text() or "").strip()
                except Exception:
                    txt = ""
                if label_pattern.search(txt):
                    chosen = opt
                    break
        if chosen is None and count > 0:
            chosen = options.first
        if chosen is None:
            return False
        chosen.click(force=True)
        self.page.wait_for_timeout(400)
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(150)
        return True

    def pick_flat_select_option_by_index(self, input_id: str, index: int) -> bool:
        inner = self.page.locator(f"#{input_id}").first
        widget = self._widget_for_select_input(input_id)
        if widget.count() == 0:
            return False
        handle = widget.locator(".ant-select-selector").first
        handle.click(force=True)
        self.page.wait_for_timeout(400)
        dropdown = self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
        try:
            dropdown.wait_for(state="visible", timeout=5000)
        except Exception:
            return False
        opt = dropdown.locator(".ant-select-item-option:not(.ant-select-item-option-disabled)").nth(index)
        if opt.count() == 0:
            return False
        opt.click(force=True)
        self.page.wait_for_timeout(400)
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(150)
        return True

    def pick_tree_select_first_option(self, input_id: str) -> bool:
        """TreeSelect: первый видимый узел (исключаем служебный measurer с aria-hidden)."""
        inner = self.page.locator(f"#{input_id}").first
        if inner.count() == 0:
            return False
        widget = self.page.locator(".ant-select.ant-tree-select").filter(has=inner).first
        if widget.count() == 0:
            widget = self.page.locator(".ant-tree-select").filter(has=inner).first
        if widget.count() == 0:
            return False
        for _ in range(40):
            cls = (widget.get_attribute("class") or "") + (
                inner.evaluate(
                    "(el) => { const r = el.closest('.ant-select'); return r ? r.className : ''; }"
                )
                or ""
            )
            if "ant-select-disabled" not in cls:
                break
            self.page.wait_for_timeout(200)
        try:
            widget.scroll_into_view_if_needed()
        except Exception:
            pass
        handle = widget.locator(".ant-select-selector").first
        if handle.count() == 0:
            return False
        try:
            handle.click(timeout=3000)
        except Exception:
            handle.click(force=True)
        self.page.wait_for_timeout(500)
        dropdown = self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
        try:
            dropdown.wait_for(state="visible", timeout=6000)
        except Exception:
            return False
        node = dropdown.locator(
            ".ant-select-tree-treenode:not([aria-hidden='true']) .ant-select-tree-node-content-wrapper"
        ).first
        if node.count() == 0:
            node = dropdown.locator(".ant-select-tree-node-content-wrapper").first
        if node.count() == 0:
            return False
        node.click(force=True)
        self.page.wait_for_timeout(450)
        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(150)
        return True

    def fill_code_and_name(self, code: str, name: str) -> None:
        self.page.locator("#ProductionUnit_Code").fill(code)
        self.page.locator("#ProductionUnit_Name").fill(name)

    def fill_mandatory_selects_for_new_unit(self) -> tuple[bool, bool, bool]:
        """Type (не Enterprise), Parent (tree), Status при необходимости."""
        # Enterprise (первая опция) даёт toast «main production unit can only be a company».
        type_pat = re.compile(
            r"Division|Shop floor|Warehouse|Repair|Other|цех|склад|подраздел|участок",
            re.I,
        )
        t_ok = self.pick_flat_select_option_matching("ProductionUnit_Type", type_pat)
        if not t_ok:
            t_ok = self.pick_flat_select_option_by_index("ProductionUnit_Type", 1)
        self.page.wait_for_timeout(500)
        p_ok = self.pick_tree_select_first_option("ProductionUnit_ParentId")
        self.page.wait_for_timeout(500)
        s_ok = self.pick_flat_select_first_option("ProductionUnit_Status")
        return t_ok, p_ok, s_ok

    def save_form(self) -> None:
        candidates = (
            self.page.locator("button.ant-btn-dangerous").filter(has_text=re.compile(r"Save|Сохранить")).first,
            self.page.get_by_role("button", name=re.compile(r"Save|Сохранить", re.I)).first,
        )
        for btn in candidates:
            if btn.count() == 0:
                continue
            try:
                if btn.is_visible():
                    btn.click(force=True)
                    self.page.wait_for_timeout(1200)
                    return
            except Exception:
                continue
        self.page.get_by_text("Save", exact=True).click(timeout=5000, force=True)
        self.page.wait_for_timeout(1200)

    def save_until_persisted(self, max_tries: int = 4) -> str | None:
        """Save + Apply в цикле, пока URL не станет /production-unit/<id> с id != 0."""
        for i in range(max_tries):
            uid = self.current_unit_id()
            if uid and uid != "0":
                return uid
            self.save_form()
            self.apply_changes_if_present()
            self.page.wait_for_timeout(800)
            uid = self.current_unit_id()
            if uid and uid != "0":
                return uid
            if i < max_tries - 1:
                self.pick_flat_select_first_option("ProductionUnit_Status")
        return self.current_unit_id()

    def recover_unit_id_from_list(self, code: str, name: str | None = None) -> str | None:
        """Если URL остался /0, id из ссылки в таблице или после клика по строке."""
        self.go_to_list()
        for key in (code, name):
            if not key:
                continue
            row = self.row_with_text(key)
            if row.count() == 0 or not row.is_visible():
                continue
            link = row.locator("a[href*='/production-unit/']").first
            if link.count() > 0:
                href = link.get_attribute("href") or ""
                m = re.search(r"/production-unit/(\d+)", href)
                if m:
                    return m.group(1)
            row.click(force=True)
            self.page.wait_for_timeout(1000)
            uid = self.current_unit_id()
            if uid and uid != "0":
                return uid
        return None

    def has_required_form_controls(self) -> bool:
        return (
            self.page.locator("#ProductionUnit_Code").count() > 0
            and self.page.locator("#ProductionUnit_Name").count() > 0
            and self.page.locator("#ProductionUnit_Type").count() > 0
            and self.page.locator("#ProductionUnit_ParentId").count() > 0
        )

    def open_unit_by_id(self, unit_id: str) -> None:
        self._login()
        url = f"{self._base()}/list/production-structure/production-unit/{unit_id}"
        self.page.goto(url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(1000)
        if "/user/login" in self.page.url:
            self._login()
            self.page.goto(url, wait_until="domcontentloaded")
            self.page.wait_for_timeout(1000)

    def trigger_delete_on_card(self) -> bool:
        """Удаление с карточки: icon-only dangerous или кнопка Delete (не Save)."""
        icon_del = self.page.locator("button.ant-btn-dangerous.ant-btn-icon-only:not([disabled])")
        for i in range(icon_del.count()):
            btn = icon_del.nth(i)
            try:
                if btn.is_visible():
                    btn.click(force=True)
                    self.page.wait_for_timeout(400)
                    return True
            except Exception:
                continue

        for label in ("Delete", "Удалить"):
            btn = self.page.get_by_role("button", name=label).first
            if btn.count() > 0 and btn.is_visible():
                btn.click(force=True)
                self.page.wait_for_timeout(400)
                return True

        n = self.page.locator("button.ant-btn-dangerous").count()
        for i in range(n):
            btn = self.page.locator("button.ant-btn-dangerous").nth(i)
            if not btn.is_visible():
                continue
            try:
                label = (btn.inner_text(timeout=500) or "").strip()
            except Exception:
                label = ""
            if re.search(r"Save|Сохранить", label, re.I):
                continue
            try:
                btn.click(timeout=3000)
            except Exception:
                btn.click(force=True)
            self.page.wait_for_timeout(400)
            return True

        icon = self.page.locator("button:has(.anticon-delete)").first
        if icon.count() > 0 and icon.is_visible():
            icon.click(force=True)
            self.page.wait_for_timeout(400)
            return True

        # Иконка удаления может быть внутри span, не в button.
        del_icon = self.page.locator(".anticon-delete").first
        if del_icon.count() > 0:
            parent_btn = del_icon.locator("xpath=ancestor::button[1]")
            if parent_btn.count() > 0 and parent_btn.first.is_visible():
                parent_btn.first.click(force=True)
                self.page.wait_for_timeout(400)
                return True
        return False

    def delete_unit_from_list_by_text(self, *texts: str) -> bool:
        self.go_to_list()
        self.page.locator("table.MuiTable-root").first.wait_for(state="visible", timeout=15_000)
        for text in texts:
            if not text:
                continue
            row = self.page.locator("table.MuiTable-root tbody tr").filter(has_text=text).first
            if row.count() == 0:
                continue
            row.scroll_into_view_if_needed()
            cb = row.locator("input[type='checkbox']").first
            if cb.count() > 0:
                try:
                    cb.check(force=True)
                except Exception:
                    cb.click(force=True)
                self.page.wait_for_timeout(300)
                if self.trigger_delete_selected_from_toolbar():
                    return True
        return False

    def apply_changes_if_present(self) -> None:
        apply_btn = self.page.locator("button:has-text('Apply'), button:has-text('Применить')").first
        if apply_btn.count() > 0 and apply_btn.is_visible():
            try:
                apply_btn.click(timeout=3000)
            except Exception:
                apply_btn.click(force=True)
            self.page.wait_for_timeout(900)

    def current_unit_id(self) -> str | None:
        m = re.search(r"/production-structure/production-unit/(\d+)", self.page.url)
        if not m:
            return None
        return m.group(1)

    def go_to_list(self) -> None:
        self.page.goto(f"{self._base()}{self.LIST_PATH}", wait_until="domcontentloaded")
        self.page.wait_for_timeout(1200)

    def row_with_text(self, text: str):
        return self.page.locator("table.MuiTable-root tbody tr, .ant-table-tbody tr").filter(has_text=text).first

    def unit_exists_in_table(self, *texts: str) -> bool:
        for text in texts:
            if text and self.row_with_text(text).count() > 0:
                row = self.row_with_text(text)
                if row.is_visible():
                    return True
        return False

    def open_unit_from_list_by_text(self, text: str) -> bool:
        row = self.row_with_text(text)
        if row.count() == 0 or not row.is_visible():
            return False
        row.scroll_into_view_if_needed()
        row.click(force=True)
        self.page.wait_for_timeout(900)
        return self.current_unit_id() is not None and self.current_unit_id() != "0"

    def cancel_form_if_present(self) -> None:
        for label in ("Cancel", "Отмена"):
            b = self.page.get_by_text(label, exact=True).first
            if b.count() > 0 and b.is_visible():
                b.click()
                self.page.wait_for_timeout(400)
                return

    def delete_dialog_visible(self) -> bool:
        dlg = self.page.locator(".ant-modal:visible, [role='dialog']:visible").first
        return dlg.count() > 0 and dlg.is_visible()

    def confirm_delete_dialog(self) -> None:
        dangerous = self.page.locator(".ant-modal .ant-modal-footer .ant-btn-dangerous").first
        if dangerous.count() > 0 and dangerous.is_visible():
            dangerous.click()
            self.page.wait_for_timeout(500)
            return
        primary = self.page.locator(".ant-modal .ant-modal-footer .ant-btn-primary").first
        if primary.count() > 0 and primary.is_visible():
            primary.click()
            self.page.wait_for_timeout(500)
            return
        for text in ("Delete", "Удалить", "OK", "Yes", "Да"):
            btn = self.page.get_by_text(text, exact=True)
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click()
                self.page.wait_for_timeout(500)
                return

    def cancel_delete_dialog(self) -> None:
        for text in ("Cancel", "Отмена", "No"):
            btn = self.page.get_by_text(text, exact=True)
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click()
                self.page.wait_for_timeout(300)
                return

    def trigger_delete_selected_from_toolbar(self) -> bool:
        """Выделенные строки → красная icon-only в тулбаре (как в списках MUI)."""
        del_btn = self.page.locator(
            "button.ant-btn-dangerous.ant-btn-icon-only:not([disabled]), "
            "button.ant-btn-dangerous.ant-btn-icon-only"
        ).first
        if del_btn.count() == 0 or not del_btn.is_visible():
            return False
        try:
            del_btn.click(timeout=3000)
        except Exception:
            del_btn.click(force=True)
        self.page.wait_for_timeout(400)
        return True

    def select_row_checkbox_for_text(self, text: str) -> bool:
        row = self.row_with_text(text)
        if row.count() == 0 or not row.is_visible():
            return False
        row.scroll_into_view_if_needed()
        cb = row.locator("input[type='checkbox']").first
        if cb.count() == 0:
            return False
        try:
            cb.check(force=True)
        except Exception:
            cb.click(force=True)
        self.page.wait_for_timeout(300)
        return True
