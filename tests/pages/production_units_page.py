"""
Page Object: Production structure → вкладка Production units.

Форма создания: `/list/production-structure/production-unit/0`.
Поле Parent — Ant Design TreeSelect (`ant-select ant-tree-select`), не плоский Select.
"""

from __future__ import annotations

import re
import time
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
    _AUTH_MARKER = "_production_units_authenticated"

    def _base(self) -> str:
        parsed = urlsplit(self.login_url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _is_authenticated(self) -> bool:
        return bool(getattr(self.page.context, self._AUTH_MARKER, False))

    def _mark_authenticated(self) -> None:
        setattr(self.page.context, self._AUTH_MARKER, True)

    def _do_login_form(self) -> None:
        self.page.goto(self.login_url, wait_until="domcontentloaded")
        self.page.locator("#login").fill(self.username)
        self.page.locator("#password").fill(self.password)
        self.page.locator("button[type='submit']").click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(900)
        self._mark_authenticated()

    def _ensure_logged_in(self) -> None:
        """Логин один раз за сессию браузера (в начале теста)."""
        if self._is_authenticated():
            return
        self._do_login_form()

    def _relogin_if_redirected(self) -> None:
        """Повторный логин только если приложение выбросило на /user/login."""
        if "/user/login" not in self.page.url:
            return
        self._do_login_form()

    def open(self) -> None:
        target = f"{self._base()}{self.LIST_PATH}"
        if not self._is_authenticated():
            if "/user/login" in self.page.url:
                self._ensure_logged_in()
            else:
                self._mark_authenticated()
        self.page.goto(target, wait_until="domcontentloaded")
        self.page.wait_for_timeout(1200)
        if "/user/login" in self.page.url:
            self._relogin_if_redirected()
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
        if (
            "/production-unit/" in self.page.url
            and self.page.locator("#ProductionUnit_Code").count() > 0
        ):
            expect(self.page.locator("#ProductionUnit_Code")).to_be_visible(timeout=10_000)
            return True

        if "/list/production-structure" not in self.page.url or "productionUnits" not in self.page.url:
            self.open()
        else:
            self.page.locator("table.MuiTable-root, .ant-table").first.wait_for(
                state="visible", timeout=20_000
            )
            self.page.wait_for_timeout(600)
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
        code_input = self.page.locator("#ProductionUnit_Code")
        name_input = self.page.locator("#ProductionUnit_Name")
        code_input.wait_for(state="visible", timeout=15_000)
        name_input.wait_for(state="visible", timeout=15_000)
        code_input.fill(code)
        name_input.fill(name)

    def _select_has_value(self, input_id: str) -> bool:
        widget = self._widget_for_select_input(input_id)
        if widget.count() == 0:
            return False
        item = widget.locator(".ant-select-selection-item").first
        if item.count() == 0:
            return False
        try:
            return item.is_visible()
        except Exception:
            return False

    def _form_has_validation_errors(self) -> bool:
        return self.page.locator(".ant-form-item-has-error").count() > 0

    def fill_mandatory_selects_for_new_unit(self) -> tuple[bool, bool, bool]:
        """Type (не Enterprise), Parent (tree), Status при необходимости."""
        expect(self.page.locator("#ProductionUnit_Type")).to_be_attached(timeout=15_000)
        self.page.wait_for_timeout(400)

        type_pat = re.compile(
            r"Division|Shop floor|Warehouse|Repair|Other|цех|склад|подраздел|участок",
            re.I,
        )
        t_ok = p_ok = s_ok = False
        for attempt in range(3):
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(200)

            if not self._select_has_value("ProductionUnit_Type"):
                t_ok = self.pick_flat_select_option_matching("ProductionUnit_Type", type_pat)
                if not t_ok:
                    t_ok = self.pick_flat_select_option_by_index("ProductionUnit_Type", 1)
            else:
                t_ok = True
            self.page.wait_for_timeout(500)

            if not self._select_has_value("ProductionUnit_ParentId"):
                p_ok = self.pick_tree_select_first_option("ProductionUnit_ParentId")
            else:
                p_ok = True
            self.page.wait_for_timeout(500)

            if not self._select_has_value("ProductionUnit_Status"):
                s_ok = self.pick_flat_select_first_option("ProductionUnit_Status")
            else:
                s_ok = True

            t_ok = t_ok and self._select_has_value("ProductionUnit_Type")
            p_ok = p_ok and self._select_has_value("ProductionUnit_ParentId")
            if t_ok and p_ok:
                return t_ok, p_ok, s_ok
            self.page.wait_for_timeout(600)

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
            if self._form_has_validation_errors():
                self.fill_mandatory_selects_for_new_unit()
            self.save_form()
            self.apply_changes_if_present()
            self.page.wait_for_timeout(800)
            uid = self.current_unit_id()
            if uid and uid != "0":
                return uid
            if i < max_tries - 1 and self._form_has_validation_errors():
                self.fill_mandatory_selects_for_new_unit()
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
        url = f"{self._base()}/list/production-structure/production-unit/{unit_id}"
        self.page.goto(url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(1000)
        if "/user/login" in self.page.url:
            self._relogin_if_redirected()
            self.page.goto(url, wait_until="domcontentloaded")
            self.page.wait_for_timeout(1000)

    def trigger_delete_on_card(self) -> bool:
        """Удаление с карточки: icon-only с корзиной или кнопка Delete (не Save)."""
        trash_btn = self.page.locator(
            "button.ant-btn-dangerous.ant-btn-icon-only:not([disabled])"
            ":has(svg path[d*='M10 2a1 1 0 0 1 1 1v1h3'])"
        ).first
        if trash_btn.count() > 0 and trash_btn.is_visible():
            try:
                trash_btn.click(timeout=3000)
            except Exception:
                trash_btn.click(force=True)
            self.page.wait_for_timeout(400)
            return True

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

    _PU_TABLE_ROWS = (
        "[id*='panel-productionUnits'] table.MuiTable-root tbody tr, "
        ".index_tableContainer-full table.MuiTable-root tbody tr"
    )

    def _tbody_rows(self):
        """Только строки данных (tbody), без thead с «выделить все»."""
        return self.page.locator(self._PU_TABLE_ROWS)

    def _target_row(self, unit_id: str | None, *texts: str):
        rows = self._tbody_rows()
        keys = [t for t in texts if t]
        name_key = keys[-1] if keys else None

        if unit_id:
            candidates = rows.filter(
                has=self.page.locator(f"a[href*='/production-unit/{unit_id}']")
            )
            if candidates.count() == 1:
                return candidates.first
            for i in range(candidates.count()):
                candidate = candidates.nth(i)
                if name_key and name_key not in (candidate.inner_text() or ""):
                    continue
                return candidate

        for text in keys:
            candidates = rows.filter(has_text=text)
            for i in range(candidates.count()):
                candidate = candidates.nth(i)
                if unit_id:
                    link = candidate.locator(f"a[href*='/production-unit/{unit_id}']")
                    if link.count() == 0:
                        continue
                return candidate

        if unit_id:
            fallback = self.page.locator(
                f"table.MuiTable-root tbody tr:has(a[href*='/production-unit/{unit_id}'])"
            ).first
            if fallback.count() > 0:
                return fallback
        return None

    def _row_checkbox_is_checked(self, row) -> bool:
        try:
            return row.evaluate(
                """
                (el) => {
                    const inp = el.querySelector('td input[type="checkbox"]');
                    if (inp && inp.checked) return true;
                    return !!el.querySelector('span.MuiCheckbox-root.Mui-checked svg[data-testid="CheckBoxIcon"]')
                        || !!el.querySelector('span.MuiCheckbox-root.Mui-checked')
                        || el.classList.contains('Mui-selected')
                        || el.getAttribute('aria-selected') === 'true';
                }
                """
            )
        except Exception:
            return False

    def _delete_toolbar_enabled(self) -> bool:
        btn = self._toolbar_delete_button()
        if btn.count() == 0:
            return False
        try:
            return btn.is_visible() and btn.get_attribute("disabled") is None
        except Exception:
            return False

    def _click_checkbox_cell(self, row) -> None:
        """Клик по ячейке чекбокса (td[0] или td[1] в tree-таблице), не по Name."""
        try:
            row.scroll_into_view_if_needed()
        except Exception:
            pass
        try:
            row.hover()
        except Exception:
            pass
        self.page.wait_for_timeout(300)

        for idx in (0, 1):
            td = row.locator("td").nth(idx)
            if td.count() == 0:
                continue
            if td.locator("span.MuiCheckbox-root, svg[data-testid='CheckBoxOutlineBlankIcon']").count() == 0:
                continue
            box = td.bounding_box()
            if not box:
                continue
            x = box["x"] + box["width"] / 2
            y = box["y"] + box["height"] / 2
            self.page.mouse.move(x, y)
            self.page.wait_for_timeout(150)
            self.page.mouse.click(x, y)
            self.page.wait_for_timeout(450)
            if self._row_checkbox_is_checked(row):
                return

    def _toggle_row_checkbox_via_dom(self, row) -> bool:
        try:
            return row.evaluate(
                """
                (el) => {
                    const blank = el.querySelector('svg[data-testid="CheckBoxOutlineBlankIcon"]');
                    const root = blank?.closest('span.MuiCheckbox-root')
                        || el.querySelector('td span.MuiCheckbox-root');
                    const inp = el.querySelector('td input[type="checkbox"]');
                    if (root) root.click();
                    if (inp) {
                        inp.click();
                        inp.checked = true;
                        inp.dispatchEvent(new Event('input', { bubbles: true }));
                        inp.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                    return !!(inp && inp.checked)
                        || !!el.querySelector('span.MuiCheckbox-root.Mui-checked');
                }
                """
            )
        except Exception:
            return False

    def _click_row_checkbox_only(self, row, *texts: str) -> bool:
        """Выделить только целевую tbody-строку через чекбокс в первой ячейке."""
        try:
            is_tbody_row = row.evaluate(
                "el => el.tagName === 'TR' && !!el.closest('tbody') && !el.closest('thead')"
            )
        except Exception:
            is_tbody_row = False
        if not is_tbody_row:
            return False

        if self._row_checkbox_is_checked(row):
            return True

        for _ in range(4):
            self._click_checkbox_cell(row)
            if self._row_checkbox_is_checked(row):
                return True

            blank_icon = row.locator("svg[data-testid='CheckBoxOutlineBlankIcon']").first
            if blank_icon.count() > 0:
                box = blank_icon.bounding_box()
                if box:
                    self.page.mouse.click(
                        box["x"] + box["width"] / 2,
                        box["y"] + box["height"] / 2,
                    )
                    self.page.wait_for_timeout(500)
                    if self._row_checkbox_is_checked(row):
                        return True

            if self._toggle_row_checkbox_via_dom(row):
                self.page.wait_for_timeout(500)
                if self._row_checkbox_is_checked(row):
                    return True

            row_checkbox = row.get_by_role(
                "checkbox", name=re.compile(r"Toggle select row|Переключить выбор строки", re.I)
            ).first
            if row_checkbox.count() > 0:
                try:
                    row_checkbox.check(force=True)
                except Exception:
                    try:
                        row_checkbox.click(force=True)
                    except Exception:
                        pass
                self.page.wait_for_timeout(500)
                if self._row_checkbox_is_checked(row):
                    return True

        return self._row_checkbox_is_checked(row)

    def select_row_checkbox(self, unit_id: str | None = None, *texts: str) -> bool:
        self.expand_all_tree_rows_if_present()
        row = self._target_row(unit_id, *texts)
        if row is None or row.count() == 0:
            return False
        try:
            row.scroll_into_view_if_needed()
        except Exception:
            pass
        selected = self._click_row_checkbox_only(row, *texts)
        if self._row_checkbox_is_checked(row):
            return True
        return selected

    def delete_unit_from_list_by_text(self, *texts: str) -> bool:
        self.go_to_list()
        self.page.locator("table.MuiTable-root").first.wait_for(state="visible", timeout=15_000)
        for text in texts:
            if not text:
                continue
            if self.select_row_checkbox(None, text) and self.trigger_delete_selected_from_toolbar():
                return True
        return False

    def delete_unit_from_list(self, unit_id: str, *texts: str) -> bool:
        """Выделить строку чекбоксом и нажать icon-only Delete (корзина) в тулбаре."""
        if not self.wait_until_unit_in_table(unit_id, *texts):
            return False
        keys = [t for t in texts if t]
        if keys:
            try:
                self.search_unit_in_list(keys[-1])
            except Exception:
                pass
        if not self.select_row_checkbox(unit_id, *texts):
            return False
        return self.trigger_delete_selected_from_toolbar()

    def delete_unit_from_list_and_confirm(self, unit_id: str, *texts: str) -> bool:
        if not self.delete_unit_from_list(unit_id, *texts):
            return False
        return self._confirm_delete_dialog_and_apply()

    def delete_unit_from_card_and_confirm(self, unit_id: str) -> bool:
        """Удаление с карточки подразделения (как при редактировании Name)."""
        self.open_unit_by_id(unit_id)
        self.page.locator("#ProductionUnit_Code").wait_for(state="visible", timeout=15_000)
        if not self.trigger_delete_on_card():
            return False
        return self._confirm_delete_dialog_and_apply()

    def _confirm_delete_dialog_and_apply(self) -> bool:
        if not self.wait_for_delete_dialog():
            return False
        self.confirm_delete_dialog()
        self.apply_changes_if_present()
        try:
            self.page.locator(".ant-modal:visible, [role='dialog']:visible").first.wait_for(
                state="hidden", timeout=10_000
            )
        except Exception:
            pass
        return True

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
        self._relogin_if_redirected()
        if "/user/login" in self.page.url:
            self.page.goto(f"{self._base()}{self.LIST_PATH}", wait_until="domcontentloaded")
            self.page.wait_for_timeout(1200)
        self.page.locator("table.MuiTable-root, .ant-table").first.wait_for(state="visible", timeout=20_000)

    _ROW_TYPES = (
        "[id*='panel-productionUnits'] table.MuiTable-root tbody tr, "
        ".index_tableContainer-full table.MuiTable-root tbody tr, "
        "table.MuiTable-root tbody tr, .ant-table-tbody tr"
    )

    _EXPAND_ALL_BTN = re.compile(r"Expand all|Раскрыть(?:\s+все)?", re.I)

    def expand_all_tree_rows_if_present(self) -> None:
        btn = self.page.get_by_role("button", name=self._EXPAND_ALL_BTN).first
        if btn.count() > 0 and btn.is_visible():
            btn.click(force=True)
            self.page.wait_for_timeout(700)

    def search_unit_in_list(self, query: str) -> None:
        hidden_search_button = self.page.locator(
            "div.index_inputContainer__OlsaL span.index_searchInput__Hidden__e3LW- button.index_searchButton__jEElX"
        ).first
        if hidden_search_button.count() > 0 and hidden_search_button.is_visible():
            hidden_search_button.click(force=True)
            self.page.wait_for_timeout(300)

        wrapper = None
        for _ in range(6):
            candidate = self.page.locator(
                "span.index_searchInput__ODJxi.index_searchInput__Visible__bxgWK"
            ).first
            if candidate.count() > 0 and candidate.is_visible():
                wrapper = candidate
                break
            hidden_wrapper = self.page.locator(
                "div.index_inputContainer__OlsaL span.index_searchInput__Hidden__e3LW-"
            ).first
            if hidden_wrapper.count() > 0 and hidden_wrapper.is_visible():
                hidden_btn = hidden_wrapper.locator("button.index_searchButton__jEElX").first
                if hidden_btn.count() > 0 and hidden_btn.is_visible():
                    hidden_btn.click(force=True)
                    self.page.wait_for_timeout(250)
            self.page.wait_for_timeout(400)

        if wrapper is None:
            return

        search_input = wrapper.locator("input.ant-input[type='text']").first
        if search_input.count() == 0 or not search_input.is_visible():
            return

        search_input.click()
        search_input.fill("")
        search_input.fill(query)
        self.page.wait_for_timeout(150)
        search_button = wrapper.locator("button.index_searchButton__jEElX").first
        if search_button.count() > 0 and search_button.is_visible():
            search_button.click(force=True)
            self.page.wait_for_timeout(900)

    def row_with_unit_id(self, unit_id: str):
        return self._tbody_rows().filter(
            has=self.page.locator(f"a[href*='/production-unit/{unit_id}']")
        ).first

    def row_with_text(self, text: str):
        return self._tbody_rows().filter(has_text=text).first

    def _unit_row_visible(self, unit_id: str | None, *texts: str) -> bool:
        if unit_id:
            row = self.row_with_unit_id(unit_id)
            if row.count() > 0:
                try:
                    row.scroll_into_view_if_needed()
                except Exception:
                    pass
                if row.is_visible():
                    return True
        for text in texts:
            if not text:
                continue
            row = self.row_with_text(text)
            if row.count() == 0:
                continue
            try:
                row.scroll_into_view_if_needed()
            except Exception:
                pass
            if row.is_visible():
                return True
        return False

    def unit_exists_in_table(self, unit_id: str | None = None, *texts: str) -> bool:
        self.expand_all_tree_rows_if_present()
        if self._unit_row_visible(unit_id, *texts):
            return True
        keys = [t for t in texts if t]
        if keys:
            try:
                self.search_unit_in_list(keys[0])
            except Exception:
                pass
            if self._unit_row_visible(unit_id, *texts):
                return True
        return self._unit_row_visible(unit_id, *texts)

    def wait_until_unit_in_table(
        self, unit_id: str | None, *texts: str, timeout_ms: int = 30_000
    ) -> bool:
        """Ждёт строку в иерархическом списке: expand all, search."""
        started = time.monotonic()
        while True:
            self.go_to_list()
            if self.unit_exists_in_table(unit_id, *texts):
                return True
            keys = [t for t in texts if t]
            if keys and not unit_id:
                recovered_id = self.recover_unit_id_from_list(
                    keys[0], keys[1] if len(keys) > 1 else keys[0]
                )
                if recovered_id and self.unit_exists_in_table(recovered_id, *texts):
                    return True
            if (time.monotonic() - started) * 1000 > timeout_ms:
                return self.unit_exists_in_table(unit_id, *texts)
            # self.page.reload(wait_until="domcontentloaded")
            self.page.wait_for_timeout(900)

    def wait_until_unit_not_in_table(
        self, unit_id: str | None, *texts: str, timeout_ms: int = 30_000
    ) -> bool:
        started = time.monotonic()
        while True:
            self.go_to_list()
            keys = [t for t in texts if t]
            if keys:
                try:
                    self.search_unit_in_list(keys[0])
                except Exception:
                    pass
            if not self._unit_row_visible(unit_id, *texts):
                return True
            if (time.monotonic() - started) * 1000 > timeout_ms:
                return not self._unit_row_visible(unit_id, *texts)
            # self.page.reload(wait_until="domcontentloaded")
            self.page.wait_for_timeout(900)

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

    def wait_for_delete_dialog(self, timeout_ms: int = 10_000) -> bool:
        try:
            self.page.locator(".ant-modal:visible, [role='dialog']:visible").first.wait_for(
                state="visible", timeout=timeout_ms
            )
            return True
        except Exception:
            return self.delete_dialog_visible()

    def confirm_delete_dialog(self) -> None:
        dlg = self.page.locator(".ant-modal:visible, [role='dialog']:visible").first
        if dlg.count() > 0:
            for label in ("Удалить", "Delete"):
                btn = dlg.get_by_role("button", name=label).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click(force=True)
                    self.page.wait_for_timeout(500)
                    return
            dangerous = dlg.locator(".ant-modal-footer .ant-btn-dangerous").first
            if dangerous.count() > 0 and dangerous.is_visible():
                dangerous.click(force=True)
                self.page.wait_for_timeout(500)
                return
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

    def _toolbar_delete_button(self):
        """Icon-only кнопка с иконкой корзины (без текста), активна после выбора строки."""
        return self.page.locator(
            "button.ant-btn-dangerous.ant-btn-icon-only.index_button__EOmvq:not([disabled])"
            ":has(svg path[d*='M10 2a1 1 0 0 1 1 1v1h3'])"
        ).first

    def trigger_delete_selected_from_toolbar(self) -> bool:
        del_btn = self._toolbar_delete_button()
        try:
            del_btn.wait_for(state="visible", timeout=5000)
        except Exception:
            return False
        if del_btn.get_attribute("disabled") is not None:
            return False
        try:
            del_btn.click(timeout=3000)
        except Exception:
            del_btn.click(force=True)
        self.page.wait_for_timeout(600)
        return True

    def select_row_checkbox_for_text(self, text: str) -> bool:
        return self.select_row_checkbox(None, text)
