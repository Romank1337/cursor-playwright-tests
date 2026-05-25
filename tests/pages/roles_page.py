"""
Page Object для страницы справочника ролей.
"""

from dataclasses import dataclass
import re

from playwright.sync_api import Locator, Page, expect


@dataclass(frozen=True)
class RolesPage:
    page: Page
    roles_url: str

    @property
    def add_button(self) -> Locator:
        return self.page.locator("div[role='button'][aria-label='Добавить']:visible").or_(
            self.page.locator("div.dx-button[title='Добавить']:visible")
        ).or_(
            self.page.locator("div.dx-button:has(.dx-icon-plus):visible")
        ).or_(self.page.get_by_role("button", name="Добавить")).or_(
            self.page.get_by_role("button", name="Add")
        ).first

    @property
    def edit_button(self) -> Locator:
        return self.page.locator("div[role='button'][aria-label='Редактировать']:visible").or_(
            self.page.locator("div.dx-button[title='Редактировать']:visible")
        ).or_(
            self.page.get_by_role("button", name="Редактировать")
        ).or_(
            self.page.locator(".dx-button .dx-icon-edit").locator(
                "xpath=ancestor::div[contains(@class,'dx-button')][1]"
            )
        ).first

    @property
    def delete_button(self) -> Locator:
        return self.page.locator("div[role='button'][aria-label='Удалить']:visible").or_(
            self.page.locator("div.dx-button[title='Удалить']:visible")
        ).or_(
            self.page.get_by_role("button", name="Удалить")
        ).or_(
            self.page.locator(".dx-button .dx-icon-trash").locator(
                "xpath=ancestor::div[contains(@class,'dx-button')][1]"
            )
        ).first

    @property
    def active_popup(self) -> Locator:
        # На workerRoles форма может открываться как popup или в сайд-панели.
        return self.page.locator(
            ".dx-overlay-content:visible, .dx-popup-content:visible, "
            ".ant-modal-content:visible, .ant-drawer-content:visible"
        ).first

    @property
    def role_name_input(self) -> Locator:
        return self.page.locator(
            "input[data-testid='worker_role_Name']:visible, "
            "input[name='name']:visible, input[id*='name']:visible, "
            "input[placeholder*='Наименование']:visible, input[placeholder*='Название']:visible, "
            ".dx-field-item:has-text('Наименование') .dx-texteditor-input:visible, "
            ".dx-field-item:has-text('Название') .dx-texteditor-input:visible"
        ).first

    @property
    def role_description_input(self) -> Locator:
        return self.page.locator(
            "input[data-testid='worker_role_Description']:visible, "
            "textarea[data-testid='worker_role_Description']:visible, "
            "input[name='description']:visible, textarea[name='description']:visible, "
            "input[id*='description']:visible, textarea[id*='description']:visible"
        ).first

    @property
    def save_button(self) -> Locator:
        return self.page.get_by_role("button", name="Сохранить").or_(
            self.page.get_by_role("button", name="Save")
        ).or_(
            self.page.locator(
                ".dx-button .dx-button-text"
            ).filter(has_text="Сохранить").locator("xpath=ancestor::div[contains(@class,'dx-button')][1]")
        ).or_(
            self.page.locator(
                ".dx-button .dx-button-text"
            ).filter(has_text="Save").locator("xpath=ancestor::div[contains(@class,'dx-button')][1]")
        ).first

    def open(self) -> None:
        self.page.goto(self.roles_url, wait_until="domcontentloaded")

    def assert_loaded(self) -> None:
        expect(self.page).to_have_url(re.compile(r".*/list/workerRoles.*"), timeout=20_000)
        expect(self.add_button).to_be_visible(timeout=20_000)

    def create_role(self, role_name: str) -> None:
        expect(self.add_button).to_be_visible(timeout=20_000)
        self.add_button.click()
        expect(self.role_name_input).to_be_visible(timeout=20_000)
        self.role_name_input.fill(role_name)
        expect(self.role_description_input).to_be_visible(timeout=20_000)
        self.role_description_input.fill(f"Описание для {role_name}")
        expect(self.save_button).to_be_visible(timeout=20_000)
        self.save_button.click()
        # После сохранения ожидаем закрытие формы или переход в таблицу.
        self.page.wait_for_timeout(2_000)

    def assert_role_visible(self, role_name: str) -> None:
        role_row = self._find_role_row(role_name)
        expect(role_row).to_be_visible(timeout=20_000)

    def edit_role(self, current_role_name: str, new_role_name: str) -> None:
        role_row = self._find_role_row(current_role_name)
        expect(role_row).to_be_visible(timeout=20_000)
        role_row.click()
        expect(self.edit_button).to_be_visible(timeout=20_000)
        self.edit_button.click()
        expect(self.role_name_input).to_be_visible(timeout=20_000)
        self.role_name_input.fill(new_role_name)
        expect(self.role_description_input).to_be_visible(timeout=20_000)
        self.role_description_input.fill(f"Обновленное описание для {new_role_name}")
        expect(self.save_button).to_be_visible(timeout=20_000)
        self.save_button.click()
        self.page.wait_for_timeout(2_000)

    def delete_role(self, role_name: str) -> None:
        role_row = self._find_role_row(role_name)
        expect(role_row).to_be_visible(timeout=20_000)
        role_row.click()
        expect(self.delete_button).to_be_visible(timeout=20_000)
        self.delete_button.click()

        confirm_dialog = self.page.locator(
            ".dx-overlay-content:visible, .dx-dialog:visible, .dx-popup-content:visible"
        ).first
        expect(confirm_dialog).to_be_visible(timeout=20_000)

        yes_button = confirm_dialog.locator(
            "div[role='button'][aria-label='Да'].dx-widget.dx-button.dx-dialog-button:visible"
        ).or_(
            confirm_dialog.locator("div[role='button'][aria-label='Да']:visible")
        ).or_(
            confirm_dialog.get_by_role("button", name="Да")
        ).or_(
            confirm_dialog.get_by_role("button", name="Yes")
        ).first
        expect(yes_button).to_be_visible(timeout=20_000)
        yes_button.click(force=True)
        self.page.wait_for_timeout(2_000)

    def assert_role_not_visible(self, role_name: str) -> None:
        role_row = self._find_role_row(role_name)
        expect(role_row).to_have_count(0, timeout=20_000)

    def _find_role_row(self, role_name: str) -> Locator:
        return self.page.locator("#treeList tr.dx-data-row, .dx-datagrid-rowsview tr").filter(
            has_text=role_name
        ).first
