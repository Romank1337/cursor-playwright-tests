"""
Page Object для раздела Directories -> Devices.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from urllib.parse import urlsplit

from playwright.sync_api import Page, expect


@dataclass(frozen=True)
class DevicesPage:
    page: Page
    login_url: str
    username: str
    password: str

    @property
    def new_device_button(self):
        # Поддерживаем обе локали интерфейса (EN/RU).
        return self.page.locator(
            "button:has-text('New device'), button:has-text('Новое устройство'), "
            "button:has-text('Создать устройство'), button:has-text('Новый')"
        ).first.or_(self.page.get_by_text("New device", exact=True)).or_(
            self.page.get_by_text("Новое устройство", exact=True)
        ).first

    @property
    def apply_button(self):
        # Поддерживаем обе локали интерфейса (EN/RU).
        return self.page.locator(
            "button:has-text('Apply'), button:has-text('Применить')"
        ).first.or_(self.page.get_by_text("Apply", exact=True)).or_(
            self.page.get_by_text("Применить", exact=True)
        ).first

    @property
    def delete_all_button(self):
        return self.page.locator("button:has-text('Delete all'), button:has-text('Удалить все')").first

    @property
    def name_input(self):
        return self.page.locator("#control-device_Name")

    @property
    def ip_input(self):
        return self.page.locator("#control-device_IPAddress")

    @property
    def uid_input(self):
        return self.page.locator("#control-device_UniqueDeviceID")

    @property
    def comment_input(self):
        return self.page.locator("#control-device_Comment")

    @property
    def type_select(self):
        return self.page.locator("#control-device_DeviceTypeId")

    @property
    def devices_list_items(self):
        # В текущем UI устройства отображаются карточками/листом, а не таблицей.
        return self.page.locator(".ant-list-item")

    @property
    def save_button(self):
        return self.page.get_by_text("Save", exact=True)

    @property
    def cancel_button(self):
        return self.page.get_by_text("Cancel", exact=True)

    def open(self) -> None:
        parsed = urlsplit(self.login_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        devices_url = f"{base}/list/devices"

        self.page.goto(self.login_url, wait_until="domcontentloaded")
        self.page.locator("#login").fill(self.username)
        self.page.locator("#password").fill(self.password)
        self.page.locator("button[type='submit']").click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(700)

        # Стабильный переход: идем напрямую в раздел устройств.
        self.page.goto(devices_url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(700)

        # Если неавторизовано и нас вернули на login?redirect=..., логинимся повторно.
        if "/user/login" in self.page.url:
            self.page.locator("#login").fill(self.username)
            self.page.locator("#password").fill(self.password)
            self.page.locator("button[type='submit']").click()
            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(700)
            if "/list/devices" not in self.page.url:
                self.page.goto(devices_url, wait_until="domcontentloaded")
                self.page.wait_for_timeout(700)

    def _toolbar_button_locator(self):
        # На UI кнопка может называться "New device" / "Создать" / "Create",
        # либо быть кнопкой с иконкой plus без явного текста. Берём первое попавшееся.
        return self.page.locator(
            "button:has-text('New device'), button:has-text('Create'), "
            "button:has-text('Создать'), button:has(.anticon-plus)"
        ).first

    def assert_loaded(self, timeout_ms: int = 20000) -> None:
        # Шапка раздела иногда подгружается с задержкой (фронт «прогревается»),
        # поэтому: 1) ждём долго; 2) при отсутствии — делаем один reload+open;
        # 3) принимаем расширенный набор вариантов кнопки создания.
        toolbar_btn = self._toolbar_button_locator()
        try:
            expect(toolbar_btn).to_be_visible(timeout=timeout_ms)
            return
        except AssertionError:
            pass

        # Один retry: перелогиниваемся/переходим в раздел заново.
        self.open()
        expect(self._toolbar_button_locator()).to_be_visible(timeout=timeout_ms)

    def open_create_form(self) -> bool:
        parsed = urlsplit(self.login_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        candidates = (
            self.new_device_button.first,
            self.page.get_by_text("Create", exact=True).first,
            self.page.get_by_text("Создать", exact=True).first,
            self.page.locator("button[class*='index_button']").filter(has_text="New").first,
            self.page.locator("button[class*='index_button']").filter(has_text="Создать").first,
            self.page.locator("button:has(.anticon-plus)").first,
        )
        for btn in candidates:
            if btn.count() > 0 and btn.is_visible():
                try:
                    btn.click(timeout=3000)
                except Exception:
                    btn.click(force=True)
                self.page.wait_for_timeout(500)
                if "/user/login" in self.page.url:
                    # При внезапном редиректе логинимся и возвращаемся в Devices.
                    self.open()
                    continue
                if self.name_input.count() > 0:
                    return True

        # Фолбэк: прямой переход в форму создания.
        self.page.goto(f"{base}/list/devices/0", wait_until="domcontentloaded")
        self.page.wait_for_timeout(700)
        if "/user/login" in self.page.url:
            self.open()
            self.page.goto(f"{base}/list/devices/0", wait_until="domcontentloaded")
            self.page.wait_for_timeout(700)
        if self.name_input.count() > 0 and self.name_input.first.is_visible():
            return True
        return False

    def save_form(self) -> None:
        self.save_button.click()
        self.page.wait_for_timeout(500)

    def apply_changes(self) -> None:
        btn = self.apply_button
        btn.scroll_into_view_if_needed()
        try:
            btn.click(timeout=3000)
        except Exception:
            btn.click(force=True)
        self.page.wait_for_timeout(700)

    def cancel_form(self) -> None:
        if self.cancel_button.count() > 0:
            self.cancel_button.click()
            self.page.wait_for_timeout(400)

    def fill_device_form(self, name: str, uid: str, comment: str) -> None:
        self.name_input.fill(name)
        self.uid_input.fill(uid)
        self.comment_input.fill(comment)

    def select_device_type_if_needed(self) -> None:
        # Пытаемся выбрать тип устройства в обеих возможных реализациях:
        # 1) нативный <select>, 2) AntD Select.
        native_options = self.page.locator("#control-device_DeviceTypeId option")
        if native_options.count() > 1:
            self.type_select.select_option(index=1)
            self.page.wait_for_timeout(300)
            return

        select_root = self.page.locator("#control-device_DeviceTypeId").first
        if select_root.count() > 0:
            select_root.click()
            self.page.wait_for_timeout(250)
            first_option = self.page.locator(".ant-select-item-option").first
            if first_option.count() > 0:
                first_option.click()
                self.page.wait_for_timeout(300)

    def ip_field_is_readonly_or_disabled(self) -> bool:
        # На текущем UI IP у нового устройства автозаполняется и не редактируется вручную.
        disabled_attr = self.ip_input.get_attribute("disabled")
        readonly_attr = self.ip_input.get_attribute("readonly")
        return disabled_attr is not None or readonly_attr is not None

    def has_required_form_controls(self) -> bool:
        return (
            self.name_input.count() > 0
            and self.type_select.count() > 0
            and self.ip_input.count() > 0
            and self.uid_input.count() > 0
        )

    def has_rows(self) -> bool:
        return self.devices_list_items.count() > 0

    def rows_count(self) -> int:
        return self.devices_list_items.count()

    def rows_count_wait(self, timeout_ms: int = 5000) -> int:
        # Ждём, пока список устройств стабилизируется (подгрузка после открытия раздела).
        self.page.wait_for_timeout(500)
        started = time.monotonic()
        last = self.rows_count()
        while True:
            self.page.wait_for_timeout(300)
            cur = self.rows_count()
            if cur == last and cur > 0:
                return cur
            last = cur
            if (time.monotonic() - started) * 1000 > timeout_ms:
                return cur

    def wait_until_has_rows(self, timeout_ms: int = 15000) -> int:
        started = time.monotonic()
        while True:
            cur = self.rows_count()
            if cur > 0:
                return cur
            self.page.wait_for_timeout(400)
            if (time.monotonic() - started) * 1000 > timeout_ms:
                return cur

    def click_first_row(self) -> bool:
        if self.devices_list_items.count() == 0:
            return False
        self.devices_list_items.first.click()
        self.page.wait_for_timeout(400)
        return True

    def open_device_by_name(self, name: str) -> bool:
        row = self.page.locator(".ant-list-item", has_text=name).first
        if row.count() == 0:
            return False
        row.scroll_into_view_if_needed()
        row.click()
        self.page.wait_for_timeout(500)
        return True

    def device_exists_in_list(self, name: str) -> bool:
        return self.page.locator(".ant-list-item", has_text=name).count() > 0

    def delete_device_by_name_from_list(self, name: str) -> bool:
        row = self.page.locator(".ant-list-item", has_text=name).first
        if row.count() == 0:
            return False

        row.scroll_into_view_if_needed()
        # Сначала пробуем явные текстовые кнопки удаления внутри карточки.
        candidates = (
            row.get_by_role("button", name="Delete", exact=True).first,
            row.get_by_role("button", name="Удалить", exact=True).first,
            row.locator("button.ant-btn-dangerous").first,
            row.locator("button:has(.anticon-delete)").first,
            row.locator("[title*='Delete'], [title*='Удалить']").first,
        )
        for btn in candidates:
            if btn.count() > 0 and btn.first.is_visible():
                try:
                    btn.first.click(timeout=3000)
                except Exception:
                    btn.first.click(force=True)
                self.page.wait_for_timeout(300)
                return True

        # Фолбэк: пробуем клик по иконке удаления в строке.
        icon = row.locator(".anticon-delete").first
        if icon.count() > 0 and icon.is_visible():
            icon.click(force=True)
            self.page.wait_for_timeout(300)
            return True

        return False

    def trigger_delete_all(self) -> None:
        btn = self.delete_all_button
        btn.scroll_into_view_if_needed()
        try:
            btn.click(timeout=3000)
        except Exception:
            btn.click(force=True)
        self.page.wait_for_timeout(300)

    def delete_dialog_visible(self) -> bool:
        dlg = self.page.locator(".ant-modal, [role='dialog']")
        return dlg.count() > 0 and dlg.first.is_visible()

    def cancel_delete_dialog(self) -> None:
        for text in ("Cancel", "Отмена", "No"):
            btn = self.page.get_by_text(text, exact=True)
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click()
                self.page.wait_for_timeout(200)
                return
        close_btn = self.page.locator(".ant-modal-close").first
        if close_btn.count() > 0:
            close_btn.click()
            self.page.wait_for_timeout(200)

    def confirm_delete_dialog(self) -> None:
        dangerous_in_dialog = self.page.locator(".ant-modal .ant-modal-footer .ant-btn-dangerous").first
        if dangerous_in_dialog.count() > 0 and dangerous_in_dialog.is_visible():
            dangerous_in_dialog.click()
            self.page.wait_for_timeout(400)
            return

        primary_in_dialog = self.page.locator(".ant-modal .ant-modal-footer .ant-btn-primary").first
        if primary_in_dialog.count() > 0 and primary_in_dialog.is_visible():
            primary_in_dialog.click()
            self.page.wait_for_timeout(400)
            return

        for text in ("Delete", "Удалить", "OK", "Ок", "Yes", "Да", "Confirm"):
            btn = self.page.get_by_text(text, exact=True)
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click()
                self.page.wait_for_timeout(400)
                return

    def trigger_delete_current_device(self) -> None:
        candidates = (
            self.page.get_by_role("button", name="Delete", exact=True).first,
            self.page.get_by_role("button", name="Удалить", exact=True).first,
            self.page.locator("button.ant-btn-dangerous").first,
            self.page.locator("button:has(.anticon-delete)").first,
            self.page.locator("[title*='Delete'], [title*='Удалить']").first,
        )
        for btn in candidates:
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.scroll_into_view_if_needed()
                try:
                    btn.first.click(timeout=3000)
                except Exception:
                    btn.first.click(force=True)
                self.page.wait_for_timeout(300)
                return

        delete_icon = self.page.locator(".anticon-delete").first
        if delete_icon.count() > 0 and delete_icon.is_visible():
            icon_btn = delete_icon.locator("xpath=ancestor::button[1]")
            if icon_btn.count() > 0:
                icon_btn.first.click(force=True)
                self.page.wait_for_timeout(300)
                return

        raise AssertionError("Не найдена кнопка удаления текущего устройства")

