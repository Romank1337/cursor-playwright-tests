# Отчёт: Production units UI (e2e, видимый браузер)

**Дата прогона:** 2026-05-21  
**Режим:** `--headed` (браузер открыт на экране)  
**Стенд:** `https://localhost:8001/`  
**Учётка:** Admin / 123 (по умолчанию из `conftest.py`)  
**Destructive delete:** выключен (`RUN_DESTRUCTIVE_PRODUCTION_UNITS_CRUD` не задан)

## Итог

| Метрика | Значение |
|---------|----------|
| Всего тестов | 6 |
| Passed | 4 |
| Failed | 1 |
| Skipped | 1 |
| Время | ~3 мин 4 с |

## Результаты по тестам

| # | Тест | Статус | Время |
|---|------|--------|-------|
| 1 | `test_production_units_page_opened` | **FAILED** | ~26 с |
| 2 | `test_production_units_create_form_has_required_fields` | PASSED | ~17 с |
| 3 | `test_production_units_create_cancel_if_available` | SKIPPED | ~18 с |
| 4 | `test_production_units_table_visible` | PASSED | ~9 с |
| 5 | `test_production_units_update_name_after_create` | PASSED | ~49 с |
| 6 | `test_production_units_full_crud_destructive_flagged` | PASSED | ~65 с |

## Единственное падение

**Тест:** `test_production_units_page_opened`  
**Причина:** за 15 с не появилась таблица `table.MuiTable-root` / `.ant-table` на первом открытии списка.

```
AssertionError: Locator expected to be visible
Actual value: <element(s) not found>
```

**Замечание:** сразу после этого `test_production_units_table_visible` **прошёл** (~9 с) — список на стенде доступен, возможна **нестабильность первой загрузки** в headed-режиме (медленный рендер, вкладка, редирект). Имеет смысл увеличить ожидание в `assert_loaded()` или добавить reload.

## Пропуск (ожидаемо)

**Тест:** `test_production_units_create_cancel_if_available`  
**Причина skip:** на форме создания нет кнопки Cancel — URL остаётся `/production-unit/0`.

## Что успешно проверено

- Открытие формы Create и наличие полей Code, Name, Type, Parent.
- Таблица списка (отдельный тест).
- **Create + Update:** создание записи (Type Division + Parent TreeSelect), сохранение, смена Name.
- **Full CRUD:** создание, проверка Code на карточке, диалог удаления (подтверждение **отменено** — запись не удаляется с стенда).

## Как открыть отчёты

### Allure (подробные шаги)

```bash
allure open allure-report
```

Папка: `allure-report/` (сгенерирована из `allure-results/`).

### JUnit XML

`reports/production-units-junit.xml` — для CI / импорта в другие системы.

## Команда для повторного прогона (видимый браузер)

```powershell
cd C:\Users\roman.kunpan\Desktop\Cursor_project
python -m pytest tests/test_production_units_crud_ui.py -m e2e -v --headed --alluredir=allure-results --junitxml=reports/production-units-junit.xml
allure generate allure-results -o allure-report --clean
allure open allure-report
```

### С реальным удалением на стенде

```powershell
$env:RUN_DESTRUCTIVE_PRODUCTION_UNITS_CRUD="true"
python -m pytest tests/test_production_units_crud_ui.py::test_production_units_full_crud_destructive_flagged -m e2e -v --headed
```
