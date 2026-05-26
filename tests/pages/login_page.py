"""
Page Object для страницы авторизации.

Зачем это нужно:
- здесь собраны все знания о странице (селекторы и действия);
- тесты используют методы этого класса и не зависят от деталей DOM;
- если поменяется верстка/селекторы, обычно достаточно правок только в этом файле.
"""

import re
from dataclasses import dataclass

from playwright.sync_api import Page, expect


@dataclass(frozen=True)
class LoginPage:
    page: Page
    login_url: str

    @property
    def language_menu_button(self):
        # Кнопка вызова меню выбора языка на странице авторизации.
        return self.page.locator(
            "#root > div > div > div > form > div.header___uFci3 > button"
        )

    @property
    def language_select_button(self):
        # Вторая кнопка, которая появляется после первого клика.
        return self.page.locator(
            "#root > div > div > div > form > div.selectVisible___LSabj > div"
        )

    @property
    def login_input(self):
        # Селектор поля логина из реальной формы.
        return self.page.locator("#login")

    @property
    def password_input(self):
        # Селектор поля пароля.
        return self.page.locator("#password")

    @property
    def submit_button(self):
        # Кнопка отправки формы авторизации.
        return self.page.locator("button[type='submit']")

    @property
    def settings_button(self):
        # Кнопка настроек на форме логина (обычно открывает параметры языка).
        return self.page.locator(
            "button:has([aria-label='setting']), button:has(.anticon-setting), .button___SpWF4"
        ).first

    @property
    def language_select(self):
        # Языковой селект на форме логина (например, "RU Русский").
        return self.page.locator(".ant-select-selector:visible").first

    @property
    def language_badge(self):
        # Текущий язык на форме (например, RU/EN).
        return self.page.locator("text=/\\b(RU|EN)\\b/").first

    def open(self) -> None:
        # Переходим на URL логина и ждём базовой готовности DOM.
        self.page.goto(self.login_url, wait_until="domcontentloaded")

    def assert_loaded(self) -> None:
        # Проверяем видимость ключевых элементов формы входа.
        expect(self.language_menu_button).to_be_visible()
        expect(self.login_input).to_be_visible()
        expect(self.password_input).to_be_visible()
        expect(self.submit_button).to_be_visible()

    def switch_language_to_russian(self) -> None:
        # 1) Открываем блок выбора языка первой кнопкой.
        expect(self.language_menu_button).to_be_visible(timeout=20_000)
        self.language_menu_button.click()
        # 2) Нажимаем вторую кнопку, которая раскрывает список языков.
        expect(self.language_select_button).to_be_visible(timeout=20_000)
        self.language_select_button.click()
        # 3) Выбираем русский язык в выпадающем меню.
        ru_option = self.page.locator(
            "[role='menuitem']:has-text('Русский'), "
            ".ant-dropdown-menu-item:has-text('Русский'), "
            ".ant-select-item-option:has-text('Русский'), "
            "[role='menuitem']:has-text('Russian'), "
            ".ant-dropdown-menu-item:has-text('Russian'), "
            ".ant-select-item-option:has-text('Russian')"
        ).first
        expect(ru_option).to_be_visible(timeout=20_000)
        ru_option.click()

    def login(self, username: str, password: str) -> None:
        # Унифицированное действие "войти в систему".
        self.login_input.fill(username)
        self.password_input.fill(password)
        self.submit_button.click()

    def submit_empty(self) -> None:
        # Отправка пустой формы (проверка валидации/блокировки входа).
        self.submit_button.click()

    def assert_still_on_login_page(self) -> None:
        # После неуспешной авторизации URL должен оставаться в зоне /login.
        expect(self.page).to_have_url(re.compile(r".*/user/login.*"), timeout=10_000)

    def has_auth_error_message(self) -> bool:
        # Проверка на типовое сообщение об ошибке авторизации.
        # В разных сборках это может быть toast/alert и текст может немного отличаться.
        self.page.wait_for_timeout(2_000)
        error_candidates = [
            self.page.get_by_text(re.compile(r"неверн.*(парол|имя|данн)", re.I)),
            self.page.get_by_text(re.compile(r"(invalid|wrong).*(password|user|credential)", re.I)),
            self.page.locator("[role='alert'], .ant-notification-notice, .ant-message-notice").first,
        ]
        for loc in error_candidates:
            if loc.count() > 0 and loc.first.is_visible():
                return True
        return False

    def has_language_control(self) -> bool:
        # На некоторых конфигурациях язык видно сразу, на некоторых — через кнопку настроек.
        self.page.wait_for_timeout(200)
        if self.language_select.count() > 0:
            return True
        return self.language_badge.count() > 0 or self.settings_button.count() > 0

    def current_language(self) -> str | None:
        # Возвращает текущую локаль из badge (RU/EN), если удалось определить.
        raw = ""
        if self.language_select.count() > 0:
            raw = (self.language_select.first.inner_text() or "").strip().upper()
        elif self.language_badge.count() > 0:
            raw = (self.language_badge.first.inner_text() or "").strip().upper()

        if "RU" in raw:
            return "RU"
        if "EN" in raw:
            return "EN"
        return None

    def login_placeholder(self) -> str:
        return (self.login_input.get_attribute("placeholder") or "").strip()

    def switch_language(self, target: str) -> bool:
        """
        Пытается переключить язык на target (`RU` или `EN`).
        Возвращает True, если удалось кликнуть по нужной опции.
        """
        # На этом UI селект языка может быть скрыт до клика по кнопке настроек.
        if self.language_select.count() == 0 and self.settings_button.count() > 0:
            self.settings_button.click()
            self.page.wait_for_timeout(250)

        if self.language_select.count() == 0:
            return False

        self.language_select.click()
        self.page.wait_for_timeout(250)

        # Пытаемся кликнуть видимую опцию языка из выпадающего списка.
        # На реальных стендах подписи могут быть RU/EN или Русский/English.
        synonyms = {
            "EN": ["EN", "English", "Английский"],
            "RU": ["RU", "Русский", "Russian"],
        }
        labels = synonyms.get(target.upper(), [target])

        candidates = [
            self.page.locator(".ant-select-item-option-content:visible"),
            self.page.get_by_role("option"),
            self.page.locator(".ant-select-item-option:visible"),
        ]

        option = None
        for pool in candidates:
            for i in range(pool.count()):
                cand = pool.nth(i)
                txt = (cand.inner_text() or "").strip()
                if not txt:
                    continue
                if any(lbl.lower() in txt.lower() for lbl in labels) and cand.is_visible():
                    option = cand
                    break
            if option is not None:
                break

        if option is None:
            return False

        option.click()
        self.page.wait_for_timeout(500)
        return True

