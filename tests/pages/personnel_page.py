"""
Page Object для раздела Directories -> Personnel.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from urllib.parse import urlsplit
import re

from playwright.sync_api import Page


@dataclass(frozen=True)
class PersonnelPage:
    page: Page
    login_url: str
    username: str
    password: str

    @property
    def _create_button(self):
        return self.page.locator(
            "button:has-text('New'), "
            "button:has-text('Create'), "
            "button:has-text('Add'), "
            "button:has-text('New employee'), "
            "button:has-text('New person'), "
            "button:has-text('Новый'), "
            "button:has-text('Создать'), "
            "button:has-text('Добавить'), "
            "button:has-text('Новый сотрудник'), "
            "button:has-text('Новый персонал')"
        ).first

    @property
    def _save_button(self):
        return self.page.locator(
            "button:has-text('Save'), button:has-text('Сохранить')"
        ).first

    @property
    def _apply_button(self):
        return self.page.locator(
            "button:has-text('Apply'), button:has-text('Применить')"
        ).first

    @property
    def _list_items(self):
        return self.page.locator(".ant-list-item, .ant-table-tbody tr")

    def _login(self) -> None:
        self.page.goto(self.login_url, wait_until="domcontentloaded")
        self.page.locator("#login").fill(self.username)
        self.page.locator("#password").fill(self.password)
        self.page.locator("button[type='submit']").click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(700)

    def open(self) -> None:
        parsed = urlsplit(self.login_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        candidates = (
            "/list/personnel?tab=Personnel",
            "/list/personnel",
            "/list/personal",
            "/list/staff",
            "/list/employees",
            "/directories/personnel",
        )

        self._login()
        for path in candidates:
            self.page.goto(f"{base}{path}", wait_until="domcontentloaded")
            self.page.wait_for_timeout(700)
            if "/user/login" in self.page.url:
                self._login()
                self.page.goto(f"{base}{path}", wait_until="domcontentloaded")
                self.page.wait_for_timeout(700)
            if "/user/login" not in self.page.url:
                return

        raise AssertionError("Не удалось открыть раздел Personnel")

    def assert_loaded(self) -> None:
        if "personnel" not in self.page.url.lower():
            raise AssertionError(f"Ожидали открыть Personnel-раздел, но текущий URL: {self.page.url}")

    def refresh_personnel_list_view(self) -> None:
        self.page.reload(wait_until="domcontentloaded")
        self.page.wait_for_timeout(700)

    def open_create_form(self) -> None:
        for _ in range(5):
            candidates = (
                # Точный селектор кнопки из UI: иконка "+" и текст "Создать".
                self.page.locator(
                    "button.index_button__EOmvq.index_sizeMedium__X6QMI.index_outline__LLx1E",
                    has_text="Создать",
                ).first,
                # Кнопка, которую ты показал стрелкой: иконка Create в тулбаре.
                self.page.locator("button[class*='index_button'][class*='index_outline']").first,
                self.page.get_by_text("Create", exact=True).first,
                self.page.get_by_text("Создать", exact=True).first,
                self._create_button,
                self.page.locator("button[class*='index_button']").filter(has_text="Create").first,
                self.page.locator("button[class*='index_button']").filter(has_text="Создать").first,
                self.page.locator("button:has(.anticon-plus)").first,
                self.page.locator("button.ant-btn-primary").first,
            )
            for btn in candidates:
                if btn.count() > 0 and btn.first.is_visible():
                    try:
                        btn.first.click(timeout=3000)
                    except Exception:
                        btn.first.click(force=True)
                    self.page.wait_for_timeout(900)
                    # Успех: либо открыли карточку, либо сразу получили editable-поля.
                    if re.search(r"/list/personnel/\d+", self.page.url):
                        return
                    editable = self.page.locator(
                        "input:visible:not([type='search']):not([type='checkbox']):not([disabled]):not([readonly]), "
                        "textarea:visible:not([disabled]):not([readonly]), "
                        "[contenteditable='true']:visible"
                    )
                    if editable.count() > 0:
                        return

            # Фолбэк: поиск среди button и role=button с текстом Create/Создать.
            clicked = self.page.evaluate(
                """() => {
                    const nodes = Array.from(document.querySelectorAll('button, [role="button"]'));
                    const visible = (el) => {
                        const r = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);
                        return r.width > 0 && r.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
                    };
                    const explicit = nodes.find((n) => visible(n) && /create|создать/i.test((n.innerText || '').trim()));
                    if (explicit) { explicit.click(); return true; }
                    const iconBtn = nodes.find((n) => visible(n) && n.className && String(n.className).includes('index_button'));
                    if (iconBtn) { iconBtn.click(); return true; }
                    return false;
                }"""
            )
            if clicked:
                self.page.wait_for_timeout(900)
                if re.search(r"/list/personnel/\d+", self.page.url):
                    return
                editable = self.page.locator(
                    "input:visible:not([type='search']):not([type='checkbox']):not([disabled]):not([readonly]), "
                    "textarea:visible:not([disabled]):not([readonly]), "
                    "[contenteditable='true']:visible"
                )
                if editable.count() > 0:
                    return
            self.page.reload(wait_until="domcontentloaded")
            self.page.wait_for_timeout(700)
        raise AssertionError("Не найдена кнопка создания сотрудника")

    def fill_required_fields(self, unique_suffix: str) -> tuple[str, str]:
        person_name = f"AUTOLAST-{unique_suffix}"
        personnel_number = person_name
        text_inputs = self.page.locator(
            "input:visible:not([type='search']):not([type='checkbox']):not([disabled]):not([readonly]), "
            "textarea:visible:not([disabled]):not([readonly]), "
            "[contenteditable='true']:visible"
        )
        if text_inputs.count() == 0:
            # Иногда карточка после Create открывается в read-only режиме.
            edit_candidates = (
                self.page.get_by_role("button", name="Edit").first,
                self.page.get_by_role("button", name="Редактировать").first,
                self.page.locator("button:has-text('Edit'), button:has-text('Редактировать')").first,
                self.page.locator("button:has(.anticon-edit), button:has(.anticon-form)").first,
            )
            for btn in edit_candidates:
                if btn.count() > 0 and btn.first.is_visible():
                    try:
                        btn.first.click(timeout=3000)
                    except Exception:
                        btn.first.click(force=True)
                    self.page.wait_for_timeout(600)
                    break
            text_inputs = self.page.locator(
                "input:visible:not([type='search']):not([type='checkbox']):not([disabled]):not([readonly]), "
                "textarea:visible:not([disabled]):not([readonly]), "
                "[contenteditable='true']:visible"
            )
        if text_inputs.count() == 0:
            raise AssertionError("После нажатия Create не найдены текстовые поля формы Personnel")

        values = [
            person_name,
            f"AUTONAME-{unique_suffix}",
            f"AUTOMID-{unique_suffix}",
            f"AUTOTEST-{unique_suffix}",
        ]
        filled = 0
        for i in range(min(text_inputs.count(), 8)):
            field = text_inputs.nth(i)
            field_type = (field.get_attribute("type") or "").lower()
            try:
                current = (field.input_value() or "").strip()
            except Exception:
                current = ""
            if current:
                continue
            if field_type == "email":
                value = f"autotest_{unique_suffix}@example.com"
            elif field_type in {"tel", "phone"}:
                value = "79000000000"
            else:
                value = values[min(filled, len(values) - 1)]
            try:
                field.fill(value)
            except Exception:
                field.click()
                self.page.keyboard.press("Control+A")
                self.page.keyboard.type(value)
            filled += 1

        if filled == 0:
            raise AssertionError("Не удалось заполнить обязательные поля формы Personnel")

        # Табельный номер: точное поле из UI.
        tab_number_field = self.page.locator("#PersonnelEditor_Number").first
        if tab_number_field.count() == 0:
            tab_number_field = self.page.locator(
                "input[id='PersonnelEditor_Number'], "
                "input[name='PersonnelEditor.Number'], "
                "input[aria-required='true'][id*='Number']"
            ).first
        if tab_number_field.count() > 0:
            try:
                current_number = (tab_number_field.input_value() or "").strip()
            except Exception:
                current_number = ""
            if current_number:
                # Если номер уже проставился в поле, используем его как источник истины.
                personnel_number = current_number
            else:
                self.fill_input_stable(tab_number_field, personnel_number)
                try:
                    personnel_number = (tab_number_field.input_value() or personnel_number).strip()
                except Exception:
                    pass

        # Пытаемся выбрать значения в обязательных select.
        selects = self.page.locator("select[required]:not([disabled])")
        for i in range(selects.count()):
            sel = selects.nth(i)
            options = sel.locator("option")
            if options.count() > 1:
                sel.select_option(index=1)

        ant_selects = self.page.locator(".ant-select:has(.ant-select-selection-placeholder)")
        for i in range(ant_selects.count()):
            sel = ant_selects.nth(i)
            if not sel.is_visible():
                continue
            sel.click()
            self.page.wait_for_timeout(200)
            opt = self.page.locator(".ant-select-item-option:not(.ant-select-item-option-disabled)").first
            if opt.count() > 0:
                opt.click()
                self.page.wait_for_timeout(200)

        return person_name, personnel_number

    def fill_input_stable(self, field, value: str) -> None:
        # Устойчивый ввод в поле, которое может быть временно перекрыто/нестабильно.
        for _ in range(6):
            try:
                field.scroll_into_view_if_needed()
            except Exception:
                pass
            try:
                field.click(timeout=1000, force=True)
            except Exception:
                self.page.wait_for_timeout(150)
            try:
                field.fill(value, timeout=1200)
                return
            except Exception:
                try:
                    field.click(force=True)
                    self.page.keyboard.press("Control+A")
                    self.page.keyboard.type(value)
                    return
                except Exception:
                    self.page.wait_for_timeout(250)
        raise AssertionError("Не удалось стабильно заполнить поле табельного номера")

    def save_form(self) -> None:
        candidates = (
            self._save_button,
            self.page.get_by_text("Save", exact=True).first,
            self.page.get_by_text("Сохранить", exact=True).first,
            self.page.locator(".ant-drawer button.ant-btn-primary, .ant-modal button.ant-btn-primary").first,
            self.page.locator("button.ant-btn-primary").last,
        )
        for btn in candidates:
            if btn.count() > 0 and btn.first.is_visible():
                try:
                    btn.first.click(timeout=3000)
                except Exception:
                    btn.first.click(force=True)
                self.page.wait_for_timeout(700)
                if self.current_person_id() is not None:
                    return
                # Иногда после первого клика форма не коммитится с первого раза.
                try:
                    btn.first.click(timeout=1500)
                except Exception:
                    btn.first.click(force=True)
                self.page.wait_for_timeout(700)
                return
        raise AssertionError("Не найдена кнопка сохранения на форме Personnel")

    def apply_changes_if_present(self) -> None:
        if self._apply_button.count() > 0 and self._apply_button.first.is_visible():
            try:
                self._apply_button.first.click(timeout=3000)
            except Exception:
                self._apply_button.first.click(force=True)
            self.page.wait_for_timeout(700)

    def ensure_person_saved(self) -> None:
        # Ждем, что после сохранения карточка получит id в URL.
        for _ in range(5):
            if self.current_person_id() is not None:
                return
            self.save_form()
            self.apply_changes_if_present()
            self.page.wait_for_timeout(700)
        raise AssertionError("Карточка сотрудника не сохранилась: id в URL не появился")

    def recover_person_id_from_list(self, person_name: str, personnel_number: str | None = None) -> str | None:
        # Восстановление id, если после сохранения не остались на карточке.
        if "/user/login" in self.page.url:
            self._login()
        parsed = urlsplit(self.login_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        self.page.goto(f"{base}/list/personnel?tab=Personnel", wait_until="domcontentloaded")
        self.page.wait_for_timeout(700)
        self.ensure_all_filter_selected()

        query = personnel_number or person_name
        try:
            self.search_person_in_list(query)
        except Exception:
            pass

        row = self.page.locator(".ant-table-tbody tr, .ant-list-item, .MuiTableBody-root tr", has_text=query).first
        if row.count() == 0:
            row = self.page.locator(".ant-table-tbody tr, .ant-list-item, .MuiTableBody-root tr", has_text=person_name).first
        if row.count() == 0 or not row.is_visible():
            return None

        link = row.locator("a[href*='/list/personnel/']").first
        if link.count() > 0 and link.is_visible():
            link.click(force=True)
        else:
            row.click(force=True)
        self.page.wait_for_timeout(700)
        return self.current_person_id()

    def person_exists(self, person_name: str) -> bool:
        self.page.wait_for_timeout(600)
        return self.page.locator(".ant-list-item, .ant-table-tbody tr", has_text=person_name).count() > 0

    def person_exists_in_table(self, person_id: str | None, *keys: str) -> bool:
        # Начинаем с первой страницы пагинации, чтобы не пропустить запись.
        first_page = self.page.locator(".ant-pagination-item-1, .ant-pagination-item[title='1']").first
        if first_page.count() > 0 and first_page.is_visible():
            first_page.click(force=True)
            self.page.wait_for_timeout(500)

        # Проверяем на текущей странице таблицы.
        if person_id:
            by_id = self.page.locator(
                f".ant-table-tbody tr:has(a[href*='/list/personnel/{person_id}']), "
                f".ant-list-item:has(a[href*='/list/personnel/{person_id}'])"
            )
            if by_id.count() > 0:
                return True
        for key in keys:
            if key and self.page.locator(".ant-list-item, .ant-table-tbody tr", has_text=key).count() > 0:
                return True

        # Полный проход по страницам пагинации.
        for _ in range(100):
            next_btn = self.page.locator(
                ".ant-pagination-next:not(.ant-pagination-disabled) button, "
                ".ant-pagination-next:not(.ant-pagination-disabled)"
            ).first
            if next_btn.count() == 0 or not next_btn.is_visible():
                break
            next_btn.click(force=True)
            self.page.wait_for_timeout(450)
            if person_id:
                by_id = self.page.locator(
                    f".ant-table-tbody tr:has(a[href*='/list/personnel/{person_id}']), "
                    f".ant-list-item:has(a[href*='/list/personnel/{person_id}'])"
                )
                if by_id.count() > 0:
                    return True
            for key in keys:
                if key and self.page.locator(".ant-list-item, .ant-table-tbody tr", has_text=key).count() > 0:
                    return True
        return False

    def current_person_id(self) -> str | None:
        match = re.search(r"/list/personnel/(\d+)", self.page.url)
        if not match:
            return None
        return match.group(1)

    def current_personnel_number(self) -> str | None:
        field = self.page.locator("#PersonnelEditor_Number").first
        if field.count() == 0:
            return None
        try:
            value = (field.input_value() or "").strip()
        except Exception:
            value = ""
        return value or None

    def delete_person_by_name(self, person_name: str) -> bool:
        row = self.page.locator(".ant-list-item, .ant-table-tbody tr", has_text=person_name).first
        if row.count() == 0:
            return False
        row.scroll_into_view_if_needed()

        delete_candidates = (
            row.locator("button:has-text('Delete'), button:has-text('Удалить')").first,
            row.locator("button.ant-btn-dangerous").first,
            row.locator("button:has(.anticon-delete)").first,
            row.locator("[title*='Delete'], [title*='Удалить']").first,
        )
        for btn in delete_candidates:
            if btn.count() > 0 and btn.first.is_visible():
                try:
                    btn.first.click(timeout=3000)
                except Exception:
                    btn.first.click(force=True)
                self.page.wait_for_timeout(300)
                self.confirm_delete_dialog_if_visible()
                self.apply_changes_if_present()
                return True

        return False

    def delete_current_person(
        self, person_id: str | None = None, person_name: str | None = None, personnel_number: str | None = None
    ) -> bool:
        # Основной сценарий: вернуться из карточки в общий список и удалить через чекбокс + toolbar Delete.
        if person_id and person_name and self.go_back_to_personnel_list():
            if self.delete_person_from_list_via_toolbar(person_id, person_name, personnel_number):
                return True

        candidates = (
            # Точный delete-икон путь, который ты прислал.
            self.page.locator(
                "button:has(svg path[d*='M10 2a1 1 0 0 1 1 1v1h3'])"
            ).first,
            self.page.get_by_role("button", name="Delete").first,
            self.page.get_by_role("button", name="Удалить").first,
            self.page.locator("button:has-text('Delete'), button:has-text('Удалить')").first,
            self.page.locator("button.ant-btn-dangerous").first,
            self.page.locator("button:has(.anticon-delete)").first,
        )
        for btn in candidates:
            if btn.count() > 0 and btn.first.is_visible():
                try:
                    btn.first.click(timeout=3000)
                except Exception:
                    btn.first.click(force=True)
                self.page.wait_for_timeout(300)
                had_dialog = self.delete_dialog_visible()
                self.confirm_delete_dialog_if_visible()
                self.apply_changes_if_present()
                self.page.wait_for_timeout(900)
                # Если ожидаем удаление конкретной карточки, проверяем, что id больше не открыт.
                if person_id:
                    if not had_dialog:
                        continue
                    if not self.is_person_id_openable(person_id):
                        return True
                    continue
                return had_dialog
        # Фолбэк: удалить из списка (поиск + выбор + delete в тулбаре).
        if person_id and person_name:
            return self.delete_person_from_list_via_toolbar(person_id, person_name, personnel_number)
        return False

    def go_back_to_personnel_list(self) -> bool:
        back_candidates = (
            self.page.locator("button.index_backButton__qF9z7").first,
            self.page.locator(
                "button[class*='index_backButton']:has(svg path[d*='M10.7071 3.29289'])"
            ).first,
            self.page.locator("button:has(svg path[d*='M10.7071 3.29289'])").first,
        )
        for btn in back_candidates:
            if btn.count() > 0 and btn.is_visible():
                btn.click(force=True)
                self.page.wait_for_timeout(900)
                return "/list/personnel" in self.page.url and not re.search(r"/list/personnel/\d+", self.page.url)
        if re.search(r"/list/personnel/\d+", self.page.url):
            self.page.go_back(wait_until="domcontentloaded")
            self.page.wait_for_timeout(900)
        return "/list/personnel" in self.page.url and not re.search(r"/list/personnel/\d+", self.page.url)

    def delete_dialog_visible(self) -> bool:
        dlg = self.page.locator(".ant-modal, [role='dialog']").first
        return dlg.count() > 0 and dlg.is_visible()

    def is_person_id_openable(self, person_id: str) -> bool:
        parsed = urlsplit(self.login_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        self.page.goto(f"{base}/list/personnel/{person_id}", wait_until="domcontentloaded")
        self.page.wait_for_timeout(800)
        # Если нас редиректнуло на login с redirect-параметром, карточка фактически не открыта.
        if "/user/login" in self.page.url:
            return False
        return f"/list/personnel/{person_id}" in self.page.url

    def delete_person_from_list_via_toolbar(
        self, person_id: str, person_name: str, personnel_number: str | None = None
    ) -> bool:
        print(f"[DEBUG delete] start person_id={person_id} person_name={person_name} personnel_number={personnel_number}")
        if "/list/personnel" not in self.page.url or re.search(r"/list/personnel/\d+", self.page.url):
            parsed = urlsplit(self.login_url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            self.page.goto(f"{base}/list/personnel?tab=Personnel", wait_until="domcontentloaded")
            self.page.wait_for_timeout(900)

        self.ensure_all_filter_selected()

        query = personnel_number or person_name
        try:
            self.search_person_in_list(query)
        except Exception:
            pass

        row = self.page.locator(
            ".ant-table-tbody tr.ant-table-row-selected, "
            ".ant-table-tbody tr[aria-selected='true'], "
            ".ant-list-item.ant-list-item-selected, "
            ".MuiTableBody-root tr.Mui-selected"
        ).first
        if row.count() == 0:
            row = self.page.locator(
                ".ant-table-tbody tr, .ant-list-item, .MuiTableBody-root tr",
                has_text=query
            ).first
        if row.count() == 0:
            row = self.page.locator(
                f".ant-table-tbody tr:has(a[href*='/list/personnel/{person_id}']), "
                f".ant-list-item:has(a[href*='/list/personnel/{person_id}']), "
                f".MuiTableBody-root tr:has(a[href*='/list/personnel/{person_id}'])"
            ).first
        if row.count() == 0:
            row = self.page.locator(
                ".ant-table-tbody tr, .ant-list-item, .MuiTableBody-root tr",
                has_text=person_name
            ).first
        if row.count() == 0:
            # После поиска берем первую строку результата в таблице.
            row = self.page.locator(".ant-table-tbody tr, .ant-list-item, .MuiTableBody-root tr").first
        if row.count() == 0 or not row.is_visible():
            print("[DEBUG delete] row not found/visible")
            return False
        row.scroll_into_view_if_needed()
        print("[DEBUG delete] row found and visible")

        # Приоритет: точный селектор чекбокса из шапки, который ты прислал.
        header_checkbox = self.page.locator(
            "[id^='rc-tabs-'][id$='-panel-Personnel'] > div > div:nth-child(2) > "
            "div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation2.css-1dfwvih > "
            "div.MuiTableContainer-root.index_tableContainer-full__e-HcA.css-116o2u8 > table > thead > tr > "
            "th.MuiTableCell-root.MuiTableCell-head.MuiTableCell-stickyHeader.MuiTableCell-alignLeft.MuiTableCell-sizeMedium.css-mfdvyk > "
            "div > div.Mui-TableHeadCell-Content-Labels.MuiBox-root.css-68rqdf > div > div > div.index_defaultButtons__S0Oo- > span > input"
        ).first
        if header_checkbox.count() == 0:
            header_checkbox = self.page.locator(
                "[id^='rc-tabs-'][id$='-panel-Personnel'] table thead th input.PrivateSwitchBase-input[type='checkbox']"
            ).first
        if header_checkbox.count() > 0 and header_checkbox.is_visible():
            print("[DEBUG delete] header checkbox found")
            try:
                header_checkbox.check(force=True)
            except Exception:
                header_checkbox.click(force=True)
            self.page.wait_for_timeout(300)
            try:
                if header_checkbox.is_checked():
                    print("[DEBUG delete] header checkbox checked")
                    row_checkbox = header_checkbox
                else:
                    print("[DEBUG delete] header checkbox not checked after click")
                    row_checkbox = row.locator("input[type='checkbox']").first
            except Exception:
                print("[DEBUG delete] header checkbox check-state exception")
                row_checkbox = row.locator("input[type='checkbox']").first
        else:
            print("[DEBUG delete] header checkbox not found, fallback to row checkbox")
            row_checkbox = row.locator(
            "input[aria-label='Переключить выбор строки'], "
            "input[aria-label*='Переключить выбор'], "
            "input[aria-label*='Toggle select row'], "
            "input.PrivateSwitchBase-input[data-indeterminate], "
            "input.PrivateSwitchBase-input.css-j8yymo, "
            "td:nth-child(2) div div span input[type='checkbox'], "
            "td:nth-child(2) span input[type='checkbox'], "
            "input[type='checkbox']"
            ).first
        if row_checkbox.count() == 0 or not row_checkbox.is_visible():
            row_checkbox = self.page.locator(
                ".ant-table-tbody tr.ant-table-row-selected input[aria-label='Переключить выбор строки'], "
                ".ant-table-tbody tr input[aria-label='Переключить выбор строки']"
            ).first
            if row_checkbox.count() == 0 or not row_checkbox.is_visible():
                print("[DEBUG delete] row checkbox not found/visible")
                return False
        print("[DEBUG delete] row checkbox found")
        try:
            row_checkbox.check(force=True)
        except Exception:
            row_checkbox.click(force=True)
        self.page.wait_for_timeout(300)
        # XPath-фолбэк: если чекбокс не отмечен, кликаем чекбокс ТОЛЬКО в пределах найденной строки.
        try:
            is_checked = row_checkbox.is_checked()
        except Exception:
            is_checked = False
        if not is_checked:
            xpath_checkbox = row.locator("xpath=.//td[2]//input[@type='checkbox']").first
            if xpath_checkbox.count() > 0 and xpath_checkbox.is_visible():
                xpath_checkbox.click(force=True)
                self.page.wait_for_timeout(300)
                try:
                    is_checked = xpath_checkbox.is_checked()
                except Exception:
                    is_checked = False
        if not is_checked:
            print("[DEBUG delete] checkbox is not checked")
            return False
        print("[DEBUG delete] checkbox is checked")

        toolbar_delete = self.page.locator(
            "button.index_button__EOmvq.index_sizeMedium__X6QMI.index_outline__LLx1E.ant-btn-dangerous.ant-btn-icon-only:not([disabled])"
        ).first
        if toolbar_delete.count() == 0:
            toolbar_delete = self.page.locator(
                "button.ant-btn-dangerous.ant-btn-icon-only.ant-tooltip-open:not([disabled]), "
                "button.ant-btn-dangerous.ant-btn-icon-only:not([disabled])"
            ).first
        if toolbar_delete.count() == 0 or not toolbar_delete.is_visible():
            print("[DEBUG delete] delete button not found/visible")
            return False
        print("[DEBUG delete] delete button found and visible")
        toolbar_delete.click(force=True)
        self.page.wait_for_timeout(300)

        had_dialog = self.delete_dialog_visible()
        self.confirm_delete_dialog_if_visible()
        self.apply_changes_if_present()
        self.page.wait_for_timeout(900)
        deleted_by_id = not self.is_person_id_openable(person_id)
        # Доп.проверка: строка должна исчезнуть из списка по номеру/имени.
        try:
            self.go_back_to_personnel_list()
            self.ensure_all_filter_selected()
            try:
                self.search_person_in_list(query)
            except Exception:
                pass
            still_in_list = self.person_exists(query) or self.person_exists(person_name)
        except Exception:
            still_in_list = True
        deleted_by_list = not still_in_list
        deleted = deleted_by_id or (had_dialog and deleted_by_list)
        print(f"[DEBUG delete] had_dialog={had_dialog} deleted_by_id={deleted_by_id} deleted_by_list={deleted_by_list}")
        print(f"[DEBUG delete] deleted={deleted}")
        return deleted

    def ensure_all_filter_selected(self) -> None:
        selected = self.page.locator(
            ".ant-select-selection-item[title='Все'], "
            ".ant-select-selection-item[title='All'], "
            ".ant-select-selection-item:has-text('Все'), "
            ".ant-select-selection-item:has-text('All')"
        ).first
        if selected.count() > 0 and selected.is_visible():
            return

        selector = self.page.locator(
            ".ant-select-selector:has(.ant-select-selection-search-input[role='combobox'])"
        ).first
        if selector.count() == 0 or not selector.is_visible():
            return

        selector.click(force=True)
        self.page.wait_for_timeout(250)
        all_option = self.page.locator(
            ".ant-select-item-option[title='All'], "
            ".ant-select-item-option:has-text('All'), "
            ".ant-select-item-option[title='Все'], "
            ".ant-select-item-option:has-text('Все')"
        ).first
        if all_option.count() > 0 and all_option.is_visible():
            all_option.click(force=True)
            self.page.wait_for_timeout(400)

    def search_person_in_list(self, query: str) -> None:
        # Сначала активируем скрытый search-контрол, чтобы появился Visible-вариант.
        hidden_search_button = self.page.locator(
            "div.index_inputContainer__OlsaL span.index_searchInput__Hidden__e3LW- button.index_searchButton__jEElX"
        ).first
        if hidden_search_button.count() > 0 and hidden_search_button.is_visible():
            hidden_search_button.click(force=True)
            self.page.wait_for_timeout(300)

        # Иногда тулбар со строкой поиска рендерится с задержкой после возврата из карточки.
        for _ in range(6):
            wrapper = self.page.locator(
                "span.index_searchInput__ODJxi.index_searchInput__Visible__bxgWK"
            ).first
            if wrapper.count() > 0 and wrapper.is_visible():
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
            # Фолбэк: клик по контейнеру списка, чтобы активировать toolbar.
            list_region = self.page.locator(".ant-table-wrapper, .ant-table, .ant-list, .index_table").first
            if list_region.count() > 0 and list_region.is_visible():
                list_region.click(force=True)
                self.page.wait_for_timeout(250)
        else:
            raise AssertionError("Не найден целевой поиск Personnel: index_searchInput__Visible__bxgWK")

        search_input = wrapper.locator("input.ant-input[type='text']").first
        if search_input.count() == 0 or not search_input.is_visible():
            raise AssertionError("Не найден input поиска Personnel внутри целевого search-wrapper")

        search_input.click()
        search_input.fill("")
        search_input.fill(query)
        self.page.wait_for_timeout(150)

        search_button = wrapper.locator("button.index_searchButton__jEElX").first
        if search_button.count() == 0 or not search_button.is_visible():
            raise AssertionError("Не найдена кнопка поиска Personnel: index_searchButton__jEElX")

        search_button.click(force=True)
        self.page.wait_for_timeout(900)

    def confirm_delete_dialog_if_visible(self) -> None:
        modal = self.page.locator(".ant-modal:visible, [role='dialog']:visible").first
        if modal.count() == 0:
            # В некоторых экранах подтверждение удаления приходит через popconfirm/dropdown.
            for btn in (
                self.page.locator(".ant-popover button.ant-btn-dangerous").first,
                self.page.locator(".ant-popconfirm button.ant-btn-dangerous").first,
                self.page.locator("button.ant-btn-dangerous:has-text('Delete')").first,
                self.page.locator("button.ant-btn-dangerous:has-text('Удалить')").first,
            ):
                if btn.count() > 0 and btn.is_visible():
                    btn.click(force=True)
                    self.page.wait_for_timeout(400)
                    return
            return

        dangerous = self.page.locator(".ant-modal .ant-modal-footer .ant-btn-dangerous").first
        if dangerous.count() > 0 and dangerous.is_visible():
            dangerous.click()
            self.page.wait_for_timeout(400)
            return

        primary = self.page.locator(".ant-modal .ant-modal-footer .ant-btn-primary").first
        if primary.count() > 0 and primary.is_visible():
            primary.click()
            self.page.wait_for_timeout(400)
            return

        for text in ("Delete", "Удалить", "OK", "Ок", "Yes", "Да", "Confirm", "Подтвердить"):
            btn = self.page.get_by_text(text, exact=True)
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click()
                self.page.wait_for_timeout(400)
                return
