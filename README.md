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

## Интеграция с Test IT (testit.zyfra.com → проект MDC)

Тесты подготовлены к выгрузке в Test IT через адаптер
[`testit-adapter-pytest`](https://pypi.org/project/testit-adapter-pytest/).

### Куда попадут тесты

- Инстанс: `https://testit.zyfra.com`
- Проект: **MDC** (globalId `3117`, GUID `4974a48f-041b-44ac-a42e-ebab5bb3a74b`)
- Namespace: **UI/Smoke** (рядом с уже существующим `API/Smoke`)

В дереве автотестов MDC появится узел `UI → Smoke`, в который попадут
все 22 UI-теста этого репо.

### Что уже сделано в коде

- `requirements.txt` содержит `testit-adapter-pytest`.
- Каждому тесту проставлены декораторы:
  - `@testit.nameSpace("UI/Smoke")` + `@testit.className("<Module>")` — формат
    как у существующего `API/Smoke` в MDC (namespace со слешем, classname —
    подгруппа: `Login`, `Devices`, `Personnel`, `ProductionUnits`).
  - `@testit.externalId("ui.<модуль>.<сценарий>")` — стабильный ID, не ломается при переименовании.
  - `@testit.displayName(...)` — человекочитаемое имя в TMS.
- `tests/testit_compat.py` — безопасный shim: если `testit` не установлен,
  декораторы становятся no-op, и обычный pytest-прогон продолжает работать.
- `connection_config.ini.example` — шаблон конфига с уже подставленным `projectId` MDC.
- `.env.example` — шаблон env-переменных с уже подставленными `TMS_URL` и `TMS_PROJECT_ID`.
- `.gitignore` исключает `connection_config.ini` и `.env` — privateToken не попадёт в коммит.

### Важно: про testit-adapter-pytest и этот сервер

На `testit.zyfra.com` версии pip-пакета `testit-api-client` несовместимы со
схемой сервера (поле `isFlakyAuto` есть, `workItemsCount` нет — между
`7.5.5.post570` и `7.5.6`/`7.5.10`). Поэтому `pytest --testit` падает на
старте при десериализации проекта.

Обходной путь, который реально работает на этом TMS, — **прямой publisher
через REST API v2**, см. `tools/testit_publish_ui_smoke.ps1`. Он:

- читает 22 автотеста из `tools/testit_ui_smoke_autotests.json`,
- создаёт/обновляет каждый через `POST/PUT /api/v2/autoTests`,
- идемпотентен (повторный запуск только обновит без дублей),
- не зависит от версии pip-клиента.

Запуск:

```powershell
.\tools\testit_publish_ui_smoke.ps1 -Token "<твой_токен>"
```

После этого по адресу
`https://testit.zyfra.com/projects/3117/autotests?type=Namespace&namespace=UI/Smoke`
видны все 22 теста, разнесённые по подгруппам Login/Devices/Personnel/ProductionUnits.

> Результаты прогона (passed/failed/durations) этот publisher НЕ заливает —
> только определения автотестов. Если потребуется ещё и заливать результаты,
> можно расширить publisher: создать TestRun, потом POST `/api/v2/testResults`
> по каждому автотесту. Сейчас этого не делаем намеренно (нет блокера).

### Шаг 1 — установить адаптер (опционально)

Адаптер `testit-adapter-pytest` оставлен в `requirements.txt` — он будет
работать на других инстансах Test IT, где совпадает версия схемы. На
текущем стенде используется publisher выше.

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

### Шаг 2 — получить privateToken

В `https://testit.zyfra.com` → клик по своему имени в шапке → Профиль → API-ключи →
Сгенерировать. Скопируй токен сразу — после закрытия диалога он не покажется.

### Шаг 2.5 — (опционально) сразу создать namespace UI/Smoke в TMS

Если хочешь, чтобы узел `UI/Smoke` появился в дереве автотестов MDC ещё до
полного pytest-прогона, выполни одну команду:

```powershell
.\tools\testit_create_ui_smoke.ps1 -Token "<твой_токен>"
```

Скрипт создаст один автотест-плейсхолдер с `namespace=UI`, `classname=Smoke`.
Сразу после этого по адресу
`https://testit.zyfra.com/projects/3117/autotests?type=Namespace&namespace=UI/Smoke`
будет виден узел `UI / Smoke`. После полного прогона `pytest --testit` туда
добавятся все 22 настоящих теста; плейсхолдер можно удалить руками в TMS.

### Шаг 3 — узнать `configurationId` для проекта MDC

Готовый скрипт PowerShell. Вставь свой токен и запусти; он выведет список
конфигураций MDC с их GUID-ами:

```powershell
$env:TMS_URL = "https://testit.zyfra.com"
$env:TMS_PRIVATE_TOKEN = "<your_token>"
$projectId = "4974a48f-041b-44ac-a42e-ebab5bb3a74b"

# обход self-signed/устаревших ssl на корп-сети
add-type @"
using System.Net;
using System.Security.Cryptography.X509Certificates;
public class TrustAllCertsPolicy : ICertificatePolicy {
  public bool CheckValidationResult(ServicePoint sp, X509Certificate c, WebRequest r, int p) { return true; }
}
"@ -ErrorAction SilentlyContinue
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12

Invoke-RestMethod -Uri "$env:TMS_URL/api/v2/projects/$projectId/configurations" `
  -Headers @{Authorization = "PrivateToken $env:TMS_PRIVATE_TOKEN"} -Method GET |
  Select-Object id, name, isDefault, isActive | Format-Table -AutoSize
```

Возьми GUID из колонки `id` для нужной конфигурации (обычно `Default` /
`UI / Chromium` / т.п.) и подставь в `TMS_CONFIGURATION_ID`.

### Шаг 4 — прогон с отправкой результатов

```powershell
$env:TMS_URL = "https://testit.zyfra.com"
$env:TMS_PRIVATE_TOKEN = "<your_token>"
$env:TMS_PROJECT_ID = "4974a48f-041b-44ac-a42e-ebab5bb3a74b"
$env:TMS_CONFIGURATION_ID = "<guid_из_шага_3>"
$env:TMS_TEST_RUN_ID = ""   # пусто = адаптер сам создаст TestRun

.\.venv\Scripts\python -m pytest tests/ -v --testit --alluredir=allure-results
```

После прогона в `https://testit.zyfra.com/projects/3117/autotests?type=Namespace&namespace=UI/Smoke`
появятся все 22 теста, привязанные к свежесозданному TestRun (или к указанному `TMS_TEST_RUN_ID`).

### Идентификаторы автотестов

`externalId` стабилен при переименовании pytest-функций:

- `ui.login.page_opened`, `ui.login.success_redirect`, `ui.login.password_field_type`, …
- `ui.devices.page_opened`, `ui.devices.full_crud_destructive_flagged`, …
- `ui.production_units.page_opened`, `ui.production_units.update_name_after_create`, …
- `ui.personnel.full_crud_destructive_flagged`

Если у теста уже есть Work Item в TMS — добавь к нему ещё один декоратор:

```python
@testit.workItemIds("12345")
```

