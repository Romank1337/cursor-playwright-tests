"""Publish setup guide to Confluence page 457946379."""
from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.request

PAGE_ID = "457946379"
BASE = "https://jira.zyfra.com/wiki"
TITLE = (
    "Архитектура реализации запуска автотестов UI на первом этапе "
    "реализации автотестирования с использованием Cursor AI."
)

BODY = r"""
<h1>Настройка окружения для UI-автотестов Диспетчера с использованием Cursor AI</h1>

<h2>1. Назначение документа</h2>
<p>Документ описывает, как с нуля подготовить рабочее место для запуска UI-автотестов веб-приложения <strong>Диспетчер</strong>:</p>
<ul>
<li>что установить на компьютер;</li>
<li>как скачать репозиторий с тестами;</li>
<li>как настроить подключение к локальному стенду;</li>
<li>как проверить, что окружение собрано корректно;</li>
<li>как смотреть Allure-отчёты;</li>
<li>как (опционально) подключить Cursor IDE и Test IT.</li>
</ul>
<p>Документ <strong>не</strong> описывает сами тест-кейсы и сценарии проверок.</p>

<h2>2. Что входит в решение</h2>
<table><tbody>
<tr><th>Компонент</th><th>Назначение</th></tr>
<tr><td><strong>Локальный стенд Диспетчер</strong></td><td>Веб-приложение, против которого выполняются автотесты</td></tr>
<tr><td><strong>Репозиторий автотестов</strong></td><td>Python-проект на pytest + Playwright</td></tr>
<tr><td><strong>Python 3.12+</strong></td><td>Язык и среда выполнения тестов</td></tr>
<tr><td><strong>Playwright (Chromium)</strong></td><td>Управление браузером</td></tr>
<tr><td><strong>Cursor IDE</strong> (рекомендуется)</td><td>Редактор с AI-ассистентом для разработки и отладки тестов</td></tr>
<tr><td><strong>Allure CLI</strong> (опционально)</td><td>Просмотр HTML-отчётов</td></tr>
<tr><td><strong>Test IT</strong> (опционально)</td><td>Хранение метаданных автотестов в TMS MDC</td></tr>
</tbody></table>
<p>Стек проекта: <strong>pytest + Playwright (Python)</strong>. Node.js для запуска тестов <strong>не требуется</strong>.</p>

<h2>3. Требования к рабочему месту</h2>
<h3>3.1. Операционная система</h3>
<ul>
<li><strong>Windows 10/11</strong> (инструкция ниже для PowerShell);</li>
<li>либо Linux/macOS — команды аналогичны, отличаются пути к <code>python</code> и активации venv.</li>
</ul>

<h3>3.2. Обязательное ПО</h3>
<table><tbody>
<tr><th>ПО</th><th>Минимальная версия</th><th>Зачем</th></tr>
<tr><td><strong>Git</strong></td><td>2.x</td><td>Клонирование репозитория</td></tr>
<tr><td><strong>Python</strong></td><td>3.12+</td><td>Запуск pytest и Playwright</td></tr>
<tr><td><strong>Доступ к GitHub</strong></td><td>—</td><td>Репозиторий: <code>https://github.com/Romank1337/cursor-playwright-tests</code></td></tr>
</tbody></table>
<p>Проверка:</p>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">powershell</ac:parameter><ac:plain-text-body><![CDATA[git --version
python --version]]></ac:plain-text-body></ac:structured-macro>
<p>Ожидаемый вывод Python: <code>Python 3.12.x</code> или новее.</p>

<h3>3.3. Рекомендуемое ПО</h3>
<table><tbody>
<tr><th>ПО</th><th>Зачем</th></tr>
<tr><td><strong>Cursor</strong></td><td>IDE с AI для работы с кодом тестов (<a href="https://cursor.com">cursor.com</a>)</td></tr>
<tr><td><strong>Allure CLI</strong></td><td>Просмотр отчётов (<code>allure serve</code>)</td></tr>
<tr><td><strong>VPN / корпоративная сеть</strong></td><td>Если GitHub или Test IT доступны только изнутри сети</td></tr>
</tbody></table>

<h3>3.4. Локальный стенд Диспетчер</h3>
<p>Перед запуском автотестов должно быть <strong>запущено и доступно</strong> веб-приложение Диспетчер.</p>
<table><tbody>
<tr><th>Параметр</th><th>Значение по умолчанию в проекте</th></tr>
<tr><td>URL страницы входа</td><td><code>https://localhost:8001/user/login</code></td></tr>
<tr><td>Протокол</td><td><strong>HTTPS</strong> (самоподписанный сертификат)</td></tr>
<tr><td>Тестовый пользователь</td><td><code>Admin</code> / <code>123</code> (если не переопределено в <code>.env</code>)</td></tr>
</tbody></table>
<p>Типичный состав стенда:</p>
<ul>
<li><strong>server</strong> — backend;</li>
<li><strong>web-client</strong> — фронтенд (отдаёт UI на порту <strong>8001</strong>);</li>
<li>при необходимости <strong>IMP</strong> и другие сервисы — по внутренней документации команды разработки.</li>
</ul>
<ac:structured-macro ac:name="info" ac:schema-version="1"><ac:rich-text-body>
<p><strong>Важно:</strong> в старых версиях документа указывались порты <code>8000</code> / <code>8002</code>. Актуальный порт для UI-тестов этого репозитория — <strong>8001</strong>.</p>
</ac:rich-text-body></ac:structured-macro>
<p>Проверка доступности стенда — откройте в браузере:</p>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">text</ac:parameter><ac:plain-text-body><![CDATA[https://localhost:8001/user/login]]></ac:plain-text-body></ac:structured-macro>
<p>Должна открыться страница авторизации (браузер может предупредить о недоверенном сертификате — для локального стенда это нормально).</p>

<h2>4. Скачивание репозитория</h2>
<h3>4.1. Клонирование</h3>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">powershell</ac:parameter><ac:plain-text-body><![CDATA[cd C:\Projects
git clone https://github.com/Romank1337/cursor-playwright-tests.git
cd cursor-playwright-tests]]></ac:plain-text-body></ac:structured-macro>

<h3>4.2. Структура репозитория (ключевые файлы)</h3>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">text</ac:parameter><ac:plain-text-body><![CDATA[cursor-playwright-tests/
├── tests/                  # Код автотестов и Page Object'ы
├── tests/conftest.py       # Общие настройки: URL, креды, браузер
├── pytest.ini              # Настройки pytest
├── requirements.txt        # Python-зависимости
├── .env.example            # Шаблон переменных окружения
├── connection_config.ini.example  # Шаблон для Test IT (опционально)
├── README.md               # Краткая справка по проекту
├── allure-results/         # Создаётся после прогона (в .gitignore)
└── tools/                  # Вспомогательные скрипты (Test IT и отладка)]]></ac:plain-text-body></ac:structured-macro>

<h2>5. Создание Python-окружения</h2>
<p>Все команды выполняются <strong>из корня репозитория</strong>.</p>
<h3>5.1. Виртуальное окружение</h3>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">powershell</ac:parameter><ac:plain-text-body><![CDATA[python -m venv .venv]]></ac:plain-text-body></ac:structured-macro>
<h3>5.2. Активация venv</h3>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">powershell</ac:parameter><ac:plain-text-body><![CDATA[.\.venv\Scripts\Activate.ps1]]></ac:plain-text-body></ac:structured-macro>
<p>Если PowerShell блокирует скрипты:</p>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">powershell</ac:parameter><ac:plain-text-body><![CDATA[Set-ExecutionPolicy -Scope CurrentUser RemoteSigned]]></ac:plain-text-body></ac:structured-macro>
<p>После активации в начале строки терминала появится <code>(.venv)</code>.</p>
<h3>5.3. Установка зависимостей</h3>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">powershell</ac:parameter><ac:plain-text-body><![CDATA[python -m pip install --upgrade pip
python -m pip install -r requirements.txt]]></ac:plain-text-body></ac:structured-macro>
<p>Устанавливаются: <code>pytest</code>, <code>playwright</code>, <code>pytest-playwright</code>, <code>allure-pytest</code>, <code>testit-adapter-pytest</code>.</p>

<h2>6. Установка браузеров Playwright</h2>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">powershell</ac:parameter><ac:plain-text-body><![CDATA[python -m playwright install]]></ac:plain-text-body></ac:structured-macro>
<p>Для проекта используется <strong>Chromium</strong>. Только Chromium:</p>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">powershell</ac:parameter><ac:plain-text-body><![CDATA[python -m playwright install chromium]]></ac:plain-text-body></ac:structured-macro>

<h2>7. Настройка переменных окружения</h2>
<h3>7.1. Создание файла .env</h3>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">powershell</ac:parameter><ac:plain-text-body><![CDATA[copy .env.example .env]]></ac:plain-text-body></ac:structured-macro>
<p>Файл <code>.env</code> <strong>не коммитится</strong> в git.</p>
<h3>7.2. Основные параметры</h3>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">ini</ac:parameter><ac:plain-text-body><![CDATA[# --- Стенд приложения ---
LOGIN_URL=https://localhost:8001/user/login
TEST_USER_LOGIN=Admin
TEST_USER_PASSWORD=123

# --- Деструктивные сценарии (создание/удаление данных) ---
RUN_DESTRUCTIVE_DEVICES_CRUD=false
RUN_DESTRUCTIVE_PERSONNEL_CRUD=false
RUN_DESTRUCTIVE_PRODUCTION_UNITS_CRUD=false]]></ac:plain-text-body></ac:structured-macro>
<h3>7.3. Дополнительные URL</h3>
<table><tbody>
<tr><th>Переменная</th><th>По умолчанию</th></tr>
<tr><td><code>MACHINE_PARAMS_URL</code></td><td><code>https://localhost:8001/list/machineParams</code></td></tr>
<tr><td><code>ROLES_URL</code></td><td><code>https://localhost:8001/list/workerRoles</code></td></tr>
<tr><td><code>SUCCESS_URL_REGEX</code></td><td>regex URL после успешного входа</td></tr>
</tbody></table>
<h3>7.4. Передача переменных в PowerShell</h3>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">powershell</ac:parameter><ac:plain-text-body><![CDATA[$env:LOGIN_URL = "https://localhost:8001/user/login"
$env:TEST_USER_LOGIN = "Admin"
$env:TEST_USER_PASSWORD = "123"]]></ac:plain-text-body></ac:structured-macro>
<h3>7.5. HTTPS и самоподписанный сертификат</h3>
<p>В <code>tests/conftest.py</code> для браузера включено <code>ignore_https_errors = True</code> — это позволяет работать с локальным <code>https://localhost:8001</code> без ручной настройки сертификатов в Playwright.</p>

<h2>8. Проверка, что окружение собрано корректно</h2>
<h3>8.1. Проверка Python-пакетов</h3>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">powershell</ac:parameter><ac:plain-text-body><![CDATA[python -c "import pytest, playwright; print('pytest', pytest.__version__)"
python -m playwright --version]]></ac:plain-text-body></ac:structured-macro>
<h3>8.2. Проверка, что pytest видит тесты</h3>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">powershell</ac:parameter><ac:plain-text-body><![CDATA[python -m pytest --collect-only -q]]></ac:plain-text-body></ac:structured-macro>
<h3>8.3. Проверка доступности стенда</h3>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">powershell</ac:parameter><ac:plain-text-body><![CDATA[curl.exe -k -s -o NUL -w "HTTP %{http_code}`n" https://localhost:8001/user/login]]></ac:plain-text-body></ac:structured-macro>
<h3>8.4. Минимальный smoke-запуск</h3>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">powershell</ac:parameter><ac:plain-text-body><![CDATA[python -m pytest tests/test_login_ui.py -q]]></ac:plain-text-body></ac:structured-macro>

<h2>9. Allure-отчёты</h2>
<h3>9.1. Генерация результатов</h3>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">powershell</ac:parameter><ac:plain-text-body><![CDATA[python -m pytest --alluredir=allure-results]]></ac:plain-text-body></ac:structured-macro>
<h3>9.2. Установка Allure CLI (Windows)</h3>
<p>Scoop: <code>scoop install allure</code>. Chocolatey: <code>choco install allurecommandline</code>.</p>
<h3>9.3. Просмотр отчёта</h3>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">powershell</ac:parameter><ac:plain-text-body><![CDATA[allure serve allure-results]]></ac:plain-text-body></ac:structured-macro>

<h2>10. Настройка Cursor IDE</h2>
<ol>
<li>Скачайте Cursor с <a href="https://cursor.com">cursor.com</a> и войдите в аккаунт.</li>
<li><strong>File → Open Folder</strong> — выберите папку <code>cursor-playwright-tests</code>.</li>
<li><code>Ctrl+Shift+P</code> → <strong>Python: Select Interpreter</strong> → <code>.\.venv\Scripts\python.exe</code>.</li>
<li>В терминале Cursor активируйте venv: <code>.\.venv\Scripts\Activate.ps1</code>.</li>
</ol>
<ac:structured-macro ac:name="note" ac:schema-version="1"><ac:rich-text-body>
<p><strong>Playwright MCP не является обязательным</strong> для работы этого репозитория. Тесты запускаются через <code>pytest</code> напрямую. MCP — опциональный инструмент интерактивной разведки UI в чате Cursor.</p>
</ac:rich-text-body></ac:structured-macro>

<h2>11. Интеграция с Test IT (опционально)</h2>
<ol>
<li>Получите API-токен: Test IT → профиль → API-ключи.</li>
<li>Заполните <code>.env</code> или <code>connection_config.ini</code> (см. <code>.env.example</code>).</li>
<li>Опубликуйте метаданные автотестов: <code>.\tools\testit_publish_ui_smoke.ps1 -Token "&lt;токен&gt;"</code>.</li>
</ol>
<p>Подробности — в <code>README.md</code> репозитория, раздел «Интеграция с Test IT».</p>

<h2>12. Типичные проблемы</h2>
<table><tbody>
<tr><th>Симптом</th><th>Причина</th><th>Решение</th></tr>
<tr><td><code>Connection refused</code></td><td>Стенд не запущен</td><td>Запустите server + web-client</td></tr>
<tr><td><code>Executable doesn't exist</code></td><td>Нет браузеров Playwright</td><td><code>python -m playwright install</code></td></tr>
<tr><td><code>ModuleNotFoundError</code></td><td>venv не активирован</td><td><code>.\.venv\Scripts\Activate.ps1</code></td></tr>
<tr><td>SSL errors</td><td>Самоподписанный сертификат</td><td>Проверьте URL: <code>https://localhost:8001</code></td></tr>
<tr><td><code>allure</code> не найдена</td><td>CLI не установлен</td><td>Scoop / Chocolatey</td></tr>
<tr><td>GitHub недоступен</td><td>Нет VPN</td><td>Подключите корпоративную сеть</td></tr>
</tbody></table>

<h2>13. Чек-лист «окружение готово»</h2>
<ac:structured-macro ac:name="code" ac:schema-version="1"><ac:parameter ac:name="language">text</ac:parameter><ac:plain-text-body><![CDATA[ ] Python 3.12+ установлен
[ ] Git установлен
[ ] Репозиторий склонирован
[ ] .venv создан, зависимости установлены
[ ] python -m playwright install выполнен
[ ] Диспетчер доступен по https://localhost:8001/user/login
[ ] .env создан или переменные экспортированы
[ ] python -m pytest --collect-only проходит без ошибок
[ ] (Опционально) Allure CLI установлен
[ ] (Опционально) Cursor открывает проект с .venv]]></ac:plain-text-body></ac:structured-macro>

<h2>14. Полезные ссылки</h2>
<table><tbody>
<tr><th>Ресурс</th><th>URL</th></tr>
<tr><td>Репозиторий автотестов</td><td><a href="https://github.com/Romank1337/cursor-playwright-tests">github.com/Romank1337/cursor-playwright-tests</a></td></tr>
<tr><td>Локальный стенд (login)</td><td><a href="https://localhost:8001/user/login">https://localhost:8001/user/login</a></td></tr>
<tr><td>Test IT (проект MDC)</td><td><a href="https://testit.zyfra.com/projects/3117">testit.zyfra.com/projects/3117</a></td></tr>
<tr><td>Playwright (Python)</td><td><a href="https://playwright.dev/python/">playwright.dev/python</a></td></tr>
<tr><td>pytest</td><td><a href="https://docs.pytest.org/">docs.pytest.org</a></td></tr>
</tbody></table>
<p><em>Версия документа: 2026-06. Обновление: команда MDC QA.</em></p>
"""


