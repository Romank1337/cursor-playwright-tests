"""
Page Component для формы создания "состояния" на странице machineParams.
"""

from dataclasses import dataclass

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError, expect


@dataclass(frozen=True)
class MachineStateFormComponent:
    page: Page

    @property
    def active_popup(self) -> Locator:
        # Работаем только с видимым popup, чтобы не попадать в скрытые копии полей.
        return self.page.locator(".dx-overlay-content:visible, .dx-popup-content:visible").first

    @property
    def name_input(self) -> Locator:
        # Поддерживаем несколько вариантов разметки и подписей поля.
        return self.active_popup.locator(
            "input[name='name']:visible, input[id*='name']:visible, "
            "input[placeholder*='Наименование']:visible, input[placeholder*='Название']:visible, "
            "input[aria-label='Title']:visible, input[placeholder='Title']:visible, "
            ".dx-field-item:has-text('Наименование') .dx-texteditor-input:visible"
        ).first

    @property
    def short_name_input(self) -> Locator:
        # Обязательное поле "Краткое наименование" (ShortName).
        return self.active_popup.locator(
            "input[name='ShortName']:visible, input[test-id='machine_param_ShortName']:visible, "
            "input[id*='_ShortName']:visible, .dx-field-item:has-text('Краткое наименование') .dx-texteditor-input:visible"
        ).first

    @property
    def measure_unit_input(self) -> Locator:
        # Обязательное поле единицы измерения.
        return self.active_popup.locator(
            "input[name='measureUnit']:visible, input[name='unit']:visible, input[id*='measure']:visible, "
            "input[id*='unit']:visible, .dx-field-item:has-text('Единицы измерения') .dx-texteditor-input:visible"
        ).first

    @property
    def visualization_selector(self) -> Locator:
        # Поле "Способ визуализации" (select/dropdown).
        return self.active_popup.locator(
            "input[name='VisualizationMethod']:visible, input[id*='VisualizationMethod']:visible, "
            ".dx-selectbox:has(input[name='VisualizationMethod']) .dx-dropdowneditor-input-wrapper:visible, "
            ".dx-field-item:has-text('Способ визуализации') .dx-dropdowneditor-input-wrapper:visible, "
            ".dx-field-item:has-text('Способ визуализации') .dx-texteditor-input:visible"
        ).first

    @property
    def visualization_open_button(self) -> Locator:
        return self.active_popup.locator(
            ".dx-selectbox:has(input[name='VisualizationMethod']) [role='button'][aria-label='Выбрать']:visible, "
            ".dx-field-item:has-text('Способ визуализации') [role='button'][aria-label='Выбрать']:visible, "
            ".dx-selectbox:has(input[name='VisualizationMethod']) .dx-dropdowneditor-button:visible"
        ).first

    @property
    def save_button(self) -> Locator:
        # Кнопка сохранения в диалоге/форме.
        return self.active_popup.locator(
            "xpath=//div[contains(@class,'dx-button') and contains(@class,'dx-button-has-icon') and .//span[contains(@class,'dx-button-text') and normalize-space()='Сохранить']]"
        ).first.or_(
            self.active_popup.locator(
                "xpath=//div[contains(@class,'dx-button') and contains(@class,'dx-button-has-icon') and .//span[contains(@class,'dx-button-text') and normalize-space()='Save']]"
            ).first
        ).or_(self.active_popup.get_by_role("button", name="Сохранить")).or_(
            self.active_popup.get_by_role("button", name="Save")
        ).or_(self.active_popup.locator("button[type='submit']")).or_(
            self.active_popup.get_by_text("Save", exact=True)
        ).or_(
            self.active_popup.get_by_text("Сохранить", exact=True)
        ).or_(
            self.active_popup.locator(".dx-button .dx-button-text").filter(has_text="Save").locator("xpath=ancestor::div[contains(@class,'dx-button')][1]")
        ).or_(
            self.active_popup.locator(".dx-button .dx-button-text").filter(has_text="Сохранить").locator("xpath=ancestor::div[contains(@class,'dx-button')][1]")
        ).or_(
            self.active_popup.locator(".ant-btn-primary:visible")
        ).first

    def assert_loaded(self) -> None:
        expect(self.active_popup).to_be_visible(timeout=20_000)
        expect(self.name_input).to_be_visible(timeout=20_000)
        expect(self.short_name_input).to_be_visible(timeout=20_000)
        expect(self.save_button).to_be_visible(timeout=20_000)

    def create_state(self, state_name: str) -> None:
        self.assert_loaded()
        self.name_input.fill(state_name)
        self.short_name_input.fill(self._build_short_name(state_name))
        self._select_type_if_present()
        self.page.wait_for_timeout(10_000)
        self.save_button.click()
        self._ensure_popup_closed()

    def create_parameter(self, parameter_name: str) -> None:
        self.assert_loaded()
        self.name_input.fill(parameter_name)
        self.short_name_input.fill(self._build_short_name(parameter_name))
        self.measure_unit_input.fill("шт")
        self._select_linear_visualization_if_present()
        # После выбора "Линейный" сразу сохраняем в этом же модальном окне.
        self.page.wait_for_timeout(1_000)
        self.save_button.click()
        self._ensure_popup_closed()

    def edit_state_name(self, new_state_name: str) -> None:
        self.assert_loaded()
        self.name_input.fill(new_state_name)
        self.short_name_input.fill(self._build_short_name(new_state_name))
        self.page.wait_for_timeout(10_000)
        self.save_button.click()
        self._ensure_popup_closed()

    def edit_parameter_name(self, new_parameter_name: str) -> None:
        self.edit_state_name(new_parameter_name)

    def _build_short_name(self, state_name: str) -> str:
        # Короткое имя должно отличаться от основного названия.
        short_name = f"{state_name}-sn"
        return short_name[:32]

    def _select_type_if_present(self) -> None:
        # Явно выбираем нужный radio-тип при создании состояния.
        type_radio = self.page.locator(
            "#scrollable-container > main > div.MainContainer____pTMn > div.FormContainer___QWwNX > div > div > "
            "div.dx-layout-manager.dx-widget > div > div > div:nth-child(2) > div > div > div > div > div > "
            "div > div > div > div > div > div:nth-child(1) > div > div > div > div > div > "
            "div.dx-show-invalid-badge.dx-radiogroup.dx-radiogroup-vertical.dx-widget > div > div:nth-child(2) > "
            "div.dx-radio-value-container"
        ).first
        if type_radio.count() > 0:
            type_radio.click()
            return

        # Фолбэк для окружений с другой разметкой поля Type.
        type_inputs = self.page.locator(
            "input[aria-label='Type'], input[placeholder='Type'], "
            ".dx-field-item:has-text('Type') input, .dx-field-item:has-text('Тип') input"
        )
        # Пропускаем скрытые hidden-инпуты.
        visible_type_input = type_inputs.locator(":visible").first
        if visible_type_input.count() == 0:
            return
        visible_type_input.click()
        state_option = self.page.get_by_text("State", exact=True).or_(
            self.page.get_by_text("Состояние", exact=True)
        ).first
        if state_option.count() > 0:
            state_option.click()

    def _select_parameter_type_if_present(self) -> None:
        # Для создания параметра выбираем значение "Параметр/Parameter", если поле типа доступно.
        parameter_option = self.page.get_by_text("Параметр", exact=True).or_(
            self.page.get_by_text("Parameter", exact=True)
        ).first
        if parameter_option.count() > 0:
            parameter_option.click()

    def _select_linear_visualization_if_present(self) -> None:
        expect(self.visualization_selector).to_be_visible(timeout=20_000)
        self.visualization_selector.click()
        if self.visualization_open_button.count() > 0:
            self.visualization_open_button.click()
        self._click_20px_below_visualization_selector()
        linear_option = self.page.locator(
            ".dx-overlay-content:visible .dx-item-content.dx-list-item-content:has-text('Линейный')"
        ).first.or_(
            self.page.locator(
                ".dx-overlay-content:visible .dx-item-content.dx-list-item-content:has-text('Linear')"
            ).first
        ).first
        expect(linear_option).to_be_visible(timeout=20_000)
        linear_option.click(force=True)

    def _click_20px_below_visualization_selector(self) -> None:
        # Клик ниже поля помогает выбрать первый пункт выпадающего списка.
        box = self.visualization_selector.bounding_box()
        if not box:
            return
        self.page.wait_for_timeout(1_000)
        click_x = box["x"] + (box["width"] / 2)
        click_y = box["y"] + box["height"] + 10
        self.page.mouse.click(click_x, click_y)

    def _ensure_popup_closed(self) -> None:
        try:
            expect(self.active_popup).not_to_be_visible(timeout=15_000)
            return
        except PlaywrightTimeoutError:
            close_button = self.page.locator(
                ".dx-overlay-content:visible .dx-closebutton:visible, "
                ".dx-overlay-content:visible [aria-label='Закрыть']:visible, "
                ".dx-overlay-content:visible [aria-label='Close']:visible"
            ).first
            if close_button.count() > 0:
                close_button.click(force=True)
                expect(self.active_popup).not_to_be_visible(timeout=10_000)
