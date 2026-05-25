# Production units — заметки для будущих UI-тестов

Автотесты (`tests/test_*.py`) пока **не добавлялись**; это только разведка UI и вспомогательные скрипты в `tools/`.

## URL и навигация

| Экран | URL (относительно origin) |
|--------|---------------------------|
| Список, вкладка *Production units* | `/list/production-structure?tab=productionUnits` |
| Форма создания | `/list/production-structure/production-unit/0` |

После логина кнопка создания на списке: текст **Create** / **Создать**, класс кнопки содержит `index_button__EOmvq`. В DOM бывают **несколько** кнопок с одинаковым текстом; для стабильности нужно кликать **первую видимую** `button.index_button__EOmvq` с подходящим текстом (см. `tools/probe_production_units_save.py` → `_open_create`).

## Список (таблица)

- Таблица **MUI**: `table.MuiTable-root`.
- Колонки (EN): **Code**, **Name**, **Storage location**, **Type**, **Status**.
- В шапке чекбокс «select all» (`aria-label` содержит `Toggle select all`).
- В тулбаре есть **dangerous** icon-only кнопки (удаление и др.) — для CRUD удаления понадобится отдельная разведка (диалог, Apply).

## Форма создания / редактирования

Идентификаторы полей (из снимка DOM, `tools/_probe/02_create_form.json`):

| Поле | Селектор / id |
|------|----------------|
| Code | `#ProductionUnit_Code` |
| Name | `#ProductionUnit_Name` |
| Full name | `#ProductionUnit_FullName` |
| Type | `#ProductionUnit_Type` (Ant Select, combobox `input`) |
| Status | `#ProductionUnit_Status` (каскад: до выбора Type часто **disabled**) |
| Main | `#ProductionUnit_MainId` |
| Parent | `#ProductionUnit_ParentId` |
| Organization | `#ProductionUnit_CompanyId` |
| Department | `#ProductionUnit_DeptId` |

Также есть переключатели `ant-switch` с id вида `ProductionUnit_IsSegmentLevel`, `ProductionUnit_IsOperationLevel`, …

Кнопка сохранения: **`Save`** (обычно `button` с классом `ant-btn-dangerous` и текстом Save).

## Валидация (обязательные поля)

По сообщениям формы (`ant-form-item-has-error` + подпись поля):

1. При пустой форме (только Code/Name или без селектов): **Type** и **Parent** — `Required`.
2. После успешного выбора **Type**: остаётся **Parent** — `Required`.

То есть минимальный набор для прохождения валидации — **Type + Parent** (плюс, при необходимости бэкенда, остальные поля).

## Выбор значений в Ant Select (разведка)

Рабочий приём для `#ProductionUnit_Type` и др.:

1. Найти виджет: `.ant-select`, который **содержит** нужный `#…Id` / `#…Type`.
2. Кликнуть по **`.ant-select-selector`**, дождаться портального `.ant-select-dropdown:not(.ant-select-dropdown-hidden)`.
3. Кликнуть по первой опции: `.ant-select-item-option:not(.ant-select-item-option-disabled)`.
4. Закрыть клавишей **Escape** (на случай залипшего dropdown).

Реализация: `tools/probe_production_units_save.py` → `_pick_first_ant_option`.

## Parent и Main — TreeSelect

- **Parent** (`#ProductionUnit_ParentId`): `ant-select ant-tree-select` — выбор через `.ant-select-tree-node-content-wrapper`.
- **Main** (`#ProductionUnit_MainId`): тоже tree-select, часто **disabled** до выбора Type.

## Type при создании

- Первая опция **Enterprise** даёт toast: *«The main production unit can only be a company!»* и не сохраняется.
- Для автотестов выбирать **Division** (или Shop floor / Warehouse / …), не Enterprise.
- Реализация: `fill_mandatory_selects_for_new_unit()` в `tests/pages/production_units_page.py`.

## Удаление

- На карточке: первая видимая `button.ant-btn-dangerous.ant-btn-icon-only` (не Save).
- Фолбэк: список → чекбокс строки → dangerous icon-only в тулбаре.

## Скрипты

| Файл | Назначение |
|------|------------|
| `tools/probe_production_units.py` | Скриншот списка + формы, JSON с кнопками/полями |
| `tools/probe_production_units_save.py` | Попытки Save с разным набором полей, лог `requiredRows` |

Запуск (нужны `playwright`, Chromium; для HTTPS self-signed в скрипте уже `ignore_https_errors=True`):

```bash
python tools/probe_production_units.py
python tools/probe_production_units_save.py
```

Переменные окружения (как в тестах): `LOGIN_URL`, `TEST_USER_LOGIN`, `TEST_USER_PASSWORD`.

Артефакты (`tools/_probe/`) добавлены в `.gitignore`, чтобы скриншоты и JSON не попадали в git по ошибке.
