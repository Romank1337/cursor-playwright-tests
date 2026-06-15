"""Update Confluence page 60806279 (UI-тесты) with short roadmap."""
from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request

PAGE_ID = "60806279"
BASE = "https://jira.zyfra.com/wiki"
TITLE = "UI-тесты"

BODY = """
<p>Подробная информация по UI-тестам находится <a href="https://jira.zyfra.com/wiki/pages/viewpage.action?pageId=44731139">тут</a>.</p>
<p><a href="https://docs.google.com/spreadsheets/d/1gBz2I7rh9GMCIJzJERKo9bXcd87pRWAo01GSIOkchSs/edit#gid=2091986316">План написания/актуализации</a></p>

<h2>Репозиторий и настройка окружения</h2>
<p>Автотесты: <a href="https://github.com/Romank1337/cursor-playwright-tests">cursor-playwright-tests</a> (pytest + Playwright, Python 3.12+).</p>
<p>Инструкция по установке и первому запуску: <a href="https://jira.zyfra.com/wiki/pages/viewpage.action?pageId=457946379">настройка окружения</a>.</p>
<p>Стенд: <code>https://localhost:8001</code>, тестовый вход <code>Admin</code> / <code>123</code> (переопределяется через <code>.env</code>).</p>

<h2>Что уже затронуто автоматизацией</h2>
<p><em>Состав сценариев в разработке — ниже зоны приложения, а не фиксированный список тест-кейсов.</em></p>
<ul>
<li><strong>Авторизация</strong> — форма входа, негативные попытки, язык, переход в приложение после логина.</li>
<li><strong>Справочники (Directories)</strong> — устройства, персонал, production units, роли работников: открытие раздела, формы, списки; изменение данных — под флагами <code>RUN_DESTRUCTIVE_*</code>.</li>
<li><strong>Параметры оборудования</strong> (<code>/list/machineParams</code>) — состояния и параметры в гриде (DevExtreme).</li>
<li><strong>Мониторинг</strong> — пока только косвенно: проверяется редирект после успешного входа.</li>
</ul>
<p>Метаданные автотестов публикуются в Test IT MDC, namespace <strong>UI/Smoke</strong>.</p>

<h2>Roadmap (кратко)</h2>
<table><tbody>
<tr><th>Приоритет</th><th>Направление</th></tr>
<tr><td>P0</td><td>Стабилизация уже начатых разделов (machineParams, Parent в production units)</td></tr>
<tr><td>P1</td><td>Довести справочники до единого шаблона: smoke → форма → update → CRUD за флагом</td></tr>
<tr><td>P2</td><td>Smoke мониторинга (<code>/monitoring/realtime</code>)</td></tr>
<tr><td>P3</td><td>Другие вкладки <code>production-structure</code> и пункты меню Directories — по тому же шаблону</td></tr>
<tr><td>P4</td><td>CI/nightly на тестовом стенде, выгрузка результатов в Test IT</td></tr>
</tbody></table>

<h2>Единый подход к новым разделам</h2>
<ol>
<li>Разведка UI (<code>tools/probe_*.py</code>).</li>
<li>Page Object в <code>tests/pages/</code>.</li>
<li>Smoke открытия → проверка формы/списка → при необходимости destructive CRUD через env.</li>
</ol>
<p><em>Обновлено: 2026-06.</em></p>
"""


def _auth_header(user: str, password: str) -> str:
    import base64

    return "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode("ascii")


def _request(method: str, url: str, user: str, password: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"Authorization": _auth_header(user, password), "Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')[:2000]}") from exc


def main() -> None:
    user = os.getenv("JIRA_USER") or os.getenv("CONFLUENCE_USER")
    password = os.getenv("JIRA_PASS") or os.getenv("CONFLUENCE_PASS")
    if not user or not password:
        raise SystemExit("Set JIRA_USER and JIRA_PASS.")

    current = _request("GET", f"{BASE}/rest/api/content/{PAGE_ID}?expand=version", user, password)
    payload = {
        "id": PAGE_ID,
        "type": "page",
        "title": TITLE,
        "version": {"number": current["version"]["number"] + 1},
        "body": {"storage": {"value": BODY.strip(), "representation": "storage"}},
    }
    updated = _request("PUT", f"{BASE}/rest/api/content/{PAGE_ID}", user, password, payload)
    print(f"OK version={updated['version']['number']}")
    print(f"URL: {BASE}{updated['_links']['webui']}")


if __name__ == "__main__":
    main()
