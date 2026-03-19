# Автоматизация авторизации (pytest + Playwright + Allure)

## Структура проекта

- `tests/pages/login_page.py` — Page Object для экрана логина.
- `tests/conftest.py` — фикстуры: URL, креды, regex успешного перехода.
- `tests/test_login_ui.py` — базовые UI-тесты страницы авторизации.
- `pytest.ini` — настройки pytest и маркер `e2e`.
- `requirements.txt` — зависимости.

## Установка

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m playwright install
```

## Запуск

```powershell
.\.venv\Scripts\python -m pytest -m e2e
```

## Allure-отчёт

1) Запуск тестов с сохранением результатов Allure:

```powershell
.\.venv\Scripts\python -m pytest -m e2e --alluredir=allure-results
```

2) Просмотр отчёта:

```powershell
allure serve allure-results
```

Если команда `allure` не найдена, нужно установить Allure CLI
(например, через Scoop/Chocolatey) и перезапустить терминал.

## Переменные окружения (опционально)

- `LOGIN_URL` — адрес страницы логина (по умолчанию `https://localhost:8001/user/login`)
- `TEST_USER_LOGIN` — логин (по умолчанию `Admin`)
- `TEST_USER_PASSWORD` — пароль (по умолчанию `123`)
- `SUCCESS_URL_REGEX` — regex URL после успешного входа

Пример для PowerShell:

```powershell
$env:LOGIN_URL="https://localhost:8001/user/login"
$env:TEST_USER_LOGIN="Admin"
$env:TEST_USER_PASSWORD="123"
$env:SUCCESS_URL_REGEX=".*monitoring/realtime\\?deptId=109&presetId=2.*"
.\.venv\Scripts\python -m pytest -m e2e --alluredir=allure-results
```