def _auth_header(user: str, password: str) -> str:
    import base64

    token = base64.b64encode(f"{user}:{password}".encode()).decode("ascii")
    return f"Basic {token}"


def _request(method: str, url: str, user: str, password: str, payload: dict | None = None) -> dict:
    data = None
    headers = {
        "Authorization": _auth_header(user, password),
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {body[:2000]}") from exc


def main() -> None:
    user = os.getenv("JIRA_USER") or os.getenv("CONFLUENCE_USER")
    password = os.getenv("JIRA_PASS") or os.getenv("CONFLUENCE_PASS")
    if not user or not password:
        raise SystemExit(
            "Set JIRA_USER and JIRA_PASS (or CONFLUENCE_USER / CONFLUENCE_PASS) environment variables."
        )

    current = _request(
        "GET",
        f"{BASE}/rest/api/content/{PAGE_ID}?expand=version,space",
        user,
        password,
    )
    version = current["version"]["number"] + 1
    payload = {
        "id": PAGE_ID,
        "type": "page",
        "title": TITLE,
        "version": {"number": version},
        "body": {
            "storage": {
                "value": BODY.strip(),
                "representation": "storage",
            }
        },
    }
    updated = _request(
        "PUT",
        f"{BASE}/rest/api/content/{PAGE_ID}",
        user,
        password,
        payload,
    )
    webui = updated.get("_links", {}).get("webui", "")
    print(f"OK version={updated['version']['number']}")
    print(f"URL: {BASE}{webui}")


if __name__ == "__main__":
    main()
