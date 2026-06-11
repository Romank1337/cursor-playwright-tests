"""
Page Object для раздела Directories -> Devices.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from urllib.parse import urlsplit

from playwright.sync_api import Page, expect


@dataclass(frozen=True)
class DevicesPage:
    page: Page
    login_url: str
    username: str
    password: str

    LIST_PATH = "/list/devices"
    _AUTH_MARKER = "_devices_authenticated"
    _LIST_SEARCH_INPUT = (
        'xpath=//*[@id="scrollable-container"]/main/div[2]/div/div[1]/div[2]/div/div[3]/span/input'
    )
    _LIST_SEARCH_BUTTON = (
        'xpath=//*[@id="scrollable-container"]/main/div[2]/div/div[1]/div[2]/div/div[3]/span/span/span'
    )

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
        self.page.wait_for_timeout(700)
        self._mark_authenticated()

    def _ensure_logged_in(self) -> None:
        if self._is_authenticated():
            return
        self._do_login_form()

    def _relogin_if_redirected(self) -> None:
        if "/user/login" not in self.page.url:
            return
        self._do_login_form()

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
        # Save — кликабельный текст, не всегда <button> (см. legacy devices-тесты).
        return self.page.get_by_text("Save", exact=True).or_(
            self.page.get_by_text("Сохранить", exact=True)
        ).first

    @property
    def cancel_button(self):
        return self.page.get_by_text("Cancel", exact=True).or_(
            self.page.get_by_text("Отмена", exact=True)
        ).first

    def open(self) -> None:
        target = f"{self._base()}{self.LIST_PATH}"
        if not self._is_authenticated():
            if "/user/login" in self.page.url:
                self._ensure_logged_in()
            else:
                self._mark_authenticated()
        self.page.goto(target, wait_until="domcontentloaded")
        self.page.wait_for_timeout(700)
        if "/user/login" in self.page.url:
            self._relogin_if_redirected()
            self.page.goto(target, wait_until="domcontentloaded")
            self.page.wait_for_timeout(700)

    def go_to_list(self) -> None:
        target = f"{self._base()}{self.LIST_PATH}"
        self.page.goto(target, wait_until="domcontentloaded")
        self.page.wait_for_timeout(700)
        self._relogin_if_redirected()
        if "/user/login" in self.page.url:
            self.page.goto(target, wait_until="domcontentloaded")
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
        base = self._base()
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
        btn = self.save_button
        btn.scroll_into_view_if_needed()
        try:
            btn.click(timeout=3000)
        except Exception:
            btn.click(force=True)
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

    def search_device_in_list(self, query: str) -> None:
        """Поиск устройства в списке: поле ввода + иконка лупы."""
        search_input = self.page.locator(self._LIST_SEARCH_INPUT).first
        if search_input.count() == 0 or not search_input.is_visible():
            return
        search_input.click()
        search_input.fill("")
        search_input.fill(query)
        self.page.wait_for_timeout(150)
        search_button = self.page.locator(self._LIST_SEARCH_BUTTON).first
        if search_button.count() > 0 and search_button.is_visible():
            try:
                search_button.click(timeout=3000)
            except Exception:
                search_button.click(force=True)
        else:
            search_input.press("Enter")
        self.page.wait_for_timeout(1_200)

    def _wait_for_device_row_visible(self, name: str, timeout_ms: int = 15_000) -> bool:
        started = time.monotonic()
        while True:
            row = self._device_row(name)
            if row.count() > 0 and row.is_visible():
                return True
            if (time.monotonic() - started) * 1000 > timeout_ms:
                return row.count() > 0 and row.is_visible()
            self.page.wait_for_timeout(600)

    def refresh_list_once(self) -> None:
        """Один переход на список устройств (без циклических перезагрузок)."""
        self.go_to_list()

    def _device_row(self, name: str):
        return self.page.locator(".ant-list-item", has_text=name).first

    def _row_action_menu_button(self, row):
        return row.locator(
            "button[class*='action-menu-dropdown-btn'], "
            "button.ant-dropdown-trigger:has(.anticon-more[aria-label='more'])"
        ).first

    def _visible_dropdown(self):
        return self.page.locator(".ant-dropdown:not(.ant-dropdown-hidden)").first

    def _wait_for_visible_dropdown(self, timeout_ms: int = 3_000) -> bool:
        menu = self._visible_dropdown()
        try:
            menu.wait_for(state="visible", timeout=timeout_ms)
            return True
        except Exception:
            return menu.count() > 0 and menu.is_visible()

    def _open_row_action_menu(self, row) -> bool:
        menu_btn = self._row_action_menu_button(row)
        if menu_btn.count() == 0 or not menu_btn.is_visible():
            return False
        try:
            menu_btn.click(timeout=3000)
        except Exception:
            menu_btn.click(force=True)
        return self._wait_for_visible_dropdown()

    def _click_action_menu_item(self, label_pattern: re.Pattern[str]) -> bool:
        menu = self.page.locator(".ant-dropdown:not(.ant-dropdown-hidden)")
        item = menu.locator(".ant-dropdown-menu-item").filter(has_text=label_pattern).first
        if item.count() == 0:
            item = menu.get_by_text(label_pattern).first
        if item.count() == 0:
            item = self.page.get_by_role("menuitem", name=label_pattern).first
        if item.count() == 0:
            return False
        try:
            item.click(timeout=3000)
        except Exception:
            item.click(force=True)
        self.page.wait_for_timeout(500)
        return True

    _EDIT_MENU_ITEM = re.compile(r"Edit|Редактировать", re.I)
    _DELETE_MENU_ITEM = re.compile(r"Delete|Удалить", re.I)
    _CONFIRM_DELETE_MENU_ITEM = re.compile(
        r"Подтвердить удаление|Confirm deletion|Confirm delete", re.I
    )
    _RC_MENU_POPUP_ITEM = (
        'xpath=//*[starts-with(@id, "rc-menu-uuid") and contains(@id, "-popup")]/li/span'
    )
    _CONFIRMATION_LAYER = (
        ".ant-modal:visible, .ant-popconfirm:visible, "
        "[role='alertdialog']:visible, [role='dialog']:visible"
    )
    def open_device_edit_form_by_name(self, name: str, *, search: bool = True) -> bool:
        """Открыть форму редактирования: ⋯ → Редактировать."""
        if search:
            self.search_device_in_list(name)
        row = self._device_row(name)
        if row.count() == 0:
            return False
        row.scroll_into_view_if_needed()
        if not self._open_row_action_menu(row):
            return False
        if not self._click_action_menu_item(self._EDIT_MENU_ITEM):
            return False
        try:
            self.name_input.wait_for(state="visible", timeout=10_000)
        except Exception:
            return False
        return True

    def open_device_by_name(self, name: str, *, search: bool = True) -> bool:
        return self.open_device_edit_form_by_name(name, search=search)

    def device_exists_in_list(self, name: str) -> bool:
        """Проверка строки в списке без поиска (legacy smoke-тесты)."""
        return self._device_row_visible(name)

    def find_device_in_list(self, name: str) -> bool:
        """Один проход: поиск + проверка строки."""
        self.search_device_in_list(name)
        return self._device_row_visible(name)

    def wait_until_device_found_by_search(
        self, name: str, timeout_ms: int = 20_000
    ) -> bool:
        """Ждёт появление в списке: только повторный поиск, без reload страницы."""
        started = time.monotonic()
        while True:
            self.search_device_in_list(name)
            if self._device_row_visible(name):
                return True
            if (time.monotonic() - started) * 1000 > timeout_ms:
                return self._device_row_visible(name)
            self.page.wait_for_timeout(1_200)

    def current_device_id(self) -> str | None:
        m = re.search(r"/list/devices/(\d+)", self.page.url)
        if not m:
            return None
        device_id = m.group(1)
        return None if device_id == "0" else device_id

    def open_device_by_id(self, device_id: str) -> None:
        url = f"{self._base()}/list/devices/{device_id}"
        self.page.goto(url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(1000)
        if "/user/login" in self.page.url:
            self._relogin_if_redirected()
            self.page.goto(url, wait_until="domcontentloaded")
            self.page.wait_for_timeout(1000)

    def save_and_apply(self, refresh_list: bool = False) -> None:
        """Save + Apply — как в legacy devices CRUD."""
        self.save_form()
        self.apply_changes()
        if refresh_list:
            self.page.wait_for_timeout(800)
            self.refresh_list_once()
            try:
                self.page.locator(self._LIST_SEARCH_INPUT).first.wait_for(
                    state="visible", timeout=10_000
                )
            except Exception:
                pass
            self.page.wait_for_timeout(500)

    def _device_row_visible(self, name: str) -> bool:
        row = self.page.locator(".ant-list-item", has_text=name).first
        return row.count() > 0 and row.is_visible()

    def wait_until_device_in_list(
        self, name: str, timeout_ms: int = 15_000, *, refresh_once: bool = False
    ) -> bool:
        """Ждёт появление в списке: опционально один refresh, далее только поиск (без reload)."""
        if refresh_once:
            self.refresh_list_once()
        started = time.monotonic()
        while True:
            if self.find_device_in_list(name):
                return True
            if (time.monotonic() - started) * 1000 > timeout_ms:
                return self.find_device_in_list(name)
            self.page.wait_for_timeout(900)

    def wait_until_device_not_in_list(
        self, name: str, timeout_ms: int = 15_000, *, refresh_once: bool = False
    ) -> bool:
        if refresh_once:
            self.refresh_list_once()
        started = time.monotonic()
        while True:
            self.search_device_in_list(name)
            if not self._device_row_visible(name):
                return True
            if (time.monotonic() - started) * 1000 > timeout_ms:
                return not self._device_row_visible(name)
            self.page.wait_for_timeout(900)

    def _close_edit_form_if_open(self) -> None:
        try:
            self.page.keyboard.press("Escape")
        except Exception:
            pass
        if self.name_input.count() > 0 and self.name_input.is_visible():
            try:
                self.cancel_button.click(timeout=2000)
            except Exception:
                pass
        self.page.wait_for_timeout(300)

    def _visible_confirmation_layer(self):
        return self.page.locator(self._CONFIRMATION_LAYER).last

    def _confirm_delete_dropdown_visible(self) -> bool:
        menu = self.page.locator(".ant-dropdown:not(.ant-dropdown-hidden)")
        item = menu.locator(".ant-dropdown-menu-title-content").filter(
            has_text=self._CONFIRM_DELETE_MENU_ITEM
        ).first
        return item.count() > 0 and item.is_visible()

    def _rc_menu_popup_visible(self) -> bool:
        popup = self.page.locator('[id^="rc-menu-uuid"][id$="-popup"]').first
        return popup.count() > 0 and popup.is_visible()

    def _confirmation_layer_visible(self) -> bool:
        if self._confirm_delete_dropdown_visible():
            return True
        if self._rc_menu_popup_visible():
            return True
        layer = self._visible_confirmation_layer()
        return layer.count() > 0 and layer.is_visible()

    def wait_for_delete_dialog(self, timeout_ms: int = 5_000) -> bool:
        """Ждёт появление подтверждения удаления (poll, без последовательных long-timeout)."""
        started = time.monotonic()
        while True:
            if self._confirm_delete_dropdown_visible():
                return True
            if self._rc_menu_popup_visible():
                return True
            layer = self._visible_confirmation_layer()
            if layer.count() > 0 and layer.is_visible():
                return True
            if (time.monotonic() - started) * 1000 > timeout_ms:
                return False
            self.page.wait_for_timeout(100)

    def _click_confirm_delete_dropdown_item(self) -> bool:
        """Клик «Подтвердить удаление» в ant-dropdown."""
        menu = self._visible_dropdown()
        title = menu.locator(".ant-dropdown-menu-title-content").filter(
            has_text=self._CONFIRM_DELETE_MENU_ITEM
        ).first
        if title.count() == 0 or not title.is_visible():
            return False
        menu_item = title.locator("xpath=ancestor::li[contains(@class,'ant-dropdown-menu-item')][1]")
        target = menu_item if menu_item.count() > 0 else title
        try:
            target.click(timeout=2000)
        except Exception:
            target.click(force=True)
        self.page.wait_for_timeout(200)
        return True

    def _click_rc_menu_popup_item(self, label_pattern: re.Pattern[str] | None = None) -> bool:
        """Клик по пункту rc-menu popup (id вида rc-menu-uuid-*-popup)."""
        items = self.page.locator(self._RC_MENU_POPUP_ITEM)
        item = items.filter(has_text=label_pattern).first if label_pattern else items.first
        if item.count() == 0 and label_pattern:
            item = items.first
        if item.count() == 0 or not item.is_visible():
            return False
        try:
            item.click(timeout=2000)
        except Exception:
            item.click(force=True)
        self.page.wait_for_timeout(200)
        return True

    def _click_delete_in_action_menu(self) -> bool:
        """⋯ → Удалить в ant-dropdown (как «Редактировать»)."""
        if not self._wait_for_visible_dropdown(timeout_ms=3_000):
            return False
        menu = self._visible_dropdown()
        item = menu.locator(".ant-dropdown-menu-item-dangerous").filter(
            has_text=self._DELETE_MENU_ITEM
        ).first
        try:
            item.wait_for(state="visible", timeout=2_000)
        except Exception:
            return self._click_action_menu_item(self._DELETE_MENU_ITEM)
        if item.count() > 0 and item.is_visible():
            try:
                item.click(timeout=2000)
            except Exception:
                item.click(force=True)
            return True
        return self._click_action_menu_item(self._DELETE_MENU_ITEM)

    def confirm_delete_in_visible_modal(self) -> bool:
        """Подтвердить удаление: ant-dropdown «Подтвердить удаление» и/или модальное окно."""
        if self._click_confirm_delete_dropdown_item():
            return True
        if self._click_rc_menu_popup_item():
            return True
        modal = self._visible_confirmation_layer()
        if modal.count() == 0:
            return False
        for sel in (
            ".ant-popconfirm-buttons .ant-btn-dangerous",
            ".ant-popconfirm-buttons .ant-btn-primary",
            ".ant-modal-confirm-btns .ant-btn-dangerous",
            ".ant-modal-confirm-btns .ant-btn-primary",
        ):
            btn = modal.locator(sel).first
            if btn.count() > 0 and btn.is_visible():
                try:
                    btn.click(timeout=3000)
                except Exception:
                    btn.click(force=True)
                self.page.wait_for_timeout(400)
                return True
        dangerous = modal.locator(".ant-modal-footer .ant-btn-dangerous").first
        if dangerous.count() > 0 and dangerous.is_visible():
            try:
                dangerous.click(timeout=3000)
            except Exception:
                dangerous.click(force=True)
            self.page.wait_for_timeout(400)
            return True
        for label in ("Удалить", "Delete", "Да", "Yes", "OK", "Ок", "Confirm"):
            btn = modal.get_by_role("button", name=label, exact=True).first
            if btn.count() == 0:
                btn = modal.get_by_text(label, exact=True).first
            if btn.count() > 0 and btn.is_visible():
                try:
                    btn.click(timeout=3000)
                except Exception:
                    btn.click(force=True)
                self.page.wait_for_timeout(400)
                return True
        primary = modal.locator(".ant-modal-footer .ant-btn-primary").first
        if primary.count() > 0 and primary.is_visible():
            try:
                primary.click(timeout=3000)
            except Exception:
                primary.click(force=True)
            self.page.wait_for_timeout(400)
            return True
        return False

    def apply_changes_if_present(self) -> None:
        btn = self.apply_button
        if btn.count() > 0 and btn.is_visible():
            try:
                btn.scroll_into_view_if_needed()
                btn.click(timeout=3000)
            except Exception:
                btn.click(force=True)
            self.page.wait_for_timeout(700)

    def _open_action_menu_for_device(self, name: str, *, search: bool = True) -> bool:
        """Поиск → пауза до появления строки → ⋯ (меню действий, как при редактировании)."""
        if search:
            self.search_device_in_list(name)
        if not self._wait_for_device_row_visible(name):
            self.search_device_in_list(name)
            if not self._wait_for_device_row_visible(name):
                return False
        row = self._device_row(name)
        row.scroll_into_view_if_needed()
        if self._open_row_action_menu(row):
            return True
        menu_btn = self.page.locator(
            "button[class*='action-menu-dropdown-btn'], "
            "button.ant-dropdown-trigger:has(.anticon-more[aria-label='more'])"
        ).first
        if menu_btn.count() == 0 or not menu_btn.is_visible():
            return False
        try:
            menu_btn.click(timeout=3000)
        except Exception:
            menu_btn.click(force=True)
        return self._wait_for_visible_dropdown()

    def trigger_delete_device_by_name_from_list(self, name: str, *, search: bool = True) -> bool:
        """Инициировать удаление: поиск → ⋯ → Удалить."""
        if not self._open_action_menu_for_device(name, search=search):
            return False
        return self._click_delete_in_action_menu()

    def delete_device_and_confirm(self, name: str, *, search: bool = True) -> bool:
        """
        Удаление устройства из списка:
        1. Поиск (имя в поле + лупа) → ожидание появления в списке
        2. ⋯ на строке устройства (то же меню, что для «Редактировать»)
        3. Удалить
        4. Подтвердить удаление
        """
        self._close_edit_form_if_open()
        if not self._open_action_menu_for_device(name, search=search):
            return False
        if not self._click_delete_in_action_menu():
            return False
        if not self.wait_for_delete_dialog():
            return False
        if not self.confirm_delete_in_visible_modal():
            return False
        if self._confirmation_layer_visible():
            if not self.confirm_delete_in_visible_modal():
                return False
        self.apply_changes_if_present()
        try:
            self._visible_confirmation_layer().wait_for(state="hidden", timeout=10_000)
        except Exception:
            pass
        return True

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

