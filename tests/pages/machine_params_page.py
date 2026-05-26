"""
Page Object для страницы параметров оборудования (machineParams).
"""

from dataclasses import dataclass
import re

from playwright.sync_api import Locator, Page, expect

from tests.pages.components.machine_state_form_component import MachineStateFormComponent


@dataclass(frozen=True)
class MachineParamsPage:
    page: Page
    machine_params_url: str

    @property
    def new_state_button(self) -> Locator:
        # Возможные тексты/селекторы для действия "Add/Добавить".
        return self.page.locator("div[role='button'][aria-label='Добавить']:visible").or_(
            self.page.locator("div.dx-button[title='Добавить']:visible")
        ).or_(
            self.page.locator("div.dx-button:has(.dx-icon-plus):visible")
        ).or_(
            self.page.get_by_role("button", name="Новое состояние")
        ).or_(
            self.page.get_by_role("button", name="Добавить состояние")
        ).or_(self.page.get_by_role("button", name="Создать")).or_(
            self.page.get_by_role("button", name="Добавить")
        ).or_(
            self.page.locator(".ant-btn .anticon-plus").locator("xpath=ancestor::button[1]")
        ).or_(
            self.page.get_by_text("Add", exact=True)
        ).or_(
            self.page.get_by_text("Добавить", exact=True)
        ).or_(
            self.page.locator("[data-testid='new-state'], [data-testid='create-state']")
        ).first

    @property
    def loading_spinner(self) -> Locator:
        return self.page.locator(".ant-spin-spinning")

    @property
    def edit_state_button(self) -> Locator:
        # Берём именно видимую кнопку (DevExtreme может скрывать неактивные).
        return self.page.locator(
            "div[role='button'][aria-label='Редактировать']:visible"
        ).first.or_(
            self.page.locator("div.dx-button[title='Редактировать']:visible").first
        ).or_(
            self.page.locator(
                ".dx-button:not(.dx-state-disabled) .dx-button-text:text-is('Редактировать')"
            ).locator("xpath=ancestor::div[contains(@class,'dx-button')][1]").first
        ).or_(
            self.page.get_by_role("button", name="Редактировать")
        ).first

    @property
    def delete_state_button(self) -> Locator:
        return self.page.locator(
            "div[role='button'][aria-label='Удалить']:visible"
        ).first.or_(
            self.page.locator("div.dx-button[title='Удалить']:visible").first
        ).or_(
            self.page.locator(
                ".dx-button:not(.dx-state-disabled) .dx-button-text:text-is('Удалить')"
            ).locator("xpath=ancestor::div[contains(@class,'dx-button')][1]").first
        ).or_(
            self.page.get_by_role("button", name="Удалить")
        ).first

    @property
    def edit_parameter_button(self) -> Locator:
        # Для вкладки "Параметры" кнопка может визуально оставаться в dx-state-disabled,
        # поэтому ищем по тексту/aria без фильтра по disabled и кликаем с force=True.
        return self.page.locator(
            "div[role='button'][aria-label='Редактировать']:visible, "
            "div[role='button'][aria-label='Edit']:visible, "
            "div.dx-button:has(.dx-button-text:has-text('Редактировать')):visible, "
            "div.dx-button:has(.dx-button-text:has-text('Edit')):visible"
        ).first

    @property
    def delete_parameter_button(self) -> Locator:
        return self.page.locator(
            "div[role='button'][aria-label='Удалить']:visible, "
            "div[role='button'][aria-label='Delete']:visible, "
            "div.dx-button:has(.dx-button-text:has-text('Удалить')):visible, "
            "div.dx-button:has(.dx-button-text:has-text('Delete')):visible"
        ).first

    def open(self) -> None:
        self.page.goto(self.machine_params_url, wait_until="domcontentloaded")

    def assert_loaded(self) -> None:
        expect(self.page).to_have_url(re.compile(r".*/list/machineParams.*"), timeout=20_000)
        # На странице используется общий spinner во время загрузки данных.
        expect(self.loading_spinner).to_have_count(0, timeout=30_000)
        # Базовый признак загрузки таблицы: колонка "Наименование".
        expect(self.page.get_by_text("Наименование", exact=True)).to_be_visible(timeout=20_000)

    def open_create_state_form(self) -> MachineStateFormComponent:
        expect(self.new_state_button).to_be_visible(timeout=20_000)
        self.new_state_button.click()
        return MachineStateFormComponent(page=self.page)

    def open_create_parameter_form(self) -> MachineStateFormComponent:
        self.open_parameters_tab()
        add_parameter_button = self.page.locator(
            "div[role='button'][aria-label='Добавить']:visible"
        ).first.or_(
            self.page.locator("div.dx-button[title='Добавить']:visible").first
        )
        expect(add_parameter_button).to_be_visible(timeout=20_000)
        add_parameter_button.click()
        return MachineStateFormComponent(page=self.page)

    def open_edit_state_form(self, state_name: str) -> MachineStateFormComponent:
        row = self._find_row_in_tree(state_name)
        expect(row).to_be_visible(timeout=20_000)
        self._select_row(row)
        expect(self.edit_state_button).to_be_visible(timeout=20_000)
        self.edit_state_button.click()
        return MachineStateFormComponent(page=self.page)

    def _select_row(self, row: Locator) -> None:
        # DevExtreme включает кнопки "Редактировать"/"Удалить" только после выбора строки.
        # Клик по конкретной ячейке надёжнее активирует выбор, чем клик по <tr>.
        row.scroll_into_view_if_needed()
        cell = row.locator("td[role='gridcell']:visible").first
        if cell.count() > 0:
            cell.click()
        else:
            row.click()
        self.page.wait_for_timeout(300)

    def open_edit_parameter_form(self, parameter_name: str) -> MachineStateFormComponent:
        # Для параметров кнопки тулбара могут оставаться визуально disabled, но кликабельны
        # после выделения строки — поэтому не дожидаемся снятия disabled и кликаем force=True.
        self.open_parameters_tab()
        row = self._find_row_in_tree(parameter_name)
        expect(row).to_be_visible(timeout=20_000)
        self._select_row(row)
        expect(self.edit_parameter_button).to_be_visible(timeout=20_000)
        self.edit_parameter_button.click(force=True)
        return MachineStateFormComponent(page=self.page)

    def delete_parameter(self, parameter_name: str) -> None:
        # Аналогично open_edit_parameter_form: кнопка визуально может быть disabled, но кликабельна.
        self.open_parameters_tab()
        row = self._find_row_in_tree(parameter_name)
        expect(row).to_be_visible(timeout=20_000)
        self._select_row(row)
        expect(self.delete_parameter_button).to_be_visible(timeout=20_000)
        self.delete_parameter_button.click(force=True)

        dialog = self.page.locator(".dx-overlay-content:visible").filter(
            has=self.page.locator(":text-is('Удаление записи'), :text-is('Delete record')")
        ).first
        expect(dialog).to_be_visible(timeout=20_000)

        # Точечный селектор: ищем кнопку именно по тексту "Да"/"Yes" внутри блока кнопок диалога.
        yes_button = dialog.locator(
            ".dx-dialog-buttons .dx-button .dx-button-text:text-is('Да'), "
            ".dx-dialog-buttons .dx-button .dx-button-text:text-is('Yes')"
        ).locator("xpath=ancestor::div[contains(@class,'dx-button')][1]").first
        expect(yes_button).to_be_visible(timeout=20_000)
        yes_button.click(force=True)

        # Ждём фактического закрытия диалога; force=True ранее мог сработать вхолостую.
        try:
            expect(dialog).to_be_hidden(timeout=10_000)
        except Exception:
            # Повторный клик — иногда первый промахивается мимо элемента.
            yes_button.click(force=True)
            expect(dialog).to_be_hidden(timeout=10_000)
        self.page.wait_for_timeout(2_000)

    def assert_state_visible(self, state_name: str) -> None:
        matching_row = self._find_row_in_tree(state_name)
        expect(matching_row).to_be_visible(timeout=20_000)

    def delete_state(self, state_name: str) -> None:
        row = self._find_row_in_tree(state_name)
        expect(row).to_be_visible(timeout=20_000)
        self._select_row(row)
        expect(self.delete_state_button).to_be_visible(timeout=20_000)
        self.delete_state_button.click()
        dialog = self.page.locator(
            ".dx-overlay-content.dx-popup-normal.dx-popup-draggable.dx-resizable.dx-popup-inherit-height"
        ).filter(
            has=self.page.locator(".dx-popup-title:has-text('Удаление записи')")
        ).first
        expect(dialog).to_be_visible(timeout=20_000)

        yes_button = dialog.locator(
            "div[role='button'][aria-label='Да'].dx-widget.dx-button.dx-dialog-button"
        ).first.or_(
            dialog.locator(".dx-dialog-buttons .dx-button:has(.dx-button-text:text-is('Да'))").first
        ).or_(
            dialog.locator(".dx-dialog-buttons .dx-button:has(.dx-button-text:text-is('Yes'))").first
        )

        # Фолбэк: если подпись кнопки отличается, берём первую кнопку в блоке подтверждения.
        confirm_buttons = dialog.locator(".dx-dialog-buttons .dx-button")
        expect(confirm_buttons.first).to_be_visible(timeout=20_000)
        if yes_button.count() > 0:
            yes_button.click(force=True)
        else:
            confirm_buttons.first.click(force=True)
        # Активно ждём закрытия диалога — это сигнал, что бэкенд принял запрос на удаление.
        try:
            expect(dialog).to_be_hidden(timeout=10_000)
        except Exception:
            # Иногда первый клик "промахивается" — повторяем.
            if yes_button.count() > 0:
                yes_button.click(force=True)
            else:
                confirm_buttons.first.click(force=True)
            expect(dialog).to_be_hidden(timeout=10_000)
        # Небольшая пауза, чтобы грид обновился перед последующим assert'ом отсутствия строки.
        self.page.wait_for_timeout(2_000)

    def open_parameters_tab(self) -> None:
        parameters_tab = self.page.locator("span.dx-tab-text", has_text="Параметры").first
        expect(parameters_tab).to_be_visible(timeout=20_000)
        parameters_tab.click()
        # После переключения вкладки даём гриду догрузить данные.
        expect(self.loading_spinner).to_have_count(0, timeout=20_000)
        self.page.wait_for_timeout(500)

    def assert_state_not_visible(self, state_name: str) -> None:
        row = self._find_row_in_tree(state_name)
        expect(row).to_have_count(0, timeout=20_000)

    def assert_parameter_visible(self, parameter_name: str) -> None:
        # Используем общий помощник, который умеет скроллить виртуализированный treeList.
        matching_row = self._find_row_in_tree(parameter_name)
        expect(matching_row).to_be_visible(timeout=20_000)

    def _find_row_in_tree(self, state_name: str) -> Locator:
        # Ищем строку в любом видимом DevExtreme-гриде с учётом виртуализации.
        # На странице есть как dxTreeList (вкладка "Состояния"), так и dxDataGrid
        # (вкладка "Параметры"), оба используют класс .dx-data-row для данных.
        tree_rows = self.page.locator(
            ".dx-treelist tr.dx-data-row:visible, .dx-datagrid tr.dx-data-row:visible, "
            "#treeList tr.dx-data-row, #dataGrid tr.dx-data-row"
        )
        matching_row = tree_rows.filter(has_text=state_name).first
        if matching_row.count() > 0:
            return matching_row

        scroll_container = self.page.locator(
            ".dx-treelist .dx-scrollable-container, .dx-treelist .dx-scrollable-content, "
            ".dx-datagrid .dx-scrollable-container, .dx-datagrid .dx-scrollable-content"
        ).first
        if scroll_container.count() > 0:
            scroll_container.evaluate("el => { el.scrollTop = 0; }")
            self.page.wait_for_timeout(500)
            for _ in range(30):
                if matching_row.count() > 0:
                    return matching_row
                scroll_container.evaluate(
                    "el => { el.scrollTop = Math.min(el.scrollTop + el.clientHeight, el.scrollHeight); }"
                )
                self.page.wait_for_timeout(700)

        return matching_row

    def _find_row_by_name_column(self, item_name: str) -> Locator:
        # Для параметров проверяем именно колонку "Наименование".
        name_column_cell = self.page.locator(
            "#treeList tr.dx-data-row td[role='gridcell'][aria-colindex='1']"
        ).filter(has_text=item_name).first
        if name_column_cell.count() > 0:
            return name_column_cell.locator("xpath=ancestor::tr[contains(@class,'dx-data-row')][1]").first

        # Фолбэк по тексту ячейки (если aria-colindex отличается в окружении).
        first_column_cell = self.page.locator(
            "#treeList tr.dx-data-row td[role='gridcell']"
        ).filter(has_text=item_name).first
        return first_column_cell.locator("xpath=ancestor::tr[1]").first

    def _find_row_by_name_column_with_scroll(self, item_name: str) -> Locator:
        # DevExtreme treeList виртуализирует строки, поэтому скроллим список,
        # пока не найдём нужную ячейку или пока не достигнем конца.
        matching_row = self._find_row_by_name_column(item_name)
        if matching_row.count() > 0:
            return matching_row

        scroll_container = self.page.locator(
            "#treeList .dx-scrollable-container, #treeList .dx-scrollable-content"
        ).first
        if scroll_container.count() == 0:
            return matching_row

        scroll_container.evaluate("el => { el.scrollTop = 0; }")
        self.page.wait_for_timeout(500)
        for _ in range(30):
            matching_row = self._find_row_by_name_column(item_name)
            if matching_row.count() > 0:
                return matching_row
            scroll_container.evaluate(
                "el => { el.scrollTop = Math.min(el.scrollTop + el.clientHeight, el.scrollHeight); }"
            )
            self.page.wait_for_timeout(700)
        return matching_row
