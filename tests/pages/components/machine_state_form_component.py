"""
Page Component для формы создания/редактирования состояний и параметров на странице machineParams.

UI имеет две разные формы:
- Состояния открываются как полностраничная форма по маршруту .../machineParams/new
- Параметры открываются как модальный popup (.dx-overlay-content)
Компонент детектит контекст и работает с обеими формами.
"""

from dataclasses import dataclass

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError, expect


@dataclass(frozen=True)
class MachineStateFormComponent:
    page: Page

    @property
    def active_popup(self) -> Locator:
        # Модальная форма параметра (popup).
        return self.page.locator(".dx-overlay-content:visible, .dx-popup-content:visible").first

    @property
    def fullpage_form(self) -> Locator:
        # Полностраничная форма состояния по маршруту .../machineParams/new.
        return self.page.locator(
            ".FormContainer___QWwNX, "
            ".dx-layout-manager.dx-widget:has(.dx-field-item:has-text('Наименование'))"
        ).first

    @property
    def form_container(self) -> Locator:
        # Контейнер формы: либо popup, либо полностраничная форма.
        if self._is_popup_form():
            return self.active_popup
        return self.fullpage_form

    def _is_popup_form(self) -> bool:
        # Попап-форма параметра: проверяем наличие видимого .dx-overlay-content / .dx-popup-content.
        return self.active_popup.count() > 0 and self.active_popup.is_visible()

    @staticmethod
    def _exact_label_locator_xpath(label_text: str) -> str:
        # Находим элемент .dx-field-item-label-text по тексту лейбла, поднимаемся
        # к ближайшему .dx-field-item-предку (чтобы не уйти в групповой контейнер,
        # содержащий несколько полей), и берём его собственный input.
        #
        # Используем starts-with(normalize-space(.), ...), потому что:
        # - точный match (=) ломается, если в лейбле есть ": *" или прочие маркеры;
        # - contains() ломается из-за substring-конфликта между
        #   "Наименование" и "Краткое наименование".
        # starts-with решает обе проблемы: "Краткое наименование" не начинается
        # с "Наименование", а "Наименование: *" — начинается с "Наименование".
        return (
            "xpath=//*[contains(@class,'dx-field-item-label-text') and "
            f"starts-with(normalize-space(.), '{label_text}')]"
            "/ancestor::div[contains(@class,'dx-field-item')][1]"
            "//input[contains(@class,'dx-texteditor-input')]"
        )

    @property
    def name_input(self) -> Locator:
        # Для "Наименование" обязательно нужен label-based матч (substring-конфликт с "Краткое наименование").
        return self.page.locator(self._exact_label_locator_xpath("Наименование")).first.or_(
            self.page.locator(
                "input[name='Name']:visible, input[test-id='machine_param_Name']:visible"
            ).first
        ).first

    @property
    def short_name_input(self) -> Locator:
        return self.page.locator(self._exact_label_locator_xpath("Краткое наименование")).first.or_(
            self.page.locator(
                "input[name='ShortName']:visible, input[test-id='machine_param_ShortName']:visible"
            ).first
        ).first

    @property
    def measure_unit_input(self) -> Locator:
        # Поле "Единицы измерения" — есть только в форме параметра (popup).
        # У popup-формы рабочий вариант — CSS по атрибутам/has-text; держим его первым,
        # XPath по label-text — как фолбэк.
        return self.page.locator(
            "input[name='measureUnit']:visible, input[name='unit']:visible, "
            "input[id*='measure']:visible, input[id*='unit']:visible, "
            ".dx-field-item:has-text('Единицы измерения') .dx-texteditor-input:visible"
        ).first.or_(
            self.page.locator(self._exact_label_locator_xpath("Единицы измерения"))
        ).first

    @property
    def visualization_selector(self) -> Locator:
        # Поле "Способ визуализации" (только в форме параметра).
        return self.form_container.locator(
            "input[name='VisualizationMethod']:visible, input[id*='VisualizationMethod']:visible, "
            ".dx-selectbox:has(input[name='VisualizationMethod']) .dx-dropdowneditor-input-wrapper:visible, "
            ".dx-field-item:has-text('Способ визуализации') .dx-dropdowneditor-input-wrapper:visible, "
            ".dx-field-item:has-text('Способ визуализации') .dx-texteditor-input:visible"
        ).first

    @property
    def visualization_open_button(self) -> Locator:
        return self.form_container.locator(
            ".dx-selectbox:has(input[name='VisualizationMethod']) [role='button'][aria-label='Выбрать']:visible, "
            ".dx-field-item:has-text('Способ визуализации') [role='button'][aria-label='Выбрать']:visible, "
            ".dx-selectbox:has(input[name='VisualizationMethod']) .dx-dropdowneditor-button:visible"
        ).first

    @property
    def state_type_radio(self) -> Locator:
        # Radio "Состояние" в группе "Тип" на полностраничной форме создания состояния.
        return self.page.locator(
            ".dx-radiogroup .dx-radiobutton:has(.dx-item-content:has-text('Состояние'))"
        ).first.or_(
            self.page.locator(
                "xpath=//div[contains(@class,'dx-radiobutton')][.//span[normalize-space()='Состояние']]"
            ).first
        ).first

    @property
    def save_button(self) -> Locator:
        # Кнопка сохранения. В popup — внутри active_popup, в полностраничной форме — на тулбаре.
        if self._is_popup_form():
            return self.active_popup.get_by_role("button", name="Сохранить").or_(
                self.active_popup.get_by_role("button", name="Save")
            ).or_(self.active_popup.locator("button[type='submit']")).or_(
                self.active_popup.locator(
                    ".dx-button .dx-button-text"
                ).filter(has_text="Сохранить").locator("xpath=ancestor::div[contains(@class,'dx-button')][1]")
            ).or_(
                self.active_popup.locator(
                    ".dx-button .dx-button-text"
                ).filter(has_text="Save").locator("xpath=ancestor::div[contains(@class,'dx-button')][1]")
            ).first

        # Полностраничная форма — кнопка "Сохранить" на верхнем тулбаре.
        return self.page.locator(
            "div[role='button'][aria-label='Сохранить']:visible"
        ).first.or_(
            self.page.locator("div.dx-button[title='Сохранить']:visible").first
        ).or_(
            self.page.locator(
                ".dx-button .dx-button-text"
            ).filter(has_text="Сохранить").locator("xpath=ancestor::div[contains(@class,'dx-button')][1]").first
        ).or_(self.page.get_by_role("button", name="Сохранить")).first

    def assert_loaded(self) -> None:
        # Ждём появления формы (popup или полностраничной).
        expect(self.form_container).to_be_visible(timeout=20_000)
        expect(self.name_input).to_be_visible(timeout=20_000)
        expect(self.short_name_input).to_be_visible(timeout=20_000)
        expect(self.save_button).to_be_visible(timeout=20_000)

    def create_state(self, state_name: str) -> None:
        self.assert_loaded()
        self.name_input.fill(state_name)
        self.short_name_input.fill(self._build_short_name(state_name))
        # Состояние создаётся в полностраничной форме: выбираем тип "Состояние".
        self._select_state_type_if_present()
        self.page.wait_for_timeout(1_000)
        self.save_button.click()
        self._wait_form_closed_or_saved()

    def create_parameter(self, parameter_name: str) -> None:
        self.assert_loaded()
        self.name_input.fill(parameter_name)
        self.short_name_input.fill(self._build_short_name(parameter_name))
        self.measure_unit_input.fill("шт")
        self._select_linear_visualization_if_present()
        self.page.wait_for_timeout(1_000)
        self.save_button.click()
        self._wait_form_closed_or_saved()

    def edit_state_name(self, new_state_name: str) -> None:
        self.assert_loaded()
        self.name_input.fill(new_state_name)
        self.short_name_input.fill(self._build_short_name(new_state_name))
        self.page.wait_for_timeout(1_000)
        self.save_button.click()
        self._wait_form_closed_or_saved()

    def edit_parameter_name(self, new_parameter_name: str) -> None:
        self.edit_state_name(new_parameter_name)

    def _build_short_name(self, state_name: str) -> str:
        short_name = f"{state_name}-sn"
        return short_name[:32]

    def _select_state_type_if_present(self) -> None:
        # На полностраничной форме создания нужно явно выбрать тип "Состояние" (по умолчанию "Причина простоя").
        if self.state_type_radio.count() == 0:
            return
        try:
            self.state_type_radio.first.scroll_into_view_if_needed()
        except PlaywrightTimeoutError:
            pass
        try:
            self.state_type_radio.first.click(timeout=5_000)
        except PlaywrightTimeoutError:
            self.state_type_radio.first.click(force=True)

    def _select_linear_visualization_if_present(self) -> None:
        if self.visualization_selector.count() == 0:
            return
        expect(self.visualization_selector).to_be_visible(timeout=20_000)

        # Открываем dropdown и активно ждём появления видимого overlay со списком.
        # В DOM остаются стейл-overlay'ы от прежних дропдаунов (с visibility:hidden),
        # поэтому проверяем именно computed visibility через нативный :visible фильтр.
        active_dropdown_selector = ".dx-overlay-content:visible:has(.dx-list)"

        def dropdown_visible() -> bool:
            return self.page.locator(active_dropdown_selector).count() > 0

        open_attempts = [
            self.visualization_selector.click,
            lambda: (
                self.visualization_open_button.click()
                if self.visualization_open_button.count() > 0
                else None
            ),
            self._click_20px_below_visualization_selector,
        ]

        for attempt in open_attempts:
            try:
                attempt()
            except Exception:
                pass
            for _ in range(15):
                self.page.wait_for_timeout(200)
                if dropdown_visible():
                    break
            if dropdown_visible():
                break

        active_dropdown = self.page.locator(active_dropdown_selector).first
        expect(active_dropdown).to_be_visible(timeout=20_000)

        linear_option = active_dropdown.locator(
            ".dx-list-item .dx-item-content:text-is('Линейный'), "
            ".dx-list-item .dx-item-content:text-is('Linear')"
        ).first
        expect(linear_option).to_be_visible(timeout=20_000)
        linear_option.click(force=True)

    def _click_20px_below_visualization_selector(self) -> None:
        box = self.visualization_selector.bounding_box()
        if not box:
            return
        self.page.wait_for_timeout(1_000)
        click_x = box["x"] + (box["width"] / 2)
        click_y = box["y"] + box["height"] + 10
        self.page.mouse.click(click_x, click_y)

    def _wait_form_closed_or_saved(self) -> None:
        # После клика по "Сохранить":
        # - popup-форма должна скрыться;
        # - полностраничная форма обычно меняет URL (уходит /new).
        if self.active_popup.count() > 0 and self.active_popup.is_visible():
            try:
                expect(self.active_popup).not_to_be_visible(timeout=15_000)
                return
            except PlaywrightTimeoutError:
                pass

        try:
            self.page.wait_for_url(
                lambda url: "/new" not in url, timeout=10_000
            )
        except PlaywrightTimeoutError:
            self.page.wait_for_timeout(2_000)
